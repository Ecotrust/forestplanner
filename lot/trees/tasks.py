from celery.task import task
from madrona.features import get_feature_by_uid
from madrona.raster_stats.models import zonal_stats, RasterDataset

@task
def impute(uid,raster):
    feature = get_feature_by_uid(uid)
    if raster == 'elevation':
        rast = RasterDataset.objects.get(name="elevation")
        geom = feature.geometry_final
        stats = zonal_stats(geom, rast)
        feature.imputed_elevation = stats.avg
    feature.save(impute=False)
