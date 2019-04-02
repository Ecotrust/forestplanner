from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('documentation/', views.documentation, name='documentation'),
    path('landing/', views.landing, name='landing'),
    path('account/login/', views.login, name='login'),
    path('account/register/', views.register, name='register'),
    path('account/reset/', views.reset, name='reset'),
    path('stands/', views.stands, name='stands'),
    path('find_your_forest/', views.find_your_forest, name='find_your_forest'),
    path('map/', views.map, name='map'),
    path('collect_data/', views.collect_data, name='collect_data'),
    path('enter_data/', views.enter_data, name='enter_data'),
    path('enter_stand_table/', views.enter_stand_table, name='enter_stand_table'),
    path('stand_profile/', views.stand_profile, name='stand_profile'),
]
