from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    url(r'^user_property_list/$', 
        user_property_list, name='trees-user_property_list'),
    url(r'^upload_stands/$', 
        upload_stands, name='trees-upload_stands'),
    url(r'^geosearch/$', 
        geosearch, name='trees-geosearch'),
)
