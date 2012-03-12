# Django settings for lot project.
from madrona.common.default_settings import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_ZONE = 'America/Vancouver'
ROOT_URLCONF = 'lot.urls'

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
#GEOMETRY_CLIENT_SRID = 3857 #for mercator
GEOMETRY_CLIENT_SRID = 4326 #for latlon

APP_NAME = "Forestry Land Owner Tools"

TEMPLATE_DIRS = ( os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/')), )

FEATURE_FILE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'feature_files'))
GIS_DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))

from settings_local import *
