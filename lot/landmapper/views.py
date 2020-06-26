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

################################
# MapBox Munging             ###
################################
# The next 2 functions (g2p & p2g) are from R A "@busybus"
# The following 'get_web_map_zoom' also borrows heavily from @busybus
# and his blog post here:
#   https://medium.com/@busybus/rendered-maps-with-python-ffba4b34101c

ZOOM0_SIZE = 512  # Not 256
# Geo-coordinate in degrees => Pixel coordinate
def g2p(lat, lon, zoom):
    from math import pi, log, tan, exp, atan, log2, floor
    return (
        # x
        ZOOM0_SIZE * (2 ** zoom) * (1 + lon / 180) / 2,
        # y
        ZOOM0_SIZE / (2 * pi) * (2 ** zoom) * (pi - log(tan(pi / 4 * (1 + lat / 90))))
    )
# Pixel coordinate => geo-coordinate in degrees
def p2g(x, y, zoom):
    from math import pi, log, tan, exp, atan, log2, floor
    return (
        # lat
        (atan(exp(pi - y / ZOOM0_SIZE * (2 * pi) / (2 ** zoom))) / pi * 4 - 1) * 90,
        # lon
        (x / ZOOM0_SIZE * 2 / (2 ** zoom) - 1) * 180,
    )

