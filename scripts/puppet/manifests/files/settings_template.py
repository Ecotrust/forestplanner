SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'forestplanner',
        'USER': '$user',
    }
}

# This should be a local folder created for use with the install_media command 
MEDIA_ROOT = '/usr/local/apps/forestplanner/mediaroot/'
MEDIA_URL = '$url_base/media/'
STATIC_URL = '$url_base/media/'

POSTGIS_TEMPLATE='template1'
DEBUG = True
TEMPLATE_DEBUG = DEBUG 

ADMINS = (
        ('Madrona', 'madrona@ecotrust.org')
        ) 

import logging
logging.getLogger('django.db.backends').setLevel(logging.ERROR)
import os
LOG_FILE = os.path.join(os.path.dirname(__file__),'..','trees.log')
