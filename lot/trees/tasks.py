from celery.task import task
from madrona.features import get_feature_by_uid
from madrona.raster_stats.models import zonal_stats, RasterDataset
from trees.models import ImputedData

@task
def impute(uid, raster_name, raster_proj4=None, force=False):
    """
    It seems wasteful to re-SELECT the feature and raster each time
    TODO - Make persistent/global or otherwise reduce number of queries 

    Aspect is a spectial case since it involves trig on two derivative rasters
    """
    feature = get_feature_by_uid(uid)
    orig_geom = feature.geometry_final
    if raster_proj4:
        geom = orig_geom.transform(raster_proj4, clone=True)

    save = False
    result = None
    
    try:
        raster = RasterDataset.objects.get(name=raster_name)
        if not raster.is_valid:
            raise Exception(raster.filepath + " is not a valid rasterdataset")
    except:
        impute.update_state(state="RASTERNOTFOUND")
        return None

    if force:
        stats = zonal_stats(geom, raster, read_cache = False)
    else:
        stats = zonal_stats(geom, raster)
    
    if raster_name in ['cos_aspect','sin_aspect']:  # aspect trig is special case
        result = stats.sum
    elif raster_name in ['gnn']: # gnn, we want the most common value
        #TODO ... may need to do something fancier here
        result = stats.mode
    else:
        result = stats.avg

    if result is None:
        impute.update_state(state="ZONALNULL")
        return None

    imputed_data, created = ImputedData.objects.get_or_create(raster=raster, feature=feature) 
    imputed_data.val = result 
    imputed_data.save()
    return result
