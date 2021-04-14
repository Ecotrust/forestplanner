from django.conf import settings
from landmapper import views as lm_views
from landmapper.models import Taxlot, SoilType
from django.contrib.gis.geos import Point, Polygon, MultiPolygon

import geopandas as gpd
import io, pyproj, shapely, json
from imageio import imread
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from math import pi, log, tan, exp, atan, log2, log10, floor
from matplotlib import patches, ticker
from matplotlib import pyplot as plt
from matplotlib import patheffects as pe
from matplotlib.collections import PatchCollection
from rasterio import transform
from rasterio.plot import show, reshape_as_raster
import requests
from shapely.geometry import Point as shp_Point
from shapely.ops import transform as shp_transform
import urllib.request

################################
# Map Layer Getter Functions ###
################################

def get_property_image_layer(property, property_specs, bbox=False):
    """
    Produce an image of the taxlots belonging to a property.

    Parameters
    ----------
    property : a property object
      a property record from the DB
    property_specs : dict
      pre-computed aspects of the property, including: bbox, width, and height

    Returns
    -------
    taxlot_img : dict
      dictionary with 'image' and 'attribution' as keys
    """
    if not bbox:
        bbox = property_specs['bbox']

    property_collection = get_collection_from_objects([property], 'geometry_orig', bbox)
    property_gdf = get_gdf_from_features(property_collection)

    return {
        'type': 'dataframe',
        'data': property_gdf,
        'style': settings.PROPERTY_STYLE,
        'attribution': None
    }

def get_taxlot_image_layer(property_specs, bbox=False):
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

    if not bbox:
        bbox = property_specs['bbox']

    bbox_poly = get_bbox_as_polygon(bbox)
    taxlots = Taxlot.objects.filter(geometry__intersects=bbox_poly)
    taxlot_collection = get_collection_from_objects(taxlots, 'geometry', bbox)
    taxlots_gdf = get_gdf_from_features(taxlot_collection)

    attribution = settings.ATTRIBUTION_KEYS['taxlot']

    return {
        'type': 'dataframe',
        'data': taxlots_gdf,
        'style': settings.TAXLOT_STYLE,
        'attribution': attribution
    }

def get_aerial_image_layer(property_specs, bbox=False, alt_size=False):
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

    if not bbox:
        bbox = property_specs['bbox']
    bboxSR = 3857

    if alt_size:
        width = property_specs['width_alt']
        height = property_specs['height_alt']
    else:
        width = property_specs['width']
        height = property_specs['height']

    aerial_dict = settings.BASEMAPS[settings.AERIAL_DEFAULT]
    # Get URL for request
    if aerial_dict['TECHNOLOGY'] == 'arcgis_mapserver':
        aerial_url = ''.join([
            aerial_dict['URL'],
            '?bbox=', bbox,
            '&bboxSR=', str(bboxSR),
            '&layers=', aerial_dict['LAYERS'],
            '&size=', str(width), ',', str(height),
            '&imageSR=3857&format=png&f=image',
        ])
    elif aerial_dict['TECHNOLOGY'] == 'arcgis_imageserver':

        aerial_qs = '&'.join([
            f'bbox={bbox}',
            f'bboxSR={settings.GEOMETRY_CLIENT_SRID}',
            f'size={width},{height}',
            f'imageSR={settings.GEOMETRY_CLIENT_SRID}',
            'format=tiff',
            'pixelType=U8',
            'noDataInterpretation=esriNoDataMatchAny',
            'interpolation=+RSP_BilinearInterpolation',
            'time=None',
            'noData=None',
            'compression=None',
            'compressionQuality=None',
            'bandIds=None',
            'mosaicRule=None',
            'renderingRule=None',
            'f=image',
        ])
        aerial_url = '?'.join([aerial_dict['URL'],aerial_qs])
    else:
        print('ERROR: No technologies other than ESRI\'s MapServer is supported for getting aerial layers at the moment')
        aerial_url = None

    # set Attribution
    attribution = aerial_dict['ATTRIBUTION']

    # Request URL
    image_data = lm_views.unstable_request_wrapper(aerial_url)
    base_image = image_result_to_PIL(image_data)

    return {
        'type':'image',
        'data': base_image,
        'attribution': attribution
    }

def get_topo_image_layer(property_specs, bbox=False):
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
    if not bbox:
        bbox = property_specs['bbox']
    bboxSR = 3857
    width = property_specs['width']
    height = property_specs['height']
    bbox_list = [float(x) for x in bbox.split(',')]

    topo_dict = settings.BASEMAPS[settings.TOPO_DEFAULT]

    # TODO: Rewrite so this just provides the hillshade baselayer, and contours_img comes from get_contour_image_layer, even if it's just this one next line.
    contours_img = contours_from_tnm_dem(bbox=bbox_list, width=width, height=height, dpi=settings.DPI, inSR=bboxSR)
    # Get URL for request
    if topo_dict['TECHNOLOGY'] == 'arcgis_mapserver':
        topo_url = ''.join([
            topo_dict['URL'],
            '?bbox=', bbox,
            '&bboxSR=', str(bboxSR),
            '&layers=', topo_dict['LAYERS'],
            '&size=', str(width), ',', str(height),
            '&imageSR=3857&format=png&f=image',
        ])
        image_data = lm_views.unstable_request_wrapper(topo_url)
        # Request URL
        base_image = image_result_to_PIL(image_data)
    elif topo_dict['TECHNOLOGY'] == 'XYZ':
        base_image = get_mapbox_image_data(topo_dict, property_specs, bbox, zoom_2x=topo_dict['ZOOM_2X'])
    else:
        print('ERROR: No technologies other than ESRI\'s MapServer is supported for getting topo layers at the moment')
        topo_url = None
        image_data = None
        base_image = None

    layers = [
        {'type': 'image', 'data': base_image },
        {'type': 'image', 'data': contours_img },
    ]

    topo_img = get_static_map(
        property_specs,
        layers,
        bbox = bbox
    )

    # set Attribution
    attribution = topo_dict['ATTRIBUTION']

    return {
        'type': 'image',
        'data': topo_img,
        'attribution': attribution
    }

