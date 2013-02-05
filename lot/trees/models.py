#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import math
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.simplejson import dumps, loads
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.analysistools.models import Analysis
from madrona.features import register, alternate
from madrona.raster_stats.models import RasterDataset, zonal_stats
from madrona.common.utils import get_logger
from operator import itemgetter
from django.core.cache import cache
from django.contrib.gis.geos import GEOSGeometry

logger = get_logger()

def cachemethod(cache_key, timeout=60*60*24*7):
    '''
    http://djangosnippets.org/snippets/1130/    
    default timeout = 1 week

    @property
    @cachemethod("SomeClass_get_some_result_%(id)s")
    '''
    def paramed_decorator(func):
        def decorated(self, *args):
            key = cache_key % self.__dict__
            res = cache.get(key)
            if res == None:
                res = func(self, *args)
                cache.set(key, res, timeout)
            return res
        return decorated 
    return paramed_decorator

# TODO: make this a model?
RX_CHOICES = (
    ('--', '--'),
    ('RE', 'Reserve; No Action'),
    ('RG', 'Riparian Grow Only'),
    ('UG', 'Uneven-aged Group Selection'),
    ('SW', 'Shelterwood'),
    ('CT', 'Commercial Thinning'),
    ('CC', 'Even-aged Clearcut'),
)

