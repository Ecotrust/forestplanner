from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    #user requested analysis
    url(r'properties_list/$', properties_list, name='trees-properties_list'),
    url(r'^parcel/(?P<pk>\d+).json$', parcel_geojson, name='trees-parcel_geojson'),
    url(r'^construct_stands/$', construct_stands, name='trees-construct_stands'),
    url(r'^stands/$', stands, name='trees-stands'),
    url(r'^stands_json/$', stands_json, name='trees-stands_json'),
)
