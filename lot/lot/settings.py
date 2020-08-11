# Django settings for lot project.

from madrona.common.default_settings import *
import os

# # On the advice of inlanger: https://stackoverflow.com/a/34115677 to resolve pre/post Django 1.9 issues.
# import django
# django.setup()

APP_NAME = "ForestPlanner"
ADMINS = (('Ecotrust', 'forestplanner@ecotrust.org'))
TIME_ZONE = 'America/Vancouver'
ROOT_URLCONF = 'lot.urls'
ENFORCE_SUPPORTED_BROWSER = False
POSTGIS_TEMPLATE = 'template1'
STARSPAN_REMOVE_TMP = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG
BING_API_KEY = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70"
INSTALLED_APPS += (
    'discovery.apps.DiscoveryConfig',
    'landmapper.apps.LandmapperConfig',
    'trees',
    'madrona.raster_stats',
    'django.contrib.messages',
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
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
FIXTURE_DIRS = (os.path.join(BASE_DIR, 'fixtures'),)
TEMPLATE_DIRS = (os.path.realpath(os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/')), )
FEATURE_FILE_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'feature_files'))
GIS_DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# ------------------------------------------------------------------------------
# Media
# ------------------------------------------------------------------------------
# COMPRESS_CSS['application']['source_filenames'] = (
#     'common/trees.css',
# )
# COMPRESS_JS['application']['source_filenames'] = (
#     'common/styles.js',
#     'common/trees.js',
#     'common/property.js',
#     'common/stand.js',
#     'common/scenario.js'
# )
try:
    STATICFILES_DIRS += [
        "%s%s" % (os.path.join(ROOT_DIR, 'media'), os.sep),
        str(STATIC_ROOT),   # This comes from madrona's default_settings
    ]
except Exception as e:
    STATICFILES_DIRS = [
        "%s%s" % (os.path.join(ROOT_DIR, 'media'), os.sep),
    ]

STATICFILES_DIRS += [
    "%s%s" % (os.path.join(ROOT_DIR, 'lot', 'lot', 'static'), os.sep),
    # "%s%s" % (os.path.join(ROOT_DIR, 'lot', 'trees', 'static'), os.sep),
]

MEDIA_ROOT = "%s%s" % (os.path.join(ROOT_DIR, 'lot', 'media'), os.sep)
STATIC_ROOT = "%s%s" % (os.path.join(ROOT_DIR, 'static'), os.sep)
MEDIA_URL = '/media/'
STATIC_URL = '/static/'


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
# SESSION_ENGINE = 'redis_sessions.session'
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# ------------------------------------------------------------------------------
# Celery
# Newer versions of Celery (4.0+) do not use Kombu or transport
# These settings are being re-written in accordance with:
# https://simpleisbetterthancomplex.com/tutorial/2017/08/20/how-to-use-celery-with-django.html
# ------------------------------------------------------------------------------
BROKER_URL = 'redis://localhost:6379/0'
# CELERY_BROKER_URL = 'amqp://localhost'
CELERY_BROKER_URL = 'redis://localhost:6379'
# BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}  # 12 hours
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ALWAYS_EAGER = False
CELERY_DISABLE_RATE_LIMITS = True
# from datetime import timedelta
# CELERYBEAT_SCHEDULE = {
#     'sweep_for_errors': {
#         'task': 'sweep_for_errors',
#         'schedule': timedelta(seconds=600),
#         'args': None
#     },
# }
CELERY_TIMEZONE = 'UTC'
# import djcelery
# djcelery.setup_loader()

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

INSTALLED_APPS += (
    'celery',
)

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
# Data Constants
# ------------------------------------------------------------------------------

VARIANT_BASELINES = {
    "Pacific Northwest Coast": 38.6, # units = metric tons of carbon per acre (not CO2)
    "South Central Oregon": 13.2,
    "Eastside Cascades": 13.2,
    "Inland California and Southern Cascades": 23.6,
    "Westside Cascades": 32.1,
    "Blue Mountains": 10.4
}

# ------------------------------------------------------------------------------
# New required settings from upgrades to DJANGO 2 and Python 3
# ------------------------------------------------------------------------------
SITE_ID=1

MIDDLEWARE_CLASSES += (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lot.wsgi.application'

try:
    MIDDLEWARE += MIDDLEWARE_CLASSES
except NameError as e:
    MIDDLEWARE = MIDDLEWARE_CLASSES

# ------------------------------------------------------------------------------
# Py3/Dj2 Overhaul Workarounds
# ------------------------------------------------------------------------------

# In 2015 we made better NN matching, but required DB migration and an extra script (load_new_conditions.py) to be run.
# To migrate our new code to the servers, which never got this update, we need
# to work around this code.
USE_FIA_NN_MATCHING = True


# ------------------------------------------------------------------------------
# Discovery settings
# ------------------------------------------------------------------------------
INSTALLED_APPS += (
    'django.contrib.flatpages',
    'ckeditor',
)

try:
    from discovery.settings import *
except ImportError as e:
    print("Failure to find settings file for Discovery.")
    pass


# LandMapper settings
INSTALLED_APPS += (
    'django.contrib.humanize',
)

try:
    from landmapper.settings import *
except ImportError as e:
    print('Failure to find settings file for LandMapper.')
    pass
# ------------------------------------------------------------------------------
# Local settings
# ------------------------------------------------------------------------------
try:
    from .local_settings import *
except ImportError:
    print(
        "we recommend using a local settings file; "\
        "`cp local_settings.template local_settings.py` and modify as needed"
    )
    pass

if DEBUG:
    INSTALLED_APPS += (
        # 'django_pdb',
        'django_extensions',
    )
    # MIDDLEWARE_CLASSES += ('django_pdb.middleware.PdbMiddleware',)