def get_street_image_layer(property_specs, bbox=False):
    # """
    # PURPOSE: Return ESRI Street image at the selected location of the selected size
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """
    if not bbox:
        bbox = property_specs['bbox']
    bboxSR = 3857
    width = property_specs['width']
    height = property_specs['height']

    street_dict = settings.BASEMAPS[settings.STREET_DEFAULT]
    # Get URL for request
    if street_dict['TECHNOLOGY'] == 'arcgis_mapserver':
        street_url = ''.join([
            street_dict['URL'],
            '?bbox=', bbox,
            '&bboxSR=', str(bboxSR),
            '&layers=', street_dict['LAYERS'],
            '&size=', str(width), ',', str(height),
            '&imageSR=3857&format=png&f=image',
        ])
        # Request URL
        image_data = lm_views.unstable_request_wrapper(street_url)
        base_image = image_result_to_PIL(image_data)
    elif street_dict['TECHNOLOGY'] == 'XYZ':
        base_image = get_XYZ_image_data(street_dict, property_specs, bbox, zoom_2x=street_dict['ZOOM_2X'])
    elif street_dict['TECHNOLOGY'] == 'static':
        #TODO: get zoom
        zoom = get_zoom_from_bbox(bbox, tile_height=settings.REPORT_MAP_HEIGHT, tile_width=settings.REPORT_MAP_WIDTH)
        #TODO: get center lon and lat in 4326
        [lon, lat] = get_center_lon_lat_from_bbox(bbox, inSRID=3857, outSRID=4326)
        if settings.STREET_DEFAULT in settings.KEYS.keys():
            apiKey = settings.KEYS[settings.STREET_DEFAULT]
        else:
            apiKey = ''
        street_qs = '&'.join([x.format(width=width, height=height, lon=lon, lat=lat, zoom=zoom, apiKey=apiKey) for x in street_dict['QS']])
        street_url = '?'.join([street_dict['URL'], street_qs])
        result = requests.get(street_url)
        base_image = imread(io.BytesIO(result.content))
    else:
        print('ERROR: No technologies other than ESRI\'s MapServer is supported for getting street layers at the moment')
        base_image = None

    # set Attribution
    attribution = street_dict['ATTRIBUTION']

    return {
        'type': 'image',
        'data': base_image,
        'attribution': attribution
    }

def get_soil_image_layer(property_specs, bbox=False):
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

        if not bbox:
            bbox = property_specs['bbox']

        bbox_poly = get_bbox_as_polygon(bbox)
        soils = SoilType.objects.filter(geometry__intersects=bbox_poly)
        soils_collection = get_collection_from_objects(soils, 'geometry', bbox, attrs=['musym'])
        soils_gdf = get_gdf_from_features(soils_collection)

        return {
            'type': 'dataframe',
            'data': soils_gdf,
            'style': settings.SOIL_STYLE,
            'attribution': settings.ATTRIBUTION_KEYS['soil']
        }

def get_center_lon_lat_from_bbox(bbox, inSRID=3857, outSRID=3857):
    [xmin, ymin, xmax, ymax] = [float(x) for x in bbox.split(',')]
    xmean = (xmin + xmax)/2
    ymean = (ymin + ymax)/2
    mean_point = shp_Point(xmean, ymean)

    inCRS = pyproj.CRS(f'EPSG:{inSRID}')
    outCRS = pyproj.CRS(f'EPSG:{outSRID}')
    reprojection = pyproj.Transformer.from_crs(inCRS, outCRS, always_xy=True).transform
    outPoint = shp_transform(reprojection, mean_point)
    [outLon, outLat] = [x[0] for x in outPoint.coords.xy]
    return (outLon, outLat)

def get_zoom_from_bbox(bbox, tile_height, tile_width, img_height=settings.REPORT_MAP_HEIGHT, img_width=settings.REPORT_MAP_WIDTH):
    # Get zoom value based on Meters/Pixel (get 1st zoom layer with less m/p)
    # Values from https://wiki.openstreetmap.org/wiki/Zoom_levels
    #       Note: these values are for 256x256 px tiles, do we need to adjust?
    #       See "Mapbox GL" comment - can just remove 1 from the level

    [xmin, ymin, xmax, ymax] = [float(x) for x in bbox.split(',')]
    # mp_ratio = (east-west)/width
    mp_ratio = (ymax-ymin)/img_height     #In theory, this should be less distorted... right? No?

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
    for axis in [tile_height, tile_width]:
        if axis > pixel_axis:
            pixel_axis = axis

    for (z_lvl, mp) in enumerate(ZOOM_LEVELS_MP_RATIOS):
        zoom = z_lvl
        # map_mp = mp
        if mp_ratio > (mp*(256/pixel_axis)):
            break

    return zoom


def get_XYZ_image_data(request_dict, property_specs, bbox, zoom_2x=False):
    # """
    # PURPOSE:
    # -   Retrieve mapbox tile images http response for a given bbox at a given size
    # IN:
    # -   layer_url: (string) pre-computed URL string with {z}, {x}, and {y} for the tile template
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   img_data: image as raw data (bytes)
    # """
    if not bbox:
        bbox = property_specs['bbox']
    srs = 'EPSG:3857'
    width = property_specs['width']
    height = property_specs['height']
    if zoom_2x:
        width = int(width/2)
        height = int(height/2)

    request_params = request_dict['PARAMS'].copy()

    # Get descriptions of required tiles as a 2D array
    tiles_dict_array = get_tiles_definition_array(bbox, request_dict, srs, width, height)

    request_qs = [x for x in request_dict['QS']]
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
            cell['image'] = requests.get(request_url)

    img_data = crop_tiles(tiles_dict_array, bbox, srs, width, height)

    if zoom_2x:
        img_data = img_data.resize((property_specs['width'], property_specs['height']), Image.ANTIALIAS)

    return img_data

