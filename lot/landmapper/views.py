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

# Courtesy of https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
    import math
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# Courtesy of https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def num2deg(xtile, ytile, zoom):
    # This returns the NW-corner of the square
    import math
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def get_tiles_definition_array(bbox, request_dict, srs='EPSG:3857', width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT):
    # """
    # PURPOSE:
    # -   Get descriptions of required tiles as a 2D array
    # IN:
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   request_dict: (dict) A dictionary describing the tile source
    # -   srs: (string) the formatted Spatial Reference System string describing the
    # -       default: 'EPSG:3857' (Web Mercator)
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # OUT:
    # -   tiles_dict_array: 2D array of dictionaries defining URL request parameters
    # -     zoom
    # -     lat_index
    # -     lon_index
    # -     tile_bbox
    # """
    from django.contrib.gis.geos import Point

    tiles_dict_array = []

    if type(bbox) == list:
        bbox = str(bbox)
    if type(bbox) == str:
        bbox_poly = get_bbox_as_polygon(bbox, int(str(srs).split(':')[-1]))
    else:
        # assume bbox is Polygon
        bbox_poly = bbox

    bbox_poly.transform(3857)

    # Calculate Meters/Pixel for bbox, size
    # Below gets us a rough estimate, and may give us errors later.
    # To do this right, check out this:
    #   https://wiki.openstreetmap.org/wiki/Zoom_levels#Distance_per_pixel_math
    (west, south) = bbox_poly.coords[0][0]
    (east, north) = bbox_poly.coords[0][2]
    # mp_ratio = (east-west)/width
    mp_ratio = (north-south)/height     #In theory, this should be less distorted... right? No?

    # Get zoom value based on Meters/Pixel (get 1st zoom layer with less m/p)
    # Values from https://wiki.openstreetmap.org/wiki/Zoom_levels
    #       Note: these values are for 256x256 px tiles, do we need to adjust?
    #       See "Mapbox GL" comment - can just remove 1 from the level
    ZOOM_LEVELS_MP_RATIOS = [
        156412,     # 0
        78206,      # 1
        39103,      # 2
        19551,      # 3
        9776,       # 4
        4888,       # 5
        2444,       # 6
        1222,       # 7
        610.984,    # 8
        305.492,    # 9
        152.746,    # 10
        76.373,     # 11
        38.187,     # 12
        19.093,     # 13
        9.547,      # 14
        4.773,      # 15
        2.387,      # 16
        1.193,      # 17
        0.596,      # 18
        0.298,      # 19
        0.149,      # 20
    ]

    pixel_axis = 256
    for axis in [request_dict['TILE_HEIGHT'], request_dict['TILE_WIDTH']]:
        if axis > pixel_axis:
            pixel_axis = axis

    for (z_lvl, mp) in enumerate(ZOOM_LEVELS_MP_RATIOS):
        zoom = z_lvl
        map_mp = mp
        if mp_ratio > (mp*(256/pixel_axis)):
            break

    # Calculate layer'ls lat/lon index for LL & TR corners of bbox
    #   Reference: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers
    wgs84_ll = Point(west, south, srid=3857)
    wgs84_ll.transform(4326)
    wgs84_tr = Point(east, north, srid=3857)
    wgs84_tr.transform(4326)
    (west_4326, south_4326) = wgs84_ll.coords
    (east_4326, north_4326) = wgs84_tr.coords

    # west_lon_index = floor(2^zoom*((west_4326+180)/360))
    # east_lon_index = ceil(2^zoom*((east_4326+180)/360))
    # south_lat_index = floor(2^zoom*(1-(log(tan(pi/180*south_4326)+sec(pi/180*south_4326))/pi))/2)
    # north_lat_index = ceil(2^zoom*(1-(log(tan(pi/180*north_4326)+sec(pi/180*north_4326))/pi))/2)
    (west_lon_index, south_lat_index) = deg2num(south_4326, west_4326, zoom)
    (east_lon_index, north_lat_index) = deg2num(north_4326, east_4326, zoom)

    # build 2D array of tile URL parameters (lat, lon, zoom) and placeholder 'image'
    for lon_index in range(west_lon_index, east_lon_index+1, 1):
        tile_row = []
        for lat_index in range(north_lat_index, south_lat_index+1, 1):
            (tile_north, tile_west) = num2deg(lon_index, lat_index, zoom)
            (tile_south, tile_east) = num2deg(lon_index+1, lat_index+1, zoom)
            tile_sw = Point(tile_west, tile_south, srid=4326)
            tile_sw.transform(3857)
            tile_ne = Point(tile_east, tile_north, srid=4326)
            tile_ne.transform(3857)
            tile_bbox = ','.join([str(x) for x in [tile_sw.coords[0], tile_sw.coords[1], tile_ne.coords[0], tile_ne.coords[1]]])
            cell_dict = {
                'lat_index': lat_index,
                'lon_index': lon_index,
                'zoom': zoom,
                'tile_bbox': tile_bbox
            }

            tile_row.append(cell_dict)

        tiles_dict_array.append(tile_row)

    return tiles_dict_array

