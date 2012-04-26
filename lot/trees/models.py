#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from madrona.common.utils import get_logger, cachemethod
from operator import itemgetter
from django.core.cache import cache
logger = get_logger()

@register
class Stand(PolygonFeature):
    RX_CHOICES = (
        ('--', '--'),
        ('RE', 'Reserve; No Action'),
        ('UG', 'Uneven-aged Group Selection'),
        ('SW', 'Shelterwood'),
        ('CT', 'Commercial Thinning'),
        ('CC', 'Even-aged Clearcut'),
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
        from trees.utils import classify_aspect  # avoid circular import
        def int_or_none(val):
            try:
                newval = int(val)
            except:
                newval = None
            return newval

        elevation = int_or_none(self.imputed_elevation)
        aspect = int_or_none(self.imputed_aspect)
        aspect_class = classify_aspect(aspect)
        slope = int_or_none(self.imputed_slope)
        gnn = int_or_none(self.imputed_gnn)

        d = {
                'uid': self.uid,
                'name': self.name,
                'rx': self.get_rx_display(),
                'domspp': self.domspp,
                'elevation': elevation,
                'aspect': "%s" % aspect_class,
                'slope': '%s %%' % slope,
                'gnn': gnn,
                'plot_summaries': self.plot_summaries,
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
            #TODO confirm
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
            summaries.append(summary)
        return summaries

    def save(self, *args, **kwargs):
        # placeholder for future save overrides
        super(Stand, self).save(*args, **kwargs)

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
    def acres(self):
        try:
            area_m = self.geometry_final.area 
        except:
            return None
        conversion = 0.000247105381 
        area_acres = area_m * conversion
        return area_acres

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
    fcid = models.BigIntegerField(primary_key=True)
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
                'tph_ge_3': self.baa_ge_3,
                'bac_prop': self.bac_prop,
            }
        return summary

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
