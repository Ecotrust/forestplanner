from django.urls import include, re_path
from landmapper.views import *

urlpatterns = [
    re_path(r'',
        home, name='landmapper-home'),
]