def crop_tiles(tiles_dict_array, bbox, srs='EPSG:3857', width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT):
    # """
    # PURPOSE:
    # -   Crop given map image tiles to bbox, then resize image to appropriate width/height
    # IN:
    # -   tiles_dict_array: (list) a 2D array of image tiles, where LL index = (0,0)
    # -   bbox: (string) 4 comma-separated coordinate vals: 'W,S,E,N'
    # -   width: (int) width of the desired image in pixels
    # -       default: settings.REPORT_MAP_WIDTH
    # -   height: (int) height of the desired image in pixels
    # -       default: settings.REPORT_MAP_HEIGHT
    # OUT:
    # -   img_data:
    # """
    from PIL import Image

    request_dict = settings.STREAMS_URLS[settings.STREAMS_SOURCE]

    num_cols = len(tiles_dict_array)
    num_rows = len(tiles_dict_array[0])

    base_width = num_cols * request_dict['TILE_IMAGE_WIDTH']
    base_height = num_rows * request_dict['TILE_IMAGE_HEIGHT']

    # Create overlay image
    base_image = Image.new("RGBA", (base_width, base_height), (255,255,255,0))

    # Merge tiles onto base image
    for (x, column) in enumerate(tiles_dict_array):
        for (y, cell) in enumerate(column):
            stream_image = image_result_to_PIL(tiles_dict_array[x][y]['image'])
            base_image = merge_images(base_image, stream_image, x*request_dict['TILE_IMAGE_WIDTH'], y*request_dict['TILE_IMAGE_HEIGHT'])

    # Get base image bbox
    base_west = float(tiles_dict_array[0][0]['tile_bbox'].split(',')[0])
    base_north = float(tiles_dict_array[0][0]['tile_bbox'].split(',')[3])
    base_east = float(tiles_dict_array[-1][-1]['tile_bbox'].split(',')[2])
    base_south = float(tiles_dict_array[-1][-1]['tile_bbox'].split(',')[1])

    base_width_in_meters = base_east - base_west
    base_height_in_meters = base_north - base_south

    base_meters_per_pixel = base_height_in_meters/base_height

    # crop image to target bbox
    (bbox_west, bbox_south, bbox_east, bbox_north) = (float(x) for x in bbox.split(','))
    crop_west = (bbox_west - base_west) / base_meters_per_pixel
    crop_south = abs((bbox_south - base_north) / base_meters_per_pixel)
    crop_east = (bbox_east - base_west) / base_meters_per_pixel
    crop_north = abs((bbox_north - base_north) / base_meters_per_pixel)

    base_image = base_image.crop(box=(crop_west,crop_north,crop_east,crop_south))

    # resize image to desired pixel count
    img_data = base_image.resize((width, height), Image.ANTIALIAS)

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
        request_url = "%s%s" % (request_dict['URL'].format(**request_params), '&'.join(request_qs))

        img_data = unstable_request_wrapper(request_url)

    elif '_TILE' in settings.STREAMS_SOURCE:
        # Get descriptions of required tiles as a 2D array
        tiles_dict_array = get_tiles_definition_array(bbox, request_dict, srs, width, height)
        request_qs = [x for x in request_dict['QS'] if 'access_token' not in x]
        request_qs.append('access_token=%s' % settings.MAPBOX_TOKEN)
        # Zoom should remain constant throughout all cells
        request_params['zoom'] = tiles_dict_array[0][0]['zoom']

        # Rows are stacked from South to North:
        #       https://www.maptiler.com/google-maps-coordinates-tile-bounds-projection/
        for row in tiles_dict_array:
            # Cells are ordered from West to East
            for cell in row:
                request_params['lon'] = cell['lon_index']
                request_params['lat'] = cell['lat_index']
                request_url = "%s%s" % (request_dict['URL'].format(**request_params), '&'.join(request_qs))
                cell['image'] = unstable_request_wrapper(request_url)

        img_data = crop_tiles(tiles_dict_array, bbox, srs, width, height)

    else:
        print('settings.STREAMS_SOURCE value "%s" is not currently supported.' % settings.STREAMS_SOURCE)
        img_data = None

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
    image = get_stream_overlay_tile_data(bbox, width, height, srs, zoom)
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

