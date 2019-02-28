from django.conf.urls import url
from trees.views import *
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    # Pages
    url(r'^stand_list/$',  # "test_nearest_neighbor"?
        stand_list_nn, name='trees-standlist'),
    url(r'^stands/$',
        manage_stands, name='trees-manage_stands'),
    url(r'^strata/$', # Just in case you land there without a property
        RedirectView.as_view(url='/')),
    url(r'^strata/(?P<property_uid>\w+)$',
        manage_strata, name='trees-manage_strata'),
    url(r'^scenario/(?P<property_uid>\w+)$',
        manage_scenario, name='trees-manage_scenario'),
    url(r'^intro', # /intro
        intro, name='intro'),
    url(r'^about', # /about, /about/, /about-the-forest-scenario-planner, /about-your-mom
        about, name='about'),
    url(r'^documentation$', # /about, /about/, /about-the-forest-scenario-planner, /about-your-mom
        documentation, name='documentation'),
    url(r'^manage_carbongroups/$',
        manage_carbongroups_entry, name='trees-manage_carbongroups'),
    url(r'^browse_carbongroups/$',
        browse_carbongroups, name='trees-browse_carbongroups'),

    # Services
    url(r'^geosearch/$',
        geosearch, name='trees-geosearch'),
    url(r'^variant/(?P<property_uid>\w+)/species_sizecls.json$',
        list_species_sizecls, name='trees-list_species_sizecls'),
    url(r'^variant/(?P<variant_id>\d+)_decision.xml$',
        variant_decision_xml, name='trees-variant-decision-xml'),
    url(r'^user_property_list/$',
        user_property_list, name='trees-user_property_list'),
    url(r'^upload_stands/$',
        upload_stands, name='trees-upload_stands'),
]
