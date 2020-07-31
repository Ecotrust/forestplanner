from django.conf import settings
from PIL import Image, ImageDraw
from landmapper.views import unstable_request_wrapper

################################
# Map Layer Getter Functions ###
################################

def getPropertyImageLayer(property, property_specs):
    """
    PURPOSE:
    -   Given a bounding box, return an image of all intersecting taxlots cut to the specified size.
    IN:
    -   property: (object) a property record from the DB
    -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    OUT:
    -   taxlot_image: (PIL Image object) an image of the appropriate taxlot data
    -       rendered with the appropriate styles
    """
    from django.contrib.gis.geos.collections import MultiPolygon, Polygon
    bbox = property_specs['bbox']
    width = property_specs['width']
    height = property_specs['height']

    # Create overlay image
    base_img = Image.new("RGBA", (width, height), (255,255,255,0))

    geom = property.geometry_orig
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

    return {
        'image': base_img,    # Raw http(s) response
        'attribution': None
    }

def getTaxlotImageLayer(property_specs):
    # """
    # PURPOSE: Return taxlot layer at the selected location of the selected size
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """
    bbox = property_specs['bbox']
    width = property_specs['width']
    height = property_specs['height']
    base_img = Image.new("RGBA", (width, height), (255,255,255,0))
    attribution = settings.ATTRIBUTION_KEYS['taxlot']

    # TODO: query MapBox for Taxlot Layer and add it to the base image.

    return {
        'image': base_img,    # Raw http(s) response
        'attribution': attribution
    }

def getAerialImageLayer(property_specs):
    # """
    # PURPOSE: Return USGS Aerial image at the selected location of the selected size
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """

    bbox = property_specs['bbox']
    bboxSR = 3857
    width = property_specs['width']
    height = property_specs['height']

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
    base_image = image_result_to_PIL(image_data)

    return {
        'image': base_image,
        'attribution': attribution
    }

def getTopoImageLayer(property_specs):
    # """
    # PURPOSE: Return ESRI(?) Topo image at the selected location of the selected size
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """
    bbox = property_specs['bbox']
    bboxSR = 3857
    width = property_specs['width']
    height = property_specs['height']

    topo_dict = settings.BASEMAPS[settings.TOPO_DEFAULT]
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
    base_image = image_result_to_PIL(image_data)

    return {
        'image': base_image,
        'attribution': attribution
    }

def getSoilImageLayer(property_specs):
        # """
        # PURPOSE:
        # -   given a bbox and optionally pixel width, height, and an indication of
        # -       whether or not to zoom the cartography in, return a PIL Image
        # -       instance of the soils overlay
        # IN:
        # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
        # OUT:
        # -   image_info: (dict) {
        # -       image: image as raw data (bytes)
        # -       attribution: attribution text for proper use of imagery
        # -   }
        # """
        bbox = property_specs['bbox']
        srs = 'EPSG:3857'
        width = property_specs['width']
        height = property_specs['height']
        zoom_argument = settings.SOIL_ZOOM_OVERLAY_2X

        soil_wms_endpoint = settings.SOIL_WMS_URL

        if zoom_argument:
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
        data = unstable_request_wrapper(request_url)

        image = image_result_to_PIL(data)
        if zoom_argument:
            image = image.resize((width, height), Image.ANTIALIAS)

        attribution = settings.ATTRIBUTION_KEYS['soil']

        return {
            'image': image,
            'attribution': attribution
        }

def getStreamImageLayer(property_specs):
    # """
    # PURPOSE:
    # -   Retrieve the streams tile image http response for a given bbox at a given size
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """

    import urllib.request

    bbox = property_specs['bbox']
    srs = 'EPSG:3857'
    width = property_specs['width']
    height = property_specs['height']
    zoom_argument = settings.STREAM_ZOOM_OVERLAY_2X

    if zoom_argument:
        width = int(width/2)
        height = int(height/2)

    request_dict = settings.STREAMS_URLS[settings.STREAMS_SOURCE]
    request_params = request_dict['PARAMS'].copy()

    if settings.STREAMS_SOURCE == 'MAPBOX_STATIC':
        web_mercator_dict = get_web_map_zoom(bbox, width, height, srs)
        if zoom_argument:
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

    image = image_result_to_PIL(img_data)
    if zoom_argument:
        image = image.resize((width, height), Image.ANTIALIAS)

    attribution = settings.ATTRIBUTION_KEYS['streams']

    return {
        'image': image,
        'attribution': attribution
    }

################################
# Map Image Builder Functions ##
################################

def getPropertyMap(property_specs, base_layer, property_layer):
    # """
    # PURPOSE:
    # -   given property specs, images and attributions for a base layer and
    # -       a property outline layer, return an image formatted for the
    # -       property report.
    # IN:
    # -   property_specs; (dict) width, height and other property metadata
    # -   base_layer; (dict) PIL img and attribution for basemap layer
    # -   property_layer; (dict) PIL img and attribution for property outline
    # OUT:
    # -   property_report_image: (PIL Image) the property report map image
    # """

    width = property_specs['width']
    height = property_specs['height']

    base_image = base_layer['image']
    # add property
    property_image = property_layer['image']

    # generate attribution image
    attributions = [
        base_layer['attribution'],
        property_layer['attribution']
    ]

    attribution_image = get_attribution_image(attributions, width, height)

    layer_stack = [base_image, property_image, attribution_image]

    return merge_layers(layer_stack)

