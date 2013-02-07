SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'forestplanner',
        'USER': 'vagrant',
    }
}

# This should be a local folder created for use with the install_media command 
MEDIA_ROOT = '/usr/local/apps/land_owner_tools/mediaroot/'
MEDIA_URL = 'http://localhost:8000/media/'
STATIC_URL = 'http://localhost:8000/media/'

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
