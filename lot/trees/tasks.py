from celery import task
from django.core.cache import cache
import json
import datetime


@task(max_retries=5, default_retry_delay=5)  # retry up to 5 times, 5 seconds apart
def impute_rasters(stand_id, savetime):
    # import here to avoid circular dependencies
    from trees.models import Stand
    from django.conf import settings
    from madrona.raster_stats.models import RasterDataset, zonal_stats
    import math

    try:
        stand = Stand.objects.get(id=stand_id)
    except:
        raise impute_rasters.retry()

    print "imputing raster stats for %d" % stand_id

    def get_raster_stats(stand, rastername):
        # yes we know zonal_stats has it's own internal caching but it uses the DB
        key = "zonal_%s_%s" % (stand.geometry_final.wkt.__hash__(), rastername)
        stats = cache.get(key)
        if stats is None:
            try:
                raster = RasterDataset.objects.get(name=rastername)
            except RasterDataset.DoesNotExist:
                return None
            rproj = [rproj for rname, rproj
                     in settings.IMPUTE_RASTERS
                     if rname == rastername][0]
            g1 = stand.geometry_final.transform(rproj, clone=True)
            if not raster.is_valid:
                raise Exception("Raster is not valid: %s" % raster)
            # only need 33% coverage to include pixel, helps with small stands
            stats = zonal_stats(g1, raster, pixprop=0.33)  
            cache.set(key, stats, 60 * 60 * 24 * 365)
        return stats

    elevation = aspect = slope = cost = None

    # elevation
    data = get_raster_stats(stand, 'elevation')
    if data:
        elevation = data.avg

    # aspect
    cos = get_raster_stats(stand, 'cos_aspect')
    sin = get_raster_stats(stand, 'sin_aspect')
    if cos and sin:
        result = None
        if cos and sin and cos.sum and sin.sum:
            avg_aspect_rad = math.atan2(sin.sum, cos.sum)
            result = math.degrees(avg_aspect_rad) % 360
        aspect = result

    # slope
    data = get_raster_stats(stand, 'slope')
    if data:
        slope = data.avg

    # cost
    data = get_raster_stats(stand, 'cost')
    if data:
        cost = data.avg

    # stuff might have changed, we dont want a wholesale update of all fields!
    # use the timestamp to make sure we don't clobber a more recent request
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE "trees_stand"
        SET "elevation" = %s, "slope" = %s, "aspect" = %s, "cost" = %s, "rast_savetime" = %s
        WHERE "trees_stand"."id" = %s
        AND "trees_stand"."rast_savetime" < %s;
    """, [elevation, slope, aspect, cost, savetime,
          stand_id,
          savetime])
    transaction.commit_unless_managed()

    stand.invalidate_cache()

    res = {'stand_id': stand_id, 'elevation': elevation, 'aspect': aspect, 'slope': slope, 'cost': cost}

    if None in [elevation, aspect, slope, cost]:
        raise Exception("At least one raster is NULL for this geometry. %s" % res)
     
    return res


@task(max_retries=5, default_retry_delay=5)  # retry up to 5 times, 5 seconds apart
def impute_nearest_neighbor(stand_results, savetime):
    # import here to avoid circular dependencies
    from trees.models import Stand, IdbSummary
    from trees.plots import get_nearest_neighbors

    # you can pass the output of impute_rasters OR a stand id
    try:
        stand_id = stand_results['stand_id']
    except TypeError:
        stand_id = int(stand_results)

    stand = Stand.objects.get(id=stand_id)

    # Do we have the required attributes yet?
    if not (stand.strata and stand.elevation and stand.aspect and stand.slope and stand.geometry_final):
        # if not, retry it
        exc = Exception("Cant run nearest neighbor; missing required attributes.")
        raise impute_nearest_neighbor.retry(exc=exc)

    print "imputing nearest neighbor for %d" % stand_id

    stand_list = stand.strata.stand_list
    # assume stand_list comes out as a string?? TODO JSONField acting strange?
    # stand_list = json.loads(stand_list)
    geom = stand.geometry_final.transform(4326, clone=True)
    site_cond = {
        'latitude_fuzz': geom.centroid[1],
        'longitude_fuzz': geom.centroid[0],
    }
    if stand.aspect:
        site_cond['calc_aspect'] = stand.aspect
    if stand.elevation:
        site_cond['elev_ft'] = stand.elevation
    if stand.slope:
        site_cond['calc_slope'] = stand.slope
    weight_dict = stand.default_weighting
    ps, num_candidates = get_nearest_neighbors(
        site_cond, stand_list['classes'], weight_dict, k=5)

    # Take the top match
    cond_id = int(ps[0].name)

    # just confirm that it exists
    IdbSummary.objects.get(cond_id=cond_id)

    # update the database
    # stuff might have changed, we dont want a wholesale update of all fields!
    # use the timestamp to make sure we don't clobber a more recent request
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE "trees_stand"
        SET "cond_id" = %s, "nn_savetime" = %s
        WHERE "trees_stand"."id" = %s
        AND "trees_stand"."nn_savetime" < %s;
    """, [cond_id, savetime,
          stand_id,
          savetime])
    transaction.commit_unless_managed()

    stand.invalidate_cache()

    return {'stand_id': stand_id, 'cond_id': cond_id}


