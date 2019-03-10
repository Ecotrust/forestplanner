from __future__ import absolute_import, unicode_literals
from celery import shared_task, Celery
from django.core.cache import cache
from django.conf import settings
import json
import datetime
import random
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lot.settings')

celery = Celery('tasks', broker=settings.CELERY_BROKER_URL)

DELAY = 0.5

@shared_task
def impute_rasters(stand_id, savetime):
    print("IMPUTE RASTERS CELERY!")
    # import here to avoid circular dependencies
    from trees.utils import terrain_zonal
    from trees.models import Stand
    from django.conf import settings

    try:
        stand_qs = Stand.objects.filter(id=stand_id)
        stand = stand_qs[0]
    except (Stand.DoesNotExist, IndexError):
        raise impute_rasters.retry()

    rproj = settings.TERRAIN_PROJ
    g1 = stand.geometry_final.transform(rproj, clone=True)

    # Either get cached zonal stats or generate it
    key = "terrain_zonal_%s" % (g1.wkt.__hash__())
    stats = cache.get(key)
    if stats is None:
        stats = terrain_zonal(g1)
        cache.set(key, stats, 60 * 60 * 24 * 365)
    elevation, slope, aspect, cost = stats

    # stuff might have changed, we dont want a wholesale update of all fields!
    # use the timestamp to make sure we don't clobber a more recent request
    stand_qs.filter(rast_savetime__lt=savetime).update(
        elevation=elevation,
        slope=slope,
        aspect=aspect,
        cost=cost,
        rast_savetime=savetime )

    stand.invalidate_cache()

    res = {'stand_id': stand_id, 'elevation': elevation, 'aspect': aspect, 'slope': slope, 'cost': cost}

    if None in [elevation, aspect, slope, cost]:
        raise Exception("At least one raster is NULL for this geometry. %s" % res)
    return res


@shared_task
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

    if stand.is_locked:
        if stand.cond_id != stand.locked_cond_id:
            # should never happen; fix it here
            stand_qs.filter(nn_savetime__lt=savetime).update(
                cond_id=stand.locked_cond_id, nn_savetime=savetime)
            stand.invalidate_cache()

        return {
            'stand_id': stand_id,
            'cond_id': stand.cond_id}

    # Do we have the required attributes yet?
    if not (stand.strata and stand.elevation and stand.aspect and stand.slope and stand.geometry_final):
        # if not, retry it
        exc = Exception("Cant run nearest neighbor; missing required attributes.")
        raise impute_nearest_neighbor.retry(exc=exc)

    # get variant code
    variant = stand.collection.variant.code

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

    # TODO confirm that cond_id exists in the idbsummary and fvsaggregate tables?

    # update the database
    # stuff might have changed, we don't want a wholesale update of all fields like save()
    # use the timestamp to make sure we don't clobber a more recent request
    stand_qs.filter(nn_savetime__lt=savetime).update(cond_id=cond_id, nn_savetime=savetime)

    stand.invalidate_cache()

    return {'stand_id': stand_id, 'cond_id': cond_id}


@shared_task
def schedule_harvest(scenario_id):
    # import here to avoid circular dependencies
    from trees.models import Scenario, ScenarioNotRunnable
    import time
    from celery import current_task

    try:
        scenario_qs = Scenario.objects.filter(id=scenario_id)
        scenario = scenario_qs[0]
    except Exception as e:
        raise schedule_harvest.retry()

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
        print("****************\n" * 20)
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
        if sstand.rx_internal_num == 1:
            # Special case, offset for rx=1 (Grow Only)
            # should always be zero
            random_offset = 0
        else:
            # Otherwise, randomly assign offset index, 0 to 4
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


@shared_task
def sweep_for_errors():
    print("Here we go...")
    from trees.models import Stand
    wierdos = []
    for stand in Stand.objects.all():
        if not stand.collection:
            wierdos.append((stand.uid, "Does not have a collection"))
            continue
    print(str(wierdos))
    return wierdos
