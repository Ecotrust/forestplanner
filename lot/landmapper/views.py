import decimal
from django.shortcuts import render
from django.conf import settings
from flatblocks.models import FlatBlock
from django.contrib.humanize.templatetags import humanize

def unstable_request_wrapper(url, retries=0):
    # """
    # unstable_request_wrapper
    # PURPOSE: As mentioned above, the USDA wfs service is weak. We wrote this wrapper
    # -   to fail less.
    # IN:
    # -   'url': The URL being requested
    # -   'retries': The number of retries made on this URL
    # OUT:
    # -   contents: The html contents of the requested page
    # """
    import urllib.request
    try:
        contents = urllib.request.urlopen(url)
        if retries > 0:
            print('succeeded to connect after %d tries to %s' % (retries, url))
    except ConnectionError as e:
        if retries < 10:
            print('failed [%d time(s)] to connect to %s' % (retries, url))
            contents = unstable_request_wrapper(url, retries+1)
        else:
            print("ERROR: Unable to connect to %s" % url)
            contents = None
    except Exception as e:
        print(e)
        print(url)
        contents = False
    return contents

def get_soil_data_gml(bbox, srs='EPSG:4326',format='GML3'):
    # """
    # get_soil_data_gml
    # PURPOSE: given a bounding box, SRS, and preferred version (format) of GML,
    # -   return an OGR layer read from the GML response (from unstable_request_wrapper)
    # IN:
    # -   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
    # -   srs: The Spatial Reference System used to interpret the coordinates
    # -       default: 'EPSG:4326'
    # -   format: The version of GML to use (GML2 or GML3)
    # -       default: 'GML3'
    # OUT:
    # -   gml_result: an OGR layer interpreted from the GML
    # """
    from tempfile import NamedTemporaryFile
    from osgeo import ogr
    endpoint = settings.SOIL_WFS_URL
    request = 'SERVICE=WFS&REQUEST=GetFeature&VERSION=%s&' % settings.SOIL_WFS_VERSION
    layer = 'TYPENAME=%s&' % settings.SOIL_DATA_LAYER
    projection = 'SRSNAME=%s&' % srs
    bbox = 'BBOX=%s' % get_bbox_as_string(bbox)
    gml = '&OUTPUTFORMAT=%s' % format
    url = "%s?%s%s%s%s%s" % (endpoint, request, layer, projection, bbox, gml)
    contents = unstable_request_wrapper(url)
    fp = NamedTemporaryFile()
    if contents:
        fp.write(contents.read())
    gml_result = ogr.Open(fp.name)
    fp.close()
    return gml_result

def get_soils_list(bbox, srs='EPSG:4326',format='GML3'):
    # """
    # get_soils_list
    # PURPOSE:
    # IN:
    # -   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
    # -   srs: The Spatial Reference System used to interpret the coordinates
    # -       default: 'EPSG:4326'
    # -   format: The version of GML to use (GML2 or GML3)
    # -       default: 'GML3'
    # OUT:
    # -   gml: an OGR layer interpreted from the GML
    # """
    bbox = get_bbox_as_string(bbox)
    gml = get_soil_data_gml(bbox, srs, format)
    inLayer = gml.GetLayerByIndex(0)

    inLayerDefn = inLayer.GetLayerDefn()

    soils_list = {}
    inLayer.ResetReading()
    for i in range(0, inLayer.GetFeatureCount()):
        feat = inLayer.GetNextFeature()
        feat_dict = {}
        if not feat.GetField(settings.SOIL_ID_FIELD) in soils_list.keys():
            for j in range(0, inLayerDefn.GetFieldCount()):
                field_name = inLayerDefn.GetFieldDefn(j).GetName()
                if field_name in settings.SOIL_FIELDS.keys() and settings.SOIL_FIELDS[field_name]['display']:
                    feat_dict[field_name] = feat.GetField(field_name)
            soils_list[feat.GetField(settings.SOIL_ID_FIELD)] = feat_dict

    return soils_list

