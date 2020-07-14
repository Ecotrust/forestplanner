from django.urls import include, re_path, path
from landmapper.views import *

urlpatterns = [
    # What is difference between re_path and path?
    # re_path(r'',
        # home, name='landmapper-home'),
    path('', home, name="home"),
    path('/identify/', identify, name="identify"),
    path('/report/', report, name="report"),
    path('/pages/', include('django.contrib.flatpages.urls')),
    url(r'^get_taxlot_json', views.get_taxlot_json, name='get taxlot json'),
]
