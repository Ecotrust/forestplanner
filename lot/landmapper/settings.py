import os
from datetime import date

TODAY_DATE = date.today().strftime("%D")

LANDMAPPER_DIR = os.path.dirname(os.path.abspath(__file__))

###########################################
##      Keys                            ###
###########################################
MAPBOX_TOKEN = 'set_in_landmapper_local_settings'

###########################################
##      Map Scales                      ###
###########################################
# Closest: 'fit' -- fits the property as close as possible
# Moderate: 'medium' -- approximately zoom level 12 unless the property is too big
# Regional Context: 'context' -- appx zoom 14 unless the property is larger
PROPERTY_OVERVIEW_SCALE = 'fit'
STREET_SCALE = 'context'
TOPO_SCALE = 'medium'
CONTOUR_SCALE = TOPO_SCALE
AERIAL_SCALE = PROPERTY_OVERVIEW_SCALE
TAXLOTS_SCALE = AERIAL_SCALE
SOIL_SCALE = AERIAL_SCALE
FOREST_TYPES_SCALE = AERIAL_SCALE
STREAM_SCALE = AERIAL_SCALE
STUDY_REGION = {
    'north': 46.292035,
    'south': 41.991794,
    'east': -116.463504,
    'west': -124.566244,
    'context': [
        ', OR',
        ', Oregon USA',
        # ', WA',
    ]
}


