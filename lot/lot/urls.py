from django.conf.urls import *
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from madrona.features.views import workspace
from trees.views import map
admin.autodiscover()

urlpatterns = [
    # '',

    # Looser pattern matching for workspace username (as opposed to \w+)
    # Already in madrona 4.2dev+ but just in case we're still running <=4.1
    url(r'^features/(?P<username>.+)/workspace-owner.json', workspace, kwargs={"is_owner": True}, name='workspace-owner-json'),
    url(r'^features/(?P<username>.+)/workspace-shared.json', workspace, kwargs={"is_owner": False}, name='workspace-shared-json'),

    url(r'^$', map, name='map'),

    (r'', include('madrona.common.urls')),
    (r'^trees/', include('trees.urls')),
    (r'^auth/', include('allauth.urls')),
    url(
        r'^auth/profile/',
        TemplateView.as_view(template_name = 'account/profile.html'),
        "auth_profile"
    ),
]

if settings.DEBUG:
    urlpatterns += [
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}
        ),
    ]
