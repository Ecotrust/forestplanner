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
from geopy import geocoders  
from geopy.point import Point
import json
import os

logger = get_logger()

def manage_stands(request):
    '''
    Stand management view
    '''
    return render_to_response('common/manage_stands.html', {}, 
        context_instance=RequestContext(request))

def user_property_list(request):
    '''
    Present list of properties for a given user 
    '''
    # import down here to avoid circular dependency
    from trees.models import ForestProperty

    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in.', status=401)

    user_fps = ForestProperty.objects.filter(user=request.user)
    try:
        bb = user_fps.extent(field_name='geometry_final')
    except:
        bb = settings.DEFAULT_EXTENT

    gj = """{ "type": "FeatureCollection",
    "bbox": [%s, %s, %s, %s],
    "features": [
    %s
    ]}""" % (bb[0], bb[1], bb[2], bb[3], ', '.join([fp.geojson for fp in user_fps]))

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
    Generic view to represent all Properties as GeoJSON
    '''
    return HttpResponse(instance.feature_set_geojson(), mimetype='application/json', status=200)

def geojson_features(request, instances):
    '''
    Generic view to represent Stands as GeoJSON
    '''
    featxt = ', '.join([i.geojson for i in instances])
    return HttpResponse("""{ "type": "FeatureCollection",
      "features": [
       %s
      ]}""" % featxt, mimetype='application/json', status=200)


def geosearch(request):
    """
    Returns geocoded results in MERCATOR projection
    First tries coordinates, then a series of geocoding engines
    """
    if request.method != 'GET':
        return HttpResponse('Invalid http method; use GET', status=405)        

    try:
        txt = unicode(request.GET['search'])
    except:
        return HttpResponseBadRequest()

    searchtype = lat = lon = None
    try:
        p = Point(txt) 
        lat, lon, altitude = p
        searchtype = 'coordinates'
    except:
        pass  # not a point

    if not searchtype or not lat or not lon:  # try a geocoder
        g = geocoders.Google()
        try:
            place, latlon = g.geocode(txt)  
            lat = latlon[0]
            lon = latlon[1]
            searchtype = 'geocoded_google'
        except:
            pass

    if not searchtype or not lat or not lon:  # try another geocoder
        g = geocoders.GeoNames()
        try:
            place, latlon = g.geocode(txt)  
            lat = latlon[0]
            lon = latlon[1]
            searchtype = 'geocoded_geonames'
        except:
            pass

    if searchtype and lat and lon:  # we have a winner
        cntr = GEOSGeometry('SRID=4326;POINT(%f %f)' % (lon, lat))
        cntr.transform(settings.GEOMETRY_DB_SRID)
        cntrbuf = cntr.buffer(settings.POINT_BUFFER)
        extent = cntrbuf.extent
        loc = {
            'status': 'ok',
            'search': txt, 
            'type': searchtype, 
            'extent': extent, 
            'center': (cntr[0], cntr[1]),
        }
        json_loc = json.dumps(loc)
        return HttpResponse(json_loc, mimetype='application/json', status=200)
    else:
        loc = {
            'status': 'failed',
            'search': txt, 
            'type': None, 
            'extent': None, 
            'center': None,
        }
        json_loc = json.dumps(loc)
        return HttpResponse(json_loc, mimetype='application/json', status=404)