def get_mapbox_image_data(request_dict, property_specs, bbox, zoom_2x=False, append_token=True):
    # """
    # PURPOSE:
    # -   Retrieve mapbox tile images http response for a given bbox at a given size
    # IN:
    # -   layer_url: (string) pre-computed URL string with {z}, {x}, and {y} for the tile template
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # OUT:
    # -   img_data: image as raw data (bytes)
    # """
    if not bbox:
        bbox = property_specs['bbox']
    srs = 'EPSG:3857'
    width = property_specs['width']
    height = property_specs['height']
    if zoom_2x:
        width = int(width/2)
        height = int(height/2)

    request_params = request_dict['PARAMS'].copy()

    # Get descriptions of required tiles as a 2D array
    tiles_dict_array = get_tiles_definition_array(bbox, request_dict, srs, width, height)

    request_qs = [x for x in request_dict['QS'] if 'access_token' not in x]
    if append_token:
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
            # print("Getting layer from MapBox: %s" % request_url)
            cell['image'] = lm_views.unstable_request_wrapper(request_url)

    img_data = crop_tiles(tiles_dict_array, bbox, srs, width, height)

    if zoom_2x:
        img_data = img_data.resize((property_specs['width'], property_specs['height']), Image.ANTIALIAS)

    return img_data

def get_stream_image_layer(property_specs, bbox=False):
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

    request_dict = settings.STREAMS_URLS[settings.STREAMS_SOURCE]
    zoom_argument = settings.STREAM_ZOOM_OVERLAY_2X

    if not bbox:
        bbox = property_specs['bbox']

    if settings.STREAMS_SOURCE == 'MAPBOX_STATIC':
        srs = 'EPSG:3857'
        width = property_specs['width']
        height = property_specs['height']

        if zoom_argument:
            width = int(width/2)
            height = int(height/2)

        request_params = request_dict['PARAMS'].copy()

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

        img_data = lm_views.unstable_request_wrapper(request_url)
        img_data = image_result_to_PIL(img_data)

        if type(img_data) == Image.Image:
            image = img_data
        else:
            image = image_result_to_PIL(img_data)
        if zoom_argument:
            image = image.resize((width, height), Image.ANTIALIAS)

    elif '_TILE' in settings.STREAMS_SOURCE:
        image = get_mapbox_image_data(request_dict, property_specs, bbox)


    else:
        print('settings.STREAMS_SOURCE value "%s" is not currently supported.' % settings.STREAMS_SOURCE)
        image = None


    attribution = settings.ATTRIBUTION_KEYS['streams']

    return {
        'type': 'image',
        'data': image,
        'attribution': attribution
    }

def get_contour_image_layer(property_specs, bbox=False, index_contour_style=None, zoom=True, intermediate_contour_style=None, contour_label_style=None):
    # """
    # PURPOSE:
    # -   given a bbox and optionally pixel width, height, and an indication of
    # -       whether or not to zoom the cartography in, return a PIL Image
    # -       instance of the topological contours overlay
    # IN:
    # -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    # -   bbox: (string, optional) "W,S,E,N" in EPSG:3857
    # -   index_contour_style : (dict, optional):
    # -         dict with key, value pairs indicating elements of the line style to
    # -         update for the 100-foot contour lines
    # -   intermediate_contour_style : (dict, optional)
    # -         dict with key, value pairs indicating elements of the line style to
    # -   update for intermediate (50-foot) contour lines
    # -         contour_label_style : dict, option
    # -         dict with key, value pairs indicating elements of label style to update
    # -         for the 100-foot contour labels
    # OUT:
    # -   image_info: (dict) {
    # -       image: image as raw data (bytes)
    # -       attribution: attribution text for proper use of imagery
    # -   }
    # """

    if not bbox:
        bbox = property_specs['bbox']
    bboxSR = 3857
    if zoom:
        width = 2*property_specs['width']
        height = 2*property_specs['height']

    contour_dict = settings.CONTOUR_URLS[settings.CONTOUR_SOURCE].copy()

    if index_contour_style is not None:
        contour_dict['INDEX_CONTOUR_SYMBOL'].update(index_contour_style)

    if intermediate_contour_style is not None:
        contour_dict['INTERMEDIATE_CONTOUR_SYMBOL'].update(intermediate_contour_style)

    if contour_label_style is not None:
        for key in contour_label_style:
            if isinstance(contour_label_style[key], dict):
                contour_dict['LABEL_SYMBOL'][key].update(contour_label_style[key])
            else:
                contour_dict['LABEL_SYMBOL'].update(((key, contour_label_style[key]),))

    # Get URL for request
    params = dict(
        bbox=bbox,
        bboxSR=contour_dict['SRID'],
        layers='show:%s' % contour_dict['LAYERS'],
        layerDefs=None,
        size=f'{width},{height}',
        imageSR=contour_dict['SRID'],
        historicMoment=None,
        format='png',
        transparent=True,
        dpi=None,
        time=None,
        layerTimeOptions=None,
        dynamicLayers=json.dumps(contour_dict['STYLES']),
        gdbVersion=None,
        mapScale=None,
        rotation=None,
        datumTransformations=None,
        layerParameterValues=None,
        mapRangeValues=None,
        layerRangeValues=None,
        f='image',
    )

    # set Attribution
    attribution = contour_dict['ATTRIBUTION']

    # Request URL
    image_data = lm_views.unstable_request_wrapper(contour_dict['URL'], params=params )
    base_image = image_result_to_PIL(image_data)

    if zoom:
        base_image = base_image.resize((property_specs['width'], property_specs['height']), Image.ANTIALIAS)

    return {
        'type': 'image',
        'data': base_image,
        'attribution': attribution
    }

