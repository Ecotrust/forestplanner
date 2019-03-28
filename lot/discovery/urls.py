from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('documentation/', views.documentation, name='documentation'),
    path('landing/', views.landing, name='landing'),
    path('stand_profile/', views.stand_profile, name='stand_profile'),
]
