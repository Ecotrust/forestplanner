from django.urls import path, re_path, include
from . import views
from trees import views as trees_views
# from django.contrib.flatpages import views as flat_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('documentation/', views.documentation, name='documentation'),
    path('landing/', views.landing, name='landing'),
    path('auth/login/', views.login, name='login'),
    path('auth/signup/', views.signup, name='signup'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    path('auth/password/change/', views.password_reset, name='password_reset'),
    path('stands/', views.stands, name='stands'),
    path('example_stands/', views.example_stands, name='example_stands'),
    re_path(r'^example_stands/create_stand/(?P<example_stand_uid>\w+)/$', views.create_stand_from_example, name='create_stand_from_example'),
    path('find_your_forest/', views.find_your_forest, name='find_your_forest'),
    re_path(r'^map/((?P<discovery_stand_uid>\w+)/)?$', views.map, name='map'),
    path('collect_data/', views.collect_data, name='collect_data'),
    path('enter_data/', views.enter_data, name='enter_data'),
    path('enter_stand_table/', views.enter_stand_table, name='enter_stand_table'),
    path('forest_profile/', views.forest_profile, name='forest_profile'),
    path('pages/', include('django.contrib.flatpages.urls')),
    re_path(r'^modal_content/(?P<card_type>\w+)/(?P<uid>\w+)/$', views.get_modal_content, name='discovery-get_modal_content'),
]