################################
# Map Image Builder Functions ##
################################

def get_static_map(property_specs, layers, bbox=None, alt_size=False):
    # """
    # PURPOSE:
    # -   given property specs and a list of layer objects, return a .png
    # -   map image of the data
    # IN:
    # -   property_specs; (dict) width, height and other property metadata
    # -   layers; (list of layer dicts) layer dicts contain 'type' ('image' or
    # -      'dataframe'), 'data', 'style' (if 'dataframe') and 'attribution'.
    # -      Layers will be added to themap from bottom to top (layers[0]
    # -      should be your basemap)
    # -   bbox; (string) 'w,s,e,n'. If not provided, will come from
    # -      property_specs['bbox']
    # OUT:
    # -   report_image: (PIL Image) the report map image
    # """

    if alt_size:
        width = property_specs['width_alt']
        height = property_specs['height_alt']
    else:
        width = property_specs['width']
        height = property_specs['height']

    if not bbox:
        bbox = property_specs['bbox']

    # attributions = [x['attribution'] for x in layers]
    # attribution_image = get_attribution_image(attributions, width, height)
    #
    # layers.append({'type': 'image', 'data':attribution_image})

    return merge_rasters_to_img(
        layers,
        bbox=bbox,
        img_height=height,
        img_width=width
    )