###########################################
##      Basemaps                        ###
###########################################
BASEMAPS = {
    'USGS_Aerial': {
        'URL': 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export',
        'LAYERS': '0',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': {'source': 'USGS', 'attribution': 'USGS The National Map: Orthoimagery. Data refreshed October, 2020.'}
        # Can get updated attribution at https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer?f=pjson ['copyrightText']
    },
    'ESRI_Satellite': {
        'URL': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export',
        'LAYERS': '0',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': {'source': 'ESRI', 'attribution': 'Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'}
    },
    'ESRI_Topo': {
        'URL': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/export',
        'LAYERS': '0',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': {'source': 'ESRI', 'attribution': 'Sources: Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), (c) OpenStreetMap contributors, and the GIS User Community'}
    },
    'ESRI_Street': {
        'URL': 'https://server.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/export',
        'LAYERS': '0',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': 'Sources: Esri, HERE, Garmin, USGS, Intermap, INCREMENT P, NRCan, Esri Japan, METI, Esri China (Hong Kong), Esri Korea, Esri (Thailand), NGCC, (c) OpenStreetMap contributors, and the GIS User Community'
    },
    'ESRI_NatGeo': {
        'URL': 'https://server.arcgisonline.com/arcgis/rest/services/NatGeo_World_Map/MapServer/export',
        'LAYERS': '0',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC'
    },
    'TNM_Aerial': {
        'URL': 'https://services.nationalmap.gov/arcgis/rest/services/USGSNAIPPlus/MapServer/export',
        'LAYERS': '8',
        'TECHNOLOGY': 'arcgis_mapserver',
        'ATTRIBUTION': 'USGS The National Map: Orthoimagery'
    },
    'TNM_NAIP': {
        'URL': 'https://services.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage',
        'TECHNOLOGY': 'arcgis_imageserver',
        'ATTRIBUTION': {'source': 'USGS', 'attribution': 'USGS The National Map: Imagery'}
    },
    'Custom_Topo': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/cke0j10sj1gta19o9agb1w8pq/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'TECHNOLOGY': 'mapbox',
        'ATTRIBUTION': 'Sources: MapBox',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'cke0j10sj1gta19o9agb1w8pq',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512,
        'ZOOM_2X': False
    },
    'OSM': {
        # 'URL': 'https://tile.openstreetmap.org/{zoom}/{lon}/{lat}.png',
        'URL': 'https://maps.geoapify.com/v1/staticmap',
        'TECHNOLOGY': 'static',
        # 'ATTRIBUTION': 'Sources: MapBox',
        'ATTRIBUTION': 'Powered by <a href="https://www.geoapify.com/">Geoapify</a>; © OpenStreetMap contributors',
        'PARAMS': {},
        'QS': [
            # 'style=osm-bright-smooth',
            'style=osm-carto',
            'width={width}',
            'height={height}',
            'center=lonlat%3A{lon}%2C{lat}',
            'zoom={zoom}', # float
            'apiKey={apiKey}',
            ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 256,
        'TILE_IMAGE_WIDTH': 256,
        'ZOOM_2X': False
    },
    'OSM_Mapnik': {
        'URL': 'https://a.tile.openstreetmap.org/{zoom}/{lon}/{lat}.png',
        'TECHNOLOGY': 'XYZ',
        'ATTRIBUTION': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        'PARAMS': {
        },
        'QS': [
            # 'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 256,
        'TILE_IMAGE_WIDTH': 256,
        'ZOOM_2X': True
    },
    # https://tiles.wmflabs.org/hikebike/{z}/{x}/{y}.png
    'Hike_Bike': {
        'URL': 'https://tiles.wmflabs.org/hikebike/{zoom}/{lon}/{lat}.png',
        'TECHNOLOGY': 'XYZ',
        'ATTRIBUTION': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        'PARAMS': {
        },
        'QS': [
            # 'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 256,
        'TILE_IMAGE_WIDTH': 256,
        'ZOOM_2X': False
    },
    'USGS_TopoImage': {
        'URL': 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{zoom}/{lat}/{lon}',
        'TECHNOLOGY': 'XYZ',
        'ATTRIBUTION': 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>',
        'PARAMS': {
        },
        'QS': [
            # 'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 256,
        'TILE_IMAGE_WIDTH': 256,
        'ZOOM_2X': False
    },
    'MAPBOX_Outdoor': {
        'URL': 'https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'TECHNOLOGY': 'mapbox',
        'ATTRIBUTION': 'Sources: MapBox',
        'PARAMS': {
            # 'userid':'',
            # 'layerid': '',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512,
        'ZOOM_2X': False
    },
    'MAPBOX_Streets': {
        'URL': 'https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'TECHNOLOGY': 'mapbox',
        'ATTRIBUTION': {'source': 'MapBox', 'attribution': None},
        'PARAMS': {
            # 'userid':'',
            # 'layerid': '',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512,
        'ZOOM_2X': False
    },
    'ESRI_NAIP': {
        'URL': 'https://naip.maptiles.arcgis.com/arcgis/rest/services/NAIP/MapServer/tile/{zoom}/{lat}/{lon}',
        'TECHNOLOGY': 'XYZ',
        'ATTRIBUTION': 'Tiles courtesy of ESRI>',
        'PARAMS': {
        },
        'QS': [
            # 'access_token=%s' % MAPBOX_TOKEN,
        ],
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 256,
        'TILE_IMAGE_WIDTH': 256,
        'ZOOM_2X': False
    },

}

AERIAL_DEFAULT = 'ESRI_Satellite'
AERIAL_UPDATED = 'ESRI_Satellite'
TOPO_DEFAULT = 'ESRI_Topo'
STREET_DEFAULT = 'MAPBOX_Streets'
# STREET_DEFAULT = 'ESRI_Street'

###########################################
##      REPORTS                         ###
###########################################
SHOW_AERIAL_REPORT = True
SHOW_STREET_REPORT = True
SHOW_TERRAIN_REPORT = True
SHOW_STREAMS_REPORT = True
SHOW_SOILS_REPORT = True
SHOW_FOREST_TYPES_REPORT = True

# Based on map size on slide 4 in the XD Specs
# This assumes the 'landscape' report layout (image will feel like 'portrait')
# REPORT_MAP_WIDTH = 509
REPORT_MAP_WIDTH = 768
# REPORT_MAP_HEIGHT = 722
REPORT_MAP_HEIGHT = 816

REPORT_MAP_ALT_WIDTH = 509
REPORT_MAP_ALT_HEIGHT = 722

# What is this used for?
REPORT_CONTENT_WIDTH = 508
# REPORT_CONTENT_WIDTH = 616
REPORT_CONTENT_HEIGHT = REPORT_MAP_HEIGHT

REPORT_SUPPORT_ORIENTATION = False

REPORT_MAP_MIN_BUFFER = 0.1

# These values approximate zoom 12 & 14 at the Oregon/California border.
# MAX_METER_RESOLUTION_CONTEXT = 30.0  # ~15,000m/509px (current pixel width)
# MAX_METER_RESOLUTION_MEDIUM = 7.5   # 30/4 (or more illustratively: 30/2/2)

# MAX width resolution in 3857 degrees:
# MAX_WEB_MERCATOR_RESOLUTION_CONTEXT = 40  # ~20,000 degrees/509px (current pixel width)
MAX_WEB_MERCATOR_RESOLUTION_CONTEXT = 26  # ~20,000 degrees/768px (current pixel width)
# MAX_WEB_MERCATOR_RESOLUTION_MEDIUM = 10   # 40/4 (or more illustratively: 40/2/2)
MAX_WEB_MERCATOR_RESOLUTION_MEDIUM = 6.5   # 26/4 (or more illustratively: 26/2/2)

# Report Image Dots Per Inch
DPI = 300
PROPERTY_STYLE = {'lw':1, 'ec': '#FF00FF', 'fc': 'none'}
TAXLOT_STYLE = {'lw':0.2, 'ec': '#CCCCCC', 'fc': 'none'}
SOIL_STYLE = {
    'lw':0.8,
    'ec': '#EBAE33',
    'fc': 'none',
    'label': {
        'fontsize': 3,
        'halo': {
            'size': 1,
            'color': 'black'
        },
        'bbox': None,
        # 'bbox': {
        #     'facecolor': '#000000',
        #     'alpha':0.4,
        #     'pad': 0.2,
        #     'edgecolor':'none'
        # }
    }
}
FOREST_TYPES_STYLE = {
    'lw':0.8,
    # 'ec': '#00FF44', # GREEN
    # 'ec': '#E11845', # Strawberry
    'ec': '#F2CA19', # Mustard
    # 'ec': '#0057E9', # Blue
    'fc': 'none',
    'label': {
        'fontsize': 3,
        'halo': {
            'size': 1,
            'color': 'black'
        },
        'bbox': None,
        # 'bbox': {
        #     'facecolor': '#000000',
        #     'alpha':0.4,
        #     'pad': 0.2,
        #     'edgecolor':'none'
        # }
    }
}
CONTOUR_STYLE = {
    'fine_color': (32/255., 96/255., 0., 255/255.),
    'fine_step': 40,
    'fine_width': 0.05,
    'bold_color': (32/255., 96/255., 0., 255/255.),
    'bold_step': 200,
    'bold_width': 0.25,
    'font_size': 2.5,
    'inline_spacing': -2,
    'format_string': "{x:.0f}"
}

SCALEBAR_DEFAULT_WIDTH = 1.5
SCALEBAR_DEFAULT_HEIGHT = 0.2
# SCALEBAR_BG_W = 508
SCALEBAR_BG_W = 616
# SCALEBAR_BG_H = 70
SCALEBAR_BG_H = 77

MAXIMUM_BBOX_WIDTH = 30000
NO_RENDER_MESSAGE = "Unable to render some details. Please create smaller properties."

###########################################
##      Properties                      ###
###########################################
# PROPERTY_OUTLINE_COLOR = (255,0,255,255)
PROPERTY_OUTLINE_COLOR = (1,0,1,1)  # matplotlib does not understand 0-255, only hex or 0-1.0 vals
PROPERTY_OUTLINE_WIDTH = 1


###########################################
##      Soils                           ###
###########################################
SOIL_BASE_LAYER = 'aerial'
# WMS (raster image tile)
# SOIL_WMS_URL = 'https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms'
# SOIL_WMS_VERSION = '1.1.1'
# SOIL_TILE_LAYER = 'mapunitpoly'
SOIL_ZOOM_OVERLAY_2X = False

SOILS_URLS = {
    'USDA_WMS': {
        'URL': 'https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms',
        'WMS_VERSION': '1.1.1',
        'TILE_LAYER': 'mapunitpoly',
        'ZOOM_OVERLAY_2X': SOIL_ZOOM_OVERLAY_2X,
        'ATTRIBUTION': ''.join([
            "Soil Survey Staff, Natural Resources Conservation Service, ",
            "United States Department of Agriculture. ",
            "Soil Survey Geographic (SSURGO) Database. ",
            "Available online at https://sdmdataaccess.sc.egov.usda.gov. ",
            "Accessed %s" % TODAY_DATE
        ])
    },
    'USDA_WFS': {
        'URL': 'https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs',
        'WFS_VERSION': '1.1.0',
        'DATA_LAYER': 'mapunitpolyextended',
        'ID_FIELD': 'musym',
        'ATTRIBUTION': ''.join([        # RDH 2020-10-20: I am not sure this is the correct acctibution for this service.
            "Soil Survey Staff, Natural Resources Conservation Service, ",
            "United States Department of Agriculture. ",
            "U.S. General Soil Map (STATSGO2). ",
            "Available online at https://sdmdataaccess.sc.egov.usda.gov. ",
            "Accessed %s" % TODAY_DATE,
        ])
    },
    'MAPBOX': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/{layerid}/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'ckg85xmw7084119mpbf5a69sf',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        # 'ATTRIBUTION': 'Soil Survey Staff. The Gridded Soil Survey Geographic (gSSURGO) Database for Oregon. United States Department of Agriculture, Natural Resources Conservation Service. Available online at https://gdg.sc.egov.usda.gov/. October 12, 2020 (202007 official release).',
        'ATTRIBUTION': {'source': 'NRCS', 'attribution': 'Soil Survey Staff. The Gridded Soil Survey Geographic (gSSURGO) Database for Oregon. United States Department of Agriculture, Natural Resources Conservation Service. Available online at https://gdg.sc.egov.usda.gov/. October 12, 2020 (202007 official release).'},
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512
    }

}

# WFS (soil data)
# SOIL_WFS_URL = 'https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs'
# SOIL_WFS_VERSION = '1.1.0'
# SOIL_DATA_LAYER = 'mapunitpolyextended'
# SOIL_ID_FIELD = 'musym'

# https://sdmdataaccess.sc.egov.usda.gov/Citation.htm
SOIL_SSURGO_ATTRIBUTION = SOILS_URLS['USDA_WMS']['ATTRIBUTION']

SOIL_SOURCE = 'MAPBOX'

SOIL_ATTRIBUTION = SOILS_URLS[SOIL_SOURCE]['ATTRIBUTION']

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
STREAMS_BASE_LAYER = 'topo'
# STREAMS_BASE_LAYER = 'aerial'
# STREAMS_BASE_LAYER = 'ESRI_Topo'
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
        ],
        'ATTRIBUTION': 'National Hydrography Dataset: USGS, Esri'
    },
    'MAPBOX_STATIC': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/{layerid}/static/{lon},{lat},{zoom}/{width}x{height}{retina}?',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'ckbv10von10qw1iqs1cgdccw7',
            'lon': '',
            'lat': '',
            'zoom': '',
            'width': '',
            'height': '',
            'retina': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
            'attribution=false',
            'logo=false'
        ],
        'ATTRIBUTION': 'Oregon Department of Forestry'
    },
    'MAPBOX_TILE': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/{layerid}/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'ckbv10von10qw1iqs1cgdccw7',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        'ATTRIBUTION': {'source': 'ODF', 'attribution':'Oregon Department of Forestry'},
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512
    }
}
STREAMS_SOURCE = 'MAPBOX_TILE'
STREAM_ZOOM_OVERLAY_2X = False
STREAMS_ATTRIBUTION = STREAMS_URLS[STREAMS_SOURCE]['ATTRIBUTION']

