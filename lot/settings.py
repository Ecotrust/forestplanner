# Django settings for lot project.
from lingcod.common.default_settings import *

SECRET_KEY = 'v%d&go+gr6zk-)rlm78n1ah$f92b(wb@eus#43f!)((3^+0n95'

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

INSTALLED_APPS += ( 'trees', )

GEOMETRY_DB_SRID = 3857
GEOMETRY_CLIENT_SRID = 3857

APP_NAME = "Forestry Land Owner Tools"

TEMPLATE_DIRS = ( os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/')), )

from settings_local import *
