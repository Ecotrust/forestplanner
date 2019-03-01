from django.conf.urls import url
from django.urls import include, path, re_path
from trees.views import *
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    # Pages
    re_path(r'^stand_list/$',  # "test_nearest_neighbor"?
        stand_list_nn, name='trees-standlist'),
    re_path(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    re_path(r'^strata/$', # Just in case you land there without a property
        RedirectView.as_view(url='/')),
    re_path(r'^strata/(?P<property_uid>\w+)$',
        manage_strata, name='trees-manage_strata'),
    re_path(r'^scenario/(?P<property_uid>\w+)$',
        manage_scenario, name='trees-manage_scenario'),
    re_path(r'^intro', # /intro
        intro, name='intro'),
    re_path(r'^about', # /about, /about/, /about-the-forest-scenario-planner, /about-your-mom
        about, name='about'),
    re_path(r'^documentation$', # /about, /about/, /about-the-forest-scenario-planner, /about-your-mom
        documentation, name='documentation'),
    re_path(r'^manage_carbongroups/$',
        manage_carbongroups_entry, name='trees-manage_carbongroups'),
    re_path(r'^browse_carbongroups/$',
        browse_carbongroups, name='trees-browse_carbongroups'),

    # Services
    re_path(r'^geosearch/$',
        geosearch, name='trees-geosearch'),
    re_path(r'^variant/(?P<property_uid>\w+)/species_sizecls.json$',
        list_species_sizecls, name='trees-list_species_sizecls'),
    re_path(r'^variant/(?P<variant_id>\d+)_decision.xml$',
        variant_decision_xml, name='trees-variant-decision-xml'),
    re_path(r'^user_property_list/$',
        user_property_list, name='trees-user_property_list'),
    re_path(r'^upload_stands/$',
        upload_stands, name='trees-upload_stands'),
]