def get_web_map_zoom(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857'):
    # """
    # PURPOSE:
    # -   Determine the zoom level for a web map tile server to match the image size
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # OUT:
    # -   out_dict: dictionary containing:
    # -     lat: a float representing the centroid latitude
    # -     lon: a float representing the centroid longitude
    # -     zoom: a float representing the appropriate zoom value within 0.01
    # """
    from math import log, log2, floor
    bbox = get_bbox_as_string(bbox)
    if not srs in ['EPSG:4326', '4326', 4326]:
        if type(srs) == str:
            if ':' in srs:
                srid = int(srs.split(':')[-1])
            else:
                srid = int(srs)
        else:
            srid = int(srs)
        bbox_polygon = get_bbox_as_polygon(bbox, srid)
        bbox_polygon.transform(4326)
        bbox = get_bbox_as_string(bbox_polygon)
    else:
        bbox_polygon = get_bbox_as_polygon(bbox)

    [left, bottom, right, top] = [float(x) for x in bbox.split(',')]
    # Sanity check
    assert (-90 <= bottom < top <= 90)
    assert (-180 <= left < right <= 180)

    # The center point of the region of interest
    (lat, lon) = ((top + bottom) / 2, (left + right) / 2)

    # Reduce precision of (lat, lon) to increase cache hits
    snap_to_dyadic = (lambda a, b: (lambda x, scale=(2 ** floor(log2(abs(b - a) / 4))): (round(x / scale) * scale)))
    lat = snap_to_dyadic(bottom, top)(lat)
    lon = snap_to_dyadic(left, right)(lon)

    # Rendered image map size in pixels (no retina)
    (w, h) = (width, height)

    zoom = 11
    delta = 11
    while abs(delta) > 0.0001:
        delta = abs(delta)/2
        fits = False
        # Center point in pixel coordinates at this zoom level
        (x0, y0) = g2p(lat, lon, zoom)
        # The "container" geo-region that the downloaded map would cover
        (TOP, LEFT)     = p2g(x0 - w / 2, y0 - h / 2, zoom)
        (BOTTOM, RIGHT) = p2g(x0 + w / 2, y0 + h / 2, zoom)
        # Would the map cover the region of interest?
        if (LEFT <= left < right <= RIGHT):
            if (BOTTOM <= bottom < top <= TOP):
                fits = True

        if not fits:
            # decrease the zoom value (zoom out)
            delta = 0-delta
        zoom = zoom + delta

    return {
        'lat': lat,
        'lon': lon,
        'zoom': zoom
    }

def get_soil_overlay_tile_data(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857', zoom=settings.SOIL_ZOOM_OVERLAY_2X):
    # """
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
    # -   zoom: (bool) whether or not to zoom in on the cartography to make it
    # -       bolder in the final image
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

def get_stream_overlay_tile_data(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857', zoom=settings.STREAM_ZOOM_OVERLAY_2X):
    # """
    # PURPOSE:
    # -   Retrieve the streams tile image http response for a given bbox at a given size
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # -   zoom: (bool) whether or not to zoom in on the cartography to make it
    # -       bolder in the final image
    # OUT:
    # -   img_data: http(s) response from the request
    # """

    import urllib.request
    bbox = get_bbox_as_string(bbox)

    if zoom:
        width = int(width/2)
        height = int(height/2)

    request_dict = settings.STREAMS_URLS[settings.STREAMS_SOURCE]
    request_params = request_dict['PARAMS'].copy()

    if settings.STREAMS_SOURCE == 'MAPBOX_STATIC':
        web_mercator_dict = get_web_map_zoom(bbox, width, height, srs)
        if zoom:
            request_params['retina'] = "@2x"

        request_params['lon'] = web_mercator_dict['lon']
        request_params['lat'] = web_mercator_dict['lat']
        request_params['zoom'] = web_mercator_dict['zoom']
        request_params['width'] = width
        request_params['height'] = height

        request_qs = [x for x in request_dict['QS'] if 'access_token' not in x]
        request_qs.append('access_token=%s' % settings.MAPBOX_TOKEN)

    else:
        print('settings.STREAMS_SOURCE value "%s" is not currently supported.' % settings.STREAMS_SOURCE)

    request_url = "%s%s" % (request_dict['URL'].format(**request_params), '&'.join(request_qs))

    print(request_url)

    img_data = unstable_request_wrapper(request_url)
    return img_data

def get_soil_overlay_tile_image(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857', zoom=settings.SOIL_ZOOM_OVERLAY_2X):
    # """
    # PURPOSE:
    # -   given a bbox and optionally pixel width, height, and an indication of
    # -       whether or not to zoom the cartography in, return a PIL Image
    # -       instance of the soils overlay
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # -   zoom: (bool) whether or not to zoom in on the cartography to make it
    # -       bolder in the final image
    # OUT:
    # -   a PIL Image instance of the soils overlay
    # """
    from PIL import Image
    data = get_soil_overlay_tile_data(bbox, width, height, srs, zoom)
    image = image_result_to_PIL(data)
    if zoom:
        image = image.resize((width, height), Image.ANTIALIAS)

    return image

def get_stream_overlay_tile_image(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, srs='EPSG:3857', zoom=settings.SOIL_ZOOM_OVERLAY_2X):
    # """
    # PURPOSE:
    # -   given a bbox and optionally pixel width, height, and an indication of
    # -       whether or not to zoom the cartography in, return a PIL Image
    # -       instance of the streams overlay
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # -   zoom: (bool) whether or not to zoom in on the cartography to make it
    # -       bolder in the final image
    # OUT:
    # -   a PIL Image instance of the soils overlay
    # """
    from PIL import Image
    data = get_stream_overlay_tile_data(bbox, width, height, srs, zoom)
    image = image_result_to_PIL(data)
    if zoom:
        image = image.resize((width, height), Image.ANTIALIAS)


    return image

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

    if type(bbox) in [Polygon, MultiPolygon]:
        west = bbox.envelope.coords[0][0][0]
        south = bbox.envelope.coords[0][0][1]
        east = bbox.envelope.coords[0][2][0]
        north = bbox.envelope.coords[0][2][1]
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
        elif len(bbox) == 1 and len(bbox[0]) == 1 and len(bbox[0][0]) > 5:  # Non-envelope MultiPolygon coords
            return get_bbox_as_string(Polygon( bbox[0][0] ).envelope)
        elif len(bbox) == 1 and len(bbox[0]) > 5:   # Non-envelope Polygon coords
            return get_bbox_as_string(Polygon(bbox[0]).envelope)
        elif len(bbox) == 4:    # Simple list [W,S,E,N]
            return ','.join([str(x) for x in bbox])
        elif len(bbox) == 2 and len(bbox[0]) == 2 and len(bbox[1]) == 2: # list of two sets of Point coordinates
            return ','.join([
                ','.join([str(x) for x in bbox[0]]),
                ','.join([str(x) for x in bbox[1]])
            ])

    if type(bbox) == str:
        if len(bbox.split(',')) == 4:
            return bbox

    print('ERROR: Format of BBOX unrecognized. Crossing fingers and hoping for the best...')
    return bbox

def get_bbox_as_polygon(bbox, srid=3857):
    # """
    # PURPOSE:
    # -   return a polygon bounding box from a large number of possible formats
    # IN:
    # -   bbox: (str, GEOS geom, list or tuple) any one of the bbox representations
    # -       of a bounding box supported by 'get_bbox_as_string'
    # -   ssrid: (int) the EPSG spatial reference identifier for the coordinate
    # -       system used to interpret the given coordinates
    # -       default: 3857
    # OUT:
    # -   bbox_geom: (GEOS Polygon) A GEOS Polygon feature of the provided bounding
    # -       box
    # """
    from django.contrib.gis.geos import Polygon
    # Get BBOX into consistant format
    bbox_str = get_bbox_as_string(bbox)
    # convert list into W,S,E,N components
    [west, south, east, north] = [float(x) for x in bbox_str.split(',')]
    # Format W,S,E,N into point coordinates
    polygon_input = [(west,south),(east,south),(east,north),(west,north),(west,south)]
    # Create the Polygon with the provided SRID
    bbox_geom = Polygon(polygon_input, srid=srid)
    return bbox_geom

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

def get_topo_image(bbox, bboxSR=3857, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT):
    # """
    # PURPOSE: Return ESRI(?) Topo image at the selected location of the selected size
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
    topo_dict = settings.BASEMAPS[settings.TOPO_DEFAULT]
    bbox = get_bbox_as_string(bbox)
    # Get URL for request
    if topo_dict['technology'] == 'arcgis_mapserver':
        topo_url = ''.join([
            topo_dict['url'],
            '?bbox=', bbox,
            '&bboxSR=', str(bboxSR),
            '&layers=', topo_dict['layers'],
            '&size=', str(width), ',', str(height),
            '&imageSR=3857&format=png&f=image',
        ])
    else:
        print('ERROR: No technologies other than ESRI\'s MapServer is supported for getting topo layers at the moment')
        topo_url = None

    # set Attribution
    attribution = topo_dict['attribution']

    # Request URL
    image_data = unstable_request_wrapper(topo_url)

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

def get_bbox_from_property(property):       # TODO: This should be a method on property instances called 'bbox'
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
    if hasattr(property, 'geometry_final') and property.geometry_final:
        geometry = property.geometry_final
    elif hasattr(property, 'geometry_orig') and property.geometry_orig:
        geometry = property.geometry_orig
    elif hasattr(property, 'envelope'):
        geometry = property
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
        target_width = settings.REPORT_MAP_HEIGHT
        target_height = settings.REPORT_MAP_WIDTH
        orientation = 'portrait'

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
    """
    PURPOSE:
    -   Given a bounding box, return an image of all intersecting taxlots cut to the specified size.
    IN:
    -   bbox: (string) comma-separated W,S,E,N coordinates
    -   width: (int) The number of pixels for the width of the image
    -       default: REPORT_MAP_WIDTH from settings
    -   height: (int) The number of pixels for the height of the image
    -       default: REPORT_MAP_HEIGHT from settings
    -   bboxSR: (int) EPSG ID for Spatial Reference system used for input bbox coordinates
    -       default: 3857
    OUT:
    -   taxlot_image: (PIL Image object) an image of the appropriate taxlot data
    -       rendered with the appropriate styles
    """
    from PIL import Image
    from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
    from landmapper.models import Taxlot
    bbox_geom = get_bbox_as_polygon(bbox)
    taxlots = Taxlot.objects.filter(geometry_final__intersects=bbox_geom)

    return None

def get_property_image(bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, bboxSR=3857):      # TODO
    bbox = get_bbox_as_string(bbox)
    return None

def get_attribution_image(attribution_list):            # TODO
    return None

def get_soil_report_image(property, bbox=None, orientation='landscape', width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, debug=False):
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
    if debug:
        import os
    if not bbox:
        (bbox, orientation) = get_bbox_from_property(property)
    if orientation == 'portrait' and settings.REPORT_SUPPORT_ORIENTATION:
        print("ORIENTATION SET TO 'PORTRAIT'")
        temp_width = width
        width = height
        height = temp_width

    bboxSR = 3857
    aerial_dict = get_aerial_image(bbox, bboxSR, width, height)
    base_image = image_result_to_PIL(aerial_dict['image'])
    # add taxlots
    taxlot_image = get_taxlot_image(bbox, width, height, bboxSR)
    # add property
    property_image = get_property_image(bbox, width, height, bboxSR)
    # default soil cartography
    soil_image = get_soil_overlay_tile_image(bbox, width, height)

    # generate attribution image
    attributions = [
        aerial_dict['attribution'],
        get_layer_attribution('soils'),
        get_layer_attribution('taxlot'),
    ]

    attribution_image = get_attribution_image(attributions)

    merged = base_image
    if debug:
        base_image.save(os.path.join(settings.IMAGE_TEST_DIR, 'base_image.png'),"PNG")
    if taxlot_image:
        merged = merge_images(base_image, taxlot_image)
    if property_image:
        merged = merge_images(merged, property_image)
    if soil_image:
        if debug:
            soil_image.save(os.path.join(settings.IMAGE_TEST_DIR, 'soil_image.png'),"PNG")
        merged = merge_images(merged, soil_image)
    if attribution_image:
        merged = merge_images(merged, attribution_image)

    return merged

def get_streams_report_image(property, bbox=None, orientation='landscape', width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, debug=False):
    # """
    # PURPOSE:
    # -   given a property object, return an image formatted for the streams report.
    # -       This will include a topo base layer, the rendered, highlighted
    # -       property outline, taxlots, the streams layer, and on top, the attribution.
    # IN:
    # -   property; (property object) the property to be displayed on the map
    # OUT:
    # -   stream_report_image: (PIL Image) the streams report map image
    # """
    if debug:
        import os
    if not bbox:
        (bbox, orientation) = get_bbox_from_property(property)
    if orientation == 'portrait' and settings.REPORT_SUPPORT_ORIENTATION:
        print("ORIENTATION SET TO 'PORTRAIT'")
        temp_width = width
        width = height
        height = temp_width

    bboxSR = 3857
    topo_dict = get_topo_image(bbox, bboxSR, width, height)
    base_image = image_result_to_PIL(topo_dict['image'])
    # add taxlots
    taxlot_image = get_taxlot_image(bbox, width, height, bboxSR)
    # add property
    property_image = get_property_image(bbox, width, height, bboxSR)
    # default streams cartography
    stream_image = get_stream_overlay_tile_image(bbox, width, height)

    # generate attribution image
    attributions = [
        topo_dict['attribution'],
        get_layer_attribution('streams'),
        get_layer_attribution('taxlot'),
    ]

    attribution_image = get_attribution_image(attributions)

    merged = base_image
    if debug:
        base_image.save(os.path.join(settings.IMAGE_TEST_DIR, 'base_image.png'),"PNG")
    if taxlot_image:
        merged = merge_images(base_image, taxlot_image)
    if property_image:
        merged = merge_images(merged, property_image)
    if stream_image:
        if debug:
            stream_image.save(os.path.join(settings.IMAGE_TEST_DIR, 'stream_image.png'),"PNG")
        merged = merge_images(merged, stream_image)
    if attribution_image:
        merged = merge_images(merged, attribution_image)

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
    (landing: slide 1)
    '''
    return render(request, 'landmapper/base.html', {})

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
    return render(request, 'landmapper/base.html', {})

def report(request):
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
    return None

def aboutMenuPage(request):
    '''
    Land Mapper: About Menu Page
    '''
    from landmapper.models import MenuPage
    about_page = MenuPage.objects.get(name='about')
    # return about_page


def CreateProperty(request):
    '''
    CreateAerialReport: (slide 7b)
    IN:
        Property
    OUT:
        Context for appropriately rendered report template
    USES:
    BuildLegend
    '''
    return render(request, 'landmapper/base.html', {})

def CreateStreetReport(request):
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

def CreateTerrainReport(request):
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

def CreateStreamsReport(request):
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

def CreateForestTypeReport(request):
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

def CreateSoilReport(request):
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

def CreatePDF(request):
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

def ExportLayer(request):
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
def GetSoilsData():
    return

def BuildLegend():
    return

def BuildForestTypeLegend():
    return

def BuildSoilLegend():
    return

def BuildTable():
    return

def BuildForestTypeLegend():
    return

def BuildSoilTable():
    return

def BuildCacheKey():
    '''
    sort taxlot IDs and add to property name for consistent cache keys
    Doing it here is the lowest-common-denominator: don't worry about sorting taxlots when adding them to the querystring on the client side
    '''
    return