def geocode(search_string, srs=4326, service='arcgis'):
    # """
    # geocode
    # PURPOSE: Convert a provided place name into geographic coordinates
    # IN:
    # -   search_string: (string) An address or named landmark/region
    # -   srs: (int) The EPSG ID for the spatial reference system in which to output coordinates
    # -       defaut: 4326
    # -   service: (string) The geocoding service to query for a result
    # -       default = 'arcgis'
    # -       other supported options: 'google'
    # OUT:
    # -   coords: a list of two coordinate elements -- [lat(y), long(x)]
    # -       projected in the requested coordinate system
    # """

    # https://geocoder.readthedocs.io/
    import geocoder

    g = False
    # Query desired service
    if service.lower() == 'arcgis':
        g = geocoder.arcgis(search_string)
    elif service.lower() == 'google':
        if hasattr(settings, 'GOOGLE_API_KEY'):
            g = geocoder.google(search_string, key=settings.GOOGLE_API_KEY)
        else:
            print('To use Google geocoder, please configure "GOOGLE_API_KEY" in your project settings. ')
    if not g or not g.ok:
        print('Selected geocoder not available or failed. Defaulting to ArcGIS')
        g = geocoder.arcgis(search_string)

    coords = g.latlng

    # Transform coordinates if necessary
    if not srs == 4326:
        from django.contrib.gis.geos import GEOSGeometry
        if ':' in srs:
            try:
                srs = srs.split(':')[1]
            except Exception as e:
                pass
        try:
            int(srs)
        except ValueError as e:
            print('ERROR: Unable to interpret provided srs. Please provide a valid EPSG integer ID. Providing coords in EPSG:4326')
            return coords

        point = GEOSGeometry('SRID=4326;POINT (%s %s)' % (coords[1], coords[0]), srid=4326)
        point.transform(srs)
        coords = [point.coords[1], point.coords[0]]

    return coords

def get_property_from_taxlot_selection(request, taxlot_list):
    """
    PURPOSE:
    -   Given a list of taxlots, unify them into a single property object
    IN:
    -   List of at least 1 taxlot
    OUT:
    -   One multipolygon property record (unsaved)
    """
    # NOTE: Create a property without adding to the database with Property()
    #   SEE: https://stackoverflow.com/questions/26672077/django-model-vs-model-objects-create
    from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
    from landmapper.models import Property
    # get_taxlot_user
    user = request.user

    # Collect taxlot geometries
    geometries = [x.geometry_final for x in taxlot_list]

    # Merge taxlot geometries
    merged_geom = False
    for geom in geometries:
        if not merged_geom:
            merged_geom = geom
        else:
            merged_geom = merged_geom.union(geom)

    merged_geom = MultiPolygon(merged_geom.unary_union,)

    # Create Property object (don't use 'objects.create()'!)
    property = Property(user=user, geometry_orig=merged_geom, name='test_property')

    return property

def getHeaderMenu(context):
    # Get MenuPage content for pages
    # get_menu_page(<name of MenuPage>)
    #   returns None | MenuPage
    about_page = get_menu_page('about')
    help_page = get_menu_page('help')

    # add pages to context dict
    context['about_page'] = about_page
    context['help_page'] = help_page

    return context


def getPanelButtonsCreateReport(context):

    context['btn_back_href'] = '/landmapper/'
    context['btn_next_href'] = 'property_name'
    context['btn_create_maps_href'] = '/landmapper/report/'
    context['btn_next_disabled'] = 'disabled'; # disabled is a css class for <a> tags

    return context

# Create your views here.
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_sameorigin
@xframe_options_sameorigin
def get_taxlot_json(request):
    from django.contrib.gis.geos import GEOSGeometry
    from django.http import HttpResponse
    from .models import Taxlot
    import json
    coords = request.GET.getlist('coords[]') # must be [lon, lat]
    intersect_pt = GEOSGeometry('POINT(%s %s)' % (coords[0], coords[1]))
    try:
        lot = Taxlot.objects.get(geometry__intersects=intersect_pt)
        lot_json = lot.geometry.wkt
        lot_id = lot.id
    except:
        lots = Taxlot.objects.filter(geometry__intersects=intersect_pt)
        if len(lots) > 0:
            lot = lots[0]
            lot_json = lot.geometry.json
            lot_id = lot.id
        else:
            lot_json = []
            lot_id = lot.id
    return HttpResponse(json.dumps({"id": lot_id, "geometry": lot_json}), status=200)