@register
class Stand(PolygonFeature):
    strata = models.ForeignKey("Strata", blank=True, default=None, null=True)
    cond_id = models.BigIntegerField(blank=True, null=True, default=None)

    class Options:
        form = "trees.forms.StandForm"
        manipulators = []

    def get_idb_cond(self):
        from trees.plots import get_nearest_neighbors
        if not self.cond_id:
            stand_list = self.strata.stand_list 
            site_cond = {
                'calc_aspect': self.imputed_aspect,
                'elev_ft': self.imputed_elevation, 
                'latitude_fuzz': self.geometry_final.centroid[0],
                'longitude_fuzz': self.geometry_final.centroid[1],
                'calc_slope': self.imputed_slope,
            }
            weight_dict = self.default_weighting
            ps, num_candidates = get_nearest_neighbors(site_cond, stand_list, weight_dict, k=5)
            self.cond_id = ps[0].name
            self.save()
        idb = IdbSummary.objects.get(id=self.cond_id) # TODO handle missing/bad cond_id
        return idb

    @property
    def default_weighting(self):
        return {
            'TOTAL_PCTBA': 5,
        }

    @property
    def acres(self):
        g2 = self.geometry_final.transform(settings.EQUAL_AREA_SRID, clone=True)
        try:
            area_m = g2.area 
        except:
            return None
        return area_m * settings.EQUAL_AREA_ACRES_CONVERSION

    #@property
    @cachemethod("Stand_%(id)s_geojson")
    def geojson(self, srid=None):
        '''
        Couldn't find any serialization methods flexible enough for our needs
        So we do it the hard way.
        '''
        from trees.utils import classify_aspect  # avoid circular import
        def int_or_none(val):
            try:
                newval = int(val)
            except:
                newval = None
            return newval

        elevation = int_or_none(self.imputed_elevation)
        # Unit conversion
        if elevation:
            elevation = int(elevation * 3.28084)
        aspect = int_or_none(self.imputed_aspect)
        aspect_class = classify_aspect(aspect)
        slope = int_or_none(self.imputed_slope)
        gnn = int_or_none(self.imputed_gnn)
        if self.acres:
            acres = round(self.acres, 1)
        else:
            acres = None

        d = {
                'uid': self.uid,
                'name': self.name,
                'rx': '', #TODO rm ; was self.get_rx_display(),
                'acres': acres,
                'domspp': '', #TODO rm, was self.domspp,
                'elevation': elevation,
                'aspect': "%s" % aspect_class,
                'slope': '%s %%' % slope,
                'gnn': gnn,
                'plot_summary': self.plot_summary,
                'plot_summaries': self.plot_summaries, #TODO rm
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

    def get_raster_stats(self, rastername):
        raster = RasterDataset.objects.get(name=rastername)
        rproj = [rproj for rname, rproj in settings.IMPUTE_RASTERS if rname == rastername][0]
        g1 = self.geometry_final
        g2 = g1.transform(rproj, clone=True)
        if not raster.is_valid:
            raise Exception("Raster is not valid: %s" % raster )
        stats = zonal_stats(g2, raster)
        return stats

    @property
    def imputed_elevation(self):
        data = self.get_raster_stats('elevation')
        return data.avg

    @property
    def imputed_aspect(self):
        cos = self.get_raster_stats('cos_aspect')
        sin = self.get_raster_stats('sin_aspect')
        result = None
        if cos and sin and cos.sum and sin.sum:
            avg_aspect_rad = math.atan2(sin.sum, cos.sum)
            result = math.degrees(avg_aspect_rad) % 360
        return result

    @property
    def imputed_slope(self):
        data = self.get_raster_stats('slope')
        return data.avg

    @property
    def imputed_gnn(self):
        data = self.get_raster_stats('gnn')
        return data.mode

    @property
    def imputed_fcids(self):
        stats = self.get_raster_stats('gnn')
        total_pixels = stats.pixels
        fcid_dict = {}
        for cat in stats.categories.all():
            fcid_dict[cat.category] = cat.count / total_pixels

        fsorted = sorted(fcid_dict.iteritems(), key=itemgetter(1), reverse=True)
        return fsorted[:4]  # return 4 most common GNN pixels

    @property
    def plot_summaries(self):
        ''' 
        Site charachteristics according to the most common FCID GNN pixels 
        These will mainly be used to confirm with the user that the GNN data is accurate.
        '''
        fcids = self.imputed_fcids  # ((fcid, pct), ..)
        summaries = []
        for fcid, prop in fcids:
            ps = PlotSummary.objects.get(fcid=fcid)
            summary = ps.summary
            summary['fcid_coverage'] = prop * 100
            # Unit conversions
            try:
                summary['stndhgt_ft'] = int(summary['stndhgt'] * 3.28084)   # m to ft
            except TypeError:
                summary['stndhgt_ft'] = None
            try:
                summary['baa_ge_3_sqft'] = int(summary['baa_ge_3'] * 10.7639) # sqm to sqft
            except TypeError:
                summary['baa_ge_3_sqft'] = None
            try:
                summary['tph_ge_3_tpa'] = int(summary['tph_ge_3'] * 0.404686) # h to acres
            except TypeError:
                summary['tph_ge_3_tpa'] = None
            try:
                summary['qmda_dom_in'] = int(summary['qmda_dom'] * 0.393701) # cm to inches
            except TypeError:
                summary['qmda_dom_in'] = None
            summaries.append(summary)
        return summaries

    @property
    def plot_summary(self):
        ''' 
        Site charachteristics according to the chosen plot
        '''
        if not self.plot:
            return None

        ps = self.plot
        summary = ps.summary
        # Unit conversions
        summary['stndhgt_ft'] = int(summary['stndhgt'] * 3.28084)   # m to ft
        summary['baa_ge_3_sqft'] = int(summary['baa_ge_3'] * 10.7639) # sqm to sqft
        summary['tph_ge_3_tpa'] = int(summary['tph_ge_3'] * 0.404686) #h to acres
        summary['qmda_dom_in'] = int(summary['qmda_dom'] * 0.393701) # cm to inches

        return summary

    def invalidate_cache(self):
        '''
        Remove any cached values associated with this scenario.
        Warning: additional caches will need to be added to this method
        '''
        if not self.id:
            return True
        keys = ["Stand_%(id)s_geojson"]
        keys = [x % self.__dict__ for x in keys]
        cache.delete_many(keys)
        for key in keys:
            assert cache.get(key) == None
        logger.debug("invalidated cache for %s" % str(keys))
        return True

    def save(self, *args, **kwargs):
        self.invalidate_cache()
        super(Stand, self).save(*args, **kwargs)

@register
class ForestProperty(FeatureCollection):
    geometry_final = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, null=True,blank=True,
            verbose_name="Forest Property MultiPolygon Geometry")

    #@property
    def geojson(self, srid=None):
        '''
        Couldn't find any serialization methods flexible enough for our needs
        So we do it the hard way.
        '''
        if self.acres:
            acres = round(self.acres, 0)
        else:
            acres = None

        d = {
                'uid': self.uid,
                'id': self.id,
                'name': self.name,
                'user_id': self.user.pk,
                'acres': acres,
                'location': self.location,
                'stand_summary': self.stand_summary,
                'variant': self.variant,
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
    def has_plots(self):
        ''' 
        Boolean. 
        Do all the stands have associated plots?
        '''
        for stand in self.feature_set(feature_classes=[Stand]):
            if not stand.plot:
                return False
        return True

    @property 
    def stand_summary(self):
        '''
        Summarize the status of stands in this property
        '''
        n_with_plot = 0
        n_without_plot = 0
        stands = self.feature_set(feature_classes=[Stand])
        for stand in stands:
            if not stand.plot:
                n_without_plot += 1
            else:
                n_with_plot += 1
        assert(n_with_plot + n_without_plot == len(stands))
        return {
                'total': len(stands),
                'with_plot': n_with_plot,
                'without_plot': n_without_plot,
               }

    @property
    def acres(self):
        try:
            g2 = self.geometry_final.transform(settings.EQUAL_AREA_SRID, clone=True)
            area_m = g2.area 
        except:
            return None
        return area_m * settings.EQUAL_AREA_ACRES_CONVERSION

    @property
    def variant(self):
        '''
        Returns: FVS variant name (string)
        '''
        geom = self.geometry_final
        if geom:
            variants = FVSVariant.objects.filter(geom__bboverlaps=geom)
        else:
            return None

        if not geom.valid:
            geom = geom.buffer(0)
        the_size = 0
        the_variant = None
        for variant in variants:
            variant_geom = variant.geom
            if not variant_geom.valid:
                variant_geom = variant_geom.buffer(0)
            if variant_geom.intersects(geom):
                try:
                    overlap = variant_geom.intersection(geom)
                except Exception as e:
                    logger.error(self.uid + ": " + str(e))
                    continue
                area = overlap.area
                if area > the_size:
                    the_size = area
                    the_variant = variant.fvsvariant.strip()
        return the_variant

    @property
    def location(self):
        '''
        Returns: (CountyName, State)
        '''
        geom = self.geometry_final
        if geom:
            counties = County.objects.filter(geom__bboverlaps=geom)
        else:
            return None

        if not geom.valid:
            geom = geom.buffer(0)
        the_size = 0
        the_county = (None, None)
        for county in counties:
            county_geom = county.geom
            if not county_geom.valid:
                county_geom = county_geom.buffer(0)
            if county_geom.intersects(geom):
                try:
                    overlap = county_geom.intersection(geom)
                except Exception as e:
                    logger.error(self.uid + ": " + str(e))
                    continue
                area = overlap.area
                if area > the_size:
                    the_size = area
                    the_county = (county.cntyname.title(), county.stname)
        return the_county

    def feature_set_geojson(self):
        # We'll use the bbox for the property geom itself
        # Instead of using the overall bbox of the stands  
        # Assumption is that property boundary SHOULD contain all stands
        # and, if not, they should expand the property boundary
        bb = self.bbox  
        featxt = ', '.join([i.geojson() for i in self.feature_set()])
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
            # Link to grab ALL *stands* associated with a property
            alternate('Property Scenarios',
                'trees.views.forestproperty_scenarios',  
                type="application/json",
                select='single'),
        )

