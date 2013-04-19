#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import datetime
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.simplejson import dumps, loads
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit
from madrona.common.utils import get_logger
from django.core.cache import cache
from django.contrib.gis.geos import GEOSGeometry
from trees.tasks import impute_rasters, impute_nearest_neighbor, schedule_harvest
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import connection

logger = get_logger()


def cachemethod(cache_key, timeout=60 * 60 * 24 * 7):
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
            if res is None:
                res = func(self, *args)
                cache.set(key, res, timeout)
            return res
        return decorated
    return paramed_decorator

RX_CHOICES = (
    ('--', '--'),
    ('RE', 'Reserve; No Action'),
    ('RG', 'Riparian Grow Only'),
    ('UG', 'Uneven-aged Group Selection'),
    ('SW', 'Shelterwood'),
    ('CT', 'Commercial Thinning'),
    ('CC', 'Even-aged Clearcut'),
)


def datetime_to_unix(dt):
    start = datetime.datetime(year=1970, month=1, day=1)
    diff = dt - start
    try:
        total = diff.total_seconds()
    except AttributeError:
        # for the benefit of python 2.6
        total = (diff.microseconds + (diff.seconds + diff.days * 24 * 3600) * 1e6) / 1e6
    return total


def postgres_now():
    '''
    Alternative to datetime.datetime.now()
    for comparison with model instances having a field = date_modified(auto_now=True)
    '''
    cursor = connection.cursor()
    cursor.execute("SELECT now();")
    now = cursor.fetchone()[0]
    return now