def home(request):
    '''
    Land Mapper: Home Page
    '''
    # Get aside content Flatblock using name of Flatblock
    aside_content = 'aside-home'
    if len(FlatBlock.objects.filter(slug=aside_content)) < 1:
        # False signals to template that it should not evaluate
        aside_content = False

    context = {
        'aside_content': aside_content,
        'show_panel_buttons': False,
        'q_address': 'Enter your property address here',
    }
    # context = getPanelButtonsCreateReport(context)
    context = getHeaderMenu(context)

    return render(request, 'landmapper/landing.html', context)

def index(request):
    '''
    Land Mapper: Index Page
    (landing: slide 1)
    '''
    return render(request, 'landmapper/landing.html', context)

def identify(request):
    '''
    Land Mapper: Identify Pages
    IN
        coords
        search string
        (opt) taxlot ids
        (opt) property name
    OUT
        Rendered Template
    '''
    # Get aside content Flatblock using name of Flatblock
    aside_content = 'aside-map-pin'
    if len(FlatBlock.objects.filter(slug=aside_content)) < 1:
        # False signals to template that it should not evaluate
        aside_content = False

    if request.method == 'POST':
        if request.POST.get('q-address'):
            q_address = request.POST.get('q-address')
            q_address_value = request.POST.get('q-address')
            coords = geocode(q_address)
        else:
            q_address = 'Enter your property address here'

        if coords:
            context = {
                'coords': coords,
                'q_address': q_address,
                'q_address_value': q_address_value,
                'aside_content': aside_content,
                'show_panel_buttons': True,
            }
            context = getPanelButtonsCreateReport(context)
            context = getHeaderMenu(context)
            return render(request, 'landmapper/landing.html', context)
    else:
        print('requested identify page with method other than POST')

    return home(request)

def create_property_id(request):
    '''
    Land Mapper: Create Property Cache ID
    IN

    '''
    from django.http import HttpResponse
    from django.utils.http import urlencode
    from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
    from .models import Taxlot, Property
    import json

    if request.method == 'POST':
        property_name = request.POST.get('property_name')
        taxlot_ids = request.POST.getlist('taxlot_ids[]')

        # modifies request for anonymous user
        if not (hasattr(request, 'user') and request.user.is_authenticated) and settings.ALLOW_ANONYMOUS_DRAW:
            from django.contrib.auth.models import User
            user = User.objects.get(pk=settings.ANONYMOUS_USER_PK)
        else:
            user = request.user

        property_id = generate_property_id(taxlot_ids, property_name)
        return HttpResponse(json.dumps({'property_id':property_id}), status=200)

    else:

        return HttpResponse('Improper request method', status=405)

    return HttpResponse('Create property failed', status=402)

def report(request, property_id):
    '''
    Land Mapper: Report Pages
    Report (slides 5-7a)
    IN
        taxlot ids
        property name
    OUT
        Rendered Template
        Uses: CreateProperty, CreatePDF, ExportLayer, BuildLegend, BuildTables
    '''
    from django.http import HttpResponse
    import json

    property = get_property_by_id(property_id)

    context = {
        'property_id': property_id,
        'property_name': property.name,
        'property': property,
        'property_report': property.report_data,
    }

    context = getHeaderMenu(context)

    return render(request, 'landmapper/report/report.html', context)

