from django.urls import include, re_path, path
from landmapper.views import *

urlpatterns = [
    re_path(r'',
        home, name='landmapper-home'),
    path('', index, name="index"),
    path('identify/', identify, name="identify"),
    path('report/', report, name="report"),
]
