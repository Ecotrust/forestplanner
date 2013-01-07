# Create your views here.
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from madrona.common.utils import get_logger
from geopy import geocoders  
from geopy.point import Point
import json
import simplejson
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
            fp = None
            try:
                s = StandImporter(request.user)

                if new_prop_name:
                    s.import_ogr(ogr_path, new_property_name=new_prop_name, pre_impute=True) 
                else:
                    try:
                        fp = ForestProperty.objects.get(pk=prop_pk)
                    except ForestProperty.DoesNotExist:
                        return HttpResponse('<p class="label label-important">Could not find forest property %s</p>' % prop_pk, status=404)
                    s.import_ogr(ogr_path, forest_property=fp, pre_impute=True) 
            except Exception as err:
                return HttpResponse('<p class="label label-important">Error importing stands:\n%s</p>' % (err,), status=500)

            if not fp: 
                fp = ForestProperty.objects.filter(name=new_prop_name).latest('date_modified')
            res = HttpResponse(json.dumps({'X-Madrona-Select': fp.uid}), status=201, mimetype='application/json')
            return res
    else:
        form = UploadStandsForm()

    return HttpResponse('<p class="label label-important">Error importing stands: Invalid form submission</p>', status=400)
    #return render_to_response('upload.html', {'form': form}, status=status)

def geojson_forestproperty(request, instance):
    '''
    Generic view to represent all Properties as GeoJSON
    '''
    return HttpResponse(instance.feature_set_geojson(), mimetype='application/json', status=200)

def forestproperty_scenarios(request, instance):
    from trees.models import Scenario

    # TODO secure this 
    scenarios = Scenario.objects.filter(user=request.user, input_property=instance)
    if len(scenarios) == 0:
        s1 = Scenario(user=request.user, 
                input_property=instance,
                name="Grow Only",
                description="No management activities; allow natural regeneration for entire time period.",
                input_target_boardfeet=0,
                input_target_carbon=True,
                input_rxs={},
                input_site_diversity = 10,
                input_age_class = 10, 
        )
        s1.save()
        s2 = Scenario(user=request.user, 
                input_property=instance,
                name="Conventional Even-Aged",
                description="Even-aged management for timber. 40-year rotation clear cut.",
                input_target_boardfeet=2000,
                input_target_carbon=False,
                input_rxs={},
                input_site_diversity = 1,
                input_age_class = 1, 
        )
        s2.save()
        scenarios = Scenario.objects.filter(user=request.user, input_property=instance)

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

    currentloc = Point("45.0 N 122.0 W")

    if not searchtype or not lat or not lon:  # try a geocoder
        g = geocoders.Google()
        max_dist = 100000000
        try:
            for p, loc in g.geocode(txt, exactly_one=False):
                d = distance.distance(loc, currentloc).miles
                if d < max_dist:
                    place = p
                    lat = loc[0]
                    lon = loc[1]
                    max_dist = d
                else:
                    pass
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

def potential_minmax(request):
    from trees.utils import potential_minmax as _pmm
    from trees.models import PlotLookup
    categories = request.GET.get("categories", None)
    if categories:
        categories = json.loads(categories)
    else:
        categories = {}
    pld = PlotLookup.weight_dict()
    pmm = _pmm(categories, pld)
    jpmm = json.dumps(pmm)
    return HttpResponse(jpmm, mimetype='application/json', status=200)