class DirtyFieldsMixin(object):
    """
    http://stackoverflow.com/a/4676107/519385
    """
    def __init__(self, *args, **kwargs):
        self._original_state = None
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(self._reset_state, sender=self.__class__,
                          dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        self._reset_state()

    def _reset_state(self, *args, **kwargs):
        if self.id:
            self._original_state = self._as_dict()

    def _as_dict(self):
        return dict([(f.attname, getattr(self, f.attname, None)) for f in self._meta.local_fields])

    def get_dirty_fields(self):
        new_state = self._as_dict()
        if self._original_state:
            return dict([(key, value) for key, value in self._original_state.iteritems()
                         if value != new_state[key]])
        else:
            return {}


@register
class Stand(DirtyFieldsMixin, PolygonFeature):
    strata = models.ForeignKey("Strata", blank=True, default=None,
                               null=True, on_delete=models.SET_NULL)
    cond_id = models.BigIntegerField(blank=True, null=True, default=None)
    elevation = models.FloatField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)
    aspect = models.FloatField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    nn_savetime = models.FloatField(default=0.0)
    rast_savetime = models.FloatField(default=0.0)

    class Options:
        form = "trees.forms.StandForm"
        form_template = "trees/stand_form.html"
        manipulators = []

    def get_idb(self, force=False):
        '''
        Synchronous computation of nearest neighbor
        Prefer instead:
          impute_nearest_neighbor.delay(stand_id)
        '''
        if self.cond_id and not force:
            return self.cond_id

        res = impute_nearest_neighbor(self.id)
        return res['cond_id']

    @property
    def default_weighting(self):
        return {
            'TOTAL_PCTBA': 5,
        }

    @property
    def acres(self):
        g2 = self.geometry_final.transform(
            settings.EQUAL_AREA_SRID, clone=True)
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

        elevation = int_or_none(self.elevation)
        # Unit conversion
        if elevation:
            elevation = int(elevation * 3.28084)
        aspect = int_or_none(self.aspect)
        aspect_class = classify_aspect(aspect)
        slope = int_or_none(self.slope)

        try:
            strata = self.strata._dict
        except:
            strata = None

        if self.cond_id:
            cond_inst = IdbSummary.objects.get(cond_id=self.cond_id)
            cond = cond_inst._dict
        else:
            cond = None

        if self.acres:
            acres = round(self.acres, 1)
        else:
            acres = None

        d = {
            'uid': self.uid,
            'name': self.name,
            'acres': acres,
            'elevation': elevation,
            'strata': strata,
            'condition': cond,
            'aspect': "%s" % aspect_class,
            'slope': '%s %%' % slope,
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

    def invalidate_cache(self):
        '''
        Remove any cached values associated with this stand.
        '''
        if not self.id:
            return True
        # assume that all stand-related keys will start with Stand_<id>_*
        # depends on django-redis as the cache backend!!!
        key_pattern = "Stand_%d_*" % self.id
        cache.delete_pattern(key_pattern)
        assert cache.keys(key_pattern) == []
        return True

    def save(self, *args, **kwargs):
        self.invalidate_cache()

        if not self.name or self.name.strip() == '':
            self.name = str(datetime_to_unix(datetime.datetime.now()))

        # Depending on what changed, null out fields (post-save signal will pick them up)
        if 'geometry_final' in self.get_dirty_fields().keys() or not self.id:
            # got new geom - time to recalc terrain rasters!
            self.elevation = self.slope = self.aspect = self.cost = self.cond_id = None
        if 'strata_id' in self.get_dirty_fields().keys() or (not self.id and self.strata):
            # got new strata - time to recalc nearest neighbor!
            self.cond_id = None

        super(Stand, self).save(*args, **kwargs)


@register
class ForestProperty(FeatureCollection):
    geometry_final = models.MultiPolygonField(
        srid=settings.GEOMETRY_DB_SRID, null=True, blank=True,
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
            'variant': self.variant.fvsvariant.strip(),
            'variant_id': self.variant.id,
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
    def is_runnable(self):
        '''
        Boolean.
        Do all the stands have associated plots?
        '''
        for stand in self.feature_set(feature_classes=[Stand]):
            if not stand.cond_id:
                return False
        return True

    @property
    def stand_summary(self):
        '''
        Summarize the status of stands in this property
        '''
        n_with_strata = 0
        n_with_terrain = 0
        n_with_condition = 0
        stands = self.feature_set(feature_classes=[Stand])
        for stand in stands:

            if stand.cond_id:
                n_with_condition += 1

            if stand.elevation and stand.slope and stand.aspect and stand.cost:
                n_with_terrain += 1

            if stand.strata:
                n_with_strata += 1

        return {
            'total': len(stands),
            'with_strata': n_with_strata,
            'with_condition': n_with_condition,
            'with_terrain': n_with_terrain,
        }

    @property
    def status(self):
        d = self.stand_summary
        d['is_runnable'] = self.is_runnable
        d['scenarios'] = []
        for scenario in self.scenario_set.all():
            sd = {
                'uid': scenario.uid,
                'needs_rerun': scenario.needs_rerun,
                'runnable': scenario.is_runnable,
            }
            d['scenarios'].append(sd)
        return d

    def reset_scenarios(self):
        """
        The 'reset' button for all property's scenarios
        """
        for scenario in self.scenario_set.all():
            scenario.run()

    def reset_stands(self):
        """
        Strips all imputed data from stands and attempts to recalculate it
        The 'reset' button for seriously screwed up data
        """
        stands = self.feature_set(feature_classes=[Stand])
        for stand in stands:
            stand.elevation = stand.slope = stand.aspect = stand.cost = stand.cond_id = None
            stand.save()

    @property
    def acres(self):
        try:
            g2 = self.geometry_final.transform(
                settings.EQUAL_AREA_SRID, clone=True)
            area_m = g2.area
        except:
            return None
        return area_m * settings.EQUAL_AREA_ACRES_CONVERSION

    @property
    @cachemethod("ForestProperty_%(id)s_variant")
    def variant(self):
        '''
        Returns: Closest FVS variant instance
        '''
        geom = self.geometry_final.point_on_surface

        variants = FVSVariant.objects.all()

        min_distance = 99999999999999.0
        the_variant = None
        for variant in variants:
            variant_geom = variant.geom
            if not variant_geom.valid:
                variant_geom = variant_geom.buffer(0)
            dst = variant_geom.distance(geom)
            if dst == 0.0:
                return variant
            if dst < min_distance:
                min_distance = dst
                the_variant = variant
        return the_variant

    @property
    @cachemethod("ForestProperty_%(id)s_location")
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
        featxt = ', '.join(
            [i.geojson() for i in self.feature_set(feature_classes=[Stand])])
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

    def invalidate_cache(self):
        if not self.id:
            return True
        # depends on django-redis as the cache backend!!!
        key_pattern = "ForestProperty_%d_*" % self.id
        cache.delete_pattern(key_pattern)
        assert cache.keys(key_pattern) == []
        return True

    def save(self, *args, **kwargs):
        self.invalidate_cache()
        super(ForestProperty, self).save(*args, **kwargs)

    class Options:
        valid_children = ('trees.models.Stand', 'trees.models.Strata', 'trees.models.MyRx')
        form = "trees.forms.PropertyForm"
        links = (
            # Link to grab ALL *stands* associated with a property
            alternate('Property Stands GeoJSON',
                      'trees.views.geojson_forestproperty',
                      type="application/json",
                      select='single'),
            # Link to grab ALL *scenarios* associated with a property
            alternate('Property Scenarios',
                      'trees.views.forestproperty_scenarios',
                      type="application/json",
                      select='single'),
            # Link to grab ALL *strata* belonging to a property
            alternate('Property Strata List',
                      'trees.views.forestproperty_strata_list',
                      type="application/json",
                      select='single'),
            alternate('Property status',
                      'trees.views.forestproperty_status',
                      type="application/json",
                      select='single'),
            # Link to grab ALL MyRx associated with a property
            alternate('Property MyRx JSON',
                      'trees.views.forestproperty_myrx',
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
        if value == "" or value is None:
            return None

        if isinstance(value, basestring):
            # if it's a string
            return loads(value)
        else:
            # if it's not yet saved and is still a python data structure
            return value

    def get_db_prep_save(self, value, *args, **kwargs):
        """Convert our JSON object to a string before we save"""
        if value == "":
            return None
        if isinstance(value, dict):
            value = dumps(value, cls=DjangoJSONEncoder)

        return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)

# http://south.readthedocs.org/en/latest/customfields.html#extending-
# introspection
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^trees\.models\.JSONField"])


class ScenarioNotRunnable(Exception):
    pass


@register
class Scenario(Feature):
    """
    NOTE: if no input Rx for a stand, use the default from stand model
    """
    description = models.TextField(
        default="", null=True, blank=True, verbose_name="Description/Notes")
    input_property = models.ForeignKey('ForestProperty')
    input_target_boardfeet = models.FloatField(
        verbose_name='Target Boardfeet', null=True, blank=True,
        help_text="Target an even flow of timber")
    input_age_class = models.FloatField(
        verbose_name='Target Mature Age Class', null=True, blank=True,
        help_text="Optimize for target proportion of mature trees")
    input_target_carbon = models.BooleanField(
        verbose_name='Target Carbon', default=False,
        help_text="Optimize harvest schedule for carbon sequestration")
    input_rxs = JSONField(
        null=True, blank=True, default="{}",
        verbose_name="Prescriptions associated with each stand")
    # 2 char code from SpatialConstraint.category (see SpatialConstraintCategories)
    spatial_constraints = models.TextField(
        default="", verbose_name='CSV List of spatial constraints to apply')

    # All output fields should be allowed to be Null/Blank
    output_scheduler_results = JSONField(null=True, blank=True)

    def constraint_set(self):
        scs = self.spatial_constraints.split(",")
        return SpatialConstraint.objects.filter(
            category__in=scs,
            geom__bboverlaps=self.input_property.geometry_final
        )

    def stand_set(self):
        return self.input_property.feature_set(feature_classes=[Stand, ])

    @property
    def output_property_results(self):
        res = self.output_scheduler_results
        if not res:
            return None
        return {'__all__': res['__all__']}

    @property
    def output_stand_results(self):
        res = self.output_scheduler_results
        if not res:
            return None
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
                'input_age_class': self.input_age_class,
                'input_target_carbon': self.input_target_carbon,
                'name': self.name,
                'output_scheduler_results': self.output_property_results,  # don't include stand-level results
                'needs_rerun': self.needs_rerun,
                'user': self.user.username,
            }
        }
        return d

    @property
    def needs_rerun(self):
        if not self.output_scheduler_results:
            return True

        results = self.output_scheduler_results

        # make sure we have exactly the same IDs
        sstand_ids = [int(x.id) for x in self.scenariostand_set.all()]
        sstand_ids.sort()
        result_ids = [int(x) for x in results.keys() if x != '__all__']
        result_ids.sort()
        sstand_id_mismatch = (sstand_ids != result_ids)

        sstand_stand_ids = list(set([int(x.stand_id) for x in self.scenariostand_set.all()]))
        sstand_stand_ids.sort()
        stand_ids = [int(x.id) for x in self.stand_set()]
        stand_ids.sort()
        stand_id_mismatch = (sstand_stand_ids != stand_ids)

        # make sure the scenario date modified is after the stands nn timestamp
        time_mismatch = False
        stand_nn_edit = max([x.nn_savetime for x in self.stand_set()])
        stand_mod = datetime_to_unix(max([x.date_modified for x in self.stand_set()]))
        scenario_mod = datetime_to_unix(self.date_modified)
        if stand_nn_edit > scenario_mod or stand_mod > scenario_mod:
            # at least one stand has been updated since last time scenario was run
            time_mismatch = True

        if sstand_id_mismatch or stand_id_mismatch or time_mismatch:
            return True

        return False

    @property
    def is_runnable(self):
        stands_w_rx = [x for x in self.input_rxs.keys()]
        for stand in self.stand_set():
            if not stand.cond_id:
                logger.debug("%s not runnable; %s does not have .cond_id" % (self.uid, stand.uid))
                return False
            if not (stand.id in stands_w_rx or str(stand.id) in stands_w_rx):
                logger.debug("%s not runnable; %s not in self.input_rxs" % (self.uid, stand.uid))
                return False
        return True

    def run(self):
        if not self.is_runnable:
            raise ScenarioNotRunnable("%s is not runnable; each stand needs a condition ID" % self.uid)

        task = schedule_harvest.delay(self.id)
        cache.set("Taskid_%s" % self.uid, task.task_id)
        return True

    def geojson(self, srid=None):
        res = self.output_stand_results
        stand_data = []
        for stand in self.scenariostand_set.all():
            try:
                stand_dict = loads(stand.geojson())
            except:
                import ipdb; ipdb.set_trace()
                continue
            stand_dict['properties']['id'] = stand.pk
            stand_dict['properties']['scenario'] = self.pk

            stand_results = None
            if res:
                try:
                    stand_results = res[stand.pk]
                except KeyError:
                    stand_results = res[str(stand.pk)]  # if it's a string

            stand_dict['properties']['results'] = stand_results
            stand_data.append(stand_dict)

        gj = dumps(stand_data, indent=2)
        # madrona doesn't expect an array/list of features here
        # we have to hack it by removing the []
        if gj.startswith("["):
            gj = gj[1:]
        if gj.endswith("]"):
            gj = gj[:-1]
        return gj

    @property
    def valid_rx_ids(self):
        return [x.id for x in Rx.objects.filter(variant=self.input_property.variant)]

    def clean(self):
        """
        this shows up in the form as form.non_field_errors
        """
        inrx = self.input_rxs
        valid_stand_ids = [x.pk for x in self.input_property.feature_set(feature_classes=[Stand])]
        for stand, rx in inrx.items():
            if int(stand) not in valid_stand_ids:
                raise ValidationError(
                    '%s is not a valid stand id for this property' % stand)
            if rx not in self.valid_rx_ids:
                raise ValidationError('%s is not a valid Rx id' % rx)
        return True

    def save(self, *args, **kwargs):
        super(Scenario, self).save(*args, **kwargs)
        if 'rerun' in kwargs and kwargs['rerun'] is False:
            pass  # don't rerun
        else:
            try:
                self.run()
            except ScenarioNotRunnable:
                pass  # don't have enough info to run()

    class Options:
        form = "trees.forms.ScenarioForm"
        form_template = "trees/scenario_form.html"
        verbose_name = 'Forest Scenario'
        form_context = {}
        links = (
            edit('Run Scenario',
                 'trees.views.run_scenario',
                 edits_original=True,
                 select='single'),
        )


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


class IdbSummary(models.Model):
    plot_id = models.BigIntegerField(null=True, blank=True)
    cond_id = models.BigIntegerField(primary_key=True)
    sumofba_ft2 = models.FloatField(null=True, blank=True)
    avgofba_ft2_ac = models.FloatField(null=True, blank=True)
    avgofht_ft = models.FloatField(null=True, blank=True)
    avgoftpa = models.FloatField(null=True, blank=True)
    avgofdbh_in = models.FloatField(null=True, blank=True)
    state_name = models.CharField(max_length=40, blank=True, null=True)
    county_name = models.CharField(max_length=100, blank=True, null=True)
    halfstate_name = models.CharField(max_length=100, blank=True, null=True)
    forest_name = models.CharField(max_length=510, blank=True, null=True)
    acres = models.FloatField(null=True, blank=True)
    acres_vol = models.FloatField(null=True, blank=True)
    fia_forest_type_name = models.CharField(
        max_length=60, blank=True, null=True)
    latitude_fuzz = models.FloatField(null=True, blank=True)
    longitude_fuzz = models.FloatField(null=True, blank=True)
    aspect_deg = models.IntegerField(null=True, blank=True)
    stdevofaspect_deg = models.FloatField(null=True, blank=True)
    firstofaspect_deg = models.IntegerField(null=True, blank=True)
    slope = models.IntegerField(null=True, blank=True)
    stdevofslope = models.FloatField(null=True, blank=True)
    avgofslope = models.FloatField(null=True, blank=True)
    elev_ft = models.IntegerField(null=True, blank=True)
    fvs_variant = models.CharField(max_length=4, blank=True, null=True)
    site_species = models.IntegerField(null=True, blank=True)
    site_index_fia = models.IntegerField(null=True, blank=True)
    plant_assoc_code = models.CharField(max_length=20, blank=True, null=True)
    countofsubplot_id = models.BigIntegerField(null=True, blank=True)
    qmd_hwd_cm = models.FloatField(null=True, blank=True)
    qmd_swd_cm = models.FloatField(null=True, blank=True)
    qmd_tot_cm = models.FloatField(null=True, blank=True)
    calc_aspect = models.IntegerField(null=True, blank=True)
    calc_slope = models.IntegerField(null=True, blank=True)
    stand_size_class = models.IntegerField(null=True, blank=True)
    site_class_fia = models.IntegerField(null=True, blank=True)
    stand_age_even_yn = models.CharField(max_length=2, blank=True, null=True)
    stand_age = models.IntegerField(null=True, blank=True)
    for_type = models.IntegerField(null=True, blank=True)
    for_type_secdry = models.IntegerField(null=True, blank=True)
    for_type_name = models.CharField(max_length=60, blank=True, null=True)
    for_type_secdry_name = models.CharField(
        max_length=60, blank=True, null=True)
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
        plot_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % (
            self.longitude_fuzz, self.latitude_fuzz))
        plot_centroid.transform(settings.EQD_SRID)
        return plot_centroid

    @property
    @cachemethod('IdbSummary-%(cond_id)s')
    def _dict(self):
        '''
        Plot characteristics according to the FCID
        '''
        summary = {
            'cond_id': self.cond_id,
            'for_type_name': self.for_type_name,
            'for_type_secdry_name': self.for_type_secdry_name,
            'cancov': self.cancov,
            'stndhgt_stunits': self.stndhgt,
            'sdi': self.sdi,
            'age_dom': self.age_dom,
            'qmda_dom_stunits': self.qmda_dom_stunits,
            'baa_ge_3_stunits': self.baa_ge_3_stunits,
            'tph_ge_3_stunits': self.tph_ge_3_stunits,
            'bac_prop': self.bac_prop,
        }
        return summary

