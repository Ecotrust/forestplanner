from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('madrona.common.urls')),
    (r'^trees/', include('trees.urls')),
    (r'^auth/', include('allauth.urls')),
    url(r'^auth/profile/', direct_to_template, { 'template' : 'account/profile.html' }, "auth_profile"),
)
