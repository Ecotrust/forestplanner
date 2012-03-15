# Create your views here.
from django.http import HttpResponse
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User 
from itertools import izip
from madrona.raster_stats.models import zonal_stats, RasterDataset
from madrona.common.utils import get_logger
from madrona.common import default_mimetypes as mimetypes
from madrona.news.models import Entry
from madrona.common.utils import valid_browser
from madrona.features import user_sharing_groups
from madrona.studyregion.models import StudyRegion
from madrona.layers.models import PublicLayerList
from madrona.layers.views import has_privatekml
from madrona.features.views import has_features, get_object_for_viewing
from madrona.features import get_feature_by_uid
from madrona.common.utils import get_logger
import json
import os

logger = get_logger()

def user_property_list(request):
    '''
    Present list of properties for a given user 
    '''
    # import down here to avoid circular dependency
    from trees.models import ForestProperty

    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in.', status=401)

    user_fps = ForestProperty.objects.filter(user=request.user)
    gj = """{ "type": "FeatureCollection",
    "features": [
    %s
    ]}""" % '%s' % ', '.join([fp.geojson for fp in user_fps])
    return HttpResponse(gj, mimetype='application/json', status=200)

def property_stand_list(request, property_uid):
    '''
    Present list of stands for a given property
    '''
    from trees.models import ForestProperty

    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in.', status=401)

    fp = get_object_for_viewing(request, property_uid, target_klass=ForestProperty)
    if isinstance(fp, HttpResponse):
        return fp # some sort of http error response

    gj = fp.stand_set_geojson()
    return HttpResponse(gj, mimetype='application/json', status=200)

def upload_stands(request):
    '''
    Upload stands via OGR datasource
    '''
    from trees.forms import UploadStandsForm
    from trees.models import ForestProperty
    import tempfile
    import zipfile

    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in.', status=401)

    if request.method == 'POST':
        form = UploadStandsForm(request.POST, request.FILES)

        if form.is_valid():
            # confirm property 
            prop_pk = request.POST['property_pk']
            try:
                prop = ForestProperty.objects.get(pk=prop_pk, user=request.user)
            except ForestProperty.DoesNotExist:
                return HttpResponse('Could not find Forest Property %s' % prop_pk, status=404)

            # Save to disk
            f = request.FILES['ogrfile']
            tempdir = os.path.join(tempfile.gettempdir(), request.user.username)
            if not os.path.exists(tempdir):
                os.makedirs(tempdir)
            ogr_path = os.path.join(tempdir, f.name)
            dest = open(ogr_path, 'wb+')
            for chunk in f.chunks():
                dest.write(chunk)
            dest.close()
            
            #if zipfile, unzip and change ogr_path
            if ogr_path.endswith('zip'):
                shp_path = None
                zf = zipfile.ZipFile(ogr_path)
                for info in zf.infolist():
                    contents = zf.read(info.filename)
                    shp_part = os.path.join(tempdir, info.filename.split(os.path.sep)[-1])
                    fout = open(shp_part, "wb")
                    fout.write(contents)
                    fout.close()
                    if shp_part.endswith(".shp"):
                        shp_path = shp_part
                ogr_path = shp_path

            assert os.path.exists(ogr_path)

            # Import
            from trees.utils import StandImporter
            try:
                s = StandImporter(prop)
                s.import_ogr(ogr_path) 
            except Exception as err:
                return HttpResponse('Error importing stands\n\n%s' % err, status=500)

            return HttpResponse('success', status=200)
    else:
        form = UploadStandsForm()

    return render_to_response('upload.html', {'form': form})

def geojson_forestproperty(request, instance):
    '''
    Generic view to represent Properties as GeoJSON
    '''
    return HttpResponse(instance.stand_set_geojson(), mimetype='application/json', status=200)

def geojson_stands(request, instances):
    '''
    Generic view to represent Stands as GeoJSON
    '''
    featxt = ', '.join([i.geojson for i in instances])
    return HttpResponse("""{ "type": "FeatureCollection",
      "features": [
       %s
      ]}""" % featxt , mimetype='application/json', status=200)

