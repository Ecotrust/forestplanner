# Django settings for lot project.
from madrona.common.default_settings import *
import logging
import os

APP_NAME = "ForestPlanner"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'),)
TIME_ZONE = 'America/Vancouver'
ROOT_URLCONF = 'urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'land_owner_tools',
        'USER': 'postgres',
    }
}

COMPRESS_CSS['application']['source_filenames'] = (
    'common/trees.css',
)

COMPRESS_JS['application']['source_filenames'] = (
    'common/styles.js',
    'common/trees.js',
    'common/property.js',
    'common/stand.js',
    'common/scenario.js'
)

INSTALLED_APPS += ('trees', 'madrona.raster_stats')

GEOMETRY_DB_SRID = 3857
GEOMETRY_CLIENT_SRID = 3857  # for mercator
EQD_SRID = 3786  # World Equidistant Cylindrical (Sphere)

TEMPLATE_DIRS = (
        os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/')),
)

FEATURE_FILE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'feature_files'))
GIS_DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))

DEFAULT_EXTENT = [-14056200, 4963200, -12471500, 6128400]  # in mercator

# List of tuples: raster name and proj4 string of the raster
# proj4==None implies mercator
albers = '+proj=aea +lat_1=43 +lat_2=48 +lat_0=34 +lon_0=-120 +x_0=600000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
IMPUTE_RASTERS = [
        ('elevation', albers),
        ('cos_aspect', albers),
        ('sin_aspect', albers),
        ('aspect', albers),
        ('slope', albers),
        ('cost', albers),
        ('gnn', albers),
]

POINT_BUFFER = 500  # meters

ENFORCE_SUPPORTED_BROWSER = False

EQUAL_AREA_SRID = 26910  # NAD83 UTM Zone 10 N meters
EQUAL_AREA_ACRES_CONVERSION = 0.000247105381  # sq m to acres
SLIVER_THRESHOLD = 100.0  # square meters

BING_API_KEY = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70"

SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0
#SESSION_REDIS_PASSWORD = 'password'
#SESSION_REDIS_PREFIX = 'session'
#If you prefer domain socket connection, you can just add this line instead of SESSION_REDIS_HOST and SESSION_REDIS_PORT.
# SESSION_REDIS_UNIX_DOMAIN_SOCKET_PATH = '/var/run/redis/redis.sock'

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

MEDIA_ROOT = '/usr/local/apps/land_owner_tools/mediaroot/'
MEDIA_URL = 'http://localhost:8000/media/'
STATIC_URL = 'http://localhost:8000/media/'

POSTGIS_TEMPLATE = 'template1'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (('Ecotrust', 'ksdev@ecotrust.org'))

logging.getLogger('django.db.backends').setLevel(logging.INFO)
logging.getLogger('madrona.features.models').setLevel(logging.INFO)
logging.getLogger('madrona.common.utils').setLevel(logging.INFO)

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'trees.log')

BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}  # 12 hours
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # ? or use django ?
CELERY_ALWAYS_EAGER = False
CELERY_DISABLE_RATE_LIMITS = True
from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    'sweep_for_errors': {
        'task': 'sweep_for_errors',
        'schedule': timedelta(seconds=600),
        'args': None
    },
}
CELERY_TIMEZONE = 'UTC'
#CELERY_IGNORE_RESULT = True  # set on per-task basis

# see http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html

import djcelery
djcelery.setup_loader()

################# BEGIN Auth
TEMPLATE_CONTEXT_PROCESSORS += (
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
    "django.core.context_processors.request",
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

INSTALLED_APPS += (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.twitter',
    #'allauth.socialaccount.providers.github',
    #'allauth.socialaccount.providers.linkedin',
)

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # user logs in by entering either his username or e-mail address

# install postfix
EMAIL_HOST = 'localhost'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True
################# END Auth

try:
    from settings_local import *
except ImportError:
    pass

if DEBUG:
    INSTALLED_APPS += ('django_pdb',)
    MIDDLEWARE_CLASSES += ('django_pdb.middleware.PdbMiddleware',)
