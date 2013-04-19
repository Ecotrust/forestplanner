from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from madrona.common.utils import get_logger
from geopy import geocoders
from geopy.point import Point
from trees.models import Stand
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import json
import os

logger = get_logger()


@cache_page(60 * 60 * 24 * 365)
def list_species_sizecls(request, variant_id):
    '''
    Provide a json list of all species and available size classes
    in the specified variant
    '''
    from trees.models import FVSVariant
    from django.db import connection

    try:
        variant = FVSVariant.objects.get(id=int(variant_id))
    except FVSVariant.DoesNotExist:
        return HttpResponse(json.dumps({'error': 'Variant %s does not exist' % variant_id}), status=404)

    sql = """
    SELECT fia_forest_type_name,
           --variant_code,
           MIN(calc_dbh_class) AS min_dbh,
           MAX(calc_dbh_class) AS max_dbh
           --avg(calc_dbh_class) as avg_dbh,
           --count(calc_dbh_class) as count_trees,
           --stddev(calc_dbh_class) as sdev_dbh
    FROM treelive_summary summary, trees_conditionvariantlookup cvl
    WHERE cvl.cond_id = summary.cond_id
    AND cvl.variant_code = %s
    GROUP BY fia_forest_type_name, variant_code
    """
    cursor = connection.cursor()
    cursor.execute(sql, (variant.code,))
    return HttpResponse(json.dumps(list(cursor.fetchall())), mimetype='application/json', status=200)


def manage_stands(request):
    '''
    Stand management view
    '''
    return render_to_response('common/manage_stands.html', {},
                              context_instance=RequestContext(request))


def manage_strata(request, property_uid):
    '''
    Strata management view
    '''
    return render_to_response(
        'common/manage_strata.html', {'property_id': property_uid},
        context_instance=RequestContext(request))


