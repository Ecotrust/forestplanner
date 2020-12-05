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
    path('report/<str:property_id>', report, name='report'),
    # map_type expects one of the following: aerial, street, terrain, stream, soil_types, forest_types
    path('report/<str:property_id>/<str:map_type>/map', get_property_map_image, name='get_property_map_image'),
    path('report/<str:property_id>/pdf', get_property_pdf, name='get_property_pdf'),
    path('report/<str:property_id>/scalebar', get_scalebar_as_image, name='get_scalebar_as_image'),
    path('report/<str:property_id>/scalebar/<str:scale>', get_scalebar_as_image, name='get_scalebar_as_image'),
    path('get_taxlot_json/', get_taxlot_json, name='get taxlot json'),
]