def get_property_report(property, taxlots):
    # TODO: call this in "property" after creating the object instance
    from landmapper.map_layers import views as map_views

    # calculate orientation, w x h, bounding box, centroid, and zoom level
    property_specs = get_property_specs(property)
    property_layer = map_views.get_property_image_layer(property, property_specs)
    # TODO (Sara is creating the layer now)
    taxlot_layer = map_views.get_taxlot_image_layer(property_specs)

    aerial_layer = map_views.get_aerial_image_layer(property_specs)
    street_layer = map_views.get_street_image_layer(property_specs)
    topo_layer = map_views.get_topo_image_layer(property_specs)
    soil_layer = map_views.get_soil_image_layer(property_specs)
    stream_layer = map_views.get_stream_image_layer(property_specs)

    property.property_map_image = map_views.get_property_map(property_specs, base_layer=aerial_layer, property_layer=property_layer)
    property.aerial_map_image = map_views.get_aerial_map(property_specs, base_layer=aerial_layer, lots_layer=taxlot_layer, property_layer=property_layer)
    property.street_map_image = map_views.get_street_map(property_specs, base_layer=street_layer, lots_layer=taxlot_layer, property_layer=property_layer)
    property.terrain_map_image = map_views.get_terrain_map(property_specs, base_layer=topo_layer, property_layer=property_layer)
    if settings.STREAMS_BASE_LAYER == 'aerial':
        stream_base_layer = aerial_layer
    else:
        stream_base_layer = topo_layer
    property.stream_map_image = map_views.get_stream_map(property_specs, base_layer=stream_base_layer, stream_layer=stream_layer, property_layer=property_layer)
    property.soil_map_image = map_views.get_soil_map(property_specs, base_layer=aerial_layer, lots_layer=taxlot_layer, soil_layer=soil_layer, property_layer=property_layer)
    property.scalebar_image = map_views.get_scalebar_image(property_specs, span_ratio=0.75)

    property.report_data = get_property_report_data(property, property_specs, taxlots)

def get_property_report_data(property, property_specs, taxlots):
    report_data = {
        # '${report_page_name}': {
        #     'data': [ 2d array, 1 row for each entry, 1 column for each attr, 1st col is name],
        # }
    }
    report_pages = ['property', 'aerial', 'street', 'terrain', 'streams','soils','forest_type']

    #Property
    property_data = get_aggregate_property_data(property, taxlots)


    report_data['property'] = {
        'data': property_data,
        'legend': None
    }

    #aerial
    aerial_data = None

    report_data['aerial'] = {
        'data': aerial_data,
        'legend': settings.AERIAL_MAP_LEGEND_URL
    }

    #street
    street_data = None

    report_data['street'] = {
        'data': street_data,
        'legend': settings.STREET_MAP_LEGEND_URL
    }

    #terrain
    terrain_data = None

    report_data['terrain'] = {
        'data': terrain_data,
        'legend': settings.TERRAIN_MAP_LEGEND_URL
    }

    #streams
    streams_data = None

    report_data['streams'] = {
        'data': streams_data,
        'legend': settings.STREAM_MAP_LEGEND_URL
    }

    #soils
    soil_data = get_soils_data(property_specs)

    report_data['soils'] = {
        'data': soil_data,
        'legend': settings.SOIL_MAP_LEGEND_URL
    }

    #forest_type
    forest_type_data = None

    report_data['forest_type'] = {
        'data': forest_type_data,
        'legend': settings.FOREST_TYPE_MAP_LEGEND_URL
    }

    return report_data

def get_aggregate_property_data(property, taxlots):
    acres = []
    sq_miles = []
    min_elevation = []
    max_elevation = []
    legal = []
    odf_fpd = []
    agency = []
    orzdesc = []
    huc12 = []
    name = []
    twnshpno = []
    rangeno = []
    frstdivno = []
    # mean_elevation = []

    for taxlot in taxlots:
        acres.append(taxlot.acres)
        min_elevation.append(taxlot.elev_min_1)
        max_elevation.append(taxlot.elev_max_1)
        legal.append("Section %s, Township %s, Range %s" % (taxlot.frstdivno, taxlot.twnshpno, taxlot.rangeno))
        agency.append(taxlot.agency)
        odf_fpd.append(taxlot.odf_fpd)
        name.append(taxlot.name)
        huc12.append(taxlot.huc12)
        orzdesc.append(taxlot.orzdesc)
        # twnshpno.append(taxlot.twnshpno)
        # rangeno.append(taxlot.rangeno)
        # frstdivno.append(taxlot.frstdivno)

    return [
        ['Acres', pretty_print_float(sq_ft_to_acres(aggregate_sum(acres)))],
        ['Square Miles', pretty_print_float(sq_ft_to_sq_mi(aggregate_sum(acres)))],
        ['Min Elevation', pretty_print_float(aggregate_min(min_elevation))],
        ['Max Elevation', pretty_print_float(aggregate_max(max_elevation))],
        ['Legal Description', aggregate_strings(legal)],
        ['Structural Fire Disctrict', aggregate_strings(agency)],
        ['Forest Fire District', aggregate_strings(odf_fpd)],
        ['Watershed', aggregate_strings(name)],
        ['Watershed (HUC)', aggregate_strings(huc12)],
        ['Zoning', aggregate_strings(orzdesc)]
        # ['twnshpno', aggregate_strings(twnshpno)],
        # ['rangeno', aggregate_strings(rangeno)],
        # ['frstdivno', aggregate_strings(frstdivno)],
    ]

