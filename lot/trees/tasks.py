from celery import task
import json


@task()
def impute_rasters(stand_id):
    # import here to avoid circular dependencies
    from trees.models import Stand
    from django.conf import settings
    from madrona.raster_stats.models import RasterDataset, zonal_stats
    import math

    stand = Stand.objects.get(id=stand_id)
    print "imputing raster stats for %d" % stand_id

    def get_raster_stats(stand, rastername):
        try:
            raster = RasterDataset.objects.get(name=rastername)
        except RasterDataset.DoesNotExist:
            return None
        rproj = [rproj for rname, rproj
                 in settings.IMPUTE_RASTERS
                 if rname == rastername][0]
        g1 = stand.geometry_final
        g2 = g1.transform(rproj, clone=True)
        if not raster.is_valid:
            raise Exception("Raster is not valid: %s" % raster)
        stats = zonal_stats(g2, raster)
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
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""UPDATE "trees_stand"
        SET "elevation" = %s, "slope" = %s, "aspect" = %s, "cost" = %s
        WHERE "trees_stand"."id" = %s;
    """, [elevation, slope, aspect, cost,
          stand_id])
    transaction.commit_unless_managed()
    # alternative with django 1.5:
    # update only the fields that we've calculated
    # save(update_fields=['elevation', 'slope', 'aspect'])

    stand.invalidate_cache()

    return {'stand_id': stand_id, 'elevation': elevation, 'aspect': aspect, 'slope': slope}


@task()
def impute_nearest_neighbor(stand_results):
    # import here to avoid circular dependencies
    from trees.models import Stand, IdbSummary
    from trees.plots import get_nearest_neighbors

    # you can pass the output of impute_rasters OR a stand id
    try:
        stand_id = stand_results['stand_id']
    except TypeError:
        stand_id = int(stand_results)

    stand = Stand.objects.get(id=stand_id)
    print "imputing nearest neighbor for %d" % stand_id

    stand_list = stand.strata.stand_list
    # assume stand_list comes out as a string?? TODO JSONField acting strange?
    stand_list = json.loads(stand_list)
    site_cond = {
        'latitude_fuzz': stand.geometry_final.centroid[0],
        'longitude_fuzz': stand.geometry_final.centroid[1],
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

    cond_id = int(ps[0].name)

    # just confirm that it exists
    IdbSummary.objects.get(cond_id=cond_id)

    # update the database
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""UPDATE "trees_stand"
        SET "cond_id" = %s
        WHERE "trees_stand"."id" = %s;
    """, [cond_id, stand_id])
    transaction.commit_unless_managed()

    stand.invalidate_cache()

    return {'stand_id': stand_id, 'cond_id': cond_id}
