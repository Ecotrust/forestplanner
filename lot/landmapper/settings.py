import os
from datetime import date

TODAY_DATE = date.today().strftime("%D")

LANDMAPPER_DIR = os.path.dirname(os.path.abspath(__file__))

###########################################
##      Keys                            ###
###########################################
MAPBOX_TOKEN = 'set_in_landmapper_local_settings'

###########################################
##      Basemaps                        ###
###########################################
BASEMAPS = {
    'USGS_Aerial': {
        'url': 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export',
        'layers': '0',
        'technology': 'arcgis_mapserver',
        'attribution': 'USGS The National Map: Orthoimagery. Data refreshed April, 2019.'
    },
    'ESRI_Satellite': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export',
        'layers': '0',
        'technology': 'arcgis_mapserver',
        'attribution': 'Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'
    },
    'ESRI_Topo': {
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/export',
        'layers': '0',
        'technology': 'arcgis_mapserver',
        'attribution': 'Sources: Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), (c) OpenStreetMap contributors, and the GIS User Community'
    },
}
AERIAL_DEFAULT = 'ESRI_Satellite'
TOPO_DEFAULT = 'ESRI_Topo'

###########################################
##      REPORTS                         ###
###########################################
# Based on map size on slide 4 in the XD Specs
# This assumes the 'landscape' report layout (image will feel like 'portrait')
REPORT_MAP_WIDTH = 509
REPORT_MAP_HEIGHT = 722

REPORT_CONTENT_WIDTH = 508
REPORT_CONTENT_HEIGHT = REPORT_MAP_HEIGHT

REPORT_SUPPORT_ORIENTATION = False

REPORT_MAP_MIN_BUFFER = 0.1

###########################################
##      Soils                           ###
###########################################
# WMS (raster image tile)
SOIL_WMS_URL = 'https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms'
SOIL_WMS_VERSION = '1.1.1'
SOIL_TILE_LAYER = 'mapunitpoly'
SOIL_ZOOM_OVERLAY_2X = True

# WFS (soil data)
SOIL_WFS_URL = 'https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs'
SOIL_WFS_VERSION = '1.1.0'
SOIL_DATA_LAYER = 'mapunitpolyextended'
SOIL_ID_FIELD = 'musym'

# https://sdmdataaccess.sc.egov.usda.gov/Citation.htm
SOIL_SSURGO_ATTRIBUTION = ''.join([
    "Soil Survey Staff, Natural Resources Conservation Service, ",
    "United States Department of Agriculture. ",
    "Soil Survey Geographic (SSURGO) Database. ",
    "Available online at https://sdmdataaccess.sc.egov.usda.gov. ",
    "Accessed %s" % TODAY_DATE
])
SOIL_STATSGO_ATTRIBUTION = ''.join([
    "Soil Survey Staff, Natural Resources Conservation Service, ",
    "United States Department of Agriculture. ",
    "U.S. General Soil Map (STATSGO2). ",
    "Available online at https://sdmdataaccess.sc.egov.usda.gov. ",
    "Accessed %s" % TODAY_DATE
])

