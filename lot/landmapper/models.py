from django.conf import settings
from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature, MultiPolygonFeature
from django.contrib.gis.db.models import MultiPolygonField, PointField
from django.db.models import Manager as GeoManager
from madrona.features import register, alternate, edit, get_feature_by_uid
from django.contrib.postgres.fields import JSONField
# from madrona.features.forms import SpatialFeatureForm
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from landmapper.map_layers.utilities import get_bbox_as_string, get_bbox_as_polygon

def sq_meters_to_sq_miles(area_m2):
    return area_m2/2589988.11

def sq_meters_to_acres(area_m2):
    return area_m2/4046.86

"""
    From MVC/MTV Components Doc

    Flatblock (django-flatblocks)
    #Flatpage (django-flatpages)
    MenuPage (Custom)
    Taxlot (custom)
    Property (madrona polygon-feature)
        We don't want to save these - creating them on the fly may be helpful, but we'll need to delete them immediately.
    ForestType
        will all data be aggregated to a single geometric model, or will there be a forest-type lookup to go with the feature layer?
    ReportPage (optional idea)
        Could capture "Get Help" content
        Could make any future updates/additions to the report more flexible
        Would totally %$&@ with some of the proposed views below (not good).
"""

class MenuPage(models.Model):
    name = models.CharField(max_length=255, verbose_name="Menu Item")
    order = models.SmallIntegerField(default=10)
    staff_only = models.BooleanField(default=False)
    header = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Popup Header")
    content = RichTextUploadingField(null=True, blank=True, default=None, verbose_name="Popup Body",
                                        external_plugin_resources=[(
                                            'youtube',
                                            '/static/landmapper/vendor/ckeditor/youtube/',
                                            'plugin.js'
                                        )])

    def __str__(self):
        return "%s" % self.name

# @register
# class Taxlot(MultiPolygonFeature):
#
#     class Options:
#         form = 'features.forms.SpatialFeatureForm'
#         manipulators = []
#
#     class Meta:
#         abstract = False

class Taxlot(models.Model):
    class Meta:
        verbose_name = 'Taxlot'
        verbose_name_plural = 'Taxlots'
        app_label = 'landmapper'

    # ODF_FPD
    odf_fpd = models.CharField(max_length=25, null=True, blank=True, default=None)
    # Agency
    agency = models.CharField(max_length=100, null=True, blank=True, default=None)
    # orZDesc - "Elevation?"
    orzdesc = models.CharField(max_length=255, null=True, blank=True, default=None)
    # HUC12 - "Watershed"
    huc12 = models.CharField(max_length=12, null=True, blank=True, default=None)
    # Name
    name = models.CharField(max_length=120, null=True, blank=True, default=None)
    # TWNSHPNO
    # twnshpno = models.CharField(max_length=3, null=True, blank=True, default=None)
    # RANGENO
    # rangeno = models.CharField(max_length=3, null=True, blank=True, default=None)
    # FRSTDIVNO
    # frstdivno = models.CharField(max_length=10, null=True, blank=True, default=None)
    # TWNSHPLAB
    # twnshplab = models.CharField(max_length=20, null=True, blank=True, default=None)
    # MEAN, formerly ele_mean
    # mean_elevation = models.FloatField(null=True, blank=True, default=None)
    # MIN, formerly ele_min
    min_elevation = models.FloatField(null=True, blank=True, default=None)
    # MAX, formerly ele_max
    max_elevation = models.FloatField(null=True, blank=True, default=None)
    # legal_label Fully formatted legal description
    legal_label = models.CharField(max_length=255, null=True, blank=True, default=None)
    # county -- The county name that the taxlot belongs to.
    county = models.CharField(max_length=255, null=True, blank=True, default=None)
    # source -- The source for the taxlot data
    source = models.CharField(max_length=255, null=True, blank=True, default=None)
    # map_id -- the identifier of the map used by the source provider
    map_id = models.CharField(max_length=255, null=True, blank=True, default=None)
    # map_taxlot -- the identifier of the taxlot used by the source map
    map_taxlot = models.CharField(max_length=255, null=True, blank=True, default=None)

    geometry = MultiPolygonField(
        srid=3857,
        null=True, blank=True,
        verbose_name="Grid Cell Geometry"
    )
    objects = GeoManager()

    @property
    def area_in_sq_miles(self):
        true_area = self.geometry.transform(2163, clone=True).area
        return sq_meters_to_sq_miles(true_area)

    @property
    def area_in_acres(self):
        return sq_meters_to_acres(self.geometry.transform(2163, clone=True).area)

    @property
    def formatted_area(self):
        return int((self.area_in_sq_miles * 10) + .5) / 10.

    def serialize_attributes(self):
        attributes = []
        attributes.append({'title': 'Area', 'data': '%.1f sq miles' % (self.area_in_sq_miles)})
        # attributes.append({'title': 'Description', 'data': self.description})
        return { 'event': 'click', 'attributes': attributes }

    # @classmethod
    # def fill_color(self):
    #     return '776BAEFD'

    @classmethod
    def outline_color(self):
        return '776BAEFD'

    class Options:
        verbose_name = 'Taxlot'
        icon_url = None
        export_png = False
        manipulators = []
        optional_manipulators = []
        form = None
        form_template = None
        show_template = None