# modified from fetch.py
def contours_from_tnm_dem(bbox, width, height, dpi=settings.DPI, inSR=3857):
    """Fetches a DEM from The National Map and returns a PIL image with
    labeled contours

    Parameters
    ----------
    bbox : list-like
      bounding box with coordinats as (xmin, ymin, xmax, ymax)
    width : int
      width of image to return
    height : int
      height of image to return
    dpi : int
      dots per inch to be used in plotting
    inSR : int
      code for coordinate reference system

    Returns
    -------
    img : PIL Image
      rendered image with contours styled and labeled
    """

    # get the DEM data as a TIFF image, multiply value to convert meters to feet
    dem = dem_from_tnm(bbox=bbox, width=width, height=height, inSR=inSR) * 3.28084
    # Flip the image, to match plotting indices
    dem = np.flip(dem, axis=0)
    fig = plt.figure(frameon=False)
    fig.set_size_inches(width/dpi, height/dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    ax.set_aspect('equal')
    fig.add_axes(ax)

    fine_step = settings.CONTOUR_STYLE['fine_step']
    bold_step = settings.CONTOUR_STYLE['bold_step']

    min_fine, max_fine = (np.floor(dem.min()/fine_step)*fine_step,
                        np.ceil(dem.max()/fine_step)*fine_step+fine_step)
    min_bold, max_bold = (np.floor(dem.min()/bold_step)*bold_step,
                        np.ceil(dem.max()/bold_step)*bold_step+bold_step)

    # smaller, 40ft interval contour lines
    cont_fine = ax.contour(dem, levels=np.arange(min_fine, max_fine, fine_step),
                         colors=[settings.CONTOUR_STYLE['fine_color']],
                         linewidths=[settings.CONTOUR_STYLE['fine_width']])

    # bolder, 200ft interval contour lines
    cont_bold = ax.contour(dem, levels=np.arange(min_bold, max_bold, bold_step),
                          colors=[settings.CONTOUR_STYLE['bold_color']],
                          linewidths=[settings.CONTOUR_STYLE['bold_width']])

    # labels for the 200ft/bold contour lines
    fmt = ticker.StrMethodFormatter("{x:,.0f} ft")
    labels = ax.clabel(cont_bold, fontsize=settings.CONTOUR_STYLE['font_size'],
                       colors=[settings.CONTOUR_STYLE['bold_color']], fmt=fmt,
                       inline_spacing=0)
    for label in labels:
        # add halo effect to labels
        label.set_path_effects([pe.withStroke(linewidth=1, foreground='w')])

    img = plt_to_pil_image(fig, dpi=dpi)
    return img

# modified from fetch.py
def dem_from_tnm(bbox, width, height, inSR=3857, **kwargs):
    """
    Retrieves a Digital Elevation Model (DEM) image from The National Map (TNM)
    web service.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    width : int
      pixel width of desired image
    height: int
      pixel height of desired image
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)

    Returns
    -------
    dem : numpy array
      DEM image as array
    """
    BASE_URL = ''.join([
        'https://elevation.nationalmap.gov/arcgis/rest/',
        'services/3DEPElevation/ImageServer/exportImage?'
    ])

    params = dict(bbox=','.join([str(x) for x in bbox]),
                  bboxSR=inSR,
                  size=f'{width},{height}',
                  imageSR=inSR,
                  time=None,
                  format='tiff',
                  pixelType='F32',
                  noData=None,
                  noDataInterpretation='esriNoDataMatchAny',
                  interpolation='+RSP_BilinearInterpolation',
                  compression=None,
                  compressionQuality=None,
                  bandIds=None,
                  mosaicRule=None,
                  renderingRule=None,
                  f='image')
    for key, value in kwargs.items():
        params.update({key: value})

    result = requests.get(BASE_URL, params=params)
    dem = imread(io.BytesIO(result.content))

    return dem

################################
# Scalebar Functions          ###
################################

def get_scalebar_image(property_specs, span_ratio=0.75):
    image_width_in_pixels = property_specs['width']
    bbox = [float(x) for x in property_specs['bbox'].split(',')]
    # image_width_in_meters = bbox[2] - bbox[0]

    # get coords in EPSG:4326
    bbox_poly = get_bbox_as_polygon(property_specs['bbox'])
    bbox_poly.transform(4326)
    nw = Point(bbox_poly.coords[0][3])
    ne = Point(bbox_poly.coords[0][2])
    # geodesic measurement
    geod = pyproj.Geod(ellps='WGS84')
    angle1,angle2,distance = geod.inv(nw.coords[0], nw.coords[1], ne.coords[0], ne.coords[1])
    image_width_in_meters = distance

    return generate_scalebar_for_image(image_width_in_meters, image_width_in_pixels, span_ratio)

# Thanks to Senshin @ https://stackoverflow.com/a/33947673/706797
def get_first_sig_dig(x):
    return round(x / (10**floor(log10(x))))

# Thanks to Evgeny and Tobias Kienzler @ https://stackoverflow.com/a/3411435/706797
def round_to_1(x):
    return round(x, -int(floor(log10(abs(x)))))

def refit_step(step_tick, num_steps, max_width_in_units, min_step_width_in_pixels, units_per_pixel):

    sig_dig = get_first_sig_dig(step_tick)
    if num_steps > 1:
        step_tick = increase_step_size(step_tick, sig_dig)
        num_steps = int(max_width_in_units/step_tick)
    else:
        step_tick = reduce_step_size(step_tick, sig_dig)
        num_steps = int(max_width_in_units/step_tick)

    step_width_in_pixels = step_tick/units_per_pixel
    if step_width_in_pixels < min_step_width_in_pixels:
        growth_ratio = int(min_step_width_in_pixels/step_width_in_pixels)+1
        step_tick = step_tick * growth_ratio
        num_steps = int(max_width_in_units/step_tick)

    if num_steps < 1:
        # punt and worry about other things.
        step_tick = min_step_width_in_pixels * units_per_pixel
        num_steps = 1

    if step_tick > 10:
        step_tick = int(step_tick)

    return {
        'step_tick': step_tick,
        'num_steps': num_steps
    }

def increase_step_size(step_tick, sig_dig):
    if sig_dig in [1,2,5]:
        return step_tick
    elif sig_dig < 5:
        resize_factor = 5/sig_dig
    else:
        resize_factor = 10/sig_dig

    new_step_tick = resize_factor * step_tick
    return resize_factor * step_tick

def reduce_step_size(step_tick, sig_dig):
    if sig_dig < 3:
        resize_factor = 0.5
    elif sig_dig < 5:
        resize_factor = 2/sig_dig
    elif sig_dig == 5:
        return step_tick
    else:
        resize_factor = 5/sig_dig

    return step_tick * resize_factor

def generate_scalebar_for_image( img_width_in_meters, img_width_in_pixels=509, scale_width_ratio=1, min_step_width=100, dpi=300):
    bottom_units_per_pixel = img_width_in_meters/img_width_in_pixels
    if img_width_in_pixels > 500:
        units_bottom = 'meters'
        units_top = 'feet'
    else:
        units_bottom = 'm'
        units_top = 'ft'
    scale_bottom = 1
    scale_top = 0.3048
    scale_width_in_meters = img_width_in_meters*scale_width_ratio
    scale_width_in_pixels = scale_width_in_meters/bottom_units_per_pixel
    max_step_count = int(scale_width_in_pixels/min_step_width)
    num_steps_bottom = max_step_count
    if num_steps_bottom < 1:
        num_steps_bottom = 1
    if scale_width_in_meters/num_steps_bottom > 1000:
        if img_width_in_pixels > 500:
            units_bottom = 'km'
            units_top = 'miles'
        else:
            units_bottom = 'km'
            units_top = 'mi'
        scale_bottom = 1000
        scale_top = 1609.34
        bottom_units_per_pixel = bottom_units_per_pixel/scale_bottom
    bottom_unit_count = scale_width_in_meters/scale_bottom
    top_unit_count = scale_width_in_meters/scale_top
    step_ticks_bottom = round_to_1(bottom_unit_count/num_steps_bottom)

    refit_dict = refit_step(
        step_ticks_bottom,
        num_steps_bottom,
        scale_width_in_meters/scale_bottom,
        min_step_width,
        bottom_units_per_pixel/scale_bottom
    )
    step_ticks_bottom = refit_dict['step_tick']
    num_steps_bottom = refit_dict['num_steps']

    step_ticks_top = round_to_1(top_unit_count/num_steps_bottom)
    num_steps_top = num_steps_bottom

    refit_dict = refit_step(
        step_ticks_top,
        num_steps_top,
        top_unit_count,
        min_step_width,
        bottom_units_per_pixel*scale_bottom/scale_top
    )

    step_ticks_top = refit_dict['step_tick']
    num_steps_top = refit_dict['num_steps']

    num_ticks_top = num_steps_top + 1
    num_ticks_bottom = num_steps_bottom + 1

    return make_scalebar(
        num_ticks_top,
        step_ticks_top,
        num_ticks_bottom,
        step_ticks_bottom,
        bottom_units_per_pixel,
        scale_top=scale_top,
        scale_bottom=scale_bottom,
        units_top=units_top,
        units_bottom=units_bottom
    )

def format_label(value):
    if int(value) >= 1000:
        return '{:,d}'.format(value)
    # elif type(value) == int or value >= 10:
    #     return str(int(value))
    else:
        # 3 digits should be more than enough - in theory there should only be 1 unless things go sideways
        return '{:.3g}'.format(value)

def make_scalebar( num_ticks_top, step_ticks_top, num_ticks_bottom, step_ticks_bottom, bottom_units_per_pixel=None, scale_top=1.0, scale_bottom=3.28084, units_top='feet', units_bottom='meters'):

    """Renders a dual scale bar as a PIL Image.
    Parameters
    ----------
    num_ticks_top, num_ticks_bottom : int
      number of ticks, including starting and ending points, to use for drawing scale bars
    step_ticks_top, step_ticks_bottom : int
      amount that each successive tick adds to previous tick
    bottom_units_per_pixel : numeric
      the width of each pixel in the resulting image in the same units as
      the bottom scale bar. This parameters helps resize the resulting figure
      to ensure an accurate scale is generated.
    scale_top, scale_bottom : numeric
      relative scales of units in top and bottom scale bars
    units_top, units_bottom : str
      string used to label units on the last tick in the scale bar

    Returns
    -------
    img : PIL Image
      the dual scale bar rendered as an in-memory image
    """

    from matplotlib import pyplot as plt
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    DPI = 350

    width_top = (num_ticks_top - 1) * step_ticks_top * (scale_top / scale_bottom)
    width_bot = (num_ticks_bottom - 1) * step_ticks_bottom
    min_top, max_top = -width_top / 2, width_top / 2
    min_bot, max_bot = -width_bot / 2, width_bot / 2
    both_min, both_max = min(min_top, min_bot), max(max_top, max_bot)

    fig = plt.figure(frameon=False)
    fig.set_size_inches(settings.SCALEBAR_DEFAULT_WIDTH, settings.SCALEBAR_DEFAULT_HEIGHT)
    fig.dpi = DPI
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    # make the top scalebar
    # first, the line
    ax.plot((min_top, max_top), (1.0, 1.0), lw=0.25, color='black')
    # then, create the tick marks
    ticks_top = np.linspace(min_top, max_top, num_ticks_top)

    for i, x in enumerate(ticks_top):
        ax.plot((x, x), (1.0, 3.0), lw=0.25, color='black')
        # add the labels for each tick mark
        ax.text(x,
                4.0,
                format_label(step_ticks_top*i),
                horizontalalignment='center',
                verticalalignment='bottom',
                fontname='arial',
               fontsize=2)
        # add the units after the last tick mark
        if x == ticks_top[0]:
            spaces = ' ' * (len(format_label(step_ticks_top*i))+1)
            ax.text(x,
                    4.0,
                    spaces + units_top,
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    fontname='arial',
                   fontsize=2)

    # make the bottom scalebar
    # first, the line
    ax.plot((min_bot, max_bot), (-1, -1), lw=0.25, color='black')
    # then, create the tick marks
    ticks_bot = np.linspace(min_bot, max_bot, num_ticks_bottom)
    for i, x in enumerate(ticks_bot):
        ax.plot((x, x), (-1.0, -3.0), lw=0.25, color='black')
        # add the labels for each tick mark
        ax.text(x,
                -4.0,
                format_label(step_ticks_bottom*i),
                horizontalalignment='center',
                verticalalignment='top',
                fontname='arial',
                fontsize=2)
         # add the units after the last tick mark
        if x == ticks_bot[0]:
            spaces = ' ' * (len(format_label(step_ticks_bottom*i))+1)
            ax.text(x,
                    -4.0,
                    spaces + units_bottom,
                    horizontalalignment='left',
                    verticalalignment='top',
                    fontname='arial',
                    fontsize=2)
    # set display options so that ticks and labels are appropriately sized
    ax.set_ylim(-10, 10)
    ax.set_xlim(both_min * 1.05, both_max * 1.30)
    ax.axis('off')
    # calculate units per pixel for top scale bar
    img_coords_step_bot = fig.dpi_scale_trans.inverted().transform(
        ax.transData.transform(((ticks_bot[0], 1), (ticks_bot[-1], 1)))) * DPI
    img_scale_bot = (step_ticks_bottom *
                     (num_ticks_bottom - 1)) / (img_coords_step_bot[1][0] -
                                                img_coords_step_bot[0][0])
    # calculate adjustment factor to resize figure to enforce accurate scale
    adjust = img_scale_bot / bottom_units_per_pixel
    fig.set_size_inches(*(fig.get_size_inches() * adjust))
    img = plt_to_pil_image(fig, dpi=DPI)

    return img

def plt_to_pil_image(plt_figure, dpi=200, transparent=False):
    """
    Converts a matplotlib figure to a PIL Image (in memory).

    Parameters
    ---------
    plt_figure : matplotlib Figure object
      the figure to convert
    dpi : int
      the number of dots per inch to render the image
    transparent : bool, optional
      render plt with a transparent background

    Returns
    -------
    pil_image : Image
      the figure converted to a PIL Image
    """
    fig = plt.figure(plt_figure.number)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, transparent=transparent)
    buf.seek(0)
    pil_image = Image.open(buf)
    plt.close()

    return pil_image

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
    pil_image = False
    if data_content:
        try:
            fp.write(data_content)
        except TypeError as e:
            pil_image = Image.open(io.BytesIO(data_content.content))
    try:
        if not pil_image:
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
        if data_content:
            temp_file = open(outfilename, 'wb')
            temp_file.write(data_content)
            temp_file.close()
            pil_image = Image.open(outfilename)
            rgba_image = pil_image.convert("RGBA")
            os.remove(outfilename)
        else:
            rgba_image = Image.new("RGBA", (settings.REPORT_MAP_WIDTH, settings.REPORT_MAP_HEIGHT), (255,255,255,0))

    return rgba_image

