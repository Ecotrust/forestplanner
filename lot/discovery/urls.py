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
    path('stand_profile/', views.stand_profile, name='stand_profile'),
]