###########################################
##      Taxlots                         ###
###########################################
TAXLOTS_URLS = {
    'MAPBOX_TILE': {
        'URL': 'https://api.mapbox.com/styles/v1/{userid}/{layerid}/tiles/256/{zoom}/{lon}/{lat}@2x?',
        'PARAMS': {
            'userid':'forestplanner',
            'layerid': 'ckdgho51i084u1inx1a70iwim',
            'lon': '',
            'lat': '',
            'zoom': '',
        },
        'QS': [
            'access_token=%s' % MAPBOX_TOKEN,
        ],
        'ATTRIBUTION': {'source': 'ORMAP', 'attribution': None},
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512
    }
}
TAXLOTS_SOURCE = 'MAPBOX_TILE'
TAXLOT_ZOOM_OVERLAY_2X = False
TAXLOTS_ATTRIBUTION = TAXLOTS_URLS[TAXLOTS_SOURCE]['ATTRIBUTION']


###########################################
##      Topo Conours                    ###
###########################################

CONTOUR_URLS = {
    'TNM_TOPO': {
        'URL': 'https://carto.nationalmap.gov/arcgis/rest/services/contours/MapServer/export',
        'LAYERS': '21,25,26',
        'TECHNOLOGY': 'arcgis_mapserver',
        'SRID': 3857,
        'ATTRIBUTION': 'USGS The National Map: 3D Elevation Program. Data Refreshed October, 2020.',
        'INDEX_CONTOUR_SYMBOL': {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": [32,96,0,255],
            "width": 1.5
        },
        'INTERMEDIATE_CONTOUR_SYMBOL': {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": [32,96,0,255],
            "width": 0.5
        },
        'LABEL_SYMBOL': {
            "type":"esriTS",
            "color":[15,39,3,255],
            "backgroundColor":None,
            "outlineColor":None,
            "verticalAlignment":"baseline",
            "horizontalAlignment":"left",
            "rightToLeft":False,
            "angle":0,
            "xoffset":0,
            "yoffset":0,
            "kerning":True,
            "haloSize":2,
            "haloColor":[255,255,255,255],
            "font":{
                "family":"Arial",
                "size":12,
                "style":"italic",
                "weight":"normal",
                "decoration":"none"
            }
        },
        'STYLES': []
    }
}