def aggregate_strings(agg_list):
    agg_list = [x for x in agg_list if not x == None]
    out_str = '; '.join(list(dict.fromkeys(agg_list)))
    if len(out_str) == 0:
        out_str = "None"
    return out_str

def aggregate_min(agg_list):
    out_min = None
    for min in agg_list:
        if out_min == None:
            out_min = min
        if min:
            if min < out_min:
                out_min = min
    return out_min

def aggregate_max(agg_list):
    out_max = None
    for max in agg_list:
        if out_max == None:
            out_max = max
        if max:
            if max > out_max:
                out_max = max
    return out_max

def aggregate_mean(agg_list):
    mean_sum = 0
    for mean in agg_list:
        if not mean == None:
            mean_sum += mean
    return mean_sum/len(agg_list)

def aggregate_sum(agg_list):
    sum_total = 0
    for sum in agg_list:
        if not sum == None:
            sum_total += sum
    return sum_total

def sq_ft_to_acres(sq_ft_val):
    return sq_ft_val/43560

def sq_ft_to_sq_mi(sq_ft_val):
    return sq_ft_val/27878400

def pretty_print_float(value):
    if isinstance(value, (int, float, decimal.Decimal)):
        if abs(value) >= 1000000:
            return humanize.intword(round(value))
        elif abs(value) >= 1000:
            return humanize.intcomma(round(value))
        elif abs(value) >= 100:
            return str(round(value))
        elif abs(value) >= 1:
            return format(value, '.3g')
        else:
            return format(value, '.3g')
    else:
        return str(value)


def get_property_specs(property):
    from landmapper.map_layers import views as map_views
    property_specs = {
        'orientation': None,# 'portrait' or 'landscape'
        'width': None,      # Pixels
        'height': None,     # Pixels
        'bbox': None,       # "W,S,E,N" (EPSG:3857, Web Mercator)
        'zoom': None        # {'lat': (EPSG:4326 float), 'lon': (EPSG:4326 float), 'zoom': float}
    }
    (bbox, orientation) = map_views.get_bbox_from_property(property)

    property_specs['orientation'] = orientation
    property_specs['bbox'] = bbox

    width = settings.REPORT_MAP_WIDTH
    height = settings.REPORT_MAP_HEIGHT

    if orientation.lower() == 'portrait' and settings.REPORT_SUPPORT_ORIENTATION:
        temp_width = width
        width = height
        height = temp_width

    property_specs['width'] = width
    property_specs['height'] = height

    property_specs['zoom'] = map_views.get_web_map_zoom(bbox, width=width, height=height, srs='EPSG:3857')

    return property_specs

def generate_property_id(taxlot_ids, property_name):
    '''
    Land Mapper: Generate Property ID

    PURPOSE:
        Create a unique id for combination of taxlots and user provided name
    IN:
        taxlot_ids
        property_name
    OUT:
        string of sorted taxlots preceeded by slugified property name
        e.g.: my-property|01234|2731001|80085
    '''
    from django.utils.text import slugify
    property_id = slugify(property_name)
    sorted_taxlots = sorted(taxlot_ids)
    id_elements = [str(x) for x in [property_id,] + sorted_taxlots]
    join_id_elements = '|'.join(id_elements)
    return join_id_elements

def parse_property_id(property_id):
    '''
    Land Mapper: Parse Property ID

    PURPOSE:
        Extract the property name and taxlots from a property id
    IN:
        property_id
    OUT (dict):
        name
        taxlot_ids
        e.g.: my-property|01234|2731001|80085
    '''
    id_elements = property_id.split('|')
    name = id_elements.pop(0)
    name = name.title()
    return {
        'name': name,
        'taxlot_ids': id_elements,
    }

