#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import math
import random
import time
import operator
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.simplejson import dumps, loads
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit, get_feature_by_uid
from madrona.common.utils import clean_geometry
from madrona.common.utils import get_logger
from django.core.cache import cache
from django.contrib.gis.geos import GEOSGeometry
from trees.tasks import impute_rasters, impute_nearest_neighbor, schedule_harvest
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import connection
from celery.result import AsyncResult
from collections import defaultdict

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
            cond_id = self.cond_id
            cond_age = IdbSummary.objects.get(cond_id=cond_id).age_dom
            cond_stand_list = list(x.treelist for x in
                                  TreeliveSummary.objects.filter(cond_id=cond_id))
        else:
            cond_id = None
            cond_age = None
            cond_stand_list = []

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
            'cond_id': cond_id,
            'condition_age': cond_age,
            'condition_stand_list': cond_stand_list,
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

    def check_or_create_default_myrxs(self):
        """
        based on RX_TYPE_CHOICES, check for all default myrxs and create them if they don't exist
        """
        myrxs = self.feature_set(feature_classes=[MyRx, ])
        for rx_choice in RX_TYPE_CHOICES:
            if rx_choice[0] == "NA":
                # don't create default myrx for NA rxs
                continue
            matching_myrxs = [x for x in myrxs if x.rx.internal_type == rx_choice[0]]
            if len(matching_myrxs) == 0:
                try:
                    rx = Rx.objects.get(variant=self.variant, internal_type=rx_choice[0])
                except Rx.DoesNotExist:
                    logger.warning("Rx with type %s doesn't exist in %s" % (rx_choice[0], self.variant))
                    continue
                m1 = MyRx(name=rx_choice[1], rx=rx, user=self.user)
                m1.save()
                m1.add_to_collection(self)
                m1.save()

    def create_default_scenarios(self):
        """
        Create two scenarios for the property (should only be called if self.is_runnable)
        """
        if not self.is_runnable:
            return

        if Scenario.objects.filter(input_property=self, name="Grow Only").count() == 0:
            rxs = Rx.objects.filter(internal_type='GO', variant=self.variant)
            if not rxs.count() > 0:
                return
            rx = rxs[0]
            in_rxs = {}
            for stand in self.feature_set(feature_classes=[Stand]):
                in_rxs[stand.id] = rx.id

            s1 = Scenario(user=self.user,
                          input_property=self,
                          name="Grow Only",
                          description="No management activities; allow natural regeneration for entire time period.",
                          input_target_boardfeet=0,
                          input_target_carbon=True,
                          input_rxs=in_rxs,
                          input_age_class=10,
                          )
            s1.save()
            s1.run()

        if Scenario.objects.filter(input_property=self, name="Conventional Even-Aged").count() == 0:
            rxs = Rx.objects.filter(internal_type='CI', variant=self.variant)
            if not rxs.count() > 0:
                return
            rx = rxs[0]
            in_rxs = {}
            for stand in self.feature_set(feature_classes=[Stand]):
                in_rxs[stand.id] = rx.id

            s2 = Scenario(user=self.user,
                          input_property=self,
                          name="Conventional Even-Aged",
                          description="Even-aged management for timber. 40-year rotation clear cut.",
                          input_target_boardfeet=2000,
                          input_target_carbon=False,
                          input_rxs=in_rxs,
                          input_age_class=1,
                          )
            s2.save()
            s2.run()

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
        # ensure multipolygon validity
        if self.geometry_final:
            self.geometry_final = clean_geometry(self.geometry_final)
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

    # contains dictionary of {scenariostand id: offset}
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
    @cachemethod("Scenario_%(id)s_property_metrics")
    def output_property_metrics(self):
        """
        Note the data structure for stands is different than properties
        (stands are optimized for openlayers map while property-level works with jqplot)
        """
        d = {
            "agl_carbon": [],
            "total_carbon": [],
            "harvested_timber": [],
            "standing_timber": [],
            "cum_harvest": [],
        }
        sql = """SELECT
                    a.year AS year,
                    SUM(a.total_stand_carbon * ss.acres) AS total_carbon,
                    SUM(a.agl * ss.acres) AS agl_carbon,
                    SUM(a.removed_merch_bdft * ss.acres)/1000.0 AS harvested_timber, -- convert to mbf
                    SUM(a.after_merch_bdft * ss.acres)/1000.0 AS standing_timber -- convert to mbf
                FROM
                    trees_fvsaggregate a
                JOIN
                    trees_scenariostand ss
                  ON  a.cond = ss.cond_id
                  AND a.rx = ss.rx_internal_num
                  AND a.offset = ss.offset
                -- WHERE a.site = 2 -- TODO if we introduce multiple site classes, we need to fix
                AND   a.var = '%s' -- get variant_code from current property
                AND   ss.scenario_id = %d -- get id from current scenario
                GROUP BY a.year
                ORDER BY a.year;""" % (self.input_property.variant.code, self.id)

        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        cum_harvest = 0
        for rawrow in cursor.fetchall():
            row = dict(zip([col[0] for col in desc], rawrow))
            date = "%d-12-31 11:59PM" % row['year']
            d['agl_carbon'].append([date, row['agl_carbon']])
            d['total_carbon'].append([date, row['total_carbon']])
            d['harvested_timber'].append([date, row['harvested_timber']])
            d['standing_timber'].append([date, row['standing_timber']])

            cum_harvest += row['harvested_timber']
            d['cum_harvest'].append([date, cum_harvest])

        return {'__all__': d}

    @property
    @cachemethod("Scenario_%(id)s_stand_metrics")
    def output_stand_metrics(self):
        """
        Note the data structure for stands is different than properties
        (stands are optimized for openlayers map while property-level works with jqplot)
        stands are normalized to area (i.e. values are per-acre)
        """
        d = {}
        scenariostands = self.scenariostand_set.all()
        for sstand in scenariostands:
            d[sstand.pk] = {
                "years": [],
                "total_carbon": [],
                "agl_carbon": [],
                "standing_timber": [],
                "harvested_timber": [],
                "cum_harvest": [],
            }

        sql = """SELECT
                    ss.id AS sstand_id, a.cond, a.rx, a.year, a.offset, ss.acres AS acres,
                    a.total_stand_carbon AS total_carbon,
                    a.agl AS agl_carbon,
                    a.removed_merch_bdft / 1000.0 AS harvested_timber, -- convert to mbf
                    a.after_merch_bdft / 1000.0 AS standing_timber -- convert to mbf
                FROM
                    trees_fvsaggregate a
                JOIN
                    trees_scenariostand ss
                  ON  a.cond = ss.cond_id
                  AND a.rx = ss.rx_internal_num
                  AND a.offset = ss.offset
                -- WHERE a.site = 2 -- TODO if we introduce multiple site classes, we need to fix
                AND   var = '%s' -- get from current property
                AND   ss.scenario_id = %d -- get from current scenario
                ORDER BY ss.id, a.year;""" % (self.input_property.variant.code, self.id)

        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        cum_harvest_dict = {}
        for rawrow in cursor.fetchall():
            row = dict(zip([col[0] for col in desc], rawrow))
            ds = d[row["sstand_id"]]
            ds['years'].append(row["year"])
            ds['agl_carbon'].append(row["agl_carbon"])
            ds['total_carbon'].append(row["total_carbon"])
            ds['standing_timber'].append(row["standing_timber"])
            ds['harvested_timber'].append(row["harvested_timber"])

            if row['sstand_id'] not in cum_harvest_dict:
                cum_harvest_dict[row['sstand_id']] = 0

            cum_harvest_dict[row['sstand_id']] += row["harvested_timber"]
            ds['cum_harvest'].append(cum_harvest_dict[row['sstand_id']])

        return d

    @property
    @cachemethod("Scenario_%(id)s_cash_metrics")
    def output_cash_metrics(self):
        from forestcost import main_model
        from forestcost import routing
        from forestcost import landing

        sql = """SELECT
                    ss.id AS sstand_id,
                    a.cond, a.rx, a.year, a.offset,
                    ST_AsText(ss.geometry_final) AS stand_wkt,
                    ss.acres         AS acres,
                    a.LG_CF          AS LG_CF,
                    a.LG_HW          AS LG_HW,
                    a.LG_TPA         AS LG_TPA,
                    a.SM_CF          AS SM_CF,
                    a.SM_HW          AS SM_HW,
                    a.SM_TPA         AS SM_TPA,
                    a.CH_CF          AS CH_CF,
                    a.CH_HW          AS CH_HW,
                    a.CH_TPA         AS CH_TPA,
                    stand.elevation  AS elev,
                    stand.slope      AS slope,
                    a.CUT_TYPE       AS CUT_TYPE
                FROM
                    trees_fvsaggregate a
                JOIN
                    trees_scenariostand ss
                  ON  a.cond = ss.cond_id
                  AND a.rx = ss.rx_internal_num
                  AND a.offset = ss.offset
                JOIN trees_stand stand
                  ON ss.stand_id = stand.id
                -- WHERE a.site = 2 -- TODO if we introduce multiple site classes, we need to fix
                WHERE   var = '%s' -- get from current property
                AND   ss.scenario_id = %d -- get from current scenario
                ORDER BY a.year, ss.id;""" % (self.input_property.variant.code, self.id)

        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        rows = [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
            if None not in row  # remove any nulls; incomplete data can't be used
        ]

        # Landing Coordinates
        center = self.input_property.geometry_final.point_on_surface
        centroid_coords = center.transform(4326, clone=True).tuple
        landing_coords = landing.landing(centroid_coords=centroid_coords)

        haulDist, haulTime, coord_mill = routing.routing(
            landing_coords, mill_shp=settings.MILL_SHAPEFILE
        )

        annual_total_cost = defaultdict(float)
        annual_haul_cost = defaultdict(float)
        annual_heli_harvest_cost = defaultdict(float)
        annual_ground_harvest_cost = defaultdict(float)
        annual_cable_harvest_cost = defaultdict(float)
        used_records = 0
        skip_noharvest = 0
        skip_error = 0

        year = None
        years = []
        for row in rows:
            if year != int(row['year']):
                year = int(row['year'])
                years.append(year)
                annual_total_cost[year] += 0
                annual_haul_cost[year] += 0
                annual_heli_harvest_cost[year] += 0
                annual_ground_harvest_cost[year] += 0
                annual_cable_harvest_cost[year] += 0

            ### Tree Data ###
            # Cut type code indicating type of harvest implemented.
            # 0 = no harvest, 1 = pre-commercial thin,
            # 2 = commercial thin, 3 = regeneration harvest
            try:
                cut_type = int(row['cut_type'])
            except:
                # no harvest so don't attempt to calculate
                cut_type = 0

            # PartialCut(clear cut = 0, partial cut = 1)
            if cut_type == 3:
                PartialCut = 0
            elif cut_type in [1, 2]:
                PartialCut = 1
            else:
                # no harvest so don't attempt to calculate
                skip_noharvest += 1
                continue

            cost_args = (
                # stand info
                row['acres'], row['elev'], row['slope'], row['stand_wkt'],
                # harvest info
                row['ch_tpa'], row['ch_cf'],
                row['sm_tpa'], row['sm_cf'],
                row['lg_tpa'], row['lg_cf'],
                row['ch_hw'], row['sm_hw'], row['lg_hw'],
                PartialCut,
                # routing info
                landing_coords, haulDist, haulTime, coord_mill
            )

            try:
                result = main_model.cost_func(*cost_args)
                annual_haul_cost[year] += result['total_haul_cost']
                annual_total_cost[year] += result['total_cost']

                system = result['harvest_system']
                if system.startswith("Helicopter"):
                    annual_heli_harvest_cost[year] += result['total_harvest_cost']
                elif system.startswith("Ground"):
                    annual_ground_harvest_cost[year] += result['total_harvest_cost']
                elif system.startswith("Cable"):
                    annual_cable_harvest_cost[year] += result['total_harvest_cost']
                else:
                    # TODO
                    raise ValueError
                used_records += 1
            except (ZeroDivisionError, ValueError):
                skip_error += 1

        def ordered_costs(x):
            sorted_x = sorted(x.iteritems(), key=operator.itemgetter(0))
            return [-1 * z[1] for z in sorted_x]

        data = {}
        data['heli'] = ordered_costs(annual_heli_harvest_cost)
        data['cable'] = ordered_costs(annual_cable_harvest_cost)
        data['ground'] = ordered_costs(annual_ground_harvest_cost)
        data['haul'] = ordered_costs(annual_haul_cost)
        data['years'] = sorted(annual_haul_cost.keys())

        # Just make a random attempt at revenue; TODO HACK
        import numpy as np
        total_cost = np.array(data['heli']) + np.array(data['cable']) + \
            np.array(data['ground']) + np.array(data['haul'])
        gross = [-1 * x * (1.0 + (1.35 - (random.random() * 1.75))) for x in total_cost.tolist()]
        net = (np.array(gross) + total_cost).tolist()
        data['gross'] = gross
        data['net'] = net

        return data

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
                'output_property_metrics': self.output_property_metrics,  # don't include stand-level results
                'needs_rerun': self.needs_rerun,
                'property_is_runnable': self.input_property.is_runnable,
                'is_runnable': self.is_runnable,
                'is_running': self.is_running,
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

    @property
    def is_running(self):
        # determine if there is already a process running using the redis cache
        taskid = cache.get('Taskid_%s' % self.uid)
        if taskid:
            task = AsyncResult(taskid)
            status = task.status
            print status
            if status not in ["SUCCESS", "FAILED", "FAILURE"]:
                # still running
                return True
            else:
                return False
        else:
            return False

    def run(self):
        self.invalidate_cache()
        if not self.is_runnable:
            raise ScenarioNotRunnable("%s is not runnable; each stand needs a condition ID" % self.uid)
        task = schedule_harvest.delay(self.id)
        cache.set("Taskid_%s" % self.uid, task.task_id)
        return True

    def geojson(self, srid=None):
        res = self.output_stand_metrics
        stand_data = []
        for stand in self.scenariostand_set.all():
            try:
                stand_dict = loads(stand.geojson())
            except:
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

        if not inrx:
            inrx = {}
            # don't raise validation error, just proceed with empty dict

        valid_stand_ids = [x.pk for x in self.input_property.feature_set(feature_classes=[Stand])]
        for stand, rx in inrx.items():
            if int(stand) not in valid_stand_ids:
                raise ValidationError(
                    '%s is not a valid stand id for this property' % stand)
            if rx not in self.valid_rx_ids:
                raise ValidationError('%s is not a valid Rx id' % rx)
        return True

    def invalidate_cache(self):
        '''
        Remove any cached values associated with this stand.
        '''
        if not self.id:
            return True
        # assume that all related keys will start with Scenario_<id>_*
        # depends on django-redis as the cache backend!!!
        key_pattern = "Scenario_%d_*" % self.id
        cache.delete_pattern(key_pattern)
        assert cache.keys(key_pattern) == []
        return True

    def fill_with_default_rxs(self):
        """
        check self.input_rxs
        if it's missing any stand keys,
            add them with the default rx_id for the variant
        """
        default_rx = self.input_property.variant.default_rx
        new_input_rxs = self.input_rxs.copy()
        stands_w_rx = [x for x in self.input_rxs.keys()]
        for stand in self.stand_set():
            if not (stand.id in stands_w_rx or str(stand.id) in stands_w_rx):
                #scenario not runnable; stand not in self.input_rxs
                new_input_rxs[str(stand.id)] = default_rx.id
        self.input_rxs = new_input_rxs

    def save(self, *args, **kwargs):
        self.invalidate_cache()
        super(Scenario, self).save(*args, **kwargs)
        self.fill_with_default_rxs()
        super(Scenario, self).save(*args, **kwargs)
        if 'rerun' in kwargs and kwargs['rerun'] is False:
            pass  # don't rerun
        else:
            try:
                self.run()
            except ScenarioNotRunnable:
                pass  # don't have enough info to run()

    class Meta:
        ordering = ['-date_modified']

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
            # Link to calculate cash flow metrics for a scenario
            alternate('Scenario Cash Flow',
                      'trees.views.scenario_cash_flow',
                      type="application/json",
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

    @property
    def desc(self):
        return "description created from stand list attrs"

    class Options:
        form = "trees.forms.StrataForm"
        # not the actual form template, just container for validation errors
        form_template = "trees/strata_form.html"
        links = (
            alternate('Add Stands',
                      'trees.views.add_stands_to_strata',
                      type="application/json",
                      select='single'),
        )

    def clean(self):
        """
        Ensure that the stand list is valid and gives us some candidates
        this shows up in the form as form.non_field_errors
        """

        if 'classes' not in self.stand_list or 'property' not in self.stand_list:
            raise ValidationError("Not a valid stand list object. " +
                                  "Looking for \"{'property': 'trees_forestproperty_<id>', " +
                                  "classes': [(species, min_dbh, max_dbh, tpa),...]}\".")

        for cls in self.stand_list['classes']:
            if len(cls) != 4:
                raise ValidationError("Each stand list class needs 4 entries: species, min_dbh, max_dbh, tpa")

        try:
            fp = get_feature_by_uid(self.stand_list['property'])
            variant = fp.variant
        except:
            raise ValidationError("Cannot look up variant from stand list.property")

        from plots import get_candidates, NearestNeighborError
        min_candidates = 1
        try:
            candidates = get_candidates(self.stand_list['classes'], variant.code, min_candidates)
        except NearestNeighborError:
            raise ValidationError("Stand list did not return enough candidate plots.")

        if len(candidates) < min_candidates:
            raise ValidationError("Stand list did not return enough candidate plots.")

        return True

    def save(self, *args, **kwargs):
        # Depending on what changed, trigger recalc of stand info
        recalc_required = False
        dirty = self.get_dirty_fields()
        if 'stand_list' in dirty.keys() or 'search_age' in dirty.keys() or \
           'search_tpa' in dirty.keys() or not self.id:
             # got new strata info - time to recalc terrain rasters for each stand!
                recalc_required = True

        super(Strata, self).save(*args, **kwargs)

        if recalc_required:
            # null out nearest neighbor field
            # (post-save signal must be triggered so can't use qs.update)
            for stand in self.stand_set.all():
                stand.cond_id = None
                stand.save()

        for stand in self.stand_set.all():
            #print "Invalidating ", stand
            stand.invalidate_cache()


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

    @property
    def treelist(self):
        return [self.fia_forest_type_name, int(self.calc_dbh_class - 1),
                int(self.calc_dbh_class + 1), self.sumoftpa]

    def __unicode__(self):
        return u"cond::%s (%s %d in X %d tpa) %s %% total BA" % (
            self.cond_id, self.fia_forest_type_name, self.calc_dbh_class, self.sumoftpa, self.pct_of_totalba)


class ConditionVariantLookup(models.Model):
    """
    Instead of making a M2M relationship on IdbSummary, we will maintain this table
    (which is easier to generate in ArcGIS based on variant buffers)

    However, it is more difficult to maintain referential integrity so the
    check_integrity management command should be used 
    whenever FVSVariant, IdbSummary or this table is updated
    """
    cond_id = models.BigIntegerField(db_index=True)
    variant_code = models.CharField(max_length=2)


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

    @property
    def default_rx(self):
        """
        The default rx for the variant
        currently defined as the first GO rx
        """
        return Rx.objects.filter(variant=self, internal_type="GO")[0]


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


# Used to determine
# a) the grow-only Rx for a given variant
# b) all non-NA Rx types get autopopulated as default myrxs
RX_TYPE_CHOICES = (
    ('NA', 'N/A'),
    ('GO', 'Grow Only, No Management Actions'),
    ('CI', 'Conventional, Even-aged, Short rotation'),
)


class Rx(models.Model):
    variant = models.ForeignKey(FVSVariant)
    internal_name = models.TextField()
    internal_desc = models.TextField()
    # type used to identify e.g. the industrial prescription for a variant
    internal_type = models.CharField(max_length=2, choices=RX_TYPE_CHOICES, default="NA")

    def __unicode__(self):
        return u"Rx %s" % (self.internal_name)

    @property
    def internal_num(self):
        """
        Strip the variant to match with FVS records e.g. "WC17" => 17
        Assumes a 2 char preceding variant code
        """
        return int(self.internal_name[2:])


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
            'internal_type': self.rx.internal_type,
        }

    class Meta:
        ordering = ['date_modified']

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
    # assert that all cond_ids are present or make FK?
    cond_id = models.BigIntegerField()
    rx = models.ForeignKey(Rx)
    rx_internal_num = models.IntegerField(null=True, blank=True)
    scenario = models.ForeignKey(Scenario)
    stand = models.ForeignKey(Stand)
    constraint = models.ForeignKey(SpatialConstraint, null=True)
    acres = models.FloatField()
    offset = models.IntegerField(default=0)

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
        gjf['properties']['rx'] = self.rx.internal_name
        try:
            gjf['properties']['constraint'] = self.constraint.category
        except AttributeError:
            gjf['properties']['constraint'] = None
        gjf['properties']['scenario_uid'] = self.scenario.uid
        gjf['properties']['stand_uid'] = self.stand.uid
        return dumps(gjf)

    def save(self, *args, **kwargs):
        # ensure this gets calculated and put in the db
        # why? So raw sql query on FVSAggregate can avoid yet another join to the Rx table
        self.rx_internal_num = self.rx.internal_num
        super(ScenarioStand, self).save(*args, **kwargs)