def getAerialMap(property_specs, base_layer, lots_layer, property_layer):
    # """
    # PURPOSE:
    # -   given property specs, images and attributions for a base layer and
    # -       a property outline layer, return an image formatted for the
    # -       property report.
    # IN:
    # -   property_specs; (dict) width, height and other property metadata
    # -   base_layer; (dict) PIL img and attribution for basemap layer
    # -   lots_layer; (dict) PIL img and attribution for tax lots
    # -   property_layer; (dict) PIL img and attribution for property outline
    # OUT:
    # -   property_report_image: (PIL Image) the property report map image
    # """

    width = property_specs['width']
    height = property_specs['height']

    base_image = base_layer['image']
    # add tax lot layer
    lots_image = lots_layer['image']
    # add property
    property_image = property_layer['image']

    # generate attribution image
    attributions = [
        base_layer['attribution'],
        lots_image['attribution'],
        property_layer['attribution'],
    ]

    attribution_image = get_attribution_image(attributions, width, height)

    layer_stack = [base_image, lots_image, property_image, attribution_image]

    return merge_layers(layer_stack)

def getStreamMap(property_specs, base_layer, stream_layer, property_layer):
    # """
    # PURPOSE:
    # -   given property specs, images and attributions for a base layer and
    # -       a property outline layer, return an image formatted for the
    # -       property report.
    # IN:
    # -   property_specs; (dict) width, height and other property metadata
    # -   base_layer; (dict) PIL img and attribution for basemap layer
    # -   stream_layer; (dict) PIL img and attribution for streams layer
    # -   property_layer; (dict) PIL img and attribution for property outline
    # OUT:
    # -   property_report_image: (PIL Image) the property report map image
    # """

    width = property_specs['width']
    height = property_specs['height']

    base_image = base_layer['image']
    # add tax lot layer
    stream_image = stream_layer['image']
    # add property
    property_image = property_layer['image']

    # generate attribution image
    attributions = [
        base_layer['attribution'],
        stream_layer['attribution'],
        property_layer['attribution'],
    ]

    if settings.STREAMS_SOURCE == 'MAPBOX_STATIC':
        attributions.append('MapBox')

    attribution_image = get_attribution_image(attributions, width, height)

    layer_stack = [base_image, stream_image, property_image, attribution_image]

    return merge_layers(layer_stack)

def getSoilMap(property_specs, base_layer, soil_layer, property_layer):
    # """
    # PURPOSE:
    # -   given property specs, images and attributions for a base layer and
    # -       a property outline layer, return an image formatted for the
    # -       property report.
    # IN:
    # -   property_specs; (dict) width, height and other property metadata
    # -   base_layer; (dict) PIL img and attribution for basemap layer
    # -   soil_layer; (dict) PIL img and attribution for soils layer
    # -   property_layer; (dict) PIL img and attribution for property outline
    # OUT:
    # -   property_report_image: (PIL Image) the property report map image
    # """

    width = property_specs['width']
    height = property_specs['height']

    base_image = base_layer['image']
    # add tax lot layer
    soil_image = soil_layer['image']
    # add property
    property_image = property_layer['image']

    # generate attribution image
    attributions = [
        base_layer['attribution'],
        soil_layer['attribution'],
        property_layer['attribution'],
    ]

    attribution_image = get_attribution_image(attributions, width, height)

    layer_stack = [base_image, soil_image, property_image, attribution_image]

    return merge_layers(layer_stack)

################################
# Helper Functions           ###
################################

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
    from PIL import UnidentifiedImageError
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
    from PIL import ImageDraw, ImageFont
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

def merge_layers(layer_list):

    merged = False
    for layer in layer_list:
        if layer:
            if not merged:
                merged = layer
            else:
                marged = merge_images(merged, layer)

    return merged

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

    # Calculate Meters/Pixel for bbox, size
    # Below gets us a rough estimate, and may give us errors later.
    # To do this right, check out this:
    #   https://wiki.openstreetmap.org/wiki/Zoom_levels#Distance_per_pixel_math
    [west, south, east, north] = [int(x) for x in bbox.split(',')]
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