def create_property(taxlot_ids, property_name, user_id=False):
    # '''
    # Land Mapper: Create Property
    #
    # TODO:
    #     can a memory instance of feature be made as opposed to a database feature
    #         meta of model (ref: madrona.features) to be inherited?
    #         don't want this in a database
    #         use a class (python class) as opposed to django model class?
    #     add methods to class for
    #         creating property
    #         turn into shp
    #         CreatePDF, ExportLayer, BuildLegend, BuildTables?
    #     research caching approaches
    #         django docs
    #         django caching API
    # '''
    '''
    (called before loading 'Report', cached)
    IN:
        taxlot_ids[ ]
        property_name
    OUT:
        Madrona polygon feature
    NOTES:
        CACHE THESE!!!!
    '''
    from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
    from django.contrib.auth.models import User
    from .models import Taxlot, Property
    import json

    # modifies request for anonymous user
    if settings.ALLOW_ANONYMOUS_DRAW:
        if settings.ANONYMOUS_USER_PK:
            user = User.objects.get(pk=settings.ANONYMOUS_USER_PK)
        else:
            user = User.objects.all()[0]
    elif user_id:
        user = User.objects.get(pk=user_id)

    # taxlot_geometry = {}
    taxlot_multipolygon = False

    taxlots = Taxlot.objects.filter(pk__in=taxlot_ids)

    for lot in taxlots:
        # lot = Taxlot.objects.get(pk=lot_id)
        if not taxlot_multipolygon:
            taxlot_multipolygon = lot.geometry
            # taxlot_multipolygon = MultiPolygon(taxlot_multipolygon)
        else:
            taxlot_multipolygon = taxlot_multipolygon.union(lot.geometry)


    # Create Property object (don't use 'objects.create()'!)
    # now create property from cache id on report page
    if type(taxlot_multipolygon) == Polygon:
        taxlot_multipolygon = MultiPolygon(taxlot_multipolygon)

    property = Property(user=user, geometry_orig=taxlot_multipolygon, name=property_name)

    get_property_report(property, taxlots)

    return property

def get_property_by_id(property_id):
    from django.core.cache import cache
    from django.contrib.sites import shortcuts

    property = cache.get('%s' % property_id)

    if not property:
        property_dict = parse_property_id(property_id)
        property = create_property(property_dict['taxlot_ids'], property_dict['name'])
        if not property.report_data['soils']['data'][0][0] == 'Error':
            # Cache for 1 week
            cache.set('%s' % property_id, property, 60*60*24*7)

    return property


def get_property_map_image(request, property_id, map_type):
    from django.http import HttpResponse
    from PIL import Image

    property = get_property_by_id(property_id)

    if map_type == 'stream':
        image = property.stream_map_image
    elif map_type == 'street':
        image = property.street_map_image
    elif map_type == 'aerial':
        image = property.aerial_map_image
    elif map_type == 'soil_types':
        image = property.soil_map_image
    elif map_type == 'property':
        image = property.property_map_image
    elif map_type == 'terrain':
        image = property.terrain_map_image
    else:
        image = None

    response = HttpResponse(content_type="image/png")
    image.save(response, 'PNG')

    return response

def get_scalebar_image(request, property_id):
    from django.http import HttpResponse
    from PIL import Image

    property = get_property_by_id(property_id)
    image = property.scalebar_image
    response = HttpResponse(content_type="image/png")
    image.save(response, 'PNG')

    return response

def get_menu_page(name):
    '''
    PURPOSE:
        Get a MenuPage
        Used for modals
    IN:
        name (str): MenuPage name given through Django admin
    OUT:
        MenuPage (obj): MenuPage with matching name

    '''
    from landmapper.models import MenuPage

    page = MenuPage.objects.get(name=name)
    if not page:
        page = None

    return page

def create_street_report(request):
    '''
    (slide 7b)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
        BuildLegend
    '''
    return render(request, 'landmapper/base.html', {})

def create_terrain_report(request):
    '''
    (slide 7b)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
        BuildLegend
    '''
    return render(request, 'landmapper/base.html', {})