def nearest_plots(request):
    from trees.utils import potential_minmax as _potential_minmax
    from trees.utils import nearest_plots as _nearest_plots
    from trees.utils import NoPlotMatchError
    from trees.models import PlotLookup, IdbSummary 

    categories = request.GET.get("categories", None)
    if categories:
        categories = simplejson.loads(categories)

    input_params = request.GET.get("input_params", None)
    if input_params:
        input_params = json.loads(input_params)

    weight_dict = PlotLookup.weight_dict()
    field_dict = PlotLookup.field_dict() 

    # Get all unique forest type names
    for_type_names_json = json.dumps([x.for_type_name 
        for x in IdbSummary.objects.all().distinct('for_type_name')])
    for_type_secdry_names_json = json.dumps([x.for_type_secdry_name 
        for x in IdbSummary.objects.filter(for_type_secdry_name__isnull=False).distinct('for_type_secdry_name')])

    if not categories and not input_params:
        return render_to_response("trees/nearest_plot_results.html", locals())
        
    # Construct a description string for the forest type
    if 'for_type_name' in categories.keys():
        category_string = categories['for_type_name']
    else:
        category_string = "No primary forest type"

    if 'for_type_secdry_name' in categories.keys():
        category_string = "%s and %s" % (category_string, categories['for_type_secdry_name'])

    # offset for plotid, fortype, certainty
    pmm = _potential_minmax(categories, weight_dict)

    try:
        top, num_candidates = _nearest_plots(categories, input_params, weight_dict, k=10)
    except NoPlotMatchError:
        top = []
        num_candidates = 0

    plots = []
    plot_coords = []
    for plot in top:
        if plot.for_type_secdry_name:
            for_type = "%s and %s" % (plot.for_type_name, plot.for_type_secdry_name)
        else:
            for_type = plot.for_type_name

        vals = [plot.cond_id] + [for_type, str(int(plot._certainty*100))] + [str(plot.__dict__[x]) for x in input_params.keys()] 
        plots.append(vals)
        
        if plot.latitude_fuzz and plot.longitude_fuzz:
            plot_coords.append((plot.longitude_fuzz, plot.latitude_fuzz, plot.cond_id))
        else:
            plot_coords.append(None)

    return render_to_response("trees/nearest_plot_results.html", locals())


def nearest_plot_old(request):
    from trees.utils import nearest_plot as _nearest_plot
    return_format = 'html'  #TODO support json, get from url parsing
    r = request.REQUEST

    # split requested items into categorical and numeric
    categorical = {}
    numeric = {}
    cats = ['imap_domspp', 'hdwpliv', 'conpliv', 'fortypiv', 'vegclass', 'sizecl', 'covcl', 'half_state']
    from trees.models import PlotSummary as PS
    nums = [x.name for x in PS._meta.fields if 
             x.get_internal_type() != 'CharField' and x.name not in cats]
    orig = dict(r)
    species = {}
    forest_class = None
    for k,v in orig.iteritems():
        if k == "_DOMSPECIES":
            species['dom'] = v
        if k == "_CODOMSPECIES":
            species['codom'] = v
        elif k == '_FORCLASS':
            forest_class = v
        elif k in ['sizecl','covcl']:
            categorical[k] = int(v)
        elif k in cats:
            categorical[k] = v
        elif k in nums:
            if v and v != '':
                numeric[k] = float(v)

    all_species = {
        'PSME': 'Douglas Fir',
        'ALRU2': 'Red Alder',
    }

    if len(orig.keys()) == 0:
        return render_to_response("trees/nearest_plot_form.html", locals())

    dist, plot, candidates = _nearest_plot(categorical, numeric, species, forest_class)
    closest = dict([(k,v) for k,v in plot.__dict__.iteritems()]) # if k in orig])
    
    if return_format == 'html':
        specified_vars = []
        for k in orig.keys():
            iscat = ''
            if k in cats:
                iscat = '*' 
            try:
                specified_vars.append((k, iscat, orig[k], closest[k]))
            except:
                if k == "_DOMSPECIES":
                    specified_vars.append((k, iscat, orig[k], closest['imap_domspp']))
                elif k == "_CODOMSPECIES":
                    specified_vars.append((k, iscat, orig[k], closest['fortypba']))
                elif k == '_FORCLASS':
                    specified_vars.append((k, iscat, orig[k], "hdwd = %s " % closest['bah_prop'] ))

        return render_to_response("trees/nearest_plot_results.html", locals())

def svs_image(request, gnn):
    imgs = ["/media/img/svs_sample/svs%d.png" % x for x in range(1,7)]
    idx = int(gnn) % len(imgs)
    return HttpResponsePermanentRedirect(imgs[idx])

