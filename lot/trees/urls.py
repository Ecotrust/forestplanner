from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    url(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    url(r'^user_property_list/$', 
        user_property_list, name='trees-user_property_list'),
    url(r'^property_stand_list/(?P<property_uid>\w+)/$', 
        property_stand_list, name='trees-property_stand_list'),
    url(r'^upload_stands/$', 
        upload_stands, name='trees-upload_stands'),
    url(r'^geosearch/$', 
        geosearch, name='trees-geosearch'),
)