# Reference: https://sdmdataaccess.nrcs.usda.gov/documents/TablesAndColumnsReport.pdf
SOIL_FIELDS = {
    'areasymbol': {
        'name': 'Area Symbol',
        'display': False,
        'format': 'string',
        'UOM': ''
    },
    'musym': {
        'name': 'Map Unit Symbol',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'nationalmusym': {
        'name': 'National Map Unit Symbol',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'mukey': {
        'name': 'Map Unit Key',
        'display': False,
        'format': 'integer',
        'UOM': ''
    },
    'spatialversion': {
        'name': 'Spatial Version',
        'display': False,
        'format': 'integer',
        'UOM': ''
    },
    'muname': {
        'name': 'Map Unit Name',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'mustatus': {
        'name': 'Map Unit Status',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'slopegraddcp': {
        'name': 'Slope Gradient - Dominant Component',
        'display': True,
        'format': 'float',
        'UOM': '%'
    },
    'slopegradwta': {
        'name': 'Slope Gradient - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': '%'
    },
    'brockdepmin': {
        'name': 'Bedrock Depth - Minimum',
        'display': True,
        'format': 'integer',
        'UOM': 'cm'
    },
    'wtdepannmin': {
        'name': 'Water Table Depth - Annual - Minimum',
        'display': True,
        'format': 'integer',
        'UOM': 'cm'
    },
    'wtdepaprjunmin': {
        'name': 'Water Table Depth - April - June - Minimum',
        'display': True,
        'format': 'integer',
        'UOM': 'cm'
    },
    'flodfreqdcd': {
        'name': 'Flooding Frequency - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'flodfreqmax': {
        'name': 'Flooding Frequency - Maximum',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'pondfreqprs': {
        'name': 'pondfrePonding Frequency - Presenceqprs',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'aws025wta': {
        'name': 'Available Water Storage 0-25 cm - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': 'cm'
    },
    'aws050wta': {
        'name': 'Available Water Storage 0-50 cm - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': 'cm'
    },
    'aws0100wta': {
        'name': 'Available Water Storage 0-100 cm - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': 'cm'
    },
    'aws0150wta': {
        'name': 'Available Water Storage 0-150 cm - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': 'cm'
    },
    'drclassdcd': {
        'name': 'Drainage Class - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'drclasswettest': {
        'name': 'Drainage Class - Wettest',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'hydgrpdcd': {
        'name': 'Hydrologic Group - Dominant Conditions',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'iccdcd': {
        'name': 'Irrigated Capability Class - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'iccdcdpct': {
        'name': 'Irrigated Capability Class - Dominant Condition Aggregate Percent',
        'display': True,
        'format': 'integer',
        'UOM': '%'      # not listed in docs
    },
    'niccdcd': {
        'name': 'Non-Irrigated Capability Class - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'niccdcdpct': {
        'name': 'Non-Irrigated Capability Class - Dominant Condition Aggregate Percent',
        'display': True,
        'format': 'integer',
        'UOM': '%'      # not listed in docs
    },
    'engdwobdcd': {
        'name': 'ENG - Dwellings W/O Basements - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engdwbdcd': {
        'name': 'ENG - Dwellings with Basements - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engdwbll': {
        'name': 'ENG - Dwellings with Basements - Least Limiting',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engdwbml': {
        'name': 'ENG - Dwellings with Basements - Most Limiting',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engstafdcd': {
        'name': 'ENG - Septic Tank Absorption Fields - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engstafll': {
        'name': 'ENG - Septic Tank Absorption Fields - Least Limiting',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engstafml': {
        'name': 'ENG - Septic Tank Absorption Fields - Most Limiting',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engsldcd': {
        'name': 'ENG - Sewage Lagoons - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engsldcp': {
        'name': 'ENG - Sewage Lagoons - Dominant Component',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'englrsdcd': {
        'name': 'ENG - Local Roads and Streets - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engcmssdcd': {
        'name': 'ENG - Construction Materials; Sand Source - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'engcmssmp': {
        'name': 'ENG - Construction Materials; Sand Source - Most Probable',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'urbrecptdcd': {
        'name': 'URB/REC - Paths and Trails - Dominant Condition',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'urbrecptwta': {
        'name': 'URB/REC - Paths and Trails - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': ''
    },
    'forpehrtdcp': {
        'name': 'FOR - Potential Erosion Hazard (Road/Trail) - Dominant Component',
        'display': True,
        'format': 'string',
        'UOM': ''
    },
    'hydclprs': {
        'name': 'Hydric Classification - Presence',
        'display': True,
        'format': 'integer',
        'UOM': ''
    },
    'awmmfpwwta': {
        'name': 'AWM - Manure and Food Processing Waste - Weighted Average',
        'display': True,
        'format': 'float',
        'UOM': ''
    }
}

###########################################
##      Streams                         ###
###########################################
STREAMS_URLS = {
    'AGOL': {
        'URL': [
            'https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Detailed_Streams/FeatureServer/0/query?'
        ],
        'PARAMS': {},
        'QS':[
            'f=geojson',
            'returnGeometry=true',
            'spatialRel=esriSpatialRelIntersects',
            # 'maxAllowableOffset=76.43702828515632',
            'geometryType=esriGeometryEnvelope',
            'inSR=102100',
            'outFields=*',
            'returnCentroid=false',
            'returnExceededLimitFeatures=false',
            'maxRecordCountFactor=3',
            'outSR=102100',
            'resultType=tile',
        ]
    },
    'MAPBOX_STATIC': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/{layerid}/static/{lon},{lat},{zoom}/{width}x{height}?',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'ckbv10von10qw1iqs1cgdccw7',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN
        ]
    }
}



###########################################
##      Map Info                        ###
###########################################
ATTRIBUTION_KEYS = {
    'aerial': BASEMAPS[AERIAL_DEFAULT]['attribution'],
    'topo': 'Set topo attr in settings',
    'streets': 'Set street attr in settings',
    'streams': 'Set streams attr in settings',
    'taxlot': 'Set taxlot attr in settings',
    'soil': SOIL_SSURGO_ATTRIBUTION
}

###########################################
##      Tests                           ###
###########################################
TESTING_DIR = os.path.join(LANDMAPPER_DIR, 'testing_files')
IMAGE_TEST_DIR = os.path.join(TESTING_DIR, 'image_test')


try:
    from .local_settings import *
except Exception as e:
    pass
