"""
Functions that retrieve images and features from public web services.
"""

import io
import numpy as np
import requests
from functools import partial
from multiprocessing.pool import ThreadPool

from rasterio import transform, windows
from rasterio.features import rasterize
import shapely
from shapely.errors import TopologicalError
from shapely.geometry import box, LineString, MultiLineString
import geopandas as gpd

from imageio import imread
from scipy.ndimage.filters import convolve
from scipy.ndimage.morphology import distance_transform_edt as edt
from skimage.morphology import disk
from skimage import filters
from skimage.transform import resize
from skimage.util import apply_parallel


def soils_from_nrcs(bbox, inSR, **kwargs):
    """
    Retrieve soil map units from NRCS Soil Data Mart within user-defined
    bounding box.

    Parameters
    ----------
    bbox : 4-tuple or list
      coordinates of x_min, y_min, x_max, and y_max for bounding box of tile
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)

    Returns
    -------
    soils : GeoDataFrame
    """

    from landmapper.views import unstable_request_wrapper

    wgs_gdf = gpd.GeoDataFrame(geometry=[box(*bbox)], crs=inSR).to_crs(4326)
    wgs_bbox = wgs_gdf.iloc[0].geometry.bounds

    BASE_URL = ''.join([
        'https://sdmdataaccess.sc.egov.usda.gov/Spatial/',
        'SDMWGS84GEOGRAPHIC.wfs?SERVICE=WFS&REQUEST=GetFeature'
    ])
    params = dict(
        VERSION='1.1.0',
        TYPENAME='mapunitpoly',
        SRSNAME=f'EPSG:4326',
        bbox=','.join([str(x) for x in wgs_bbox]),
    )
    for key, value in kwargs.items():
        params.update({key: value})

    url = requests.Request('GET', BASE_URL, params=params).prepare().url
    url_response = unstable_request_wrapper(url)
    soils = gpd.read_file(url_response)

    # for some reason, the NRCS web service is mixing up X and Y coordinates
    soils['geometry'] = soils.geometry.map(  # swap them here
        lambda polygon: shapely.ops.transform(lambda x, y: (y, x), polygon))

    soils = soils.set_crs('EPSG:4326')
    soils = soils.to_crs(inSR)
    soils = gpd.clip(soils, box(*bbox))
    KEEP_COLS = {'areasymbol': str,
                 'spatialversion': int,
                 'musym': str,
                 'nationalmusym': str,
                 'mukey': int,
                 'mupolygonkey': int}
    for key, value, in KEEP_COLS.items():
        soils[key] = soils[key].astype(value)

    if soils.crs.is_projected:
        if soils.crs.axis_info[0].unit_name == 'metre':
            soils['acres'] = soils.area / 4046.86
        elif 'foot' in soils.crs.axis_info[0].unit_name:
            soils['acres'] = soils.area / 43560

    return soils


