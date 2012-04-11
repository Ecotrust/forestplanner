# Django settings for lot project.
from madrona.common.default_settings import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'),)
TIME_ZONE = 'America/Vancouver'
ROOT_URLCONF = 'urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'murdock',
        'USER': 'postgres',
    }
}

COMPRESS_CSS['application']['source_filenames'] = (
    'common/trees.css',
)

COMPRESS_JS['application']['source_filenames'] = (
    'common/trees.js',
)

INSTALLED_APPS += ( 'trees', 'madrona.raster_stats')

GEOMETRY_DB_SRID = 3857
GEOMETRY_CLIENT_SRID = 3857 #for mercator

APP_NAME = "Forestry Land Owner Tools"

TEMPLATE_DIRS = ( 
        os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/')), 
)

FEATURE_FILE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'feature_files'))
GIS_DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))

DEFAULT_EXTENT = [-14056200,4963200,-12471500,6128400] # in mercator

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# List of tuples: raster name and proj4 string of the raster 
# proj4==None implies mercator
albers = '+proj=aea +lat_1=43 +lat_2=48 +lat_0=34 +lon_0=-120 +x_0=600000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs' 
IMPUTE_RASTERS = [
        ('elevation', albers), 
        ('cos_aspect', albers), 
        ('sin_aspect', albers), 
        ('slope', albers), 
        ('gnn', albers), 
]

POINT_BUFFER = 500  #meters

ENFORCE_SUPPORTED_BROWSER = False

from settings_local import *