# based on the "Paired" color palette from ColorBrewer
colors_rgb = [
    (166, 206, 227), (31, 120, 180), (178, 223, 138),
    (51, 160, 44), (251, 154, 153), (227, 26, 28),
    (253, 191, 111), (255, 127, 0), (202, 178, 214),
    (106, 61, 154), (255, 255, 153), (177, 89, 40)
]
color_hex = ['#%02x%02x%02x' % rgb_tuple for rgb_tuple in colors_rgb]


@register
class Strata(DirtyFieldsMixin, Feature):
    search_age = models.FloatField()
    search_tpa = models.FloatField()
    additional_desc = models.TextField(blank=True, null=True)
    stand_list = JSONField()  # {'classes': [(species, age class, tpa), ...]}

    @property
    def _dict(self):
        """ Make sure obj._dict is json-serializable """
        dct = self.__dict__
        dct['uid'] = self.uid
        dct['pk'] = self.pk
        rmfields = ['_state', 'object_id', 'content_type_id',
                    'date_modified', 'date_created', '_original_state']
        for fld in rmfields:
            try:
                del dct[fld]
            except KeyError:
                pass
        return dct

    def candidates(self, min_candidates=5):
        from plots import get_candidates
        return get_candidates(self.stand_list['classes'], min_candidates=min_candidates)

    @property
    def desc(self):
        return "description created from stand list attrs"

    class Options:
        form = "trees.forms.StrataForm"
        links = (
            alternate('Add Stands',
                      'trees.views.add_stands_to_strata',
                      type="application/json",
                      select='single'),
        )

    def save(self, *args, **kwargs):
        # Depending on what changed, trigger recalc of stand info
        recalc_required = False
        dirty = self.get_dirty_fields()
        if 'stand_list' in dirty.keys() or 'search_age' in dirty.keys() or \
           'search_tpa' in dirty.keys() or not self.id:
             # got new strata info - time to recalc terrain rasters for each stand!
                recalc_required = True

        if 'classes' not in self.stand_list:
            raise Exception("Not a valid stand list. " +
                            "Looking for \"{'classes': [(species, age class, tpa), ...]}\".")
        for cls in self.stand_list['classes']:
            try:
                assert(len(cls) == 4)
                # c[0] is valid species?
                assert(TreeliveSummary.objects.filter(fia_forest_type_name=cls[0]).count() > 0)
                # c[1] thru c[2] is valid diam class ? TODO actually query the database
                assert(cls[1] < cls[2])
                # c[3] is a valid tpa
                assert(cls[3] > 0 and cls[3] < 5000)
            except:
                raise Exception("Not a valid stand list. " +
                                "Looking for \"{'classes': [(species, age class, tpa), ...]}\".")
        super(Strata, self).save(*args, **kwargs)

        if recalc_required:
            # null out nearest neighbor field
            # (post-save signal must be triggered so can't use qs.update)
            for stand in self.stand_set.all():
                stand.cond_id = None
                stand.save()