def get_bbox_from_property(property, alt_size=False):       # TODO: This should be a method on property instances called 'bbox'
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
        alt_target_width = settings.REPORT_MAP_ALT_WIDTH
        alt_target_height = settings.REPORT_MAP_ALT_HEIGHT
        orientation = 'portrait'

    else:
        target_width = float(settings.REPORT_MAP_WIDTH)
        target_height = float(settings.REPORT_MAP_HEIGHT)
        alt_target_width = float(settings.REPORT_MAP_ALT_WIDTH)
        alt_target_height = float(settings.REPORT_MAP_ALT_HEIGHT)
        orientation = 'landscape'

    target_ratio = target_width / target_height
    pixel_width = target_width * (1 - settings.REPORT_MAP_MIN_BUFFER)
    pixel_height = target_height * (1 - settings.REPORT_MAP_MIN_BUFFER)

    alt_target_ratio = alt_target_width / alt_target_height
    alt_pixel_width = alt_target_width * (1 - settings.REPORT_MAP_MIN_BUFFER)
    alt_pixel_height = alt_target_height * (1 - settings.REPORT_MAP_MIN_BUFFER)

    # compare envelope ratio to target image ratio to make sure we constrain the correct axis first
    if property_ratio >= target_ratio: # limit by width
        if not alt_size:
            coord_per_pixel = property_width / pixel_width
            buffer_width_pixel = target_width * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_width_coord = abs(buffer_width_pixel * coord_per_pixel)
            property_pixel_height = property_height / coord_per_pixel
            height_diff = target_height - property_pixel_height
            buffer_height_pixel = height_diff / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
        else:
            coord_per_pixel = property_width / alt_pixel_width
            buffer_width_pixel = alt_target_width * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_width_coord = abs(buffer_width_pixel * coord_per_pixel)
            property_pixel_height = property_height / coord_per_pixel
            height_diff = alt_target_height - property_pixel_height
            buffer_height_pixel = height_diff / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
    else:   # limit by height
        if not alt_size:
            coord_per_pixel = property_height / pixel_height
            buffer_height_pixel = target_height * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
            property_pixel_width = property_width / coord_per_pixel
            width_diff = target_width - property_pixel_width
            buffer_width_pixel = width_diff / 2
            buffer_width_coord = abs(buffer_width_pixel * coord_per_pixel)
        else:
            coord_per_pixel = property_height / alt_pixel_height
            buffer_height_pixel = alt_target_height * settings.REPORT_MAP_MIN_BUFFER / 2
            buffer_height_coord = abs(buffer_height_pixel * coord_per_pixel)
            property_pixel_width = property_width / coord_per_pixel
            width_diff = alt_target_width - property_pixel_width
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

