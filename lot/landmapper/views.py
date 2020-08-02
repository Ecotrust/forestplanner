from django.shortcuts import render
from django.conf import settings
from flatblocks.models import FlatBlock

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
    except ConnectionError as e:
        if retries < 10:
            print('failed [%d time(s)] to connect to %s' % (retries, url))
            contents = unstable_request_wrapper(url, retries+1)
        else:
            print("ERROR: Unable to connect to %s" % url)
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
            coords = geocode(q_address)
        else:
            q_address = 'Enter your property address here'
        if coords:
            context = {
                'coords': coords,
                'q_address': q_address,
                'aside_content': aside_content,
                'show_panel_buttons': True,
                'btn_back_href': '/landmapper/',
                'btn_next_href': 'property_name',
                'btn_create_maps_href': '/landmapper/report/',
                'btn_next_disabled': 'disabled', # disabled is a css class for <a> tags
            }
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

    return render(request, 'landmapper/report/report.html', {})

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

    property_dict = parse_property_id(property_id)
    property = create_property(property_dict['taxlot_ids'], property_dict['name'])

    get_property_report(property)

    context = {
        'property_name': property_dict['name'],
        'property_map_image': property.property_map_image,
        'report': property.report_data,
    }
    # if report:
        # for page in report:
            # context['report_pages'][page] = page.data

    context = getHeaderMenu(context)

    return render(request, 'landmapper/report/report.html', context)


def get_property_report(property):
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
    property.street_map_image = map_views.get_street_map(property_specs, base_layer=street_layer, property_layer=property_layer)
    property.terrain_map_image = map_views.get_terrain_map(property_specs, base_layer=topo_layer, property_layer=property_layer)
    property.stream_map_image = map_views.get_stream_map(property_specs, base_layer=topo_layer, stream_layer=stream_layer, property_layer=property_layer)
    property.soil_map_image = map_views.get_soil_map(property_specs, base_layer=aerial_layer, soil_layer=soil_layer, property_layer=property_layer)

    property.report_data = get_property_report_data(property, property_specs)

def get_property_report_data(property, property_specs):
    report_data = {
        # '${report_page_name}': {
        #     'data': [ 2d array, 1 row for each entry, 1 column for each attr, 1st col is name],
        # }
    }
    report_pages = ['property', 'aerial', 'street', 'terrain', 'streams','soils','forest_type']

    #Property
    property_data = [
        ['Acres', property.formatted_area],
        # ['Legal Description', property.get_legal_description],
        # ['Structural Fire Disctrict', property.get_strctural_fire_district],
        # ['Forest Fire Disctrict', property.get_forest_fire_district],
        # ['Watershed Name', property.get_watershed_name],
        # ['Watershed #', property.get_watershed_number],
        # ['Zoning', property.get_zoning],
    ]

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
    from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
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

    for lot_id in taxlot_ids:
        lot = Taxlot.objects.get(pk=lot_id)

        if not taxlot_multipolygon:
            taxlot_multipolygon = lot.geometry
        else:
            taxlot_multipolygon = taxlot_multipolygon.union(lot.geometry)


    # Create Property object (don't use 'objects.create()'!)
    # now create property from cache id on report page

    property = Property(user=user, geometry_orig=taxlot_multipolygon, name=property_name)

    return property

# Property() is a Dict of JSON
# Create property will check the cache first then
# use django to cache
#
# decorators (@decor) - some available for caching shortcut
#
# django caching
#
# generate unique id
#
# turn id to string
#
# associate with data (pref dict)
#
# cache_key
#     take all taxlot ids
#     sort Alpahbetly
#     join list delinate (seperate) ids with something like a pipe (|) or tilda (~) or plus (+) (unlikey to show up in taxlot ids)
#         - need to create unique id that cannot be broken
#         - if we cna't get id from data we will generate it ourselves
#         - IDs may be alphanumeric so sorting will make sure the same cache key is used
#             Caching properties
#             111011 (ambiguous)
#             11 + 1011
#             1110 + 11
#             11|1011 (non-ambiguous)
#
# store other properties in Property dict
#
# use django caching syntax to store Property in cache




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

def create_pdf(request):
    '''
    (called on request for download map, cached)
    IN:
        Map ID (default: 'all', options: 'all', 'aerial', 'street', 'terrain', 'streams','forest','soil')
        property (from CreateProperty)
    OUT:
        PDF file
    NOTES:
        Leverage Template(s) from Report?
        Cache?
    USES:
        CreateAerialReport, CreateStreetReport, CreateTerrainReport, CreateStreamsReport, CreateForestTypeReport, CreateSoilReport
    '''
    return render(request, 'landmapper/base.html', {})

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

    soils = soils_from_nrcs(bbox, inSR)

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