def create_streams_report(request):
    '''
    (slide 7b)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
        BuildLegend
    '''
    return render(request, 'landmapper/base.html', {})

def create_forest_type_report(request):
    '''
    (Slide 7c)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
        BuildLegend
    '''
    return render(request, 'landmapper/base.html', {})

def create_soil_report(request):
    '''
    (Slides 7d-f)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
        BuildLegend, BuildTable, GetSoilsData, (API Wrapper?)
    '''
    return render(request, 'landmapper/base.html', {})

def create_property_pdf_id(property_id):
    property_pdf_id = property_id + '_pdf'
    return property_pdf_id

def get_property_pdf_by_id(property_id):
    from django.core.cache import cache
    from django.contrib.sites import shortcuts

    property_pdf_id = create_property_pdf_id(property_id)
    property_pdf = cache.get('%s' % property_pdf_id)

    if not property_pdf:
        property = get_property_by_id(property_id)
        property_pdf = create_property_pdf(property, property_id)
        if property_pdf:
            cache.set('%s' % property_pdf_id, property_pdf, 60*60*24*7)

    return property_pdf

def get_property_pdf(request, property_id):
    from django.contrib.sites import shortcuts
    from django.http import HttpResponse

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="property.pdf"'

    property_pdf = get_property_pdf_by_id(property_id)

    response.write(property_pdf)

    return response

def create_property_pdf(property, property_id):
    '''
    HOW TO CREATE PDFs
    ----------
    template_pdf_file : str
        path to path to the template PDF
    rendered_pdf : function (dict)
        dict - fields to populate and the values to populate them with
        function - uses pdfjinja to crete pdf
    output_file_location : str, path to file
        path to the PDF output file that will be generated
    '''
    import os
    import io
    import datetime
    import PyPDF2 as pypdf
    from django.http import HttpResponse
    from pdfjinja import PdfJinja
    import requests
    from tempfile import NamedTemporaryFile
    from django.core import files

    property_url = settings.APP_URL + '/report/' + property_id + '/property/map'
    aerial_url = settings.APP_URL + '/report/' + property_id + '/aerial/map'
    street_url = settings.APP_URL + '/report/' + property_id + '/street/map'
    terrain_url = settings.APP_URL + '/report/' + property_id + '/terrain/map'
    stream_url = settings.APP_URL + '/report/' + property_id + '/stream/map'
    soil_types_url = settings.APP_URL + '/report/' + property_id + '/soil_types/map'
    scalebar_url = settings.APP_URL + '/report/' + property_id + '/scalebar'

    get_property_image = requests.get(property_url, stream=True)
    get_aerial_image = requests.get(aerial_url, stream=True)
    get_street_image = requests.get(street_url, stream=True)
    get_terrain_image = requests.get(terrain_url, stream=True)
    get_stream_image = requests.get(stream_url, stream=True)
    get_soil_image = requests.get(soil_types_url, stream=True)
    get_scalebar_image = requests.get(scalebar_url, stream=True)

    tmp_property = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_property_name = tmp_property.name
    with open(tmp_property_name, 'wb') as f:
        for chunk in get_property_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_aerial = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_aerial_name = tmp_aerial.name
    with open(tmp_aerial_name, 'wb') as f:
        for chunk in get_aerial_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_street = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_street_name = tmp_street.name
    with open(tmp_street_name, 'wb') as f:
        for chunk in get_street_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_topo = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_topo_name = tmp_topo.name
    with open(tmp_topo_name, 'wb') as f:
        for chunk in get_terrain_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_stream = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_stream_name = tmp_stream.name
    with open(tmp_stream_name, 'wb') as f:
        for chunk in get_stream_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_soils = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_soils_name = tmp_soils.name
    with open(tmp_soils_name, 'wb') as f:
        for chunk in get_soil_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_scalebar = NamedTemporaryFile(suffix='.png', dir=settings.PROPERTY_REPORT_PDF_DIR, delete=True)
    tmp_scalebar_name = tmp_scalebar.name
    with open(tmp_scalebar_name, 'wb') as f:
        for chunk in get_scalebar_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # 1. write API to create local URL /landmapper/overview_map/{{ taxlot_ids }}/
    # 2. wirte .... /rest of maps

    # 1. give each image a unique name
    # 2. write images to media as files
    # 3. create PDF
    # 4. assign pdf to variable
    # 5. delete image files
    # 6. return pdf variable

    template_pdf_file = settings.PROPERTY_REPORT_PDF_TEMPLATE
    template_pdf = PdfJinja(template_pdf_file)

    current_datetime = datetime.datetime.now()
    current_datetime = current_datetime.strftime("%c")

    rendered_pdf = template_pdf({
        'date': str(current_datetime),
        'propName': property.name,
        'acres' : property.report_data['property']['data'][0][1],
        'elevation' : property.report_data['property']['data'][2][1],
        'legalDesc' : property.report_data['property']['data'][4][1],
        'structFire' : property.report_data['property']['data'][5][1],
        'fire' : property.report_data['property']['data'][6][1],
        'watershed' : property.report_data['property']['data'][7][1],
        'watershedNum' : property.report_data['property']['data'][8][1],
        'zone' : property.report_data['property']['data'][9][1],
        'introAerialImagery': tmp_property_name,
        'propName2': property.name,
        'aerial' :  tmp_aerial_name,
        'scale' :  tmp_scalebar_name,
        'directions': tmp_street_name,
        'scale_directions' :  tmp_scalebar_name,
        'topo': tmp_topo_name,
        'hydro': tmp_stream_name,
        'soils': tmp_soils_name,
    })

    rendered_pdf_name = property.name + '.pdf'

    if os.path.exists(settings.PROPERTY_REPORT_PDF_DIR):
        output_pdf = os.path.join(settings.PROPERTY_REPORT_PDF_DIR, rendered_pdf_name)
        rendered_pdf.write(open(output_pdf, 'wb'))
    else:
        print('Directory does not exit')

    get_property_image.close()
    get_aerial_image.close()
    get_soil_image.close()
    get_street_image.close()
    get_terrain_image.close()
    get_stream_image.close()
    get_scalebar_image.close()

    if os.path.exists(output_pdf):
        buffer = io.BytesIO()
        new_output = pypdf.PdfFileWriter()
        new_pdf = pypdf.PdfFileReader(output_pdf)
        for page in range(new_pdf.getNumPages()):
            new_output.addPage(new_pdf.getPage(page))
        new_output.write(buffer)
        # buffer.seek(0)
        return buffer.getvalue()
    else:
        raise FileNotFoundError('Failed to produce output file.')

