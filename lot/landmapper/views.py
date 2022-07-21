# https://geocoder.readthedocs.io/
import decimal, json, geocoder
from django.conf import settings
from django.contrib.auth import authenticate,login as django_login
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_sameorigin
from flatblocks.models import FlatBlock
from landmapper.models import *
from landmapper import properties, reports
from urllib.parse import quote
import urllib.request
from PIL import Image
import requests

def unstable_request_wrapper(url, params=False, retries=0):
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

    try:
        if params:
            contents = requests.get(url, params)
            # contents = contents.raw
            # RDH 2020-12-07: SUPER HACKY way to turning params dict into urlencoded string.
            #       WHY?:
            #           When converting the 'requests' contents into 'raw' the
            #               image was blank
            #       TODO: Find a better way that either:
            #           - Doesn't require making the request twice
            #           - ideally pulls the correct data from the requests syntax
            contents = urllib.request.urlopen(contents.url)
        else:
            contents = urllib.request.urlopen(url)
    except ConnectionError as e:
        if retries < 10:
            print('failed [%d time(s)] to connect to %s' % (retries, url))
            contents = unstable_request_wrapper(url, params, retries + 1)
        else:
            print("ERROR: Unable to connect to %s" % url)
            contents = None
    except Exception as e:
        # print(e)
        # print(url)
        contents = False
    return contents

def geocode(search_string, srs=4326, service='arcgis', with_context=False):
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
    # CALLED BY:
    # -   identify
    # """

    hits = []
    g_hits = []
    hit_names = []

    # Query desired service
    # TODO: support more than just ArcGIS supplied geocodes
    #       Use other services if no matches are found.
    # if service.lower() == 'arcgis':
    g_matches = geocoder.arcgis(search_string, maxRows=100)
    for match in g_matches:
        if (match.latlng[0] <= settings.STUDY_REGION['north'] and
                match.latlng[0] >= settings.STUDY_REGION['south'] and
                match.latlng[1] <= settings.STUDY_REGION['east'] and
                match.latlng[1] >= settings.STUDY_REGION['west']):
            if not match.raw['name'] in hit_names:
                g_hits.append(match)
                hit_names.append(match.raw['name'])
    for hit in g_hits:
        hits.append({
            'name': hit.raw['name'],
            'coords': hit.latlng,
            'confidence': hit.confidence
        })

    if not with_context:

        if len(hits) == 0:
            for context in settings.STUDY_REGION['context']:
                new_hits = geocode("%s%s" % (search_string, context), srs=srs, service=service, with_context=True)
                for hit in new_hits:
                    if not hit['name'] in hit_names:
                        hits.append(hit)
                        hit_names.append(hit['name'])
                        # TODO: If new hits match but have better confidence, replace

        # Transform coordinates if necessary
        if not srs == 4326:

            if ':' in srs:
                try:
                    srs = srs.split(':')[1]
                except Exception as e:
                    pass
            try:
                int(srs)
            except ValueError as e:
                print(
                    'ERROR: Unable to interpret provided srs. Please provide a valid EPSG integer ID. Providing coords in EPSG:4326'
                )
                return coords

            hits_transform = []
            for hit in hits:
                coords = hit.latlng
                point = GEOSGeometry('SRID=4326;POINT (%s %s)' %
                                     (coords[1], coords[0]),
                                     srid=4326)
                point.transform(srs)
                coords = [point.coords[1], point.coords[0]]
                hits_transform.append(coords)
            hits = hits_transfrom

    hits = sorted(hits, key = lambda i: i['confidence'], reverse=True)
    if len(hits) > 5:
        hits = hits[:5]

    return hits

@xframe_options_sameorigin
def get_taxlot_json(request):
    coords = request.GET.getlist('coords[]')  # must be [lon, lat]
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
    return HttpResponse(json.dumps({
                            "id": lot_id,
                            "geometry": lot_json
                        }),
                        status=200)
# TODO: Consolidate home, index, and Identify
# TODO: Re-write logic to avoid page reload on Identify
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
        'overlay': 'overlay',
    }
    context['menu_items'] = MenuPage.objects.all().order_by('order')

    return render(request, 'landmapper/landing.html', context)

