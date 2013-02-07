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
    url(r'^nearest_plots/$', 
        nearest_plots, name='trees-nearest_plot'),
    url(r'^stand_list/$', 
        stand_list_nn, name='trees-standlist'),
    url(r'^potential_minmax/$', 
        potential_minmax, name='trees-potential_minmax'),
    url(r'^gnn2svs/(\d+)/$', 
        svs_image, name='trees-svs'),
)