# def get_attribution_image(attribution_list, width, height):
#     # """
#     # PURPOSE:
#     # -   given a stringified list of attributions, return an image overlay.
#     # IN:
#     # -   attribution: a string of attributions for included layers
#     # -   width: (int) number of pixels wide the image is.
#     # -   height: (int) number of pixels tall the image is.
#     # OUT:
#     # -   attribution_image: (PIL Image) the the attribution image to be imposed atop report images
#     # """
#     TEXT_BUFFER = settings.ATTRIBUTION_TEXT_BUFFER
#     LINE_SPACING = settings.ATTRIBUTION_TEXT_LINE_SPACING
#     box_fill = settings.ATTRIBUTION_BOX_FILL_COLOR
#     text_color = settings.ATTRIBUTION_TEXT_COLOR
#     text_font = ImageFont.truetype(settings.ATTRIBUTION_TEXT_FONT, settings.ATTRIBUTION_TEXT_FONT_SIZE)
#
#     # Create overlay image
#     base_img = Image.new("RGBA", (width, height), (255,255,255,0))
#
#     if type(attribution_list) == list:
#         # clean list
#         attribution_list = [x for x in attribution_list if x]
#
#         attribution_list = ', '.join(attribution_list)
#     # calculate text size
#     (text_width, text_height) = text_font.getsize(attribution_list)
#
#     # Create a list of rows of attribution text
#     attribution_rows = []
#     attribution_word_list = attribution_list.split(' ')
#     while len(attribution_word_list) > 0:
#         new_row = [attribution_word_list.pop(0)]
#         while len(attribution_word_list) > 0 and text_font.getsize(' '.join(new_row + [attribution_word_list[0]]))[0] < (width-2*TEXT_BUFFER):
#             new_row.append(attribution_word_list.pop(0))
#         attribution_rows.append(' '.join(new_row))
#
#     # determine text_block size
#     text_block_height = 2*TEXT_BUFFER + (text_height + LINE_SPACING) * len(attribution_rows) - LINE_SPACING
#     if len(attribution_rows) > 1:
#         text_block_width = width
#     else:
#         text_block_width = text_width + 2*TEXT_BUFFER
#
#     # draw box
#     left_px = width - text_block_width
#     top_px = height - text_block_height
#     right_px = width
#     bottom_px = height
#     box_shape = [(left_px, top_px), (right_px, bottom_px)]
#     text_box = ImageDraw.Draw(base_img)
#     text_box.rectangle(box_shape, fill=settings.ATTRIBUTION_BOX_FILL_COLOR, outline=settings.ATTRIBUTION_BOX_OUTLINE)
#
#     # TODO: create box and text separately with full opacity, apply to base using:
#     #       out = Image.alpha_composite(base, txt)
#     # or something similar to remove 'checkered pattern' on attribute box.
#
#     # draw text
#     # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html?highlight=RGBA#example-draw-partial-opacity-text
#     text_top = top_px + TEXT_BUFFER
#     text_left = left_px + TEXT_BUFFER
#     for (idx, text_row) in enumerate(attribution_rows):
#         if idx != 0:
#             text_top += LINE_SPACING
#         txt = ImageDraw.Draw(base_img)
#         txt.text((text_left, text_top), text_row, font=text_font, fill=text_color)
#         text_top += text_height
#
#     return base_img

