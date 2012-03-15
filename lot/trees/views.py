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

def properties_list(request):
    parcels = Parcel.objects.all()
    apns = [{p.pk: p.apn} for p in parcels]
    response = HttpResponse(json.dumps(apns), status=200)
    response.ContentType = 'application/json'
    return response

def stands(request):
    stands_jsons = request.POST.getlist('stands[]')
    stand_geoms = []
    for sj in stands_jsons:
        j = json.loads(sj)
        gj = j['geometry']
        stand_geom = GEOSGeometry(json.dumps(gj))
        # TODO Store stands in TreesAnalysis
        stand_geoms.append(stand_geom)

    def get_json(geom):
        gnn = RasterDataset.objects.get(name="gnn")
        # Assume srid is same as client, need to transform to gnn srs
        geom.srid = settings.GEOMETRY_CLIENT_SRID
        raster_proj4 = '+proj=aea +lat_1=43 +lat_2=48 +lat_0=34 +lon_0=-120 +x_0=600000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs' 
        new_geom = geom.transform(raster_proj4, clone=True)
        stats = zonal_stats(new_geom, gnn)
        stats.save()
        total_pixels = stats.pixels
        if total_pixels is None:
            raise Exception("No pixels found, check projection and make sure input geom overlaps the raster extent")
        fcids = []
        fcid_counts = []
        for cat in stats.categories.all():
            fcids.append(cat.category)
            fcid_counts.append(cat.count)
        fcid_table = "<table>"
        fcid_table += "<tr><th>FCID</th><th>Count</th></tr>" 
        for r in range(len(fcids)):
            fcid_table += "<tr><td>%s</td><td>%s</td></tr>" % (fcids[r],fcid_counts[r])
        fcid_table += "<tr><td><em>TOTAL</em></td><td>%s</td></tr>" % (sum(fcid_counts),)
        fcid_table += "</table>"

        # Find the tree_live record of all FCIDs
        from django.db import connection, transaction
        cursor = connection.cursor()
        cursor.execute("SELECT FCID, SCIENTIFIC_NAME, HT_M, BA_M2 FROM TREE_LIVE WHERE FCID IN (%s) ORDER BY FCID, BA_M2 DESC" % ','.join([str(f) for f in fcids]) )
        rows = cursor.fetchall()
        tree_live =  "<table>"
        tree_live += "<tr><th>FCID</th><th>Species</th><th>Height (m)</th><th>Basal Area (m<sup>2</sup>)</th></tr>" 
        for r in rows:
            tree_live += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % r
        tree_live += "</table>"


        logger.debug(geom.extent)
        dem = RasterDataset.objects.get(name="dem")
        stats = zonal_stats(geom, dem)
        stats.save()
        elev = stats.avg
        if elev is None: elev = 0

        slope = RasterDataset.objects.get(name="slope")
        stats = zonal_stats(geom, slope)
        stats.save()
        slope = stats.avg
        if slope is None: slope = 0

        aspect = RasterDataset.objects.get(name="aspect")
        stats = zonal_stats(geom, aspect)
        stats.save()
        aspect = stats.median
        if aspect is None: aspect = 0

        return """
                {
                  "geometry": %s, 
                  "type": "Feature", 
                  "properties": {
                    "area": %s,
                    "elevation": %s,
                    "slope": %s,
                    "aspect": %s,
                    "fcids": [%s],
                    "fcid_counts": [%s],
                    "fcid_table": "%s",
                    "tree_live_html": "%s"
                   }
                }
        """ % (geom.geojson, new_geom.area, 
                elev, slope, aspect, 
                ','.join([str(f) for f in fcids]), 
                ','.join([str(f) for f in fcid_counts]),
                fcid_table, 
                tree_live
               )

    collection = """{
              "type": "FeatureCollection", 
              "features": [ %s ]
           }""" % ',\n'.join([get_json(s) for s in stand_geoms])

    response = HttpResponse(collection, status=200)
    response.ContentType = 'application/json'
    return response


def construct_stands(request):
    if not request.method == 'POST':
        return HttpResponse("Not a valid request method. Try POST.", status=405)

    edges_json = request.POST.getlist('edges[]')
    edges = []
    for ej in edges_json:
        j = json.loads(ej)
        gj = j['geometry']
        edge = GEOSGeometry(json.dumps(gj))
        edges.append(edge)
    # TODO Store edges in TreesAnalysis

    parcel_pk = int(request.POST['parcel_pk'])
    parcels = Parcel.objects.filter(pk=parcel_pk).geojson()
    parcel_polys = []
    for parcel in parcels:
        g = parcel.geom
        if g.geom_type == 'MultiPolygon':
            for sg in g:
                if sg.geom_type == 'Polygon':
                    parcel_polys.append(sg)
                else:
                    raise Exception("was expecting a polygon - got a %s" % sg.geom_type)
        elif g.geom_type == 'Polygon':
            parcel_polys.append(g)
        else:
            raise Exception("was expecting a (multi)polygon - got a %s" % sg.geom_type)

    stream_buffers = StreamBuffer.objects.filter(geom__bboverlaps=parcels.collect()).geojson()
    strbuf_polys = []
    for strbuf in stream_buffers:
        g = strbuf.geom
        if g.geom_type == 'MultiPolygon':
            for sg in g:
                if sg.geom_type == 'Polygon':
                    if sg.intersects(parcels.collect()):
                        strbuf_polys.append(sg)
                else:
                    raise Exception("was expecting a polygon - got a %s" % sg.geom_type)
        elif g.geom_type == 'Polygon':
            if g.intersects(parcels.collect()):
                strbuf_polys.append(g)
        else:
            raise Exception("was expecting a (multi)polygon - got a %s" % sg.geom_type)

    # Take the edges, and the parcel and ST_Polygonize them
    sql = """
    SELECT 
        ST_AsText(
            ST_POLYGONIZE(
                ST_Union(
                    ARRAY[
                        %s, 
                        %s
                    ]
                )
            )
        )
        AS polygon
    """ % (',\n                        '.join(["ST_GeomFromText('%s')" % e.wkt for e in edges]), 
           ',\n                        '.join(["ST_GeomFromText(ST_ExteriorRing('%s'))" % p.wkt for p in parcel_polys]), 
    )
    results = list(query_to_dicts(sql))
    newgeom = GEOSGeometry(results[0]['polygon'])
    print newgeom

    #TODO intersect with stream buffers
    #',\n                        '.join(["ST_GeomFromText(ST_ExteriorRing('%s'))" % s.wkt for s in strbuf_polys]), 
    # TODO Store polygons in TreesAnalysis

    # TODO Loop through polygons and auto-attribute them individually

    # TODO Deliver a summary of the analysis : "X stands were created with X acres of ...."

    collection = """{
              "type": "FeatureCollection", 
              "features": [
                {
                  "geometry": %s, 
                  "type": "Feature", 
                  "properties": {}
                }
              ]
           }""" % newgeom.json
    response = HttpResponse(collection, status=200)
    response.ContentType = 'application/json'
    return response
    
def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return

from django.views.decorators.cache import cache_page

def stands_json(request):
    stands = Stand.objects.all()
    collection_template = """{ "type": "FeatureCollection",
    "features": [ %s
    ]} """
    json_geoms = []
    for s in stands:
        json_geoms.append("""
        { 
        "type": "Feature",
        "geometry": %s,
        "properties": {"id": %s}
        }
        """ % (s.geometry_final.json, s.pk))
    geojson = collection_template % ','.join(json_geoms)
    return HttpResponse(geojson, status=200, content_type = 'application/json')

def demo(request, template_name='common/map_demo.html', extra_context={}):
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