class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""
    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value == "":
            return None
        # Actually we'll just return the string
        # need to explicitly call json.loads(X) in your code
        # reason: converting to dict then repr that dict in a form is invalid json
        # i.e. {"test": 0.5} becomes {u'test': 0.5} (not unicode and single quotes)
        return value

    def get_db_prep_save(self, value, *args, **kwargs):
        """Convert our JSON object to a string before we save"""
        if value == "":
            return None
        if isinstance(value, dict):
            value = dumps(value, cls=DjangoJSONEncoder)

        return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)

# http://south.readthedocs.org/en/latest/customfields.html#extending-introspection
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^trees\.models\.JSONField"])

@register
class Scenario(Analysis):
    """
    NOTE: if no input Rx for a stand, use the default from stand model
    """
    description = models.TextField(default="", null=True, blank=True, verbose_name="Description/Notes")
    input_property = models.ForeignKey('ForestProperty')
    input_target_boardfeet = models.FloatField(verbose_name='Target Boardfeet', null=True, blank=True, 
        help_text="Target an even flow of timber")
    input_site_diversity = models.FloatField(verbose_name='Target Site Diversity Index', null=True, blank=True, 
        help_text="Optimize for a target site diversity")
    input_age_class = models.FloatField(verbose_name='Target Mature Age Class', null=True, blank=True, 
        help_text="Optimize for target proportion of mature trees")
    input_target_carbon = models.BooleanField(verbose_name='Target Carbon', default=False, 
        help_text="Optimize harvest schedule for carbon sequestration") 
    input_rxs = JSONField(verbose_name="Prescriptions associated with each stand")

    # All output fields should be allowed to be Null/Blank
    output_scheduler_results = JSONField(null=True, blank=True)

    def stand_set(self):
        return self.input_property.feature_set()

    @property
    def output_property_results(self):
        res = loads(self.output_scheduler_results)
        return {'__all__': res['__all__']}

    @property
    def output_stand_results(self):
        res = loads(self.output_scheduler_results)
        del res['__all__']
        return res

    @property
    def property_level_dict(self):
        d = {
            'pk': self.pk, 
            'model': 'trees.scenario',
            'fields': {
                'description': self.description,
                'input_property': self.input_property.pk,
                'input_rxs': self.input_rxs,
                'input_target_boardfeet': self.input_target_boardfeet,
                'input_site_diversity': self.input_site_diversity,
                'input_age_class': self.input_age_class,
                'input_target_carbon': self.input_target_carbon,
                'name': self.name,
                'output_scheduler_results': self.output_property_results, # don't include stand-level results
                'user': self.user.username,
            }
        }
        return d


    def run(self):
        # TODO prep scheduler, run it, parse the outputs
        d = {}

        # TODO Randomness is random
        import math
        import random
        a = range(0,100)
        rsamp = [(math.sin(x) + 1) * 10.0 for x in a]

        # Stand-level outputs
        # Note the data structure for stands is different than properties
        # (stands are optimized for openlayers map while property-level works with jqplot)
        for stand in self.stand_set():
            c = random.randint(0,90)
            t = random.randint(0,90)
            carbon = rsamp[c:c+6]
            timber = rsamp[t:t+6]
            d[stand.pk] = {
                "years": range(2020, 2121, 20),
                "carbon": [
                    carbon[0], 
                    carbon[1], 
                    carbon[2], 
                    carbon[3],
                    carbon[4],
                    carbon[5],
                ],
                "timber": [
                    timber[0], 
                    timber[1], 
                    timber[2], 
                    timber[3],
                    timber[4],
                    timber[5],
                ]
            }

        # Property-level outputs
        # note the '__all__' key
        def scale(data):
            # fake data for ~3500 acres, adjust for size
            sf = 3500.0/self.input_property.acres
            return [ x/sf for x in data ]

        carbon_alt =  scale([338243.812, 631721, 775308, 792018, 754616])
        timber_alt = scale([1361780,1861789,2371139,2613845,3172212])

        carbon_biz = scale([338243, 317594, 370360, 354604, 351987])
        timber_biz = scale([2111800,2333800,2982600,2989000,2793700])

        if self.input_target_carbon:
            carbon = carbon_alt
            timber = timber_alt
        else:
            carbon = carbon_biz
            timber = timber_biz
        if self.name.startswith("Grow"):
            carbon = [c * 1.5 for c in carbon_alt]
            carbon[0] = carbon_alt[0]
            carbon[-2] = carbon_alt[-2] * 1.6
            carbon[-1] = carbon_alt[-1] * 1.7
            timber = [1,1,1,1,1]

        d['__all__'] = {
            "carbon": [
                ['2010-08-12 4:00PM',carbon[0]], 
                ['2035-09-12 4:00PM',carbon[1]], 
                ['2060-10-12 4:00PM',carbon[2]], 
                ['2085-12-12 4:00PM',carbon[3]],
                ['2110-12-12 4:00PM',carbon[4]],
            ],
            "timber": [
                ['2010-08-12 4:00PM',timber[0]], 
                ['2035-09-12 4:00PM',timber[1]], 
                ['2060-10-12 4:00PM',timber[2]], 
                ['2085-12-12 4:00PM',timber[3]],
                ['2110-12-12 4:00PM',timber[4]],
            ]
        }

        self.output_scheduler_results = d

    def geojson(self, srid=None):
        res = self.output_stand_results
        stand_data = []
        for stand in self.stand_set():
            stand_dict = loads(stand.geojson())
            stand_dict['properties']['id'] = stand.pk
            stand_dict['properties']['scenario'] = self.pk
            stand_dict['properties']['results'] = res[str(stand.pk)]

            stand_data.append(stand_dict)

        gj = dumps(stand_data) 
        # madrona doesn't expect an array/list of features here
        # we have to hack it by removing the []
        if gj.startswith("["): 
            gj = gj[1:]
        if gj.endswith("]"): 
            gj = gj[:-1]
        return gj
        
    def clean(self):
        inrx = loads(self.input_rxs)
        valid_rx_keys = dict(RX_CHOICES).keys()
        valid_stand_ids = [x.pk for x in self.input_property.feature_set()]
        for stand, rx in inrx.iteritems():
            if int(stand) not in valid_stand_ids:
                raise ValidationError('%s is not a valid stand id for this property' % stand)
            if rx not in valid_rx_keys:
                raise ValidationError('%s is not a valid prescription' % rx)

    class Options:
        form = "trees.forms.ScenarioForm"
        form_template = "trees/scenario_form.html"
        verbose_name = 'Forest Scenario' 
        form_context = { } 

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