def naip_from_tnm(bbox, res, inSR=4326, **kwargs):
    """
    Retrieves a NAIP image from The National Map (TNM) web service.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    res : numeric
      spatial resolution to use for returned DEM (grid cell size)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)

    Returns
    -------
    img : array
      NAIP image as a 3-band or 4-band array
    """
    BASE_URL = ''.join([
        'https://services.nationalmap.gov/arcgis/rest/services/',
        'USGSNAIPImagery/ImageServer/exportImage?'
    ])

    width = int(abs(bbox[2] - bbox[0]) // res)
    height = int(abs(bbox[3] - bbox[1]) // res)

    params = dict(
        bbox=','.join([str(x) for x in bbox]),
        bboxSR=inSR,
        size=f'{width},{height}',
        imageSR=inSR,
        format='tiff',
        pixelType='U8',
        noDataInterpretation='esriNoDataMatchAny',
        interpolation='+RSP_BilinearInterpolation',
        time=None,
        noData=None,
        compression=None,
        compressionQuality=None,
        bandIds=None,
        mosaicRule=None,
        renderingRule=None,
        f='image',
    )
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    img = imread(io.BytesIO(r.content))

    return img


def dem_from_tnm(bbox, res, inSR=4326, **kwargs):
    """
    Retrieves a Digital Elevation Model (DEM) image from The National Map (TNM)
    web service.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    res : numeric
      spatial resolution to use for returned DEM (grid cell size)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)

    Returns
    -------
    dem : numpy array
      DEM image as array
    """
    width = int(abs(bbox[2] - bbox[0]) // res)
    height = int(abs(bbox[3] - bbox[1]) // res)

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

    r = requests.get(BASE_URL, params=params)
    dem = imread(io.BytesIO(r.content))

    return dem


def tpi_from_tnm(bbox,
                 irad,
                 orad,
                 dem_resolution,
                 smooth_highres_dem=True,
                 tpi_resolution=30,
                 parallel=True,
                 norm=True,
                 fixed_mean=None,
                 fixed_std=None,
                 **kwargs):
    """
    Produces a raster of Topographic Position Index (TPI) by fetching a Digital
    Elevation Model (DEM) from The National Map (TNM) web service.

    TPI is the difference between the elevation at a location from the average
    elevation of its surroundings, calculated using an annulus (ring). This
    function permits the calculation of average surrounding elevation using
    a coarser grain, and return the TPI user a higher-resolution DEM.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    irad : numeric
      inner radius of annulus used to calculate TPI
    orad : numeric
      outer radius of annulus used to calculate TPI
    dem_resolution : numeric
      spatial resolution of Digital Elevation Model (DEM)
    tpi_resolution : numeric
      spatial resolution of DEM used to calculate TPI
    norm : bool
      whether to return a normalized version of TPI, with mean = 0 and SD = 1
    fixed_mean : numeric
      mean value to use to normalize data, useful to to set as a constant when
      processing adjacent tiles to avoid stitching/edge effects
    fixed_std : numeric
      standard deviation value to use to normalize data, useful to to set as a
      constant when processing adjacent tiles to avoid stitching/edge effects

    Returns
    -------
    tpi : array
      TPI image as array
    """
    tpi_bbox = np.array(bbox)
    tpi_bbox[0:2] = tpi_bbox[0:2] - orad
    tpi_bbox[2:4] = tpi_bbox[2:4] + orad
    k_orad = orad // tpi_resolution
    k_irad = irad // tpi_resolution

    kernel = disk(k_orad) - np.pad(disk(k_irad), pad_width=(k_orad - k_irad))
    weights = kernel / kernel.sum()

    if dem_resolution != tpi_resolution:
        dem = dem_from_tnm(bbox, dem_resolution, **kwargs)
        if dem_resolution < 3 and smooth_highres_dem:
            dem = filters.gaussian(dem, 3)
        dem = np.pad(dem, orad // dem_resolution)
        tpi_dem = dem_from_tnm(tpi_bbox, tpi_resolution, **kwargs)

    else:
        tpi_dem = dem_from_tnm(tpi_bbox, tpi_resolution, **kwargs)
        dem = tpi_dem

    if parallel:

        def conv(tpi_dem):
            return convolve(tpi_dem, weights)

        convolved = apply_parallel(conv, tpi_dem, compute=True, depth=k_orad)
        if tpi_resolution != dem_resolution:
            tpi = dem - resize(convolved, dem.shape)
        else:
            tpi = dem - convolved

    else:
        if tpi_resolution != dem_resolution:
            tpi = dem - resize(convolve(tpi_dem, weights), dem.shape)
        else:
            tpi = dem - convolve(tpi_dem, weights)

    # trim the padding around the dem used to calculate TPI
    tpi = tpi[orad // dem_resolution:-orad // dem_resolution,
              orad // dem_resolution:-orad // dem_resolution]

    if norm:
        if fixed_mean is not None and fixed_std is not None:
            tpi_mean = fixed_mean
            tpi_std = fixed_std
        else:
            tpi_mean = (tpi_dem - convolved).mean()
            tpi_std = (tpi_dem - convolved).std()
        tpi = (tpi - tpi_mean) / tpi_std

    return tpi


def water_bodies_from_dnr(layer_num,
                          bbox,
                          inSR=4326,
                          raster_resolution=None,
                          distance_transform=False,
                          **kwargs):
    """
    Returns hydrographic features from the Washington DNR web service.

    Parameters
    ----------
    layer_num : int
      0 will request water courses, 1 will request water bodies
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy).
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      if provided, the results will be returned as a raster with grid cell size
    distance_transform : bool
      if result is rasterized, a value of True will return the distance from
      the nearest feature rather than the binary raster of features.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified

    """
    BASE_URL = ''.join([
        'https://gis.dnr.wa.gov/site2/rest/services/Public_Water/',
        'WADNR_PUBLIC_Hydrography/MapServer/',
        str(layer_num), '/query?'
    ])

    params = dict(text=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelEnvelopeIntersects',
                  relationParam=None,
                  outFields='*',
                  returnGeometry='true',
                  returnTrueCurves='false',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  outSR=inSR,
                  having=None,
                  returnIdsOnly='false',
                  returnCountOnly='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  returnZ='false',
                  returnM='false',
                  gdbVersion=None,
                  historicMoment=None,
                  returnDistinctValues='false',
                  resultOffset=None,
                  resultRecordCount=None,
                  queryByDistance=None,
                  returnExtentOnly='false',
                  datumTransformation=None,
                  parameterValues=None,
                  rangeValues=None,
                  quantizationParameters=None,
                  f='geojson')
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)

    if len(gdf) > 0:
        clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            clip_ras = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        if distance_transform:
            neg = np.logical_not(clip_ras)
            raster = edt(neg)
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def parcels_from_wa(bbox,
                    inSR=4326,
                    raster_resolution=None,
                    distance_transform=False,
                    **kwargs):
    """
    Returns tax lot boundaries as features from the Washington Geospatial
    Open Data Portal

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy).
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      if provided, the results will be returned as a raster with grid cell size
    distance_transform : bool
      if result is rasterized, a value of True will return the distance from
      the nearest feature rather than the binary raster of features.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified

    """
    BASE_URL = ''.join([
        'https://services.arcgis.com/jsIt88o09Q0r1j8h/arcgis/rest/services/',
        'Current_Parcels_2020/FeatureServer/0/query?'
    ])

    params = dict(
        where=None,
        objectIds=None,
        time=None,
        geometry=','.join([str(x) for x in bbox]),
        geometryType='esriGeometryEnvelope',
        inSR=inSR,
        spatialRel='esriSpatialRelEnvelopeIntersects',
        resultType='none',
        distance=0.0,
        units='esriSRUnit_Meter',
        returnGeodetic='false',
        outFields='*',
        returnGeometry='true',
        returnCentroid='false',
        featureEncoding='esriDefault',
        multipatchOption='xyFootprint',
        maxAllowableOffset=None,
        geometryPrecision=None,
        outSR=inSR,
        datumTransformation=None,
        applyVCSProjection='false',
        returnIdsOnly='false',
        returnUniqueIdsOnly='false',
        returnCountOnly='false',
        returnExtentOnly='false',
        returnQueryGeometry='false',
        returnDistinctValues='false',
        cacheHint='false',
        orderByFields=None,
        groupByFieldsForStatistics=None,
        outStatistics=None,
        having=None,
        resultOffset=None,
        resultRecordCount=None,
        returnZ='false',
        returnM='false',
        returnExceededLimitFeatures='true',
        quantizationParameters=None,
        sqlFormat='none',
        f='pgeojson',
        token=None,
    )
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)
    try:
        clip_gdf = gpd.clip(gdf, box(*bbox))
    except TopologicalError:
        try:
            clip_gdf = gpd.clip(gdf.buffer(0), box(*bbox))
        except:
            raise

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            clip_ras = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        if distance_transform:
            neg = np.logical_not(clip_ras)
            raster = edt(neg)
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def nhd_from_tnm(nhd_layer,
                 bbox,
                 inSR=4326,
                 raster_resolution=None,
                 distance_transform=False,
                 **kwargs):
    """Returns features from the National Hydrography Dataset Plus High
    Resolution web service from The National Map.

    Available layers are:

    =========  ======================
    NHD Layer  Description
    =========  ======================
    0          NHDPlusSink
    1          NHDPoint
    2          NetworkNHDFlowline
    3          NonNetworkNHDFlowline
    4          FlowDirection
    5          NHDPlusWall
    6          NHDPlusBurnLineEvent
    7          NHDLine
    8          NHDArea
    9          NHDWaterbody
    10         NHDPlusCatchment
    11         WBDHU12
    =========  ======================

    Parameters
    ----------
    nhd_layer : int
       a value from 0-11 indicating the feature layer to retrieve.
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy).
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.
    distance_transform : bool
      if result is rasterized, a value of True will return the distance from
      the nearest feature rather than the binary raster of features.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified
    """
    BASE_URL = ''.join([
        'https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/',
        'MapServer/',
        str(nhd_layer), '/query?'
    ])

    params = dict(where=None,
                  text=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelIntersects',
                  relationParam=None,
                  outFields=None,
                  returnGeometry='true',
                  returnTrueCurves='false',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  outSR=inSR,
                  having=None,
                  returnIdsOnly='false',
                  returnCountOnly='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  returnZ='false',
                  returnM='false',
                  gdbVersion=None,
                  historicMoment=None,
                  returnDistinctValues='false',
                  resultOffset=None,
                  resultRecordCount=None,
                  queryByDistance=None,
                  returnExtentOnly='false',
                  datumTransformation=None,
                  parameterValues=None,
                  rangeValues=None,
                  quantizationParameters=None,
                  featureEncoding='esriDefault',
                  f='geojson')
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    try:
        gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)

    # this API seems to return M and Z values even if not requested
    # this catches the error and keeps only the first two coordinates (x and y)
    except AssertionError:
        js = r.json()
        for f in js['features']:
            f['geometry'].update({
                'coordinates': [c[0:2] for c in f['geometry']['coordinates']]
            })
        gdf = gdf = gpd.GeoDataFrame.from_features(js)

    if len(gdf) > 0:
        clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            clip_ras = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        if distance_transform:
            neg = np.logical_not(clip_ras)
            raster = edt(neg)
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def watersheds_from_tnm(huc_level,
                        bbox,
                        inSR,
                        raster_resolution=None,
                        distance_transform=False):
    """Returns features for watershed boundaries at the geographic extent
    specified by the user from The National Map web service.

    Available Hydrologic Unit Codes (`huc_level`) are translated to the
    following feature services:

    =========  ============  ==========
    HUC Level  Description   Feature ID
    =========  ============  ==========
    2          Region            1
    4          Subregion         2
    6          Basin             3
    8          Subbasin          4
    10         Watershed         5
    12         Subwatershed      6
    14         --                7
    =========  ============  ==========

    Parameters
    ----------
    huc_level : int
       the number of digits for the Hydrologic Unit Code, higher numbers
       correspond to smaller regional extents (more detailed delineation of
       watersheds). Must be one of {2, 4, 6, 8, 10, 12, 14}
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.
    distance_transform : bool
      if result is rasterized, a value of True will return the distance from
      the nearest feature rather than the binary raster of features.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified
    """
    feature_ids = {2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6, 14: 7}
    keys = feature_ids.keys()
    if huc_level not in keys:
        raise ValueError(f'huc_level not recognized, must be one of {keys}')

    feat_id = feature_ids[huc_level]
    BASE_URL = ''.join([
        'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/',
        'MapServer/',
        str(feat_id), '/query?'
    ])

    params = dict(where=None,
                  text=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelIntersects',
                  relationParam=None,
                  outFields=None,
                  returnGeometry='true',
                  returnTrueCurves='false',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  outSR=inSR,
                  having=None,
                  returnIdsOnly='false',
                  returnCountOnly='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  returnZ='false',
                  returnM='false',
                  gdbVersion=None,
                  historicMoment=None,
                  returnDistinctValues='false',
                  resultOffset=None,
                  resultRecordCount=None,
                  queryByDistance=None,
                  returnExtentOnly='false',
                  datumTransformation=None,
                  parameterValues=None,
                  rangeValues=None,
                  quantizationParameters=None,
                  featureEncoding='esriDefault',
                  f='geojson')
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)

    if len(gdf) > 0:
        clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            clip_ras = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        if distance_transform:
            neg = np.logical_not(clip_ras)
            raster = edt(neg)
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def tribal_lands_from_bia(bbox,
                          inSR,
                          layer_num=0,
                          raster_resolution=None,
                          **kwargs):
    """Returns features indicating tribal lands.

    Available layers (`layer_num`) are translated to the following feature
    services:

    =========  ============================================================
    Layer No.  Description
    =========  ============================================================
    0          American Indian Reservations / Federally Recognized Tribal
               Entities
    1          Indian Land Areas Judicially Established 1978
    =========  ============================================================

    Parameters
    ----------
    layer_num : int
       the feature layer to request. Must be one of {0, 1}
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified
    """
    BASE_URLS = [
        ''.join([
            'http://gis.wim.usgs.gov/arcgis/rest/services/AIR_NDGA/AIR_NDGA/',
            'MapServer/0/query?'
        ]), ''.join([
            'http://gis.wim.usgs.gov/arcgis/rest/services/AIR_NDGA/'
            'JudiciallyEstablished1978/MapServer/0/query?'
        ])
    ]
    BASE_URL = BASE_URLS[layer_num]

    params = dict(where=None,
                  text=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelIntersects',
                  relationParam=None,
                  outFields=None,
                  returnGeometry='true',
                  returnTrueCurves='false',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  outSR=inSR,
                  returnIdsOnly='false',
                  returnCountOnly='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  returnZ='false',
                  returnM='false',
                  gdbVersion=None,
                  historicMoment=None,
                  returnDistinctValues='false',
                  resultOffset=None,
                  resultRecordCount=None,
                  f='geojson')
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)

    if len(gdf) > 0:
        try:
            clip_gdf = gpd.clip(gdf, box(*bbox))
        except TopologicalError:
            gdf['geometry'] = gdf.buffer(0)
            clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            raster = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def indigenous_areas_from_nativeland(bbox,
                                     inSR,
                                     layer='territories',
                                     raster_resolution=None,
                                     **kwargs):
    """Returns features indicating extent indigenous lands from NativeLands.ca.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    layer : str
      type of features to return, must be one of {'territories', 'languages',
      'treaties'}
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified
    """
    BASE_URL = 'https://native-land.ca/coordinates/'
    urls = {
        'territories': BASE_URL + 'indigenousTerritories.json',
        'treaties': BASE_URL + 'indigenousTreaties.json',
        'languages': BASE_URL + 'indigenousLanguages.json'
    }

    gdf = gpd.read_file(urls[layer]).to_crs(inSR)

    if len(gdf) > 0:
        try:
            clip_gdf = gpd.clip(gdf, box(*bbox))
        except TopologicalError:
            gdf['geometry'] = gdf.buffer(0)
            clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            raster = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def tribal_cessions_from_usfs(bbox, inSR, raster_resolution=None, **kwargs):
    """Returns features indicating land ceded by Tribes and First Nations from
    a US Forest Service web service.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.

    Returns
    -------
    clip_gdf : GeoDataFrame
      features in vector format, clipped to bbox
    raster : array
      features rasterized into an integer array with 0s as background values
      and 1s wherever features occured; only returned if `raster_resolution` is
      specified
    """
    BASE_URL = ''.join([
        'https://apps.fs.usda.gov/arcx/rest/services/EDW/',
        'EDW_TribalCessionLands_01/MapServer/0/query?'
    ])

    params = dict(where=None,
                  text=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelIntersects',
                  relationParam=None,
                  outFields='*',
                  returnGeometry='true',
                  returnTrueCurves='false',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  having=None,
                  outSR=inSR,
                  returnIdsOnly='false',
                  returnCountOnly='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  returnZ='false',
                  returnM='false',
                  gdbVersion=None,
                  historicMoment=None,
                  returnDistinctValues='false',
                  resultOffset=None,
                  resultRecordCount=None,
                  queryByDistance=None,
                  returnExtentOnly='false',
                  datumTransformation=None,
                  parameterValues=None,
                  rangeValues=None,
                  quantizationParameters=None,
                  featureEncoding='esriDefault',
                  f='geojson')
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)
    rename_cols = [col.split('.')[-1] for col in gdf.columns]
    gdf.columns = rename_cols

    if len(gdf) > 0:
        try:
            clip_gdf = gpd.clip(gdf, box(*bbox))
        except TopologicalError:
            gdf['geometry'] = gdf.buffer(0)
            clip_gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        gdf_box = [int(x) for x in gdf.unary_union.bounds]
        gdf_width = int(abs(gdf_box[2] - gdf_box[0]) // raster_resolution)
        gdf_height = int(abs(gdf_box[3] - gdf_box[1]) // raster_resolution)

        full_transform = transform.from_bounds(*gdf_box, gdf_width, gdf_height)
        clip_win = windows.from_bounds(*bbox,
                                       transform=full_transform,
                                       width=width,
                                       height=height)
        if len(gdf) > 0:
            full_raster = rasterize(gdf.boundary.geometry,
                                    out_shape=(gdf_height, gdf_width),
                                    transform=full_transform,
                                    dtype='uint8')
            raster = full_raster[
                clip_win.round_offsets().round_lengths().toslices()]
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return clip_gdf


def buildings_from_microsoft(bbox, inSR, raster_resolution=None):
    """Returns building footprints generated by Microsoft and hosted by an
    ArcGIS Feature Server.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy).
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    raster_resolution : numeric
      causes features to be returned in raster (rather than vector) format,
      with spatial resolution defined by this parameter.
    """
    BASE_URL = ''.join([
        'https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/',
        'MSBFP2/FeatureServer/0/query?'
    ])

    params = dict(where=None,
                  objectIds=None,
                  time=None,
                  geometry=','.join([str(x) for x in bbox]),
                  geometryType='esriGeometryEnvelope',
                  inSR=inSR,
                  spatialRel='esriSpatialRelIntersects',
                  resultType='none',
                  distance=0.0,
                  units='esriSRUnit_Meter',
                  returnGeodetic='false',
                  outFields=None,
                  returnGeometry='true',
                  returnCentroid='false',
                  featureEncoding='esriDefault',
                  multipatchOption='xyFootprint',
                  maxAllowableOffset=None,
                  geometryPrecision=None,
                  outSR=inSR,
                  datumTransformation=None,
                  applyVCSProjection='false',
                  returnIdsOnly='false',
                  returnUniqueIdsOnly='false',
                  returnCountOnly='false',
                  returnExtentOnly='false',
                  returnQueryGeometry='false',
                  returnDistinctValues='false',
                  cacheHint='false',
                  orderByFields=None,
                  groupByFieldsForStatistics=None,
                  outStatistics=None,
                  having=None,
                  resultOffset=None,
                  resultRecordCount=None,
                  returnZ='false',
                  returnM='false',
                  returnExceededLimitFeatures='true',
                  quantizationParameters=None,
                  sqlFormat='none',
                  f='pgeojson',
                  token=None)

    r = requests.get(BASE_URL, params=params)
    gdf = gpd.GeoDataFrame.from_features(r.json(), crs=inSR)

    if len(gdf) > 0:
        gdf = gpd.clip(gdf, box(*bbox))

    if raster_resolution:
        width = int(abs(bbox[2] - bbox[0]) // raster_resolution)
        height = int(abs(bbox[3] - bbox[1]) // raster_resolution)
        trf = transform.from_bounds(*bbox, width, height)
        if len(gdf) > 0:
            raster = rasterize(gdf.geometry,
                               out_shape=(height, width),
                               transform=trf,
                               dtype='uint8')
        else:
            raster = np.zeros((height, width), dtype='uint8')
        return raster

    else:
        return gdf


def split_quad(bbox):
    """Splits a bounding box into four quadrants and returns their bounds.

    Parameters
    ---------
    bbox : 4-tuple or list
      coordinates of x_min, y_min, x_max, and y_max for bounding box of tile

    Returns
    -------
    quads : list
      coordinates of x_min, y_min, x_max, and y_max for each quadrant, in order
      of nw, ne, sw, se
    """
    xmin, ymin, xmax, ymax = bbox
    nw_bbox = [xmin, (ymin + ymax) / 2, (xmin + xmax) / 2, ymax]
    ne_bbox = [(xmin + xmax) / 2, (ymin + ymax) / 2, xmax, ymax]
    sw_bbox = [xmin, ymin, (xmin + xmax) / 2, (ymin + ymax) / 2]
    se_bbox = [(xmin + xmax) / 2, ymin, xmax, (ymin + ymax) / 2]
    quads = [nw_bbox, ne_bbox, sw_bbox, se_bbox]

    return quads


def quad_fetch(fetcher, bbox, num_threads=4, qq=False, *args, **kwargs):
    """Breaks user-provided bounding box into quadrants and retrieves data
    using `fetcher` for each quadrant in parallel using a ThreadPool.

    Parameters
    ----------
    fetcher : callable
      data-fetching function, expected to return an array-like object
    bbox : 4-tuple or list
      coordinates of x_min, y_min, x_max, and y_max for bounding box of tile
    num_threads : int
      number of threads to use for parallel executing of data requests
    qq : bool
      whether or not to execute request for quarter quads, which executes this
      function recursively for each quadrant
    *args
      additional positional arguments that will be passed to `fetcher`
    **kwargs
      additional keyword arguments that will be passed to `fetcher`

    Returns
    -------
    quad_img : array
      image returned with quads stitched together into a single array

    """
    bboxes = split_quad(bbox)

    if qq:
        nw = quad_fetch(fetcher, bbox=bboxes[0], *args, **kwargs)
        ne = quad_fetch(fetcher, bbox=bboxes[1], *args, **kwargs)
        sw = quad_fetch(fetcher, bbox=bboxes[2], *args, **kwargs)
        se = quad_fetch(fetcher, bbox=bboxes[3], *args, **kwargs)

    else:
        get_quads = partial(fetcher, *args, **kwargs)
        with ThreadPool(num_threads) as p:
            quads = p.map(get_quads, bboxes)
            nw, ne, sw, se = quads

    quad_img = np.vstack([np.hstack([nw, ne]), np.hstack([sw, se])])

    return quad_img


def nlcd_from_mrlc(bbox, res, layer, inSR=4326, nlcd=True, **kwargs):
    """
    Retrieves National Land Cover Data (NLCD) Layers from the Multiresolution
    Land Characteristics Consortium's web service.

    Parameters
    ----------
    bbox : list-like
      list of bounding box coordinates (minx, miny, maxx, maxy)
    res : numeric
      spatial resolution to use for returned DEM (grid cell size)
    layer : str
      title of layer to retrieve (e.g., 'NLCD_2001_Land_Cover_L48')
    inSR : int
      spatial reference for bounding box, such as an EPSG code (e.g., 4326)
    nlcd : bool
      if True, will re-map the values returned to the NLCD land cover codes

    Returns
    -------
    img : numpy array
      map image as array
    """
    width = int(abs(bbox[2] - bbox[0]) // res)
    height = int(abs(bbox[3] - bbox[1]) // res)
    BASE_URL = ''.join([
        'https://www.mrlc.gov/geoserver/mrlc_display/wms?',
        'service=WMS&request=GetMap',
    ])

    params = dict(bbox=','.join([str(x) for x in bbox]),
                  crs=f'epsg:{inSR}',
                  width=width,
                  height=height,
                  format='image/tiff',
                  layers=layer)
    for key, value in kwargs.items():
        params.update({key: value})

    r = requests.get(BASE_URL, params=params)
    img = imread(io.BytesIO(r.content), format='tiff')

    if nlcd:
        MAPPING = {
            1: 11,  # open water
            2: 12,  # perennial ice/snow
            3: 21,  # developed, open space
            4: 22,  # developed, low intensity
            5: 23,  # developed, medium intensity
            6: 24,  # developed, high intensity
            7: 31,  # barren land (rock/stand/clay)
            8: 32,  # unconsolidated shore
            9: 41,  # deciduous forest
            10: 42,  # evergreen forest
            11: 43,  # mixed forest
            12: 51,  # dwarf scrub (AK only)
            13: 52,  # shrub/scrub
            14: 71,  # grasslands/herbaceous,
            15: 72,  # sedge/herbaceous (AK only)
            16: 73,  # lichens (AK only)
            17: 74,  # moss (AK only)
            18: 81,  # pasture/hay
            19: 82,  # cultivated crops
            20: 90,  # woody wetlands
            21: 95,  # emergent herbaceous wetlands
        }

        k = np.array(list(MAPPING.keys()))
        v = np.array(list(MAPPING.values()))

        mapping_ar = np.zeros(k.max() + 1, dtype=v.dtype)
        mapping_ar[k] = v
        img = mapping_ar[img]

    return img
