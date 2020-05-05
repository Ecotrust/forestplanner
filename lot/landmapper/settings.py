SOIL_WMS_URL = 'https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms'

SOIL_WMS_VERSION = '1.1.1'

SOIL_WFS_URL = 'https://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs'

SOIL_WFS_VERSION = '1.1.0'

SOIL_TILE_LAYER = 'mapunitpoly'

SOIL_DATA_LAYER = 'mapunitpolyextended'


SOIL_ID_FIELD = 'musym'

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