class FVSVariant(models.Model):
    code = models.CharField(max_length=3)
    fvsvariant = models.CharField(max_length=100)
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

class FVSSpecies(models.Model):
    usda = models.CharField(max_length=8, null=True, blank=True)
    fia = models.CharField(max_length=3, null=True, blank=True)
    fvs = models.CharField(max_length=2, null=True, blank=True)
    common = models.TextField()
    scientific = models.TextField()
    AK = models.CharField(max_length=2)
    BM = models.CharField(max_length=2)
    CA = models.CharField(max_length=2)
    CI = models.CharField(max_length=2)
    CR = models.CharField(max_length=2)
    EC = models.CharField(max_length=2)
    EM = models.CharField(max_length=2)
    IE = models.CharField(max_length=2)
    KT = models.CharField(max_length=2)
    NC = models.CharField(max_length=2)
    NI = models.CharField(max_length=2)
    PN = models.CharField(max_length=2)
    SO = models.CharField(max_length=2)
    TT = models.CharField(max_length=2)
    UT = models.CharField(max_length=2)
    WC = models.CharField(max_length=2)
    WS = models.CharField(max_length=2)

class TreeLive(models.Model):
    live_id = models.BigIntegerField(primary_key=True)
    pntid = models.BigIntegerField(null=True, blank=True)
    ccid = models.BigIntegerField(null=True, blank=True)
    fcid = models.BigIntegerField(null=True, blank=True)
    pltid = models.BigIntegerField(null=True, blank=True)
    loc_id = models.BigIntegerField(null=True, blank=True)
    pnt_num = models.IntegerField(null=True, blank=True)
    plot_type = models.CharField(max_length=40, blank=True)
    data_source = models.CharField(max_length=30, blank=True)
    source_db = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=4, blank=True)
    plot = models.BigIntegerField(null=True, blank=True)
    assessment_date = models.DateTimeField(null=True, blank=True)
    spp_symbol = models.CharField(max_length=20, blank=True)
    scientific_name = models.CharField(max_length=200, blank=True)
    con = models.CharField(max_length=2, blank=True)
    dbh_cm = models.FloatField(null=True, blank=True)
    dbh_class = models.FloatField(null=True, blank=True)
    dbh_est_method = models.FloatField(null=True, blank=True)
    ba_m2 = models.FloatField(null=True, blank=True)
    ht_m = models.FloatField(null=True, blank=True)
    ht_est_method = models.IntegerField(null=True, blank=True)
    mod_htm_fvs = models.IntegerField(null=True, blank=True)
    for_spec = models.BigIntegerField(null=True, blank=True)
    age_bh = models.IntegerField(null=True, blank=True)
    crown_class = models.IntegerField(null=True, blank=True)
    crown_ratio = models.IntegerField(null=True, blank=True)
    hcb = models.FloatField(null=True, blank=True)
    ucc = models.FloatField(null=True, blank=True)
    vol_m3 = models.FloatField(null=True, blank=True)
    cull_cubic = models.FloatField(null=True, blank=True)
    plot_size = models.IntegerField(null=True, blank=True)
    tree_count = models.IntegerField(null=True, blank=True)
    source_id = models.BigIntegerField(null=True, blank=True)
    baph_pnt = models.FloatField(null=True, blank=True)
    baph_cc = models.FloatField(null=True, blank=True)
    baph_fc = models.FloatField(null=True, blank=True)
    baph_plt = models.FloatField(null=True, blank=True)
    tph_pnt = models.FloatField(null=True, blank=True)
    tph_cc = models.FloatField(null=True, blank=True)
    tph_fc = models.FloatField(null=True, blank=True)
    tph_plt = models.FloatField(null=True, blank=True)
    pctcov_pnt = models.FloatField(null=True, blank=True)
    pctcov_cc = models.FloatField(null=True, blank=True)
    pctcov_fc = models.FloatField(null=True, blank=True)
    pctcov_plt = models.FloatField(null=True, blank=True)
    rem_pnt = models.CharField(max_length=2, blank=True)
    rem_cc = models.CharField(max_length=2, blank=True)
    rem_fc = models.CharField(max_length=2, blank=True)
    rem_plt = models.CharField(max_length=2, blank=True)
    volph_pnt = models.FloatField(null=True, blank=True)
    volph_cc = models.FloatField(null=True, blank=True)
    volph_fc = models.FloatField(null=True, blank=True)
    volph_plt = models.FloatField(null=True, blank=True)
    iv_pnt = models.FloatField(null=True, blank=True)
    iv_cc = models.FloatField(null=True, blank=True)
    iv_fc = models.FloatField(null=True, blank=True)
    iv_plt = models.FloatField(null=True, blank=True)
    biomph_pnt = models.FloatField(null=True, blank=True)
    biomph_cc = models.FloatField(null=True, blank=True)
    biomph_fc = models.FloatField(null=True, blank=True)
    biomph_plt = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'tree_live'