class TreeliveSummary(models.Model):
    class_id = models.BigIntegerField(primary_key=True)
    plot_id = models.BigIntegerField(null=True, blank=True)
    cond_id = models.BigIntegerField(null=True, blank=True)
    varname = models.CharField(max_length=60, blank=True)
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


class ConditionVariantLookup(models.Model):
    """
    Instead of making a M2M relationship on IdbSummary, we will maintain this table
    (which is easier to generate in ArcGIS based on variant buffers)

    However, it is more difficult to maintain referential integrity so the
       ConditionVariantLookup.check_integrity()
    classmethod should be used whenever FVSVariant, IdbSummary or this table is updated
    """
    cond_id = models.BigIntegerField(db_index=True)
    variant_code = models.CharField(max_length=2)

    @classmethod
    def check_integrity(cls):
        cond_ids = [x.cond_id for x in IdbSummary.objects.all()]
        variant_codes = [x.code for x in FVSVariant.objects.all()]

        # check that all lookups have valid references
        for cvl in cls.objects.all():
            if cvl.cond_id not in cond_ids:
                raise Exception("ConditionVariantLookup table referen in the lookup tableces cond_id " +
                                "%s which doesn't exist in IdbSummary" % cvl.cond_id)
            if cvl.variant_code not in variant_codes:
                raise Exception("ConditionVariantLookup table references variant code " +
                                "%s which doesn't exist in FVSVariant" % cvl.variant_code)

        # check that all IdbSummaries are present in the lookup table
        lookup_cond_ids = [x.cond_id for x in cls.objects.all()]
        for cond_id in cond_ids:
            if cond_id not in lookup_cond_ids:
                raise Exception("Missing cond_id %s from ConditionVariantLookup table" % cond_id)

        return True


