# Django settings for lot project.
from madrona.common.default_settings import *
import os

APP_NAME = "ForestPlanner"
ADMINS = (('Ecotrust', 'forestplanner@ecotrust.org'))
TIME_ZONE = 'America/Vancouver'
ROOT_URLCONF = 'urls'
ENFORCE_SUPPORTED_BROWSER = False
POSTGIS_TEMPLATE = 'template1'
STARSPAN_REMOVE_TMP = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG
BING_API_KEY = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70"
INSTALLED_APPS += (
    'trees',
    'madrona.raster_stats'
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'land_owner_tools',
        'USER': 'postgres',
    }
}

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'),)
TEMPLATE_DIRS = (os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/')), )
FEATURE_FILE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'feature_files'))
GIS_DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# ------------------------------------------------------------------------------
# Media
# ------------------------------------------------------------------------------
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
MEDIA_ROOT = '/usr/local/apps/land_owner_tools/mediaroot/'
MEDIA_URL = '/media/'
STATIC_URL = '/media/'

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
import logging
logging.getLogger('django.db.backends').setLevel(logging.INFO)
logging.getLogger('madrona.features.models').setLevel(logging.INFO)
logging.getLogger('madrona.common.utils').setLevel(logging.INFO)
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'trees.log')
COSTLOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs', 'cost_errors')

# ------------------------------------------------------------------------------
# Spatial data settings
# ------------------------------------------------------------------------------
GEOMETRY_DB_SRID = 3857
GEOMETRY_CLIENT_SRID = 3857  # for mercator
EQD_SRID = 3786  # World Equidistant Cylindrical (Sphere)
EQUAL_AREA_SRID = 26910  # NAD83 UTM Zone 10 N meters

# List of tuples: raster name and proj4 string of the raster
# proj4==None implies mercator
TERRAIN_PROJ = '+proj=aea +lat_1=43 +lat_2=48 +lat_0=34 +lon_0=-120 +x_0=600000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
DOWNLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "downloads"))
TERRAIN_DIR = os.path.join(DOWNLOAD_DIR, "terrain")
albers = TERRAIN_PROJ
IMPUTE_RASTERS = [
        ('elevation', TERRAIN_PROJ),
        ('cos_aspect', TERRAIN_PROJ),
        ('sin_aspect', TERRAIN_PROJ),
        ('aspect', TERRAIN_PROJ),
        ('slope', TERRAIN_PROJ),
        ('cost', TERRAIN_PROJ),
        ('gnn', TERRAIN_PROJ),
]
POINT_BUFFER = 2500  # meters
DEFAULT_EXTENT = [-14056200, 4963200, -12471500, 6128400]  # in mercator
EQUAL_AREA_ACRES_CONVERSION = 0.000247105381  # sq m to acres
SLIVER_THRESHOLD = 100.0  # square meters
MILL_SHAPEFILE = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                  'fixtures', 'mills', 'mills.shp'))

# ------------------------------------------------------------------------------
# Redis sessions and caching
# ------------------------------------------------------------------------------
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

# ------------------------------------------------------------------------------
# Celery
# ------------------------------------------------------------------------------
BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}  # 12 hours
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
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
import djcelery
djcelery.setup_loader()

# ------------------------------------------------------------------------------
# Allauth
# ------------------------------------------------------------------------------
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

# user logs in by entering either his username or e-mail address
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  

ACCOUNT_EMAIL_REQUIRED = True

# Go to intermediate signup page
SOCIALACCOUNT_AUTO_SIGNUP = False

# ------------------------------------------------------------------------------
# Email
# ------------------------------------------------------------------------------
EMAIL_HOST = 'mail.ecotrust.org'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'forestplanner@ecotrust.org'
DEFAULT_FROM_EMAIL = 'forestplanner@ecotrust.org'
SERVER_EMAIL = 'forestplanner@ecotrust.org'

# ------------------------------------------------------------------------------
# Local settings
# ------------------------------------------------------------------------------
try:
    from settings_local import *
except ImportError:
    print "we recommend using a local settings file; "\
    "`cp settings_local.template settings_local.py` and modify as needed"
    pass

if DEBUG:
    INSTALLED_APPS += ('django_pdb',)
    MIDDLEWARE_CLASSES += ('django_pdb.middleware.PdbMiddleware',)