def get_collection_from_objects(source_objects, geom_field, bbox, attrs=[]):
    xmin, ymin, xmax, ymax = bbox.split(',')
    # would this be easier to read the wkt into a gpd.GeoSeries?
    features = []
    for source_object in source_objects:
        feature_obj = {
            "type": "Feature",
            "properties": {},
            "geometry": json.loads(getattr(source_object, geom_field).json)
        }
        for attr in attrs:
            feature_obj['properties'][attr] = getattr(source_object, attr)
        features.append(feature_obj)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
        "bbox": (xmin, ymin, xmax, ymax)
    }
    return feature_collection

def get_gdf_from_features(collection):
    return gpd.GeoDataFrame.from_features(collection, crs="EPSG:%s" % settings.GEOMETRY_CLIENT_SRID)

def merge_rasters_to_img(layers, bbox, img_height=settings.REPORT_MAP_HEIGHT, img_width=settings.REPORT_MAP_WIDTH, dpi=settings.DPI):
    [xmin, ymin, xmax, ymax] = [float(x) for x in bbox.split(',')]
    bbox_array = [xmin, ymin, xmax, ymax]
    fig, ax = plt.subplots(figsize=(img_width/float(dpi),img_height/float(dpi)), dpi=dpi)
    for layer in layers:
        if layer['type'] == 'image':
            trf = transform.from_bounds(*bbox_array, width=img_width, height=img_height)
            work = show(reshape_as_raster(layer['data']), ax=ax, transform=trf)
        else:   # 'gdf' only for now
            if 'label' in layer['style'].keys():
                # adding labels according to Ianery and Martien Lubberink at https://stackoverflow.com/a/38902492/706797
                # Clip the soil polygons to the view extent:
                bbox_poly = shapely.geometry.Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
                bbox_gdf = gpd.GeoDataFrame([1], geometry=[bbox_poly])
                bbox_gdf.set_crs(epsg=3857)
                layer['data'] = gpd.clip(layer['data'], bbox_gdf)
                #Create a new point layer for the label data and locations
                layer['data']['coords'] = layer['data']['geometry'].apply(lambda x: x.representative_point().coords[:])
                layer['data']['coords'] = [coords[0] for coords in layer['data']['coords']]

                # If a GDF has a key added that isn't 'geometry' or 'coords', it becomes a label.
                label_key = False
                for idx, row in layer['data'].iterrows():
                    if idx ==0:
                        for key in row.keys():
                            if key not in ['geometry', 'coords']:
                                label_key = key
                                continue
                    if label_key:
                        text = ax.text(
                            row.coords[0],
                            row.coords[1],
                            s=row[label_key],
                            color="#FFFFFF",
                            size=layer['style']['label']['fontsize'],
                            fontweight='bold',
                            horizontalalignment='center',
                            verticalalignment='center',
                            bbox=layer['style']['label']['bbox']
                        )
                        text.set_path_effects([
                            pe.Stroke(
                                linewidth=layer['style']['label']['halo']['size'],
                                foreground=layer['style']['label']['halo']['color']
                            ),
                            pe.Normal()]
                        )
            work = layer['data'].plot(
                ax=ax,
                lw=layer['style']['lw'],
                ec=layer['style']['ec'],
                fc=layer['style']['fc']
            )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    return fig2img(fig)

# Updated from https://web-backend.icare.univ-lille.fr/tutorials/convert_a_matplotlib_figure
def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )

    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.frombuffer ( fig.canvas.tostring_argb(), dtype=np.uint8 )
    buf.shape = ( w, h,4 )

    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll ( buf, 3, axis = 2 )
    return buf

def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # RDH: Trim off axes borders:
    fig.subplots_adjust(bottom = 0)
    fig.subplots_adjust(top = 1)
    fig.subplots_adjust(right = 1)
    fig.subplots_adjust(left = 0)

    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.frombytes( "RGBA", ( w ,h ), buf.tostring( ) )

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
    return (
        # x
        ZOOM0_SIZE * (2 ** zoom) * (1 + lon / 180) / 2,
        # y
        ZOOM0_SIZE / (2 * pi) * (2 ** zoom) * (pi - log(tan(pi / 4 * (1 + lat / 90))))
    )
# Pixel coordinate => geo-coordinate in degrees
def p2g(x, y, zoom):
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

    tiles_dict_array = []

    # Calculate Meters/Pixel for bbox, size
    # Below gets us a rough estimate, and may give us errors later.
    # To do this right, check out this:
    #   https://wiki.openstreetmap.org/wiki/Zoom_levels#Distance_per_pixel_math
    [west, south, east, north] = [float(x) for x in bbox.split(',')]

    zoom = get_zoom_from_bbox(bbox, tile_height=request_dict['TILE_HEIGHT'], tile_width=request_dict['TILE_WIDTH'], img_height=height, img_width=width)

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
            # stream_image = stream_image.resize((request_dict['TILE_IMAGE_WIDTH']*2,request_dict['TILE_IMAGE_HEIGHT']*2), Image.ANTIALIAS)
            base_image = merge_images(base_image, stream_image, int(x*request_dict['TILE_IMAGE_WIDTH']), int(y*request_dict['TILE_IMAGE_HEIGHT']))

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
