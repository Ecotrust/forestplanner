MEDIA_ROOT = '/usr/local/media/murdock'
GOOGLE_API_KEY = 'ABQIAAAAIcPbR_l4h09mCMF_dnut8RQbjMqOReB17GfUbkEwiTsW0KzXeRQ-3JgvCcGix8CM65XAjBAn6I0bAQ'
MEDIA_URL = 'http://murdock.labs.ecotrust.org/media/'
STATIC_URL = MEDIA_URL
WSGI_USER = 'mperry'
DEBUG = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache/murdock',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'murdock',
        'USER': 'murdock',
        'PASSWORD': '@murdock!'
    }
}

import logging
logging.getLogger('django.db.backends').setLevel(logging.ERROR) 
LOG_LEVEL = logging.DEBUG
LOG_FILE='/usr/local/apps/murdock/murdock.log'