def manage_scenario(request, property_uid):
    '''
    Scenario management view
    '''
    return render_to_response(
        'common/manage_scenario.html', {'property_id': property_uid},
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
    ]}""" % (bb[0], bb[1], bb[2], bb[3], ', '.join([fp.geojson() for fp in user_fps]))

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
            try:
                prop_pk = request.POST['property_pk']
            except KeyError:
                prop_pk = None

            try:
                new_prop_name = request.POST['new_property_name']
            except KeyError:
                new_prop_name = None

            if not prop_pk and not new_prop_name:
                return HttpResponse('You must provide either a new property name or existing property id.', status=401)

            # Save to disk
            f = request.FILES['ogrfile']
            tempdir = os.path.join(
                tempfile.gettempdir(), request.user.username)
            if not os.path.exists(tempdir):
                os.makedirs(tempdir)
            ogr_path = os.path.join(tempdir, f.name)
            dest = open(ogr_path, 'wb+')
            for chunk in f.chunks():
                dest.write(chunk)
            dest.close()

            # if zipfile, unzip and change ogr_path
            if ogr_path.endswith('zip'):
                shp_path = None
                zf = zipfile.ZipFile(ogr_path)
                for info in zf.infolist():
                    contents = zf.read(info.filename)
                    shp_part = os.path.join(
                        tempdir, info.filename.split(os.path.sep)[-1])
                    fout = open(shp_part, "wb")
                    fout.write(contents)
                    fout.close()
                    if shp_part.endswith(".shp"):
                        shp_path = shp_part
                ogr_path = shp_path

            assert os.path.exists(ogr_path)

            # Import
            from trees.utils import StandImporter
            fp = None
            try:
                s = StandImporter(request.user)

                if new_prop_name:
                    s.import_ogr(ogr_path,
                                 new_property_name=new_prop_name, pre_impute=True)
                else:
                    try:
                        fp = ForestProperty.objects.get(pk=prop_pk)
                    except ForestProperty.DoesNotExist:
                        return HttpResponse('<p class="label label-important">Could not find forest property %s</p>' % prop_pk, status=404)
                    s.import_ogr(ogr_path, forest_property=fp, pre_impute=True)
            except Exception as err:
                return HttpResponse('<p class="label label-important">Error importing stands:\n%s</p>' % (err,), status=500)

            if not fp:
                fp = ForestProperty.objects.filter(
                    name=new_prop_name).latest('date_modified')
            res = HttpResponse(json.dumps({'X-Madrona-Select': fp.uid}),
                               status=201, mimetype='application/json')
            return res
    else:
        form = UploadStandsForm()

    return HttpResponse('<p class="label label-important">Error importing stands: Invalid form submission</p>', status=400)
    # return render_to_response('upload.html', {'form': form}, status=status)


def geojson_forestproperty(request, instance):
    '''
    Generic view to represent all Properties as GeoJSON
    '''
    return HttpResponse(instance.feature_set_geojson(), mimetype='application/json', status=200)


def forestproperty_scenarios(request, instance):
    from trees.models import Scenario

    # TODO secure this
    scenarios = Scenario.objects.filter(
        user=request.user, input_property=instance)
    if len(scenarios) == 0:
        s1 = Scenario(user=request.user,
                      input_property=instance,
                      name="Grow Only",
                      description="No management activities; allow natural regeneration for entire time period.",
                      input_target_boardfeet=0,
                      input_target_carbon=True,
                      input_rxs={},
                      input_age_class=10,
                      )
        s1.save()
        s2 = Scenario(user=request.user,
                      input_property=instance,
                      name="Conventional Even-Aged",
                      description="Even-aged management for timber. 40-year rotation clear cut.",
                      input_target_boardfeet=2000,
                      input_target_carbon=False,
                      input_rxs={},
                      input_age_class=1,
                      )
        s2.save()
        scenarios = Scenario.objects.filter(
            user=request.user, input_property=instance)

    if len(scenarios) == 0:
        # this should never happen
        return HttpResponse([], mimetype='application/json', status=404)

    res_json = json.dumps([x.property_level_dict for x in scenarios])
    return HttpResponse(res_json, mimetype='application/json', status=200)


def geojson_features(request, instances):
    '''
    Generic view to represent Stands as GeoJSON
    '''
    featxt = ', '.join([i.geojson for i in instances])
    return HttpResponse("""{ "type": "FeatureCollection",
      "features": [
       %s
      ]}""" % featxt, mimetype='application/json', status=200)


@cache_page(60 * 60 * 24 * 365)
def geosearch(request):
    """
    Returns geocoded results in MERCATOR projection
    First tries coordinates, then a series of geocoding engines
    """
    from geopy import distance
    if request.method != 'GET':
        return HttpResponse('Invalid http method; use GET', status=405)

    try:
        txt = unicode(request.GET['search'])
    except:
        return HttpResponseBadRequest()

    searchtype = lat = lon = None
    place = txt
    try:
        p = Point(txt)
        lat, lon, altitude = p
        searchtype = 'coordinates'
    except:
        pass  # not a point

    centerloc = Point("45.54 N 120.64 W")
    max_dist = 315  # should be everything in WA and Oregon

    searches = [
        geocoders.GeoNames(),
        geocoders.OpenMapQuest(), 
        geocoders.Yahoo(app_id=settings.APP_NAME), 
        geocoders.Bing(api_key=settings.BING_API_KEY),
        # these are tried in reverse order, fastest first
        # TODO thread them and try them as they come in.
    ]

    while not (searchtype and lat and lon):  # try a geocoder
        try:
            g = searches.pop()
            for p, loc in g.geocode(txt, exactly_one=False):
                d = distance.distance(loc, centerloc).miles
                if d < max_dist:
                    # TODO maybe compile these and return the closest to map center?
                    # print g, p, loc 
                    place = p
                    lat = loc[0]
                    lon = loc[1]
                    max_dist = d
                else:
                    pass
            searchtype = g.__class__.__name__
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
            'place': place,
            'type': searchtype,
            'extent': extent,
            'latlon': [lat, lon],
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


def stand_list_nn(request):
    from plots import get_nearest_neighbors

    stand_list = {
        'classes': [
            ('Douglas-fir', 6, 10, 160),
            ('Douglas-fir', 10, 14, 31),
            ('Douglas-fir', 14, 18, 7),
            ('Western hemlock', 14, 18, 5),
            ('Western redcedar', 14, 18, 5),
            #('Red alder', 6, 20),
        ]
    }

    site_cond = {
        "age_dom": 40,
        "calc_aspect": 360,
        "elev_ft": 1100,
        "latitude_fuzz": 45.58,
        "longitude_fuzz": -123.83,
        "calc_slope": 5
    }

    weight_dict = {
        'PLOT_BA': 5,
        'NONSPEC_BA': 5,
        'age_dom': 1,
        "calc_aspect": 1,
        "elev_ft": 0.6,
        "latitude_fuzz": 0.3,
        "longitude_fuzz": 0.6,
        "calc_slope": 0.6,
    }

    in_stand_list = request.GET.get("stand_list", None)
    if in_stand_list:
        stand_list = json.loads(in_stand_list)
    in_site_cond = request.GET.get("site_cond", None)
    if in_site_cond:
        site_cond = json.loads(in_site_cond)
    in_weight_dict = request.GET.get("weight_dict", None)
    if in_weight_dict:
        weight_dict = json.loads(in_weight_dict)

    # Calculate basal area based on the media of the size class and TPA
    mod_stand_list = [tuple(s) + (s[3] * (0.005454 * (
        ((s[1] + s[2]) / 2.0) ** 2)),) for s in stand_list['classes']]
    total_ba = sum(s[4] for s in mod_stand_list)

    out = []
    out.append("Searching for:\n  ")
    out.extend(
        "%s, %s to %s in, %s tpa, %d ba est" % s for s in mod_stand_list)
    out.append("   (Total basal area: %d ft2/ac)" % total_ba)
    out.append("\n")

    ps, num_candidates = get_nearest_neighbors(
        site_cond, mod_stand_list, weight_dict, k=10)

    stand_list_json = json.dumps(stand_list)
    site_cond_json = json.dumps(site_cond)
    weight_dict_json = json.dumps(weight_dict)

    out.append("Candidates: %d" % num_candidates)
    out.append("\n")
    out.append("<table border='1' width='100%'>")
    out.append("<tr>\
        <th>Condition ID</th>\
        <th>Certainty</th>\
        <th>Plot Basal Area</th>\
        <th>Basal area from specified stand list classes</th>\
        <th>Basal area from same species but different diam classes</th>\
        <th>Basal area from entirely new species</th>\
        <th>Age</th>\
        </tr>")
    for pseries in ps:
        out.append(
            "<tr>\
            <td>%s</td>\
            <td>%d%%</td>\
            <td>%s</td>\
            <td><div style='background-color:green; margin:0px; color: green; display: inline-block; width:%dpx;'>_</div>%s</td>\
            <td><div style='background-color:yellow; margin:0px; color: yellow; display: inline-block; width:%dpx;'>_</div>%s</td>\
            <td><div style='background-color:red; margin:0px; color:red; display: inline-block; width:%dpx;'>_</div>%s</td>\
            <td>%s</td>\
            </tr>" % (pseries.name,
                      pseries['_certainty'] * 100,
                      pseries['PLOT_BA'],
                      pseries['TOTAL_BA'], pseries['TOTAL_BA'],
                      pseries['PLOT_BA'] - (pseries['TOTAL_BA'] + pseries['NONSPEC_BA']), pseries['PLOT_BA'] - (
                      pseries['TOTAL_BA'] + pseries['NONSPEC_BA']),
                      pseries['NONSPEC_BA'], pseries['NONSPEC_BA'],
                      pseries['age_dom'],
                      )
        )
    out.append("</table>")
    return render_to_response("trees/stand_list_nn.html", locals())


def add_stands_to_strata(request, instance):
    from madrona.features.views import get_object_for_editing
    in_stands = request.POST.get("stands", None)
    stands = in_stands.split(",")
    for uid in stands:
        stand = get_object_for_editing(request, uid, target_klass=Stand)
        if isinstance(stand, HttpResponse):
            return stand
        stand.strata = instance
        stand.save()
    instance.save()
    return HttpResponse("Stands %r added to %s" % (stands, instance.uid), mimetype='text/html', status=200)


def forestproperty_strata_list(request, instance):
    from trees.models import Strata
    slist = sorted(instance.feature_set(feature_classes=[Strata]),
                   key=lambda x: x.date_created, reverse=False)
    return HttpResponse(json.dumps([x._dict for x in slist]), mimetype="text/javascript")


def run_scenario(request, instance):
    from trees.models import Scenario, ScenarioNotRunnable  # , ForestProperty, Strata
    from celery.result import AsyncResult

    force_rerun = request.REQUEST.get("force", False)
    status = ''
    rerun = instance.needs_rerun

    # determine if there is already a process running using the redis cache
    taskid = cache.get('Taskid_%s' % instance.uid)
    if taskid:
        status = 'unknown'
        try:
            task = AsyncResult(taskid)
            status = task.status
            # if task is still running, don't rerun
            rerun = False
        except:
            pass

        if status == "SUCCESS" and instance.needs_rerun:
            # it's already been run but needs a refresher
            rerun = True

    if rerun or force_rerun:
        try:
            instance.run()
            status = "Running"
        except ScenarioNotRunnable:
            status = "Not-runnable"

    return HttpResponse(status, mimetype="text/javascript")


def forestproperty_status(request, instance):
    """
    /features/forestproperty/links/property-status/trees_forestproperty_<id>/
    """
    res_json = json.dumps(instance.status)
    return HttpResponse(res_json, mimetype='application/json', status=200)


def variant_decision_xml(request, variant_id):
    '''
    Provide the xml for decision tree
    in the specified variant
    '''
    from trees.models import FVSVariant

    try:
        variant = FVSVariant.objects.get(id=int(variant_id))
    except FVSVariant.DoesNotExist:
        return HttpResponse('<?xml version="1.0"?>' +
                            '<error>Variant %s does not exist</error>' % variant_id, status=404)

    return HttpResponse(variant.decision_tree_xml, mimetype='application/xml', status=200)


def forestproperty_myrx(request, instance):
    """
    Return json array of MyRx objects belonging to this users's property
    /features/forestproperty/links/property-myrx-json/trees_forestproperty_<id>/
    """
    from trees.models import MyRx
    myrxs = instance.feature_set(feature_classes=[MyRx,])
    res_json = json.dumps([x._dict for x in myrxs])
    return HttpResponse(res_json, mimetype='application/json', status=200)
