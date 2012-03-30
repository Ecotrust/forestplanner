import os
import math
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.simplejson import dumps
from django.conf import settings
from madrona.features.models import PolygonFeature, FeatureCollection
from madrona.features import register, alternate
from madrona.raster_stats.models import RasterDataset, zonal_stats
from madrona.common.utils import get_logger
logger = get_logger()

def try_get(model, **kwargs):
    """
    Like model.objects.get(..) but returns None instead of DoesNotExist
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

@register
class Stand(PolygonFeature):
    RX_CHOICES = (
        ('--', '--'),
        ('CC', 'Clearcut'),
        ('SW', 'Shelterwood'),
    )
    SPP_CHOICES = (
        ('--', '--'),
        ('DF', 'Douglas Fir'),
        ('MH', 'Mountain Hemlock'),
    )
    rx = models.CharField(max_length=2, choices=RX_CHOICES, 
            verbose_name="Presciption", default="--")
    domspp = models.CharField(max_length=2, choices=SPP_CHOICES, 
            verbose_name="Dominant Species", default="--")

    class Options:
        form = "trees.forms.StandForm"
        manipulators = []
        links = (
            # Link to grab stand geojson 
            alternate('GeoJSON',
                'trees.views.geojson_features',  
                type="application/json",
                select='multiple single'),
        )

    @property
    def geojson(self):
        '''
        Couldn't find any serialization methods flexible enough for our needs
        So we do it the hard way.
        '''
        d = {
                'uid': self.uid,
                'name': self.name,
                'rx': self.rx,
                'domspp': self.domspp,
                'elevation': self.imputed_elevation,
                'aspect': self.imputed_aspect,
                'gnn': self.imputed_gnn,
                'slope': self.imputed_slope,
                'user_id': self.user.pk,
                'date_modified': str(self.date_modified),
                'date_created': str(self.date_created),
            }
        gj = """{ 
              "type": "Feature",
              "geometry": %s,
              "properties": %s 
        }""" % (self.geometry_final.json, dumps(d))
        return gj

    @property
    def imputed_elevation(self):
        elevation_raster = try_get(RasterDataset, name="elevation")
        data = try_get(ImputedData, raster=elevation_raster, feature=self)
        if data:
            return data.val

    @property
    def imputed_aspect(self):
        cos_raster = try_get(RasterDataset, name="cos_aspect")
        sin_raster = try_get(RasterDataset, name="sin_aspect")
        cos_sum = try_get(ImputedData, raster=cos_raster, feature=self)
        sin_sum = try_get(ImputedData, raster=sin_raster, feature=self)
        result = None
        if cos_sum and sin_sum and cos_sum.val and sin_sum.val:
            avg_aspect_rad = math.atan2(cos_sum.val, sin_sum.val)
            result = math.degrees(avg_aspect_rad)
        return result

    @property
    def imputed_slope(self):
        slope_raster = try_get(RasterDataset, name="slope")
        data = try_get(ImputedData, raster=slope_raster, feature=self)
        if data:
            return data.val

    @property
    def imputed_gnn(self):
        gnn_raster = try_get(RasterDataset, name="gnn")
        data = try_get(ImputedData, raster=gnn_raster, feature=self)
        if data:
            return data.val

    @property
    def imputed(self):
        return {'aspect': self.imputed_aspect, 
                'elevation': self.imputed_elevation, 
                'slope': self.imputed_slope,
                'gnn': self.imputed_gnn,
               }

    def _impute(self, force=False, limit_to=None, async=False):
        '''
        limit_to: list of rasters to (re)impute
        force: if True, bypass the zonal_stats cache
        '''
        for rname, rproj in settings.IMPUTE_RASTERS:
            if limit_to and raster[0] not in limit_to:
                continue

            orig_geom = self.geometry_final
            if rproj:
                geom = orig_geom.transform(rproj, clone=True)

            result = None
            try:
                raster = RasterDataset.objects.get(name=rname)
            except RasterDataset.DoesNotExist:
                continue

            if not raster.is_valid:
                raise Exception(raster.filepath + " is not a valid rasterdataset")

            if force:
                stats = zonal_stats(geom, raster, read_cache = False)
            else:
                stats = zonal_stats(geom, raster)
            
            if rname in ['cos_aspect','sin_aspect']:  # aspect trig is special case
                result = stats.sum
            elif rname in ['gnn']: # gnn, we want the most common value
                # may need to do something fancier here like store multiple categories
                result = stats.mode
            else:
                result = stats.avg

            # cache result
            imputed_data, created = ImputedData.objects.get_or_create(raster=raster, feature=self) 
            imputed_data.val = result 
            imputed_data.save()


    def save(self, *args, **kwargs):
        """
        stand.save(impute=True, force=False) <- default; impute only if update is needed
        stand.save(impute=True, force=True) <- will force redo of all imputations
        stand.save(impute=False) <- don't trigger async impute routines, just save the model
        """
        impute = kwargs.pop('impute', True)
        force = kwargs.pop('force', False)
        async = kwargs.pop('async', False)

        if self.pk:
            # modifying an existing feature
            orig = Stand.objects.get(pk=self.pk)
            geom_fields = [f for f in Stand._meta.fields if f.attname.startswith('geometry_')]
            same_geom = True  # assume geometries have NOT changed
            for f in geom_fields:
                # Is original value different from form value?
                if orig._get_FIELD_display(f) != self._get_FIELD_display(f):
                    same_geom = False

            all_imputes_done = None not in self.imputed.values()

            # If geom is the same and all imputed fields are completed, don't reimpute unless force=True 
            if same_geom and all_imputes_done and not force:
                impute = False

        super(Stand, self).save(*args, **kwargs)

        if impute:
            self._impute(force=force, async=async)

    @property
    def is_complete(self):
        if self.rx == '--':
            return False
        if self.domspp == '--':
            return False
        for k,v in self.imputed.iteritems():
            if v is None:
                return False
        return True

class ImputedData(models.Model):
    raster = models.ForeignKey(RasterDataset)
    feature = models.ForeignKey(Stand)
    val = models.FloatField(null=True, blank=True)

@register
class ForestProperty(FeatureCollection):
    geometry_final = models.PolygonField(srid=settings.GEOMETRY_DB_SRID, 
            verbose_name="Stand Polygon Geometry")

    @property
    def geojson(self):
        '''
        Couldn't find any serialization methods flexible enough for our needs
        So we do it the hard way.
        '''
        d = {
                'uid': self.uid,
                'name': self.name,
                'user_id': self.user.pk,
                'acres': self.acres,
                'location': self.location,
                'bbox': self.bbox,
                'date_modified': str(self.date_modified),
                'date_created': str(self.date_created),
            }
        try:
            geom_json = self.geometry_final.json
        except AttributeError:
            geom_json = 'null'

        gj = """{ 
              "type": "Feature",
              "geometry": %s,
              "properties": %s 
        }""" % (geom_json, dumps(d))
        return gj

    @property
    def acres(self):
        try:
            area_m = self.geometry_final.area 
        except:
            return None
        conversion = 0.000247105381 
        area_acres = area_m * conversion
        return area_acres

    @property
    def location(self):
        '''
        Returns: (CountyName, State)
        '''
        geom = self.geometry_final
        counties = County.objects.filter(geom__bboverlaps=geom)

        the_size = 0
        the_county = (None, None)
        for county in counties:
            county_geom = county.geom
            if not county_geom.valid:
                county_geom = county_geom.buffer(0)
            if county_geom.intersects(geom):
                overlap = county_geom.intersection(geom)
                area = overlap.area
                if area > the_size:
                    the_size = area
                    the_county = (county.cntyname, county.stname)
        return the_county


    def feature_set_geojson(self):
        # We'll use the bbox for the property geom itself
        # Instead of using the overall bbox of the stands  
        # Assumption is that property boundary SHOULD contain all stands
        # and, if not, they should expand the property boundary
        bb = self.bbox  
        featxt = ', '.join([i.geojson for i in self.feature_set()])
        return """{ "type": "FeatureCollection",
        "bbox": [%f, %f, %f, %f],
        "features": [
        %s
        ]}""" % (bb[0], bb[1], bb[2], bb[3], featxt)

    @property
    def bbox(self):
        try:
            return self.geometry_final.extent
        except AttributeError:
            return settings.DEFAULT_EXTENT

    @property
    def file_dir(self):
        '''
        Standard property for determining where supporting files reside
        /feature_file_root/database_name/feature_uid/
        '''
        root = settings.FEATURE_FILE_ROOT
        try:
            dbname = settings.DATABASES['default']['NAME']
        except:
            dbname = settings.DATABASE_NAME

        path = os.path.realpath(os.path.join(root, dbname, self.uid))
        if not os.path.exists(path):
            os.makedirs(path)

        if not os.access(path, os.W_OK):
            raise Exception("Feature file_dir %s is not writeable" % path)

        return path


    def adjacency(self, threshold=1.0):
        from trees.utils import calculate_adjacency
        stands = Stand.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk
        )
        return calculate_adjacency(stands, threshold)


    class Options:
        valid_children = ('trees.models.Stand',)
        form = "trees.forms.PropertyForm"
        links = (
            # Link to grab ALL *stands* associated with a property
            alternate('Property Stands GeoJSON',
                'trees.views.geojson_forestproperty',  
                type="application/json",
                select='single'),
            # Link to grab property geojson 
            alternate('GeoJSON',
                'trees.views.geojson_features',  
                type="application/json",
                select='multiple single'),
        )

class Parcel(models.Model):
    apn = models.CharField(max_length=40)
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

class StreamBuffer(models.Model):
    area = models.FloatField()
    perimeter = models.FloatField()
    str_buf_field = models.IntegerField()
    str_buf_id = models.IntegerField()
    inside = models.IntegerField()
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

class County(models.Model):
    fips = models.IntegerField()
    cntyname = models.CharField(max_length=23)
    polytype = models.IntegerField()
    stname = models.CharField(max_length=2)
    soc_cnty = models.IntegerField()
    cnty_fips= models.IntegerField()
    st_fips = models.IntegerField()
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

county_mapping = {
        'fips': 'FIPS',
        'cntyname': 'CNTYNAME',
        'polytype': 'POLYTYPE', 
        'stname': 'STNAME',
        'soc_cnty': 'SOC_CNTY',
        'cnty_fips': 'CNTY_FIPS',
        'st_fips': 'ST_FIPS',
        'geom': 'MULTIPOLYGON'
    }

stand_mapping = {
    'name': 'STAND_TEXT',
    'geometry_final': 'POLYGON',
    'geometry_original': 'POLYGON'
}

# Auto-generated `LayerMapping` dictionary for Parcel model
parcel_mapping = {
    'apn' : 'APN',
    'geom' : 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for StreamBuffer model
streambuffer_mapping = {
    'area' : 'AREA',
    'perimeter' : 'PERIMETER',
    'str_buf_field' : 'STR_BUF_',
    'str_buf_id' : 'STR_BUF_ID',
    'inside' : 'INSIDE',
    'geom' : 'MULTIPOLYGON',
}

def example_mapping():
    parcel_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/landowner_demo/merc/Parcels.shp'))
    map1 = LayerMapping(Parcel, parcel_shp, parcel_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=verbose)