# CONTOUR_SOURCE = 'TNM_TOPO'
CONTOUR_SOURCE = False

if CONTOUR_SOURCE:
    CONTOUR_ATTRIBUTION = CONTOUR_URLS[CONTOUR_SOURCE]['ATTRIBUTION']
    CONTOUR_URLS[CONTOUR_SOURCE]['STYLES'] = [
        {
            "id":25,
            "source":{"type":"mapLayer", "mapLayerId":25},
            "drawingInfo":{
                "renderer":{
                    "type":"simple",
                    "symbol":CONTOUR_URLS[CONTOUR_SOURCE]['INDEX_CONTOUR_SYMBOL'],
                },
            },
        },
        {
            "id":26,
            "source":{"type":"mapLayer", "mapLayerId":26},
            "drawingInfo":{
                "renderer":{
                    "type":"simple",
                    "symbol":CONTOUR_URLS[CONTOUR_SOURCE]['INTERMEDIATE_CONTOUR_SYMBOL'],
                },
            },
        },
        {
            "id":21,
            "source":{"type":"mapLayer", "mapLayerId":21},
            "drawingInfo":{
                "renderer":{
                    "type":"uniqueValue",
                    "field1":"FCODE",
                    "fieldDelimiter":",",
                },
                "labelingInfo":[
                    {
                        "labelPlacement":"esriServerLinePlacementCenterAlong",
                        "labelExpression":"[CONTOURELEVATION]",
                        "useCodedValues":True,
                        "symbol":CONTOUR_URLS[CONTOUR_SOURCE]['LABEL_SYMBOL'],
                        "minScale":0,
                        "maxScale":0
                    }
                ]
            }
        }
    ]
