from django.shortcuts import render
from django.conf import settings

"""
unstable_request_wrapper
PURPOSE: As mentioned above, the USDA wfs service is weak. We wrote this wrapper
-   to fail less.
IN:
-   'url': The URL being requested
-   'retries': The number of retries made on this URL
OUT:
-   contents: The html contents of the requested page
"""
def unstable_request_wrapper(url, retries=0):
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
    return contents

"""
get_soil_overlay_tile_data
PURPOSE:
-   Retrieve the soil tile image http response for a given bbox at a given size
IN:
-   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
-   width: (int) width of the desired image in pixels
-       default: settings.REPORT_MAP_WIDTH
-   height: (int) height of the desired image in pixels
-       default: settings.REPORT_MAP_HEIGHT
-   srs: (string) the formatted Spatial Reference System string describing the
-       default: 'EPSG:3857' (Web Mercator)
OUT:
-   img_data: http(s) response from the request
"""
def get_soil_overlay_tile_data(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857'):
    soil_wms_endpoint = settings.SOIL_WMS_URL

    if settings.SOIL_ZOOM_OVERLAY_2X:
        width = int(width/2)
        height = int(height/2)

    request_url = ''.join([
        settings.SOIL_WMS_URL,
        '?service=WMS&request=GetMap&format=image%2Fpng&TRANSPARENT=true',
        '&version=', settings.SOIL_WMS_VERSION,
        '&layers=', settings.SOIL_TILE_LAYER,
        '&width=', str(width),
        '&height=', str(height),
        '&srs=', srs,
        '&bbox=', bbox,
    ])
    img_data = unstable_request_wrapper(request_url)
    return img_data

"""
get_soil_data_gml
PURPOSE: given a bounding box, SRS, and preferred version (format) of GML,
-   return an OGR layer read from the GML response (from unstable_request_wrapper)
IN:
-   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
-   srs: The Spatial Reference System used to interpret the coordinates
-       default: 'EPSG:4326'
-   format: The version of GML to use (GML2 or GML3)
-       default: 'GML3'
OUT:
-   gml_result: an OGR layer interpreted from the GML
"""
def get_soil_data_gml(bbox, srs='EPSG:4326',format='GML3'):
    from tempfile import NamedTemporaryFile
    from osgeo import ogr
    endpoint = settings.SOIL_WFS_URL
    request = 'SERVICE=WFS&REQUEST=GetFeature&VERSION=%s&' % settings.SOIL_WFS_VERSION
    layer = 'TYPENAME=%s&' % settings.SOIL_DATA_LAYER
    projection = 'SRSNAME=%s&' % srs
    bbox = 'BBOX=%s' % bbox
    gml = '&OUTPUTFORMAT=%s' % format
    url = "%s?%s%s%s%s%s" % (endpoint, request, layer, projection, bbox, gml)
    contents = unstable_request_wrapper(url)
    fp = NamedTemporaryFile()
    fp.write(contents.read())
    gml_result = ogr.Open(fp.name)
    fp.close()
    return gml_result

"""
get_soils_list
PURPOSE:
IN:
-   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
-   srs: The Spatial Reference System used to interpret the coordinates
-       default: 'EPSG:4326'
-   format: The version of GML to use (GML2 or GML3)
-       default: 'GML3'
OUT:
-   gml: an OGR layer interpreted from the GML
"""
def get_soils_list(bbox, srs='EPSG:4326',format='GML3'):
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

"""
geocode
PURPOSE: Convert a provided place name into geographic coordinates
IN:
-   search_string: (string) An address or named landmark/region
-   srs: (int) The EPSG ID for the spatial reference system in which to output coordinates
-       defaut: 4326
-   service: (string) The geocoding service to query for a result
-       default = 'arcgis'
-       other supported options: 'google'
OUT:
-   coords: a list of two coordinate elements -- [lat(y), long(x)]
-       projected in the requested coordinate system
"""
def geocode(search_string, srs=4326, service='arcgis'):
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

"""
get_aerial_image
PURPOSE: Return USGS Aerial image at the selected location of the selected size
IN:
-   bbox: (string) comma-separated W,S,E,N coordinates
-   width: (int) The number of pixels for the width of the image
-   height: (int) The number of pixels for the height of the image
-   bboxSR: (int) EPSG ID for Spatial Reference system used for input bbox coordinates
-       default: 3857
OUT:
-   image_info: (dict) {
-       image: image as raw data (bytes)
-       attribution: attribution text for proper use of imagery
-   }
"""
def get_aerial_image(bbox, width, height, bboxSR=3857):
    aerial_dict = settings.BASEMAPS[settings.AERIAL_DEFAULT]
    # Get URL for request
    if aerial_dict['technology'] == 'arcgis_mapserver':
        aerial_url = ''.join([
            aerial_dict['url'],
            '?bbox=', bbox,
            '&bboxSR=', str(bboxSR),
            '&layers=', aerial_dict['layers'],
            '&size=', str(width), ',', str(height),
            '&imageSR=3857&format=png&f=image',
        ])
    else:
        print('ERROR: No technologies other than ESRI\'s MapServer is supported for getting aerial layers at the moment')
        aerial_url = None

    # set Attribution
    attribution = aerial_dict['attribution']

    # Request URL
    image_data = unstable_request_wrapper(aerial_url)

    return {
        'image': image_data,    # Raw http(s) response
        'attribution': attribution
    }

"""
image_result_to_PIL
PURPOSE:
-   Given an image result from a url, convert to a PIL Image type without
-       needing to store the image as a file
IN:
-   image_data: raw image data pulled from a URL (http(s) request)
OUT:
-   image_object: PIL Image instance of the image
"""
def image_result_to_PIL(image_data):
    from PIL import Image
    from tempfile import NamedTemporaryFile

    fp = NamedTemporaryFile()
    fp.write(image_data.read())
    pil_image = Image.open(fp.name)
    rgba_image = pil_image.convert("RGBA")
    fp.close()

    return rgba_image

"""
merge_images
PURPOSE:
-   Given two PIL RGBA Images, overlay one on top of the other and return the
-       resulting PIL RGBA Image object
IN:
-   background: (PIL RGBA Image) The base image to have an overlay placed upon
-   foreground: (PIL RGBA Image) The overlay image to be displayed atop the
-       background
OUT:
-   merged_image: (PIL RGBA Image) the resulting merged image
"""
def merge_images(background, foreground):
    merged = background.copy()
    merged.paste(foreground, (0, 0), foreground)
    return merged

# Create your views here.
def home(request):
    '''
    Land Mapper: Home Page
    '''
    # return render(request, 'landmapper/home.html', {})
    return render(request, 'landmapper/home.html', {})

def index(request):
    '''
    Land Mapper: Index Page
    '''
    return render(request, 'landmapper/base.html', {})

def identify(request):
    '''
    Land Mapper: Identify Pages
    '''
    return render(request, 'landmapper/base.html', {})

def report(request):
    '''
    Land Mapper: Report Pages
    '''
    return render(request, 'landmapper/base.html', {})

def create_property(request, taxlot_ids, property_name):
    '''
    Land Mapper: Create Property

    TODO:
        can a memory instance of feature be made as opposed to a database feature
            meta of model (ref: madrona.features) to be inherited?
            don't want this in a database
            use a class (python class) as opposed to django model class?
        add methods to class for
            creating property
            turn into shp
            CreatePDF, ExportLayer, BuildLegend, BuildTables?
        research caching approaches
            django docs
            django caching API
    '''
