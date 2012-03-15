from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    url(r'^user_property_list/$', 
        user_property_list, name='trees-user_property_list'),
    url(r'^property_stand_list/(?P<property_uid>\w+)$', 
        property_stand_list, name='trees-property_stand_list'),
    url(r'^upload_stands/$', 
        upload_stands, name='trees-upload_stands'),
    #user requested analysis
    #url(r'properties_list/$', properties_list, name='trees-properties_list'),
    #url(r'^construct_stands/$', construct_stands, name='trees-construct_stands'),
    #url(r'^stands/$', stands, name='trees-stands'),
    #url(r'^demo/$', demo, name='twod-map2d'),
)