else:
    CONTOUR_ATTRIBUTION = {'source': 'USGS', 'attribution': CONTOUR_URLS['TNM_TOPO']['ATTRIBUTION']}

###########################################
##      Forest Types                    ###
###########################################
FOREST_TYPES_URLS = {
    'LOCAL': {
        'URL': None,
        'PARAMS': {},
        'QS': [],
        'ATTRIBUTION': {'source': 'Ecotrust', 'attribution': 'Ecotrust 2021'},
        # calculate tile assuming 256 px
        'TILE_HEIGHT': 256,
        'TILE_WIDTH': 256,
        # retrieve image at 2x resolution
        'TILE_IMAGE_HEIGHT': 512,
        'TILE_IMAGE_WIDTH': 512
    }
}

FOREST_TYPES_SOURCE = 'LOCAL'

FOREST_TYPES_ATTRIBUTION = FOREST_TYPES_URLS[FOREST_TYPES_SOURCE]['ATTRIBUTION']

###########################################
##      Map Info                        ###
###########################################
ATTRIBUTION_KEYS = {
    'aerial': BASEMAPS[AERIAL_DEFAULT]['ATTRIBUTION'],
    'topo': BASEMAPS[TOPO_DEFAULT]['ATTRIBUTION'],
    'streets': BASEMAPS[STREET_DEFAULT]['ATTRIBUTION'],
    'streams': STREAMS_ATTRIBUTION,
    'taxlot': TAXLOTS_ATTRIBUTION,
    'soil': SOIL_ATTRIBUTION,
    'foresttypes': FOREST_TYPES_ATTRIBUTION,
    'contours': CONTOUR_ATTRIBUTION
}

