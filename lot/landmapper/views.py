from django.shortcuts import render
from django.conf import settings

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
    return contents

def get_soil_overlay_tile_data(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857', zoom=settings.SOIL_ZOOM_OVERLAY_2X):
    # """
    # get_soil_overlay_tile_data
    # PURPOSE:
    # -   Retrieve the soil tile image http response for a given bbox at a given size
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # OUT:
    # -   img_data: http(s) response from the request
    # """
    soil_wms_endpoint = settings.SOIL_WMS_URL
    bbox = get_bbox_as_string(bbox)

    if zoom:
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

def get_bbox_as_string(bbox):
    # """
    # PURPOSE:
    # -   if bbox is not a string of 4 coordinates ("W,S,E,N") convert
    # IN:
    # -   A bounding box description, either a string, a list, or a GEOSGeometry
    # OUT:
    # -   A string representation of the bbox in the format of "W,S,E,N"
    # """
    from django.contrib.gis.geos import Polygon, MultiPolygon

    if type(bbox) in [MultiPolygon , Polygon]:
        west = bbox.coords[0][0][0]
        south = bbox.coords[0][0][1]
        east = bbox.coords[0][2][0]
        north = bbox.coords[0][2][1]
        return "%s,%s,%s,%s" % (west, south, east, north)

    if type(bbox) in [tuple, list]:
        if len(bbox) == 1 and len(bbox[0]) == 5: # assume coords from Polygon
            west = bbox[0][0][0]
            south = bbox[0][0][1]
            east = bbox[0][2][0]
            north = bbox[0][2][1]
            return "%s,%s,%s,%s" % (west, south, east, north)
        elif len(bbox) == 1 and len(bbox[0]) == 1 and len(bbox[0][0]) == 5:   # coords from MultiPolygon
            west = bbox[0][0][0][0]
            south = bbox[0][0][0][1]
            east = bbox[0][0][2][0]
            north = bbox[0][0][2][1]
            return "%s,%s,%s,%s" % (west, south, east, north)
        elif len(bbox) == 1 and len(bbox[0]) == 1 and len(bbox[0][0]) > 5:
            return get_bbox_as_string(MultiPolygon(bbox,).envelope())
        elif len(bbox) == 4:
            return ','.join(bbox)
        elif len(bbox) == 2 and len(bbox[0]) == 2 and len(bbox[1]) == 2:
            return ','.join([','.join(bbox[0]),','.join([bbox[1]])])
    if type(bbox) == str:
        if len(bbox.split(',')) == 4:
            return bbox

    print('ERROR: Format of BBOX unrecognized. Crossing fingers and hoping for the best...')
    return bbox

def get_aerial_image(bbox, bboxSR=3857, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT):
    # """
    # PURPOSE: Return USGS Aerial image at the selected location of the selected size
    # IN:
    # -   bbox: (string) comma-separated W,S,E,N coordinates
    # -   width: (int) The number of pixels for the width of the image
    # -   height: (int) The number of pixels for the height of the image
    # -   bboxSR: (int) EPSG ID for Spatial Reference system used for input bbox coordinates
    # -       default: 3857
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """
    aerial_dict = settings.BASEMAPS[settings.AERIAL_DEFAULT]
    bbox = get_bbox_as_string(bbox)
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

def image_result_to_PIL(image_data):
    # """
    # image_result_to_PIL
    # PURPOSE:
    # -   Given an image result from a url, convert to a PIL Image type without
    # -       needing to store the image as a file
    # IN:
    # -   image_data: raw image data pulled from a URL (http(s) request)
    # OUT:
    # -   image_object: PIL Image instance of the image
    # """
    from PIL import Image, UnidentifiedImageError
    from tempfile import NamedTemporaryFile

    fp = NamedTemporaryFile()
    data_content = image_data.read()
    fp.write(data_content)
    try:
        pil_image = Image.open(fp.name)

        rgba_image = pil_image.convert("RGBA")
        fp.close()
    except UnidentifiedImageError as e:
        # RDH 2020-05-11: PIL's Image.open does not seem to work with Django's
        #       NatedTemporaryFile (perhaps the wrong write type?). We use
        #       the unique filename created, then do everything by hand,
        #       being sure to clean up after ourselves when done.
        import os
        outfilename = fp.name
        fp.close()
        if os.path.exists(outfilename):
            os.remove(outfilename)
        temp_file = open(outfilename, 'wb')
        temp_file.write(data_content)
        temp_file.close()
        pil_image = Image.open(outfilename)
        rgba_image = pil_image.convert("RGBA")
        os.remove(outfilename)

    return rgba_image

def merge_images(background, foreground):
    # """
    # merge_images
    # PURPOSE:
    # -   Given two PIL RGBA Images, overlay one on top of the other and return the
    # -       resulting PIL RGBA Image object
    # IN:
    # -   background: (PIL RGBA Image) The base image to have an overlay placed upon
    # -   foreground: (PIL RGBA Image) The overlay image to be displayed atop the
    # -       background
    # OUT:
    # -   merged_image: (PIL RGBA Image) the resulting merged image
    # """
    merged = background.copy()
    merged.paste(foreground, (0, 0), foreground)
    return merged

def get_property_from_taxlot_selection(taxlot_list):
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
    user = taxlot_list[0].user

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


def get_bbox_from_property(property):       # TODO
    """
    TODO:
    -   Given a GEOSGeometry, get the bbox and SRS
    -   Determine whether geom is taller or wider in ratio
    -   If taller:
    -       The geom bbox should be (0.90 * settings.REPORT_MAP_HEIGHT) pixels tall
    -       Calculate how wide that would make the bbox in pixels (how?)
    -           the coordinate values to pixels ratio is constant across web mercator:
    -               This is true for both comparing x an y axis and across the entire map (at null island is the same as NW Alaska)
    -       Buffer identical numbers of pixels to the width on each side of the bbox until width == settings.REPORT_MAP_WIDTH
    -       Buffer (0.05 * settings.REPORT_MAP_HEIGHT) pixels to each the top and the bottom of the bbox
    -       Determine the bbox of the buffered shape
    -       return bbox and 'landscape' for orientation (taller maps go on 'landscape' report pages)
    -           I know this seems backwards
    -   If wider:
    -       If we support both landscape AND portrait report layouts (not clear if this is MVP):
    -           The geom bbox should be (0.90 * settings.REPORT_MAP_HEIGHT) pixels wide
    -               YES: HEIGHT - since we invert for 'portrait' report layout
    -           Calculate how tall that would make the bbox in pixels (how?)
    -           Buffer identical numbers of pixels to the height above and below the bbox until height == settings.REPORT_MAP_WIDTH
    -           Buffer (0.05 * settings.REPORT_MAP_HEIGHT) pixels to each the left and right of the bbox
    -           Determine the bbox of the buffered shape
    -           return bbox and 'portait' for orientation (wider maps go on 'portrait' report pages)
    -       Else:
    -           You fill in the blank
    """

    return (None, orientation)

def get_layer_attribution(layer_name):
    # """
    # PURPOSE: shortcut for repetitive requests to get attributions from settings by layer name
    # IN: layer_name (string): the key for the layer that needs attribution
    # OUT: (string): Attribution for the layer, or text describing missing data
    # """
    if layer_name in settings.ATTRIBUTION_KEYS.keys():
        return settings.ATTRIBUTION_KEYS[layer_name]
    else:
        return 'No known attribution for ""%s"' % layer_name

def get_taxlot_image(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, bboxSR=3857):        # TODO
    bbox = get_bbox_as_string(bbox)
    return None

def get_property_image(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, bboxSR=3857):      # TODO
    bbox = get_bbox_as_string(bbox)
    return None

def get_attribution_image(attribution_list):            # TODO
    return None

def get_soil_report_image(property, bbox=None, orientation='landscape'):
    # """
    # PURPOSE:
    # -   given a property object, return an image formatted for the soil report.
    # -       This will include an aerial base layer, the rendered, highlighted
    # -       property outline, taxlots, the soil layer, and on top, the attribution.
    # IN:
    # -   property; (property object) the property to be displayed on the map
    # OUT:
    # -   soil_report_image: (PIL Image) the soil report map image
    # """
    if not bbox:
        (bbox, orientation) = get_bbox_from_property(property)

    bboxSR = 3857
    aerial_dict = get_aerial_image(bbox, bboxSR, settings.REPORT_MAP_WIDTH, settings.REPORT_MAP_HEIGHT)
    base_image = image_result_to_PIL(aerial_dict['image'])
    # add taxlots
    taxlot_image = get_taxlot_image(bbox, settings.REPORT_MAP_WIDTH, settings.REPORT_MAP_HEIGHT, bboxSR)
    # add property
    property_image = get_property_image(bbox, settings.REPORT_MAP_WIDTH, settings.REPORT_MAP_HEIGHT, bboxSR)
    # default soil cartography
    soil_tile_http = get_soil_overlay_tile_data(bbox, width, height)
    soil_image = image_result_to_PIL(soil_tile_http)

    # generate attribution image
    attributions = [
        aerial_dict['attribution'],
        get_layer_attribution('soils'),
        get_layer_attribution('taxlot'),
    ]

    attribution_image = get_attribution_image(attributions)

    merged = aerial_image
    if taxlot_image:
        merged = merge_images(aerial_image, taxlot_image)
    if property_image:
        merged = merge_images(merged, property_image)
    if soil_image:
        merged = merge_images(merged, soil_image)
    if attribution_image:
        merged = merge_images(merged, attribution_image)
    # merged.save(os.path.join(settings.IMAGE_TEST_DIR, 'merged.png'),"PNG")

    #TODO: Build and app

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
    return None
