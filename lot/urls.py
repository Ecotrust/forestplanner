from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns(
    '',

    # Looser pattern matching for workspace username (as opposed to \w+)
    # Already in madrona 4.2dev+ but just in case we're still running <=4.1
    url(r'^features/(?P<username>.+)/workspace-owner.json', 'madrona.features.views.workspace', kwargs={"is_owner": True}, name='workspace-owner-json'),
    url(r'^features/(?P<username>.+)/workspace-shared.json', 'madrona.features.views.workspace', kwargs={"is_owner": False}, name='workspace-shared-json'),

    url(r'^$', 'trees.views.map', name='map'),

    (r'', include('madrona.common.urls')),
    (r'^trees/', include('trees.urls')),
    (r'^auth/', include('allauth.urls')),
    url(
        r'^auth/profile/',
        direct_to_template,
        {'template': 'account/profile.html'},
        "auth_profile"
    ),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}
        ),
    )