class FVSAggregate(models.Model):
    """
    Model to hold all FVS growth-and-yield results
    Each object/row represents a single
    variant/condition/offset/rx/year combination
    """
    agl = models.FloatField(null=True, blank=True)
    bgl = models.FloatField(null=True, blank=True)
    calc_carbon = models.FloatField(null=True, blank=True)
    cond = models.IntegerField()
    dead = models.FloatField(null=True, blank=True)
    offset = models.IntegerField()
    rx = models.IntegerField()
    site = models.IntegerField()
    total_stand_carbon = models.FloatField(null=True, blank=True)
    var = models.CharField(max_length=2)
    year = models.FloatField()
    merch_carbon_removed = models.FloatField(null=True, blank=True)
    merch_carbon_stored = models.FloatField(null=True, blank=True)
    cedr_bf = models.FloatField(null=True, blank=True)
    cedr_hrv = models.FloatField(null=True, blank=True)
    ch_cf = models.FloatField(null=True, blank=True)
    ch_hw = models.FloatField(null=True, blank=True)
    ch_tpa = models.FloatField(null=True, blank=True)
    cut_type = models.FloatField(null=True, blank=True)
    df_bf = models.FloatField(null=True, blank=True)
    df_hrv = models.FloatField(null=True, blank=True)
    es_btl = models.FloatField(null=True, blank=True)
    firehzd = models.FloatField(null=True, blank=True)
    hw_bf = models.FloatField(null=True, blank=True)
    hw_hrv = models.FloatField(null=True, blank=True)
    lg_cf = models.FloatField(null=True, blank=True)
    lg_hw = models.FloatField(null=True, blank=True)
    lg_tpa = models.FloatField(null=True, blank=True)
    lp_btl = models.FloatField(null=True, blank=True)
    mnconbf = models.FloatField(null=True, blank=True)
    mnconhrv = models.FloatField(null=True, blank=True)
    mnhw_bf = models.FloatField(null=True, blank=True)
    mnhw_hrv = models.FloatField(null=True, blank=True)
    nsodis = models.FloatField(null=True, blank=True)
    nsofrg = models.FloatField(null=True, blank=True)
    nsonest = models.FloatField(null=True, blank=True)
    pine_bf = models.FloatField(null=True, blank=True)
    pine_hrv = models.FloatField(null=True, blank=True)
    pp_btl = models.FloatField(null=True, blank=True)
    sm_cf = models.FloatField(null=True, blank=True)
    sm_hw = models.FloatField(null=True, blank=True)
    sm_tpa = models.FloatField(null=True, blank=True)
    spprich = models.FloatField(null=True, blank=True)
    sppsimp = models.FloatField(null=True, blank=True)
    sprc_bf = models.FloatField(null=True, blank=True)
    sprc_hrv = models.FloatField(null=True, blank=True)
    wj_bf = models.FloatField(null=True, blank=True)
    wj_hrv = models.FloatField(null=True, blank=True)
    ww_bf = models.FloatField(null=True, blank=True)
    ww_hrv = models.FloatField(null=True, blank=True)
    after_ba = models.IntegerField(null=True, blank=True)
    after_merch_bdft = models.IntegerField(null=True, blank=True)
    after_merch_ft3 = models.IntegerField(null=True, blank=True)
    after_total_ft3 = models.IntegerField(null=True, blank=True)
    after_tpa = models.IntegerField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    removed_merch_bdft = models.IntegerField(null=True, blank=True)
    removed_merch_ft3 = models.IntegerField(null=True, blank=True)
    removed_total_ft3 = models.IntegerField(null=True, blank=True)
    removed_tpa = models.IntegerField(null=True, blank=True)
    start_ba = models.IntegerField(null=True, blank=True)
    start_merch_bdft = models.IntegerField(null=True, blank=True)
    start_merch_ft3 = models.IntegerField(null=True, blank=True)
    start_total_ft3 = models.IntegerField(null=True, blank=True)
    start_tpa = models.IntegerField(null=True, blank=True)


