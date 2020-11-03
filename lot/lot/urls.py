from django.conf.urls import url
from django.urls import path, include, re_path
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from madrona.features.views import workspace
from django.views.static import serve
from trees.views import map
from lot.views import lot_landing_page
from django.conf.urls.static import static
# admin.autodiscover()

urlpatterns = [
    # '',
    path('discovery/', include('discovery.urls')),
    path('landmapper/', include('landmapper.urls')),
    re_path(r'^trees/', include('trees.urls')),
    # Looser pattern matching for workspace username (as opposed to \w+)
    # Already in madrona 4.2dev+ but just in case we're still running <=4.1
    re_path(r'^features/(?P<username>.+)/workspace-owner.json', workspace, kwargs={"is_owner": True}, name='workspace-owner-json'),
    re_path(r'^features/(?P<username>.+)/workspace-shared.json', workspace, kwargs={"is_owner": False}, name='workspace-shared-json'),

    re_path(r'^map/?$', map, name='map'),

    re_path(r'^auth/', include('allauth.urls')),
    re_path(
        r'^auth/profile/',
        TemplateView.as_view(template_name = 'account/profile.html'),
        name="auth_profile"
    ),
    # re_path('admin/', admin.site.urls),
    # re_path(r'^/?$', map, name='map'),
    # re_path(r'^/?$', include('discovery.urls')),
    re_path(r'^discovery', include('discovery.urls')),
    re_path(r'^landmapper', include('landmapper.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^$', lot_landing_page, name='lot'),
    re_path(r'^', include('madrona.common.urls')),
    # According to https://youtu.be/L6y6cn1XUfw this line will be ignored in production.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            kwargs={'document_root': settings.MEDIA_ROOT, 'show_indexes': True},
        ),
    ]
