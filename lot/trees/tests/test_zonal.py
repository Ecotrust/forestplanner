import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################e
from django.contrib.gis.gdal import DataSource
from trees.utils import terrain_zonal

if __name__ == "__main__":
    shp = os.path.join(thisdir, 'data', 'test_shapes2.shp')
    ds = DataSource(shp) 
    lyr = ds[0]
    for feat in lyr:
    	print feat['id'], terrain_zonal(feat.geom)