class PlotSummary(models.Model):
    fcid = models.BigIntegerField(primary_key=True, unique=True)
    value = models.BigIntegerField(null=True, blank=True)
    map_source = models.CharField(null=True, max_length=8, blank=True)
    eslf_code = models.IntegerField(null=True, blank=True)
    eslf_name = models.CharField(null=True, max_length=300, blank=True)
    data_source = models.CharField(null=True, max_length=40, blank=True)
    assessment_year = models.IntegerField(null=True, blank=True)
    state = models.CharField(null=True, max_length=4, blank=True)
    half_state = models.CharField(null=True, max_length=6, blank=True)
    cnty = models.SmallIntegerField(null=True, blank=True)
    plot = models.BigIntegerField(null=True, blank=True)
    occasion_num = models.SmallIntegerField(null=True, blank=True)
    idb_plot_id = models.BigIntegerField(null=True, blank=True)
    bac_ge_3 = models.FloatField(null=True, blank=True)
    bac_prop = models.FloatField(null=True, blank=True)
    bac_3_25 = models.FloatField(null=True, blank=True)
    bac_25_50 = models.FloatField(null=True, blank=True)
    bac_50_75 = models.FloatField(null=True, blank=True)
    bac_75_100 = models.FloatField(null=True, blank=True)
    bac_ge_100 = models.FloatField(null=True, blank=True)
    bah_ge_3 = models.FloatField(null=True, blank=True)
    bah_prop = models.FloatField(null=True, blank=True)
    bah_3_25 = models.FloatField(null=True, blank=True)
    bah_25_50 = models.FloatField(null=True, blank=True)
    bah_50_75 = models.FloatField(null=True, blank=True)
    bah_75_100 = models.FloatField(null=True, blank=True)
    bah_ge_100 = models.FloatField(null=True, blank=True)
    baa_ge_3 = models.FloatField(null=True, blank=True)
    baa_3_25 = models.FloatField(null=True, blank=True)
    baa_25_50 = models.FloatField(null=True, blank=True)
    baa_50_75 = models.FloatField(null=True, blank=True)
    baa_75_100 = models.FloatField(null=True, blank=True)
    baa_ge_100 = models.FloatField(null=True, blank=True)
    bph_ge_3 = models.FloatField(null=True, blank=True)
    tph_ge_3 = models.FloatField(null=True, blank=True)
    tph_3_25 = models.FloatField(null=True, blank=True)
    tph_25_50 = models.FloatField(null=True, blank=True)
    tph_50_75 = models.FloatField(null=True, blank=True)
    tph_75_100 = models.FloatField(null=True, blank=True)
    tph_ge_100 = models.FloatField(null=True, blank=True)
    tphc_ge_3 = models.FloatField(null=True, blank=True)
    tphc_ge_50 = models.FloatField(null=True, blank=True)
    tphc_ge_75 = models.FloatField(null=True, blank=True)
    tphc_ge_100 = models.FloatField(null=True, blank=True)
    tphh_ge_3 = models.FloatField(null=True, blank=True)
    tphtol_ge_3 = models.FloatField(null=True, blank=True)
    tphintol_ge_3 = models.FloatField(null=True, blank=True)
    vph_ge_3 = models.FloatField(null=True, blank=True)
    vph_3_25 = models.FloatField(null=True, blank=True)
    vph_25_50 = models.FloatField(null=True, blank=True)
    vph_50_75 = models.FloatField(null=True, blank=True)
    vph_75_100 = models.FloatField(null=True, blank=True)
    vph_ge_100 = models.FloatField(null=True, blank=True)
    vphc_ge_3 = models.FloatField(null=True, blank=True)
    vphh_ge_3 = models.FloatField(null=True, blank=True)
    qmdc_dom = models.FloatField(null=True, blank=True)
    qmdh_dom = models.FloatField(null=True, blank=True)
    qmda_dom = models.FloatField(null=True, blank=True)
    qmdc_ge_3 = models.FloatField(null=True, blank=True)
    qmdh_ge_3 = models.FloatField(null=True, blank=True)
    qmda_ge_3 = models.FloatField(null=True, blank=True)
    qmdc_75pct = models.FloatField(null=True, blank=True)
    mndbhba_all = models.FloatField(null=True, blank=True)
    mndbhba_con = models.FloatField(null=True, blank=True)
    mndbhba_hdw = models.FloatField(null=True, blank=True)
    stph_12_25 = models.FloatField(null=True, blank=True)
    stph_25_50 = models.FloatField(null=True, blank=True)
    stph_50_75 = models.FloatField(null=True, blank=True)
    stph_75_100 = models.FloatField(null=True, blank=True)
    stph_ge_12 = models.FloatField(null=True, blank=True)
    stph_ge_25 = models.FloatField(null=True, blank=True)
    stph_ge_50 = models.FloatField(null=True, blank=True)
    stph_ge_75 = models.FloatField(null=True, blank=True)
    stph_ge_100 = models.FloatField(null=True, blank=True)
    svph_12_25 = models.FloatField(null=True, blank=True)
    svph_25_50 = models.FloatField(null=True, blank=True)
    svph_50_75 = models.FloatField(null=True, blank=True)
    svph_75_100 = models.FloatField(null=True, blank=True)
    svph_ge_12 = models.FloatField(null=True, blank=True)
    svph_ge_25 = models.FloatField(null=True, blank=True)
    svph_ge_50 = models.FloatField(null=True, blank=True)
    svph_ge_75 = models.FloatField(null=True, blank=True)
    svph_ge_100 = models.FloatField(null=True, blank=True)
    sbph_5_9_in = models.FloatField(null=True, blank=True)
    sbph_9_20_in = models.FloatField(null=True, blank=True)
    sbph_ge_20_in = models.FloatField(null=True, blank=True)
    sbph_ge_12 = models.FloatField(null=True, blank=True)
    dvph_12_25 = models.FloatField(null=True, blank=True)
    dvph_25_50 = models.FloatField(null=True, blank=True)
    dvph_50_75 = models.FloatField(null=True, blank=True)
    dvph_75_100 = models.FloatField(null=True, blank=True)
    dvph_ge_12 = models.FloatField(null=True, blank=True)
    dvph_ge_25 = models.FloatField(null=True, blank=True)
    dvph_ge_50 = models.FloatField(null=True, blank=True)
    dvph_ge_75 = models.FloatField(null=True, blank=True)
    dvph_ge_100 = models.FloatField(null=True, blank=True)
    dcov_12_25 = models.FloatField(null=True, blank=True)
    dcov_25_50 = models.FloatField(null=True, blank=True)
    dcov_50_75 = models.FloatField(null=True, blank=True)
    dcov_75_100 = models.FloatField(null=True, blank=True)
    dcov_ge_12 = models.FloatField(null=True, blank=True)
    dcov_ge_25 = models.FloatField(null=True, blank=True)
    dcov_ge_50 = models.FloatField(null=True, blank=True)
    dcov_ge_75 = models.FloatField(null=True, blank=True)
    dcov_ge_100 = models.FloatField(null=True, blank=True)
    cancov = models.FloatField(null=True, blank=True)
    cancov_con = models.FloatField(null=True, blank=True)
    cancov_hdw = models.FloatField(null=True, blank=True)
    cancov_dom = models.FloatField(null=True, blank=True)
    stndhgt = models.FloatField(null=True, blank=True)
    hcb = models.FloatField(null=True, blank=True)
    sddbh = models.FloatField(null=True, blank=True)
    sdba = models.FloatField(null=True, blank=True)
    sdi = models.FloatField(null=True, blank=True)
    sdi_reineke = models.FloatField(null=True, blank=True)
    conr = models.SmallIntegerField(null=True, blank=True)
    hdwr = models.SmallIntegerField(null=True, blank=True)
    treer = models.SmallIntegerField(null=True, blank=True)
    iv_con = models.FloatField(null=True, blank=True)
    iv_hdw = models.FloatField(null=True, blank=True)
    iv_vs = models.FloatField(null=True, blank=True)
    iv_100 = models.FloatField(null=True, blank=True)
    ddi = models.FloatField(null=True, blank=True)
    age_dom = models.FloatField(null=True, blank=True)
    age_dom_no_rem = models.FloatField(null=True, blank=True)
    tph_reml = models.FloatField(null=True, blank=True)
    vph_reml = models.FloatField(null=True, blank=True)
    rem_pctl = models.FloatField(null=True, blank=True)
    tph_rems = models.FloatField(null=True, blank=True)
    vph_rems = models.FloatField(null=True, blank=True)
    rem_pcts = models.FloatField(null=True, blank=True)
    vph_remd = models.FloatField(null=True, blank=True)
    rem_pctd = models.FloatField(null=True, blank=True)
    struccond = models.SmallIntegerField(null=True, blank=True)
    vegclass = models.SmallIntegerField(null=True, blank=True)
    struccondr = models.SmallIntegerField(null=True, blank=True)
    vegclassr = models.SmallIntegerField(null=True, blank=True)
    conplba = models.CharField(null=True, max_length=20, blank=True)
    conpliv = models.CharField(null=True, max_length=20, blank=True)
    conplcov = models.CharField(null=True, max_length=20, blank=True)
    hdwplba = models.CharField(null=True, max_length=20, blank=True)
    hdwpliv = models.CharField(null=True, max_length=20, blank=True)
    hdwplcov = models.CharField(null=True, max_length=20, blank=True)
    uplcov = models.CharField(null=True, max_length=20, blank=True)
    fortypba = models.CharField(null=True, max_length=42, blank=True)
    fortypiv = models.CharField(null=True, max_length=42, blank=True)
    fortypcov = models.CharField(null=True, max_length=42, blank=True)
    sizecl = models.SmallIntegerField(null=True, blank=True)
    covcl = models.SmallIntegerField(null=True, blank=True)
    sc = models.SmallIntegerField(null=True, blank=True)
    sc_decaid = models.CharField(null=True, max_length=2, blank=True)
    imap_domspp = models.CharField(null=True, max_length=20, blank=True)
    imap_layers = models.SmallIntegerField(null=True, blank=True)
    imap_qmd = models.FloatField(null=True, blank=True)
    vc_qmda = models.SmallIntegerField(null=True, blank=True)
    vc_qmdc = models.SmallIntegerField(null=True, blank=True)
    lsog = models.CharField(null=True, max_length=2, blank=True)
    lsog_tphc_50 = models.CharField(null=True, max_length=2, blank=True)
    ogsi = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = u'sppsz_attr_all'

    def __unicode__(self):
        return "%s (%s)" % (self.fcid, self.imap_domspp)

    def get_forest_types(self, fortype_str):
        ''' 
        Get forest types based on string, Returns list
        '''
        try:
            fortypes = [FVSSpecies.objects.get(usda=x).common.title() for x in fortype_str.strip().split('/')]
            fortypes = [x.replace('-',' ') for x in fortypes]
        except (FVSSpecies.DoesNotExist, AttributeError):
            fortypes = [fortype_str]
        return fortypes

    @property
    def vegclass_decoded(self):
        ''' 
        Should this be in the database? Probably but this is quick and works for now
        If we end up doing lots of field code lookups, then we can reassess
        '''
        vegclass = self.vegclass
        if not vegclass:
            return None

        datadict = {
            1 : "Sparse",
            2 : "Open",
            3 : "Broadleaf: sap/pole: mod/closed",
            4 : "Broadleaf: sm/med/lg: mod/closed",
            5 : "Mixed: sap/pole: mod/closed",
            6 : "Mixed: sm/med: mod/closed",
            7 : "Mixed: large+giant: mod/closed",
            8 : "Conifer: sap/pole: mod/closed",
            9 : "Conifer: sm/med: mod/closed",
           10 : "Conifer: large: mod/closed",
           11 : "Conifer: giant: mod/closed",
        }
        return datadict[vegclass]

    @property
    @cachemethod('plot_summary_fcid-%(fcid)s')
    def summary(self):
        ''' 
        Plot characteristics according to the FCID
        '''
        fortype_str = self.fortypiv
        fortypes = self.get_forest_types(fortype_str)

        summary = {
                'fcid': self.fcid,
                'fortypiv': fortypes,
                'vegclass': self.vegclass_decoded,
                'cancov': self.cancov,
                'stndhgt': self.stndhgt,
                'sdi_reineke': self.sdi_reineke,
                'qmda_dom': self.qmda_dom,
                'baa_ge_3': self.baa_ge_3,
                'tph_ge_3': self.tph_ge_3,
                'bac_prop': self.bac_prop,
            }
        return summary

