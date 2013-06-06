from celery import task
from django.core.cache import cache
import json
import datetime
import random


@task(max_retries=5, default_retry_delay=5)  # retry up to 5 times, 5 seconds apart
def impute_rasters(stand_id, savetime):
    # import here to avoid circular dependencies
    from trees.models import Stand
    from django.conf import settings
    from madrona.raster_stats.models import RasterDataset, zonal_stats
    import math

    try:
        stand_qs = Stand.objects.filter(id=stand_id)
        stand = stand_qs[0]
    except (Stand.DoesNotExist, IndexError):
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
    stand_qs.filter(rast_savetime__lt=savetime).update(
        elevation=elevation,
        slope=slope,
        aspect=aspect,
        cost=cost,
        rast_savetime=savetime
    )

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

    try:
        stand_qs = Stand.objects.filter(id=stand_id)
        stand = stand_qs[0]
    except (Stand.DoesNotExist, IndexError):
        exc = Exception("Cant run nearest neighbor; Stand %s does not exist." % stand_id)
        raise impute_nearest_neighbor.retry(exc=exc)

    # Do we have the required attributes yet?
    if not (stand.strata and stand.elevation and stand.aspect and stand.slope and stand.geometry_final):
        # if not, retry it
        exc = Exception("Cant run nearest neighbor; missing required attributes.")
        raise impute_nearest_neighbor.retry(exc=exc)

    # get variant code
    variant = stand.collection.variant.code

    print "imputing nearest neighbor for %d" % stand_id

    stand_list = stand.strata.stand_list
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
    if stand.strata.search_age:
        site_cond['stand_age'] = float(stand.strata.search_age)

    weight_dict = None  # take the default defined in plots.py
    ps, num_candidates = get_nearest_neighbors(
        site_cond, stand_list['classes'], variant=variant,
        weight_dict=weight_dict, k=2
    )

    # Take the top match
    cond_id = int(ps[0].name)

    # just confirm that it exists
    # TODO confirm that cond_id exists in the fvsaggregate table
    IdbSummary.objects.get(cond_id=cond_id)

    # update the database
    # stuff might have changed, we dont want a wholesale update of all fields like save()
    # use the timestamp to make sure we don't clobber a more recent request
    stand_qs.filter(nn_savetime__lt=savetime).update(cond_id=cond_id, nn_savetime=savetime)

    stand.invalidate_cache()

    return {'stand_id': stand_id, 'cond_id': cond_id}


@task(max_retries=5, default_retry_delay=5)  # retry up to 5 times, 5 seconds apart
def schedule_harvest(scenario_id):
    # import here to avoid circular dependencies
    from trees.models import Scenario, ScenarioNotRunnable
    import time
    from celery import current_task

    try:
        scenario_qs = Scenario.objects.filter(id=scenario_id)
        scenario = scenario_qs[0]
    except:
        raise schedule_harvest.retry()

    print "Calculating schedule for %s" % scenario_id
    current_task.update_state(state='PROGRESS', meta={'current': 50})
    time.sleep(1)

    #
    # Populate ScenarioStands
    #
    # TODO implement the actual spatial identity operation
    #
    # INSTEAD, just fake it by copying over the stands 1:1

    # from trees.utils import create_scenariostands
    # scenariostands = create_scenariostands(scenario)
    # might raise ScenarioNotRunnable, retry

    from trees.utils import fake_scenariostands
    try:
        scenariostands = fake_scenariostands(scenario)
    except ScenarioNotRunnable:
        raise schedule_harvest.retry(max_retries=2)

    #
    # Determine offsets
    #
    # TODO prep scheduler, run it, parse the outputs
    #
    # INSTEAD just assign random offset to every scenariostand

    # construct scheduler results dict eventually stored as output_scheduler_results
    # (not used currently except to check scenario status so it must exist)
    offsets = {}
    for sstand in scenariostands:
        random_offset = random.randint(0, 4)
        offsets[sstand.id] = random_offset
        sstand.offset = random_offset
        sstand.save()
    # Update the offset on the scenariostands directly
    # scenariostands.update(offset=0)

    #
    # update the database
    #
    # stuff might have changed, we dont want a wholesale update of all fields!
    # use the timestamp to make sure we don't clobber a more recent request
    datemod = datetime.datetime.now()
    scenario_qs.update(output_scheduler_results=json.dumps(offsets), date_modified=datemod)

    cache.delete('Taskid_%s' % scenario.uid)

    return {'scenario_id': scenario_id, 'output_scheduler_results': offsets}


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