def get_base_image(layername, bbox, bboxSR=3857, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT):
    if layername == 'aerial':
        return get_aerial_image(bbox, bboxSR, width, height)
    elif layername == 'topo':
        return get_topo_image(bbox, bboxSR, width, height)
    else:
        print("Layername '%s' not recognized as valid base layer for maps. Defaulting to 'aerial'.")
    return get_aerial_image(bbox, bboxSR, width, height)

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
    try:
        data_content = image_data.read()
    except AttributeError as e:
        data_content = image_data
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

def merge_images(background, foreground, x=0, y=0):
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
    merged.paste(foreground, (x, y), foreground)
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
    # if this comes from MapBox, reuse the Streams code.
    # if this comes from the DB, reuse the Property code.
    from PIL import Image
    from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
    from landmapper.models import Taxlot
    bbox_geom = get_bbox_as_polygon(bbox)
    taxlots = Taxlot.objects.filter(geometry_final__intersects=bbox_geom)

    return None

def get_property_image(property, bbox, width=settings.REPORT_MAP_WIDTH, height=settings.REPORT_MAP_HEIGHT, bboxSR=3857):      # TODO
    """
    PURPOSE:
    -   Given a bounding box, return an image of all intersecting taxlots cut to the specified size.
    IN:
    -   property: (object) a property record from the DB
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
    from django.contrib.gis.geos.collections import MultiPolygon, Polygon
    from PIL import Image, ImageDraw

    # Create overlay image
    base_img = Image.new("RGBA", (width, height), (255,255,255,0))

    geom = property.geometry_orig
    bbox = get_bbox_as_string(bbox)
    [bbwest, bbsouth, bbeast, bbnorth] = [float(x) for x in bbox.split(',')]
    if type(geom) == Polygon:
        coords_set = (geom.coords)
    else:
        coords_set = geom.coords

    yConversion = float(height)/(bbnorth-bbsouth)
    xConversion = float(width)/(bbeast-bbwest)

    for poly in coords_set:
        for poly_coords in poly:
            polygon = ImageDraw.Draw(base_img)
            poly_px_coords = []
            for (gX, gY) in poly_coords:
                poly_px_coords.append(((gX-bbwest)*xConversion, (bbnorth-gY)*yConversion))
            polygon.polygon(poly_px_coords, outline=settings.PROPERTY_OUTLINE_COLOR)#, width=settings.PROPERTY_OUTLINE_WIDTH)

    return base_img

def get_attribution_image(attribution_list, width, height):
    # """
    # PURPOSE:
    # -   given a stringified list of attributions, return an image overlay.
    # IN:
    # -   attribution: a string of attributions for included layers
    # -   width: (int) number of pixels wide the image is.
    # -   height: (int) number of pixels tall the image is.
    # OUT:
    # -   attribution_image: (PIL Image) the the attribution image to be imposed atop report images
    # """
    from PIL import ImageDraw, ImageFont, Image
    TEXT_BUFFER = settings.ATTRIBUTION_TEXT_BUFFER
    LINE_SPACING = settings.ATTRIBUTION_TEXT_LINE_SPACING
    box_fill = settings.ATTRIBUTION_BOX_FILL_COLOR
    text_color = settings.ATTRIBUTION_TEXT_COLOR
    text_font = ImageFont.truetype(settings.ATTRIBUTION_TEXT_FONT, settings.ATTRIBUTION_TEXT_FONT_SIZE)

    # Create overlay image
    base_img = Image.new("RGBA", (width, height), (255,255,255,0))

    # calculate text size
    if type(attribution_list) == list:
        attribution_list = ', '.join(attribution_list)
    (text_width, text_height) = text_font.getsize(attribution_list)

    # Create a list of rows of attribution text
    attribution_rows = []
    attribution_word_list = attribution_list.split(' ')
    while len(attribution_word_list) > 0:
        new_row = [attribution_word_list.pop(0)]
        while len(attribution_word_list) > 0 and text_font.getsize(' '.join(new_row + [attribution_word_list[0]]))[0] < (width-2*TEXT_BUFFER):
            new_row.append(attribution_word_list.pop(0))
        attribution_rows.append(' '.join(new_row))

    # determine text_block size
    text_block_height = 2*TEXT_BUFFER + (text_height + LINE_SPACING) * len(attribution_rows) - LINE_SPACING
    if len(attribution_rows) > 1:
        text_block_width = width
    else:
        text_block_width = text_width + 2*TEXT_BUFFER

    # draw box
    left_px = width - text_block_width
    top_px = height - text_block_height
    right_px = width
    bottom_px = height
    box_shape = [(left_px, top_px), (right_px, bottom_px)]
    text_box = ImageDraw.Draw(base_img)
    text_box.rectangle(box_shape, fill=settings.ATTRIBUTION_BOX_FILL_COLOR, outline=settings.ATTRIBUTION_BOX_OUTLINE)

    # TODO: create box and text separately with full opacity, apply to base using:
    #       out = Image.alpha_composite(base, txt)
    # or something similar to remove 'checkered pattern' on attribute box.

    # draw text
    # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html?highlight=RGBA#example-draw-partial-opacity-text
    text_top = top_px + TEXT_BUFFER
    text_left = left_px + TEXT_BUFFER
    for (idx, text_row) in enumerate(attribution_rows):
        if idx != 0:
            text_top += LINE_SPACING
        txt = ImageDraw.Draw(base_img)
        txt.text((text_left, text_top), text_row, font=text_font, fill=text_color)
        text_top += text_height

    return base_img

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
    base_dict = get_base_image(settings.SOIL_BASE_LAYER, bbox, bboxSR, width, height)
    base_image = image_result_to_PIL(base_dict['image'])
    # add taxlots
    taxlot_image = get_taxlot_image(bbox, width, height, bboxSR)
    # add property
    property_image = get_property_image(property, bbox, width, height, bboxSR)
    # default soil cartography
    soil_image = get_soil_overlay_tile_image(bbox, width, height)

    # generate attribution image
    attributions = [
        base_dict['attribution'],
        get_layer_attribution('soil'),
        get_layer_attribution('taxlot'),
    ]

    attribution_image = get_attribution_image(attributions, width, height)

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
    base_dict = get_base_image(settings.STREAMS_BASE_LAYER, bbox, bboxSR, width, height)
    base_image = image_result_to_PIL(base_dict['image'])
    # add taxlots
    taxlot_image = get_taxlot_image(bbox, width, height, bboxSR)
    # add property
    property_image = get_property_image(property, bbox, width, height, bboxSR)
    # default streams cartography
    stream_image = get_stream_overlay_tile_image(bbox, width, height)

    # generate attribution image
    attributions = [
        base_dict['attribution'],
        get_layer_attribution('streams'),
        get_layer_attribution('taxlot'),
    ]

    if settings.STREAMS_SOURCE == 'MAPBOX_STATIC':
        attributions.append('MapBox')

    attribution_image = get_attribution_image(attributions, width, height)

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
    from .models import Taxlot
    import json
    coords = request.GET.getlist('coords[]') # must be [lon, lat]
    intersect_pt = GEOSGeometry('POINT(%s %s)' % (coords[0], coords[1]))
    try:
        lot = Taxlot.objects.get(geometry__intersects=intersect_pt)
        lot_json = lot.geometry.wkt
    except:
        lots = Taxlot.objects.filter(geometry__intersects=intersect_pt)
        if len(lots) > 0:
            lot = lots[0]
            lot_json = lot.geometry.json
        else:
            lot_json = []
    return HttpResponse(json.dumps({"geometry": lot_json}), status=200)

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
                'btn_next_href': '',
                'btn_next_disabled': 'disabled', # disabled is a css class for <a> tags
            }
            context = getHeaderMenu(context)
            return render(request, 'landmapper/landing.html', context)
    else:
        print('requested identify page')

    return home(request)

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
