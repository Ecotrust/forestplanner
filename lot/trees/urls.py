from django.conf.urls.defaults import *
from trees.views import *

urlpatterns = patterns('',
    # Pages
    url(r'^stand_list/$',  # "test_nearest_neighbor"?
        stand_list_nn, name='trees-standlist'),
    url(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    url(r'^strata/(?P<property_uid>\w+)$',
        manage_strata, name='trees-manage_strata'),

    url(r'^scenario/(?P<property_uid>\w+)$',
        manage_scenario, name='trees-manage_scenario'),

    # TODO Page urls:
    # /   (intro and property list)
    # /{property_uid}
    # /{property_uid}/stands
    # /{property_uid}/strata
    # /{property_uid}/scenario

    # Services
    url(r'^geosearch/$',
        geosearch, name='trees-geosearch'),
    url(r'^list/species.json$',
        list_species, name='trees-list_species'),
    url(r'^user_property_list/$',
        user_property_list, name='trees-user_property_list'),
    url(r'^upload_stands/$',
        upload_stands, name='trees-upload_stands'),
)