def export_layer(request):
    '''
    (called on request for download GIS data)
    IN:
        Layer (default: property, leave modular to support forest_type, soil, others...)
        Format (default: zipped .shp, leave modular to support json & others)
        property
    OUT:
        layer file
    USES:
        pgsql2shp (OGR/PostGIS built-in)
    '''
    return render(request, 'landmapper/base.html', {})

# Helper Views:
def get_soils_data(property_specs):
    import requests, json
    from landmapper.fetch import soils_from_nrcs
    soil_data = []

    bbox = [float(x) for x in property_specs['bbox'].split(',')]
    inSR = 3857

    try:
        soils = soils_from_nrcs(bbox, inSR)
    except (UnboundLocalError, AttributeError) as e:
        soil_data.append(['Error',])
        soil_data.append(['NRCS Soil data service unavailable. Try again later',])
        return soil_data


    mukeys = []
    for index, row in soils.iterrows():
        if row.mukey not in mukeys:
            mukeys.append(str(row.mukey))

    columns = ['musym', 'muname']

    query = "SELECT %s FROM mapunit WHERE mukey IN ('%s') ORDER BY %s" % (', '.join(columns),"', '".join(mukeys), columns[0])
    sdm_url = 'https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest'
    data_query = {
        'format': 'json',
        'query': query
        }
    json_result = requests.post(sdm_url, data=data_query)
    soil_json = json.loads(json_result.text)

    header_row = [settings.SOIL_FIELDS[header]['name'] for header in columns]
    soil_data.append(header_row)

    for row in soil_json['Table']:
        soil_data.append(row)

    return soil_data

def build_legend():
    return

def build_forest_type_legend():
    return

def build_soil_legend():
    return

def build_table():
    return

def build_soil_table():
    return