# Shapefile-backed models
class County(models.Model):
    fips = models.IntegerField()
    cntyname = models.CharField(max_length=23)
    polytype = models.IntegerField()
    stname = models.CharField(max_length=2)
    soc_cnty = models.IntegerField()
    cnty_fips = models.IntegerField()
    st_fips = models.IntegerField()
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()


class FVSVariant(models.Model):
    code = models.CharField(max_length=3)
    fvsvariant = models.CharField(max_length=100)
    decision_tree_xml = models.TextField(default="")
    #decision_tree_xml is validated in the admin.py form
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.fvsvariant, self.code)


# Auto-generated `LayerMapping` dictionaries for shapefile-backed models
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


# Auto-generated `LayerMapping` dictionary for FVSVariant model
fvsvariant_mapping = {
    'code': 'FVSVARIANT',
    'fvsvariant': 'VariantNm',
    'geom': 'MULTIPOLYGON',
}


def load_shp(path, feature_class):
    '''
    First run ogrinspect to generate the class and mapping.
        python manage.py ogrinspect ../data/fvs_variant/lot_fvsvariant_3857.shp \
            FVSVariant --mapping --srid=3857 --multi
    Paste code into models.py and modify as necessary.
    Finally, load the shapefile:
        from trees import models
        models.load_shp('../data/fvs_variants/lot_fvsvariant_3857.shp', models.FVSVariant)
    '''
    mapping = eval("%s_mapping" % feature_class.__name__.lower())
    print "Saving", path, "to", feature_class, "using", mapping
    map1 = LayerMapping(
        feature_class, path, mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=True)


