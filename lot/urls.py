from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('lingcod.common.urls')),
    (r'^trees/', include('trees.urls')),
    (r'^map2d/', include('map2d.urls')),
)