@task(max_retries=5, default_retry_delay=5)  # retry up to 5 times, 5 seconds apart
def schedule_harvest(scenario_id):
    # import here to avoid circular dependencies
    from trees.models import Scenario
    import time
    from celery import current_task

    try:
        scenario = Scenario.objects.get(id=scenario_id)
    except:
        raise schedule_harvest.retry()

    print "Calculating schedule for %s" % scenario_id
    current_task.update_state(state='PROGRESS', meta={'current': 50})
    time.sleep(2)

    # TODO prep scheduler, run it, parse the outputs
    d = {}

    # TODO Randomness is random
    import math
    import random
    a = range(0, 100)
    rsamp = [(math.sin(x) + 1) * 10.0 for x in a]

    # Stand-level outputs
    # Note the data structure for stands is different than properties
    # (stands are optimized for openlayers map while property-level works with jqplot)
    for stand in scenario.stand_set():
        c = random.randint(0, 90)
        t = random.randint(0, 90)
        carbon = rsamp[c:c + 6]
        timber = rsamp[t:t + 6]
        d[stand.pk] = {
            "years": range(2020, 2121, 20),
            "carbon": [
                carbon[0],
                carbon[1],
                carbon[2],
                carbon[3],
                carbon[4],
                carbon[5],
            ],
            "timber": [
                timber[0],
                timber[1],
                timber[2],
                timber[3],
                timber[4],
                timber[5],
            ]
        }

    # Property-level outputs
    # note the '__all__' key
    def scale(data):
        # fake data for ~3500 acres, adjust for size
        sf = 3500.0 / scenario.input_property.acres
        return [x / sf for x in data]

    carbon_alt = scale([338243.812, 631721, 775308, 792018, 754616])
    timber_alt = scale([1361780, 1861789, 2371139, 2613845, 3172212])

    carbon_biz = scale([338243, 317594, 370360, 354604, 351987])
    timber_biz = scale([2111800, 2333800, 2982600, 2989000, 2793700])

    if scenario.input_target_carbon:
        carbon = carbon_alt
        timber = timber_alt
    else:
        carbon = carbon_biz
        timber = timber_biz
    if scenario.name.startswith("Grow"):
        carbon = [c * 1.5 for c in carbon_alt]
        carbon[0] = carbon_alt[0]
        carbon[-2] = carbon_alt[-2] * 1.6
        carbon[-1] = carbon_alt[-1] * 1.7
        timber = [1, 1, 1, 1, 1]

    d['__all__'] = {
        "carbon": [
            ['2010-08-12 4:00PM', carbon[0]],
            ['2035-09-12 4:00PM', carbon[1]],
            ['2060-10-12 4:00PM', carbon[2]],
            ['2085-12-12 4:00PM', carbon[3]],
            ['2110-12-12 4:00PM', carbon[4]],
        ],
        "timber": [
            ['2010-08-12 4:00PM', timber[0]],
            ['2035-09-12 4:00PM', timber[1]],
            ['2060-10-12 4:00PM', timber[2]],
            ['2085-12-12 4:00PM', timber[3]],
            ['2110-12-12 4:00PM', timber[4]],
        ]
    }

    datemod = datetime.datetime.now()

    # update the database
    # stuff might have changed, we dont want a wholesale update of all fields!
    # use the timestamp to make sure we don't clobber a more recent request
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE "trees_scenario"
        SET "output_scheduler_results" = %s, "date_modified" = %s
        WHERE "trees_scenario"."id" = %s
    """, [json.dumps(d), datemod,
          scenario_id])
    transaction.commit_unless_managed()

    return {'scenario_id': scenario_id, 'output_scheduler_results': d}


@task()
def sweep_for_errors():
    print "Here we go..."
    from trees.models import Stand
    wierdos = []
    for stand in Stand.objects.all():
        if not stand.collection:
            wierdos.append((stand.uid, "Does not have a collection"))
            continue
    print wierdos
    return wierdos