class Rx(models.Model):
    variant = models.ForeignKey(FVSVariant)
    internal_name = models.TextField()
    internal_desc = models.TextField()

    def __unicode__(self):
        return u"Rx %s" % (self.internal_name)

@register
class MyRx(Feature):
    # name  (inherited)
    rx = models.ForeignKey(Rx)
    description = models.TextField(default="")

    @property
    def _dict(self):
        return {
            'user_id': self.user_id,
            'rx_id': self.rx.id,
            'myrx_id': self.uid,
            'name': self.name,
            'description': self.description,
            'rx_internal_name': self.rx.internal_name,
            'internal_desc': self.rx.internal_desc,
        } 

    class Options:
        form = "trees.forms.MyRxForm"
        form_template = "trees/myrx_form.html"
        manipulators = []

SpatialConstraintCategories = [
    ('R1', 'RiparianBuffers1'),
    ('R2', 'RiparianBuffers2'),
]


class SpatialConstraint(models.Model):
    geom = models.PolygonField(srid=3857)
    default_rx = models.ForeignKey(Rx)
    category = models.CharField(max_length=2, choices=SpatialConstraintCategories)
    objects = models.GeoManager()

    def __unicode__(self):
        return u"SpatialConstraint %s %s" % (self.category, self.geom.wkt[:80])