class GNN_ORWA(models.Model):
    """
    GNN 'histogram' for our study region
    value is the fcid, count is the number of pixels
    """
    value = models.IntegerField()
    count = models.IntegerField()


class IdbSummary(models.Model):
    plot_id = models.BigIntegerField(null=True, blank=True)
    cond_id = models.BigIntegerField(primary_key=True, unique=True)
    sumofba_ft2 = models.FloatField(null=True, blank=True)
    avgofba_ft2_ac = models.FloatField(null=True, blank=True)
    avgofht_ft = models.FloatField(null=True, blank=True)
    avgoftpa = models.FloatField(null=True, blank=True)
    avgofdbh_in = models.FloatField(null=True, blank=True)
    state_name = models.CharField(max_length=40, blank=True)
    county_name = models.CharField(max_length=100, blank=True)
    halfstate_name = models.CharField(max_length=100, blank=True)
    forest_name = models.CharField(max_length=510, blank=True)
    acres = models.FloatField(null=True, blank=True)
    acres_vol = models.FloatField(null=True, blank=True)
    fia_forest_type_name = models.CharField(max_length=60, blank=True)
    latitude_fuzz = models.FloatField(null=True, blank=True)
    longitude_fuzz = models.FloatField(null=True, blank=True)
    aspect_deg = models.IntegerField(null=True, blank=True)
    stdevofaspect_deg = models.FloatField(null=True, blank=True)
    firstofaspect_deg = models.IntegerField(null=True, blank=True)
    slope = models.IntegerField(null=True, blank=True)
    stdevofslope = models.FloatField(null=True, blank=True)
    avgofslope = models.FloatField(null=True, blank=True)
    elev_ft = models.IntegerField(null=True, blank=True)
    fvs_variant = models.CharField(max_length=4, blank=True)
    site_species = models.IntegerField(null=True, blank=True)
    site_index_fia = models.IntegerField(null=True, blank=True)
    plant_assoc_code = models.CharField(max_length=20, blank=True)
    countofsubplot_id = models.BigIntegerField(null=True, blank=True)
    qmd_hwd_cm = models.FloatField(null=True, blank=True)
    qmd_swd_cm = models.FloatField(null=True, blank=True)
    qmd_tot_cm = models.FloatField(null=True, blank=True)
    calc_aspect = models.IntegerField(null=True, blank=True)
    calc_slope = models.IntegerField(null=True, blank=True)
    stand_size_class = models.IntegerField(null=True, blank=True)
    site_class_fia = models.IntegerField(null=True, blank=True)
    stand_age_even_yn = models.CharField(max_length=2, blank=True)
    stand_age = models.IntegerField(null=True, blank=True)
    for_type = models.IntegerField(null=True, blank=True)
    for_type_secdry = models.IntegerField(null=True, blank=True)
    for_type_name = models.CharField(max_length=60, blank=True)
    for_type_secdry_name = models.CharField(max_length=60, blank=True)
    qmdc_dom = models.FloatField(null=True, blank=True)
    qmdh_dom = models.FloatField(null=True, blank=True)
    qmda_dom = models.FloatField(null=True, blank=True)
    cancov = models.FloatField(null=True, blank=True)
    stndhgt = models.FloatField(null=True, blank=True)
    sdi = models.FloatField(null=True, blank=True)
    sdi_reineke = models.FloatField(null=True, blank=True)
    age_dom = models.FloatField(null=True, blank=True)
    vegclassr = models.SmallIntegerField(null=True, blank=True)
    vegclass = models.SmallIntegerField(null=True, blank=True)
    struccondr = models.SmallIntegerField(null=True, blank=True)
    struccond = models.SmallIntegerField(null=True, blank=True)
    sizecl = models.SmallIntegerField(null=True, blank=True)
    covcl = models.SmallIntegerField(null=True, blank=True)
    ogsi = models.FloatField(null=True, blank=True)
    bac_prop = models.FloatField(null=True, blank=True)
    tph_ge_3 = models.FloatField(null=True, blank=True)
    mai = models.FloatField(null=True, blank=True)
    owner = models.IntegerField(null=True, blank=True)
    own_group = models.IntegerField(null=True, blank=True)
    bah_ge_3 = models.FloatField(null=True, blank=True)
    bac_ge_3 = models.FloatField(null=True, blank=True)
    baa_ge_3 = models.FloatField(null=True, blank=True)
    qmda_dom_stunits = models.FloatField(null=True, blank=True)
    stndhgt_stunits = models.FloatField(null=True, blank=True)
    baa_ge_3_stunits = models.FloatField(null=True, blank=True)
    tph_ge_3_stunits = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'idb_summary'

    @property
    @cachemethod("IdbSummary_eqd_point_%(cond_id)s")
    def eqd_point(self):
        plot_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % (self.longitude_fuzz, self.latitude_fuzz))
        plot_centroid.transform(settings.EQD_SRID)
        return plot_centroid