def index(request):
    '''  ## LANDING PAGE
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
            geocode_hits = geocode(q_address)
        else:
            q_address = 'Enter your property address here'

        if geocode_hits:
            if len(geocode_hits) > 0:
                coords = geocode_hits[0]['coords']
                geocode_error = False
            else:
                coords = [
                    (settings.STUDY_REGION['south'] + settings.STUDY_REGION['north'])/2,
                    (settings.STUDY_REGION['east'] + settings.STUDY_REGION['west'])/2
                ]
                geocode_error = True
            context = {
                'coords': coords,
                'geocode_hits': geocode_hits,
                'geocode_error': geocode_error,
                'q_address': q_address,
                'q_address_value': q_address_value,
                'aside_content': aside_content,
                'show_panel_buttons': True,
                'search_performed': True,
                # """Says where buttons go when you're using the UI mapping tool."""
                'btn_back_href': '/landmapper/',
                'btn_next_href': 'property_name',
                'btn_create_maps_href': '/landmapper/report/',
                'btn_next_disabled': 'disabled',
                'menu_items': MenuPage.objects.all().order_by('order'),
            }
    else:
        # User wants to bypass address search
        context = {
            'aside_content': aside_content,
            'show_panel_buttons': True,
            'search_performed': True,
            # """Says where buttons go when you're using the UI mapping tool."""
            'btn_back_href': '/landmapper/',
            'btn_next_href': 'property_name',
            'btn_create_maps_href': '/landmapper/report/',
            'btn_next_disabled': 'disabled',
            'menu_items': MenuPage.objects.all().order_by('order'),
        }

    return render(request, 'landmapper/landing.html', context)


def create_property_id(property_name, user_id, taxlot_ids):

    sorted_taxlots = sorted(taxlot_ids)

    id_elements = [str(x) for x in [
            property_name, user_id
        ] + sorted_taxlots]
    property_id = '|'.join(id_elements)

    return property_id

def create_property_id_from_request(request):
    '''
    Land Mapper: Create Property Cache ID
    IN

    '''
    if request.method == 'POST':
        property_name = request.POST.get('property_name')
        taxlot_ids = request.POST.getlist('taxlot_ids[]')

        # modifies request for anonymous user
        if not (hasattr(request, 'user') and request.user.is_authenticated
                ) and settings.ALLOW_ANONYMOUS_DRAW:
            user = User.objects.get(pk=settings.ANONYMOUS_USER_PK)
        else:
            user = request.user

        property_name = quote(property_name, safe='')
        
        if request.user.is_anonymous:
            user_id = 'anon'
        else:
            user_id = request.user.pk

        property_id =  create_property_id(property_name, user_id, taxlot_ids)
        
        return HttpResponse(json.dumps({'property_id': property_id}), status=200)
        
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

    property = properties.get_property_by_id(property_id, request.user)
    (bbox, orientation) = property.bbox()
    property_fit_coords = [float(x) for x in bbox.split(',')]
    property_width = property_fit_coords[2]-property_fit_coords[0]
    render_detailed_maps = True if property_width < settings.MAXIMUM_BBOX_WIDTH else False

    context = {
        'property_id': property_id,
        'property_name': property.name,
        'property': property,
        'property_report': property.report_data,
        'overview_scale': settings.PROPERTY_OVERVIEW_SCALE,
        'aerial_scale': settings.AERIAL_SCALE,
        'street_scale': settings.STREET_SCALE,
        'topo_scale': settings.TOPO_SCALE,
        'stream_scale': settings.STREAM_SCALE,
        'soil_scale': settings.SOIL_SCALE,
        'forest_type_scale': settings.FOREST_TYPES_SCALE,
        'menu_items': MenuPage.objects.all().order_by('order'),
        'SHOW_AERIAL_REPORT': settings.SHOW_AERIAL_REPORT,
        'SHOW_STREET_REPORT': settings.SHOW_STREET_REPORT,
        'SHOW_TERRAIN_REPORT': settings.SHOW_TERRAIN_REPORT,
        'SHOW_STREAMS_REPORT': settings.SHOW_STREAMS_REPORT,
        'SHOW_SOILS_REPORT': settings.SHOW_SOILS_REPORT,
        'SHOW_FOREST_TYPES_REPORT': settings.SHOW_FOREST_TYPES_REPORT,
        'RENDER_DETAILS': render_detailed_maps,
        'NO_RENDER_MESSAGE': settings.NO_RENDER_MESSAGE,
        'ATTRIBUTION_KEYS': settings.ATTRIBUTION_KEYS
    }

    return render(request, 'landmapper/report/report.html', context)

def get_property_map_image(request, property_id, map_type):
    property = properties.get_property_by_id(property_id, request.user)
    if map_type == 'stream':
        image = property.stream_map_image
    elif map_type == 'street':
        image = property.street_map_image
    elif map_type == 'aerial':
        image = property.aerial_map_image
    elif map_type == 'soil_types':
        image = property.soil_map_image
    elif map_type == 'forest_types':
        image = property.forest_type_map_image
    elif map_type == 'property':
        image = property.property_map_image
    elif map_type == 'terrain':
        image = property.terrain_map_image
    elif map_type == 'property_alt':
        image = property.property_map_image_alt
    else:
        image = None

    response = HttpResponse(content_type="image/png")
    image.save(response, 'PNG')

    return response


def get_scalebar_as_image(request, property_id, scale="fit"):

    property = properties.get_property_by_id(property_id, request.user)
    if scale == 'context':
        image = property.context_scalebar_image
    elif scale == 'medium':
        image = property.medium_scalebar_image
    else:
        image = property.scalebar_image
    response = HttpResponse(content_type="image/png")
    image.save(response, 'PNG')

    return response

def get_scalebar_as_image_for_pdf(request, property_id, scale="fit"):
    property = properties.get_property_by_id(property_id, request.user)
    if scale == 'context':
        image = property.context_scalebar_image
    elif scale == 'medium':
        image = property.medium_scalebar_image
    else:
        image = property.scalebar_image

    transparent_background = Image.new("RGBA", (settings.SCALEBAR_BG_W, settings.SCALEBAR_BG_H), (255,255,255,0))
    transparent_background.paste(image)

    response = HttpResponse(content_type="image/png")
    transparent_background.save(response, 'PNG')

    return response

def get_property_pdf(request, property_id):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="property.pdf"'
    property_pdf_cache_key = property_id + '_pdf'
    property_pdf = cache.get('%s' % property_pdf_cache_key)
    if not property_pdf:
        property = properties.get_property_by_id(property_id, request.user)
        property_pdf = reports.create_property_pdf(property, property_id)
        if property_pdf:
            cache.set('%s' % property_pdf_cache_key, property_pdf, 60 * 60 * 24 * 7)
    response.write(property_pdf)

    return response

def get_property_map_pdf(request, property_id, map_type):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="property.pdf"'
    property_pdf_cache_key = property_id + '_pdf'
    property_pdf = cache.get('%s' % property_pdf_cache_key)
    if not property_pdf:
        property = properties.get_property_by_id(property_id, request.user)
        property_pdf = reports.create_property_pdf(property, property_id)
        if property_pdf:
            cache.set('%s' % property_pdf_cache_key, property_pdf, 60 * 60 * 24 * 7)
    else:
        property = properties.get_property_by_id(property_id, request.user)
    property_map_pdf = reports.create_property_map_pdf(property, property_id, map_type)
    response.write(property_map_pdf)

    return response


## BELONGS IN VIEWS.py
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



### REGISTRATION/ACCOUNT MANAGEMENT ###
# account login page
def login(request):
    # TODO: write to handle wrong email address or password on login
    if request.method == 'POST':
        username = request.POST['login']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            return redirect('/landmapper')
        # else:
    context = {}
    return render(request, 'landmapper/account/login.html', context)

# account register / signup page
def signup(request):
    context = {
        'title': 'LandMapper',
    }
    return render(request, 'landmapper/account/signup.html', context)

# account password reset and username recovery page
def password_reset(request):
    context = {}
    return render(request, 'landmapper/account/password_reset.html', context)

# account profile page
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/landmapper/auth/login/', request.path))
    else:
        context = {}
        return render(request, 'landmapper/account/profile.html', context)