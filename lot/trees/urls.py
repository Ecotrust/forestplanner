from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    url(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    url(r'^strata/$',
        manage_strata, name='trees-manage_strata'),
    url(r'^list/species.json$',
        list_species, name='trees-list_species'),
    url(r'^user_property_list/$', 
        user_property_list, name='trees-user_property_list'),
    url(r'^upload_stands/$', 
        upload_stands, name='trees-upload_stands'),
    url(r'^geosearch/$', 
        geosearch, name='trees-geosearch'),
    url(r'^stand_list/$', 
        stand_list_nn, name='trees-standlist'),
    url(r'^strata_list/(?P<property_uid>\w+)/$', 
        strata_list, name='trees-propertylist'),
    url(r'^potential_minmax/$', 
        potential_minmax, name='trees-potential_minmax'),
    url(r'^gnn2svs/(\d+)/$', 
        svs_image, name='trees-svs'),
)

