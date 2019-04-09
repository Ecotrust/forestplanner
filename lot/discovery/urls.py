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
    path('stands/', views.stands, name='stands'),
    path('find_your_forest/', views.find_your_forest, name='find_your_forest'),
    path('map/', views.map, name='map'),
    path('collect_data/', views.collect_data, name='collect_data'),
    path('enter_data/', views.enter_data, name='enter_data'),
    path('enter_stand_table/', views.enter_stand_table, name='enter_stand_table'),
    path('forest_profile/', views.forest_profile, name='forest_profile'),
    path('pages/', include('django.contrib.flatpages.urls')),
]
