from django.urls import include, re_path, path
from django.views.decorators.cache import cache_page
from landmapper.views import *

urlpatterns = [
    # What is difference between re_path and path?
    # re_path(r'',
        # home, name='landmapper-home'),
    path('', home, name="home"),
    path('identify/', identify, name="identify"),
    path('create_property_id/', create_property_id, name='create_property_id'),
    # path('report/<str:property_id>', cache_page(60 * 60 * 24 * 7)(report), name='report'),
    path('report/<str:property_id>', report, name='report'),
    path('get_taxlot_json/', get_taxlot_json, name='get taxlot json'),
]
