from django.urls import include, re_path, path
from django.views.decorators.cache import cache_page
from landmapper.views import *

urlpatterns = [
    # What is difference between re_path and path?
    # re_path(r'',
        # home, name='landmapper-home'),
    path('', home, name="home"),
    path('identify/', identify, name="identify"),
    path('create_property_id/', create_property_id_from_request, name='create_property_id'),
    path('record/delete/<str:property_record_id>', delete_record, name='delete_record'),
    path('record/<str:property_record_id>', record_report, name='record_report'),
    path('report/<str:property_id>', report, name='report'),
    # map_type expects one of the following: aerial, street, terrain, stream, soil_types, forest_types
    path('report/<str:property_id>/<str:map_type>/map', get_property_map_image, name='get_property_map_image'),
    path('report/<str:property_id>/pdf', get_property_pdf, name='get_property_pdf'),
    path('report/<str:property_id>/<str:map_type>/pdf', get_property_map_pdf, name='get_property_map_pdf'),
    path('report/<str:property_id>/scalebar', get_scalebar_as_image, name='get_scalebar_as_image'),
    path('report/<str:property_id>/scalebar/<str:scale>', get_scalebar_as_image, name='get_scalebar_as_image'),
    path('report/<str:property_id>/scalebar/pdf/<str:scale>', get_scalebar_as_image_for_pdf, name='get_scalebar_as_pdf_image'),
    path('get_taxlot_json/', get_taxlot_json, name='get taxlot json'),
    path('auth/login/', login, name='login'),
    path('auth/signup/', signup, name='signup'),
    path('auth/profile/', user_profile, name='user_profile'),
    path('auth/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('auth/password/change/', change_password, name='password_reset'),
    path('tou/', terms_of_use, name='tou'),
    path('privacy/', privacy_policy, name='privacy'),
    path('user_profile/', userProfileSurvey, name='user_profile_survey'),
    path('user_followup/', userProfileFollowup, name='user_profile_followup'),
    path('register/', accountsRedirect, name='accounts_redirect'),
]