@register
class ScenarioStand(PolygonFeature):
    """
    Populated as the scenario is created (tasks.schedule_harvest)
    The result of a spatial intersection between
      1. Stands for this scenario
      2. All SpatialConstraints chosen for this scenario
    The Rx from #2 takes precedence over the Rx from #1.
    """
    # geometry_final = inherited from PolygonFeature
    cond_id = models.BigIntegerField()
    rx = models.ForeignKey(Rx)
    scenario = models.ForeignKey(Scenario)
    stand = models.ForeignKey(Stand)
    constraint = models.ForeignKey(SpatialConstraint, null=True)
    # assert that all cond_ids are present or make FK?

    class Options:
        form = "trees.forms.ScenarioStandForm"
        form_template = "trees/scenariostand_form.html"
        manipulators = []

    @cachemethod("ScenarioStand_%(id)s_geojson")
    def geojson(self, srid=None):
        # start with the stand geojson
        gj = self.stand.geojson()
        gjf = loads(gj)

        # swap for new attr
        gjf['geometry'] = loads(self.geometry_final.json)
        gjf['properties']['uid'] = self.uid
        gjf['date_modified'] = str(self.date_modified)
        gjf['date_created'] = str(self.date_created)
        #TODO add new scenariostand-specific attrs
        gjf['properties']['rx'] = self.rx.internal_name
        try:
            gjf['properties']['constraint'] = self.constraint.category
        except AttributeError:
            gjf['properties']['constraint'] = None
        gjf['properties']['scenario_uid'] = self.scenario.uid
        gjf['properties']['stand_uid'] = self.stand.uid
        return dumps(gjf)


# Signals
# Handle the triggering of asyncronous processes
@receiver(post_save, sender=Stand)
def postsave_stand_handler(sender, *args, **kwargs):
    st = kwargs['instance']

    savetime = datetime_to_unix(postgres_now())

    has_terrain = False
    if st.elevation and st.slope and st.aspect and st.cost:
        has_terrain = True

    if not has_terrain and not st.strata:
        # just impute terrain rasters"
        impute_rasters.apply_async(args=(st.id, savetime))
    elif not st.cond_id and not has_terrain and st.strata:
        # impute terrain rasters THEN calculate nearest neighbor"
        impute_rasters.apply_async(args=(st.id, savetime),
                                   link=impute_nearest_neighbor.s(savetime))
    elif has_terrain and st.strata and not st.cond_id:
        # just calculate nearest neighbors"
        impute_nearest_neighbor.apply_async(args=(st.id, savetime))
    else:
        # we already have all aux data; no need to call any async processes
        # (assuming the model save has nulled out the appropos fields)
        pass


@receiver(pre_delete, sender=Strata)
def delete_strata_handler(sender, *args, **kwargs):
    '''
    When a strata is deleted, make sure to set all stand's cond_id to null
    '''
    instance = kwargs['instance']
    instance.stand_set.all().update(
        cond_id=None, strata=None,
        nn_savetime=datetime_to_unix(datetime.datetime.now())
    )