class PlotLookupManager(models.Manager):
    def get_query_set(self):
        from django.db.models import Q
        return super(PlotLookupManager, self).get_query_set().filter(~Q(type="cat"), weight__gte=0)

class PlotLookup(models.Model):
    attr = models.CharField(max_length=30, blank=True, null=True)
    source = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=60, blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    type = models.CharField(max_length=20, blank=True, null=True)
    units = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    objects = models.Manager() # The default manager.
    nn_objects = PlotLookupManager() # The filtered manager showing ONLY plot attrs used in the NN search.

    @classmethod
    def weight_dict(cls):
        return dict([(x.attr, x.weight) for x in cls.nn_objects.all()])

    @classmethod
    def lookup(cls):
        return dict([(x.attr, x.name) for x in cls.nn_objects.all()])

    class Meta:
        ordering = ['name']

    @classmethod
    def field_dict(cls):
        return {
            'cats': cls.objects.filter(type='cat'),
            'numerics': cls.nn_objects.filter(type='num'),
            'stands': cls.nn_objects.filter(type='stand'),
        }

    def __unicode__(self):
        return u"%s (%s)" % (self.attr, self.name)

#TODO @register
class Strata(Feature):
    # stand will have a FK to Strata
    search_age = models.FloatField()
    search_tpa = models.FloatField()
    additional_desc = models.TextField(blank=True, null=True)
    stand_list = JSONField() # {'classes': [(species, age class, tpa), ...]}
    
    def candidates(self, min_candidates=5):
        from plots import get_candidates
        return get_candidates(self.stand_list['classes'], min_candidates=min_candidates) 

    @property
    def desc(self):
        return "description created from stand list attrs"

    # TODO form
    class Options:
        pass


