from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    #user requested analysis
    url(r'properties_list/$', properties_list, name='trees-properties_list'),
    url(r'^construct_stands/$', construct_stands, name='trees-construct_stands'),
    url(r'^stands/$', stands, name='trees-stands'),
    url(r'^demo/$', demo, name='twod-map2d'),
    url(r'^user_property_list/$', user_property_list, name='trees-user_property_list'),
)
