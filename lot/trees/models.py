import os
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.simplejson import dumps
from django.conf import settings
from madrona.features.models import PolygonFeature, FeatureCollection
from madrona.features import register, alternate
from madrona.async.ProcessHandler import check_status_or_begin, get_process_status

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
    imputed_elevation = models.FloatField(null=True, blank=True, editable=False)

    class Options:
        form = "lot.trees.forms.StandForm"
        manipulators = []
        links = (
            alternate('GeoJSON',
                'trees.views.geojson_stands',  
                type="application/json",
                select='multiple single'),
        )

    @property
    def status(self):
        status = {}
        for raster in settings.IMPUTE_RASTERS:
            name = "imputed_%s" % raster[0]
            url = "%s%s" % (self.get_absolute_url(), name)
            async_status = get_process_status(polling_url=url)
            if self.__dict__[name] is not None:
                status[name] = "COMPLETED"
            elif async_status is not None:
                # STARTED, PENDING, SUCCESS, FAILURE, RETRY, REVOKED
                # custom: RASTERNOTFOUND, ZONALNULL
                status[name] = async_status
            else:
                status[name] = "NOTSTARTED"
        return status

    def _impute(self, force=False, preclean=True, limit_to=None):
        '''
        preclean: if True, will wipe out the old stored value before firing the process
        limit_to: list of rasters to (re)impute
        force: if True, bypass the zonal_stats cache
        '''
        from trees.tasks import impute
        for raster in settings.IMPUTE_RASTERS:
            if limit_to and raster[0] in limit_to:
                continue
            name = "imputed_%s" % raster[0]
            url = "%s%s" % (self.get_absolute_url(), name)
            if preclean:
                self.__dict__[name] = None
                self.save(impute=False)
            status, task_id = check_status_or_begin(impute, 
                    task_args=(self.uid,raster[0],raster[1],force), 
                    polling_url=url)

    def save(self, *args, **kwargs):
        """
        stand.save(impute=True, force=False) <- default; impute only if update is needed
        stand.save(impute=True, force=True) <- will force redo of all imputations
        stand.save(impute=False) <- don't trigger async impute routines, just save the model
        """
        impute = kwargs.pop('impute', True)
        force = kwargs.pop('force', False)
        if self.pk is not None:
            # modifying an existing feature
            orig = Stand.objects.get(pk=self.pk)
            geom_fields = [f for f in Stand._meta.fields if f.attname.startswith('geometry_')]
            same_geom = True  # assume geometries have NOT changed
            for f in geom_fields:
                # Is original value different from form value?
                if orig._get_FIELD_display(f) != self._get_FIELD_display(f):
                    same_geom = False

            all_imputes_done = True  # assume they are all complete
            for raster in settings.IMPUTE_RASTERS:
                name = "imputed_%s" % raster[0]
                if self.__dict__[name] is None:
                    all_imputes_done = False
                    break

            # If geom is the same and all imputed fields are completed, don't reimpute unless force=True 
            if same_geom and all_imputes_done and not force:
                impute = False

        super(Stand, self).save(*args, **kwargs)

        if impute:
            self._impute(force=force)

    @property
    def complete(self):
        if self.rx == '--':
            return False
        if self.domspp == '--':
            return False
        return True

    @property
    def geojson(self):
        d = {'uid': self.uid,
             'name': self.name,
             'date_modified': str(self.date_modified),
             'rx': self.get_rx_display(),
             'domspp': self.get_domspp_display() }

        j = """{ 
              "type": "Feature",
              "geometry": %s,
              "properties": %s 
}""" % (self.geometry_final.json, dumps(d))

        return j

@register
class ForestProperty(FeatureCollection):
    # defaults to the approx extent (in mercator) of our study region
    minx = models.IntegerField(default=settings.DEFAULT_EXTENT[0])
    miny = models.IntegerField(default=settings.DEFAULT_EXTENT[1])
    maxx = models.IntegerField(default=settings.DEFAULT_EXTENT[2])
    maxy = models.IntegerField(default=settings.DEFAULT_EXTENT[3])

    @property
    def bbox(self):
        return (self.minx, self.miny, self.maxx, self.maxy)

    def set_bbox(self, bbox):
        if len(bbox) != 4:
            raise Exception("BBOX must be a 4-item list/tuple with minx,miny,maxx,maxy")
        self.minx, self.miny, self.maxx, self.maxy = bbox
        self.save()

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

    @property
    def geojson(self):
        featxt = ', '.join([i.geojson for i in self.feature_set()])
        return """{ "type": "FeatureCollection",
        "features": [
        %s
        ]}""" % featxt

    class Options:
        valid_children = ('lot.trees.models.Stand',)
        form = "lot.trees.forms.PropertyForm"
        links = (
            alternate('Property GeoJSON',
                'trees.views.geojson_forestproperty',  
                type="application/json",
                select='single'),
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

def run():
    verbose = True

    parcel_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/landowner_demo/merc/Parcels.shp'))
    for p in Parcel.objects.all():
        p.delete()
    map1 = LayerMapping(Parcel, parcel_shp, parcel_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=verbose)

    streambuffer_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/landowner_demo/merc/stream_buffer_clip.shp'))
    for sb in StreamBuffer.objects.all():
        sb.delete()
    map2 = LayerMapping(StreamBuffer, streambuffer_shp, streambuffer_mapping, transform=False, encoding='iso-8859-1')
    map2.save(strict=True, verbose=verbose)

def import_stands():
    stands_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/sixes/sixes_stands_3857b.shp'))
    for s in Stand.objects.all():
        s.delete()
    map1 = LayerMapping(Stand, stands_shp, stand_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=True)
