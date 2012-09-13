from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    url(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    url(r'^user_property_list/$', 
        user_property_list, name='trees-user_property_list'),
    url(r'^upload_stands/$', 
        upload_stands, name='trees-upload_stands'),
    url(r'^geosearch/$', 
        geosearch, name='trees-geosearch'),
    url(r'^nearest_plot/$', 
        nearest_plot, name='trees-nearest_plot'),
    url(r'^gnn2svs/(\d+)/$', 
        svs_image, name='trees-svs'),
)
