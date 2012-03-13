from celery.task import task
from madrona.features import get_feature_by_uid
from madrona.raster_stats.models import zonal_stats, RasterDataset


@task
def impute(uid, raster_name, raster_proj4=None):
    """
    It seems wasteful to re-SELECT the feature and raster each time
    TODO - Make persistent/global or otherwise reduce number of queries 
    """
    feature = get_feature_by_uid(uid)
    save = False
    result = None
   
    try:
        raster = RasterDataset.objects.get(name=raster_name)
    except:
        raster = None

    if raster_name == 'elevation' and raster:
        geom = feature.geometry_final
        if raster_proj4:
            geom = geom.transform(raster_proj4, clone=True)
        stats = zonal_stats(geom, raster)
        result = stats.avg
        feature.imputed_elevation = result 
        save = True

    if save:
        feature.save(impute=False)

    return result