fvsvariant_mapping = {
    'code' : 'FVSVARIANT',
    'fvsvariant': 'FULLNAME',
    'geom' : 'MULTIPOLYGON',
}

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

def load_shp(path, feature_class):
    '''
    First run ogrinspect to generate the class and mapping. 
        python manage.py ogrinspect ../data/fvs_variant/lot_fvsvariant_3857.shp FVSVariant --mapping --srid=3857 --multi
    Paste code into models.py and modify as necessary.
    Finally, load the shapefile:
        from trees import models
        models.load_shp('../data/fvs_variants/lot_fvsvariant_3857.shp', models.FVSVariant)
    '''
    mapping = eval("%s_mapping" % feature_class.__name__.lower())
    print "Saving", path, "to", feature_class, "using", mapping
    map1 = LayerMapping(feature_class, path, mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=True)

class TreeliveSummary(models.Model):
    plot_id = models.BigIntegerField(null=True, blank=True)
    cond_id = models.BigIntegerField(primary_key=True)
    fia_forest_type_name = models.CharField(max_length=60, blank=True)
    calc_dbh_class = models.FloatField(null=True, blank=True)
    calc_tree_count = models.IntegerField(null=True, blank=True)
    sumoftpa = models.FloatField(null=True, blank=True)
    avgoftpa = models.FloatField(null=True, blank=True)
    sumofba_ft2_ac = models.FloatField(null=True, blank=True)
    avgofba_ft2_ac = models.FloatField(null=True, blank=True)
    avgofht_ft = models.FloatField(null=True, blank=True)
    avgofdbh_in = models.FloatField(null=True, blank=True)
    avgofage_bh = models.FloatField(null=True, blank=True)
    total_ba_ft2_ac = models.FloatField(null=True, blank=True)
    count_speciessizeclasses = models.IntegerField(null=True, blank=True)
    pct_of_totalba = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'treelive_summary'

