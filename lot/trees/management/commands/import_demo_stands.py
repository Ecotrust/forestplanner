import os
from django.core.management.base import BaseCommand, AppCommand
from optparse import make_option
from django.conf import settings
from django.contrib.auth.models import User
from trees.models import Stand, ForestProperty
from trees.utils import StandImporter

from shapely.geometry import Point
from shapely import wkt, wkb
from shapely.ops import cascaded_union
from django.contrib.gis.gdal import DataSource

class Command(BaseCommand):
    help = 'Imports shapefile as stands in the demo account'
    args = '[shp_path]'

    def handle(self, shp_path, **options):
        assert os.path.exists(shp_path)

        try:
            user = User.objects.get(username='demo')
        except User.DoesNotExist:
            user = User.objects.create_user('demo', 'mperry@madrona.org', password='demo')

        ds = DataSource(shp_path)
        layer = ds[0]
        
        if layer.srs.srid != settings.GEOMETRY_DB_SRID:
            good_proj = raw_input('Are you sure this shapefile is in Mercator\n? ')
            if good_proj.lower() not in ['y','yes']:
                raise Exception("Shapefile must be Web Mercator projection")

        namefld = raw_input('What is your `name` field? \n Choices: \n %s \n? ' % layer.fields)
        if namefld not in layer.fields:
            raise Exception(namefld + " is not a valid field name for this dataset")

        print "Calculating property outline from stands..."
        stands = []
        for feature in layer:
            stands.append(wkt.loads(feature.geom.wkt))
        casc = cascaded_union(stands)
        
        print "Creating Property..."
        prop1, created = ForestProperty.objects.get_or_create(user=user, name=layer.name, geometry_final=casc.wkt)
        [x.delete() for x in prop1.feature_set()]
        prop1.save()

        print "Import stands..."
        field_mapping = {'name': namefld}
        s = StandImporter(prop1)
        s.import_ogr(shp_path, field_mapping) 

        print "Pre-imputing stands..."
        stands = prop1.feature_set()
        n = 0
        for stand in stands:
            n += 1
            print '\t', stand.name
            a = stand.geojson

        print "%d stands imported from %s" % (n, shp_path)