ATTRIBUTION_BOX_FILL_COLOR = (255, 255, 255, 190)
ATTRIBUTION_BOX_OUTLINE = None
ATTRIBUTION_TEXT_COLOR = "black"
# ATTRIBUTION_TEXT_FONT = 'Pillow/Tests/fonts/FreeMono.ttf'
# default UBUNTU Font
# ATTRIBUTION_TEXT_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
ATTRIBUTION_TEXT_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ATTRIBUTION_TEXT_FONT_SIZE = 10
ATTRIBUTION_TEXT_BUFFER = 3
ATTRIBUTION_TEXT_LINE_SPACING = 1

AERIAL_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/directions_aerial.png'
STREET_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/street_map_legend.png'
TERRAIN_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/topo.png'
STREAM_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/hydrology.png'
SOIL_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/soils.png'
FOREST_TYPE_MAP_LEGEND_URL = '/static/landmapper/img/legend_images/forest_types.png'

###########################################
##      Site URLs                       ###
###########################################
PRODUCTION_URL = 'http://landmapper.ecotrust.org/landmapper'
DEV_URL = 'http://localhost:8000/landmapper'

LIVE_SITE = False

if LIVE_SITE:
    APP_URL = PRODUCTION_URL
else:
    APP_URL = DEV_URL

###########################################
##      Report creation and PDF access  ###
###########################################
ALLOW_ANONYMOUS_DRAW = True
ANONYMOUS_USER_PK = 1

###########################################
##      Flatblock content               ###
###########################################
FLATBLOCK_IDS = [
    'aside-home',
    'aside-map-pin',
    'aside-name'
]

###########################################
##      Tests                           ###
###########################################
TESTING_DIR = os.path.join(LANDMAPPER_DIR, 'testing_files')
IMAGE_TEST_DIR = os.path.join(TESTING_DIR, 'image_test')

###########################################
##      PDF Files                       ###
###########################################
PROPERTY_REPORT_PDF_TEMPLATE = LANDMAPPER_DIR + '/pdf_templates/LM_Form.pdf'
PROPERTY_REPORT_PDF_TEMPLATE_SANS_FOREST_TYPES = LANDMAPPER_DIR + '/pdf_templates/LM_Form_sans_forests.pdf'
PROPERTY_REPORT_PDF_DIR = LANDMAPPER_DIR + '/static/landmapper/report_pdf/'
PDF_PAGE_LOOKUP = {
    'property_alt': 0,
    'property': 1,
    'aerial': 1,
    'street': 2,
    'terrain': 3,
    'stream': 4,
    'soil_types': [5,6,7,8],
    'forest_types': [9,10,11,12],
}

try:
    from .local_settings import *
except Exception as e:
    pass