# variable names are lower-case and must correspond
# exactly with FVSAggregate field names
timber_choices = (
    ('cedr_hrv', 'Cedar'),
    ('df_hrv', 'Doug fir'),
    ('hw_hrv', 'Major Hardwood'),
    ('mnconhrv', 'Minor Conifer'),
    ('mnhw_hrv', 'Minor Hardwood'),
    ('pine_hrv', 'Pine'),
    ('wj_hrv', 'Western Juniper'),
    ('ww_hrv', 'White Wood'),
    ('sprc_hrv', 'Spruce')
)


class TimberPrice(models.Model):
    """
    Average price for types of timber in different regions
    """
    variant = models.ForeignKey(FVSVariant)
    timber_type = models.CharField(max_length=10, choices=timber_choices)
    price = models.FloatField()

    def __unicode__(self):
        return "%s, %s: $%.2f per mbf" % (self.variant.code, self.get_timber_type_display(), self.price)

    class Meta:
        unique_together = ("variant", "timber_type")

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
    and invalidate the stand's caches
    '''
    instance = kwargs['instance']
    for stand in instance.stand_set.all():
        #print "Invalidating stand", stand, "after deleting strata ", instance
        stand.invalidate_cache()
    instance.stand_set.all().update(
        cond_id=None, strata=None,
        nn_savetime=datetime_to_unix(datetime.datetime.now())
    )
