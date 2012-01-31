# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from lingcod.common import default_mimetypes as mimetypes
from lingcod.news.models import Entry
from lingcod.common.utils import valid_browser
from lingcod.features import user_sharing_groups
from lingcod.studyregion.models import StudyRegion
from lingcod.layers.models import PublicLayerList, PrivateKml
from lingcod.layers.views import has_privatekml
from lingcod.features.views import has_features
from lingcod.raster_stats.models import zonal_stats, RasterDataset
from lingcod.common.utils import get_logger
from itertools import izip
import json
import datetime

logger = get_logger()

def map2d(request, template_name='common/map_2d.html', extra_context={}):
    """
    Main application window
    Sets/Checks Cookies to determine if user needs to see the about or news panels
    """
    # Check if the user is a member of any sharing groups (not including public shares)
    member_of_sharing_group = False
    user = request.user
    if user.is_authenticated() and user_sharing_groups(user):
        member_of_sharing_group = True
    
    context = RequestContext(request,{
        'api_key':settings.GOOGLE_API_KEY, 
        'session_key': request.session.session_key,
        #'show_panel': 'about',
        'member_of_sharing_group': member_of_sharing_group,
        'is_studyregion': StudyRegion.objects.count() > 0,
        'is_public_layers': PublicLayerList.objects.filter(active=True).count() > 0,
        'is_privatekml': has_privatekml(user),
        'has_features': has_features(user),
        #'camera': parse_camera(request),
        #'publicstate': get_publicstate(request), 
        'bookmarks_as_feature': settings.BOOKMARK_FEATURE,
    })

    context.update(extra_context)
    response = render_to_response(template_name, context)
    return response
