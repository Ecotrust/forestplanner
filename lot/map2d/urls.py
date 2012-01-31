from django.conf.urls.defaults import *
from map2d.views import *

urlpatterns = patterns('',
    #user requested analysis
    url(r'^$', map2d, name='twod-map2d'),
)