class SoilType(models.Model):
    mukey = models.CharField(max_length=100, null=True, blank=True, default=None)
    areasym = models.CharField(max_length=100, null=True, blank=True, default=None)
    spatial = models.FloatField(null=True, blank=True, default=None)
    musym = models.CharField(max_length=100, null=True, blank=True, default=None)
    shp_lng = models.FloatField(null=True, blank=True, default=None)
    shap_ar = models.FloatField(null=True, blank=True, default=None)
    si_label = models.CharField(max_length=255, null=True, blank=True, default=None)
    muname = models.CharField(max_length=255, null=True, blank=True, default=None)
    drclssd = models.CharField(max_length=100, null=True, blank=True, default=None)
    frphrtd = models.CharField(max_length=100, null=True, blank=True, default=None)
    avg_rs_l = models.FloatField(null=True, blank=True, default=None)
    avg_rs_h = models.FloatField(null=True, blank=True, default=None)

    geometry = MultiPolygonField(
        srid=3857,
        null=True, blank=True,
        verbose_name="Grid Cell Geometry"
    )
    objects = GeoManager()

    class Options:
        verbose_name = 'Soil Type'

class Property(MultiPolygonFeature):
    # Property name
    def report_default():
        return {}

    # image field
    property_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    aerial_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    street_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    terrain_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    stream_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    soil_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    forest_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    scalebar_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    context_scalebar_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    medium_scalebar_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)

    # alt image field
    property_map_image_alt = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)

    report_data = JSONField('report_data', default=report_default)

    @property
    def formatted_area(self):
        # return int((self.area_in_sq_miles * 10) +.5) / 10.
        area_acres = self.area_in_acres
        if area_acres < 10:
            return "%.2f" % area_acres
        if area_acres < 100:
            return "%.1f" % area_acres
        return "%.0f" % area_acres
        # return int((self.area_in_acres * 10) +.5) / 10.

    @property
    def area_in_sq_miles(self):
        return sq_meters_to_sq_miles(self.geometry_orig.area)

    @property
    def area_in_acres(self):
        return sq_meters_to_acres(self.geometry_orig.area)

    # @property
    def bbox(self, alt_size=False):       # TODO: This should be a method on property instances called 'bbox'
        # """
        # PURPOSE:
        # -   Given a Property instance, return the bounding box and preferred report orientation
        # IN:
        # -   property: An instance of landmapper's Property model
        # OUT:
        # -   (bbox[str], orientation[str]): A tuple of two strings, the first is the
        # -       string representation of the bounding box (EPSG:3857), the second is
        # -       the type of orientation the resulting report should use to print
        # -       itself
        # """

        # from landmapper.map_layers.views import get_bbox_as_string

        if hasattr(self, 'geometry_final') and self.geometry_final:
            geometry = self.geometry_final
        elif hasattr(self, 'geometry_orig') and self.geometry_orig:
            geometry = self.geometry_orig
        elif hasattr(self, 'envelope'):
            geometry = self
        else:
            print("ERROR: property type unrecognized")
            return ("ERROR", "ERROR")
        if not geometry.srid == 3857:
            geometry.transform(3857)
        envelope = geometry.envelope.coords
        # assumption: GEOSGeom.evnelope().coords returns (((W,S),(E,S),(E,N),(W,N),(W,S),),)
        west = envelope[0][0][0]
        south = envelope[0][0][1]
        east = envelope[0][2][0]
        north = envelope[0][2][1]

        property_width = abs(float(east - west))
        property_height = abs(float(north - south))

        property_ratio = property_width / property_height

        if abs(property_ratio) > 1.0 and settings.REPORT_SUPPORT_ORIENTATION:  # wider than tall and portrait reports allowed
            if alt_size:
                target_width = settings.REPORT_MAP_ALT_WIDTH
                target_height = settings.REPORT_MAP_ALT_HEIGHT
                orientation = 'portrait'
            else:
                target_width = settings.REPORT_MAP_HEIGHT
                target_height = settings.REPORT_MAP_WIDTH
                orientation = 'portrait'

        else:
            if alt_size:
                target_width = float(settings.REPORT_MAP_ALT_WIDTH)
                target_height = float(settings.REPORT_MAP_ALT_HEIGHT)
                orientation = 'landscape'
            else:
                target_width = float(settings.REPORT_MAP_WIDTH)
                target_height = float(settings.REPORT_MAP_HEIGHT)
                orientation = 'landscape'

        target_ratio = target_width / target_height
        pixel_width = target_width * (1 - settings.REPORT_MAP_MIN_BUFFER)
        pixel_height = target_height * (1 - settings.REPORT_MAP_MIN_BUFFER)

        # compare envelope ratio to target image ratio to make sure we constrain the correct axis first
        if property_ratio >= target_ratio: # limit by width
            coord_per_pixel = property_width / pixel_width
            buffer_width_pixel = target_width * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_width_coord = abs(buffer_width_pixel * coord_per_pixel)
            property_pixel_height = property_height / coord_per_pixel
            height_diff = target_height - property_pixel_height
            buffer_height_pixel = height_diff / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
        else:   # limit by height
            coord_per_pixel = property_height / pixel_height
            buffer_height_pixel = target_height * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
            property_pixel_width = property_width / coord_per_pixel
            width_diff = target_width - property_pixel_width
            buffer_width_pixel = width_diff / 2
            buffer_width_coord = abs(buffer_width_pixel * coord_per_pixel)

        box_west = west - buffer_width_coord
        box_east = east + buffer_width_coord
        box_north = north + buffer_height_coord
        box_south = south - buffer_height_coord


        return (get_bbox_as_string([box_west,box_south,box_east,box_north]), orientation)

    class Options:
        form = 'features.forms.SpatialFeatureForm'
        manipulators = []

    class Meta:
        abstract = False

class PopulationPoint(models.Model):
    classification = models.CharField(max_length=100, default='city')
    state = models.CharField(max_length=30, default='OR')
    population = models.IntegerField()
    place_fips = models.IntegerField()
    density_sqmi = models.FloatField(null=True, blank=True, default=None)
    area_sqmi = models.FloatField(null=True, blank=True, default=None)
    population_class = models.SmallIntegerField(null=True, blank=True, default=None)

    geometry = PointField(
        srid=3857,
        null=True, blank=True,
        verbose_name="Population Center Geometry"
    )

    class Options:
        verbose_name = 'Population Center'

class ForestType(models.Model):
    id = models.BigIntegerField(primary_key=True)
    # row_id = models.BigIntegerField()
    # col_id = models.BigIntegerField()
    # tile_id = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Row, Col")
    fortype = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Forest Type")
    symbol = models.CharField(max_length=10, default=None)
    # comp_over = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Overall Composition")
    # comp_ab = models.TextField(null=True, blank=True, default=None, verbose_name="Abundant Species")
    # comp_min = models.TextField(null=True, blank=True, default=None, verbose_name="Minor Species")
    can_class = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Cover Class")
    # can_cr_min = models.FloatField(null=True, blank=True, default=None, verbose_name="Canopy Cover Min Range")
    # can_cr_max = models.FloatField(null=True, blank=True, default=None, verbose_name="Canopy Cover Max Range")
    # can_h_min = models.FloatField(null=True, blank=True, default=None, verbose_name="Canopy Height Min")
    # can_h_max = models.FloatField(null=True, blank=True, default=None, verbose_name="Canopy Height Max")
    diameter = models.CharField(max_length=255, null=True, blank=True, default=None, verbose_name="Tree Size Class")
    # tree_r_min = models.FloatField(null=True, blank=True, default=None, verbose_name="Tree Size Est. Range Min")
    # tree_r_max = models.FloatField(null=True, blank=True, default=None, verbose_name="Tree Size Est. Range Max")

    geometry = MultiPolygonField(
        srid=3857,
        null=True, blank=True,
        verbose_name="Grid Cell Geometry"
    )
    objects = GeoManager()

    class Options:
        verbose_name = 'Forest Type'
