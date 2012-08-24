import os
from django.core.management.base import BaseCommand, AppCommand, CommandError
from optparse import make_option
from django.conf import settings
from django.contrib.auth.models import User
from trees.models import Stand, ForestProperty
from trees.utils import StandImporter

from shapely.geometry import Point, Polygon
from shapely import wkt, wkb
from shapely.ops import cascaded_union
from django.contrib.gis.gdal import DataSource

class Command(BaseCommand):
    help = 'Imports shapefile as stands in the demo account'
    args = '[shp_path] [name_field] [property_name]'

    def handle(self, *args, **options):

        try: 
            shp_path = args[0]
            assert os.path.exists(shp_path)
        except (AssertionError, IndexError):
            raise CommandError("Specify shapefile and name field\ne.g. python manage.py import_demo_stands my_stands.shp NAMEFIELD \"My Property\"")

        ds = DataSource(shp_path)
        layer = ds[0]
        
        if layer.srs.srid != settings.GEOMETRY_DB_SRID:
            print "WARNING: Shapefile must be in Web Mercator. If it's not, the results will not be good."


        try: 
            namefld = args[1]
        except (IndexError):
            raise CommandError("Specify shapefile and name field\ne.g. python manage.py import_demo_stands my_stands.shp NAMEFIELD \"My Property\" \nChoice are %s" % (', '.join(layer.fields),))

        if namefld not in layer.fields:
            raise Exception(namefld + " is not a valid field name for this dataset \nChoices are: \n %s" % (', '.join(layer.fields),))

        try:
            property_name = args[2]
        except IndexError:
            property_name = layer.name

        try:
            user = User.objects.get(username='demo')
        except User.DoesNotExist:
            user = User.objects.create_user('demo', 'mperry@ecotrust.org', password='demo')

        print "Calculating property outline from stands..."
        stands = []
        for feature in layer:
            stands.append(wkt.loads(feature.geom.wkt))
        casc_poly = cascaded_union(stands)
        casc = Polygon(casc_poly.exterior)
        
        print "Creating Property..."
        prop1, created = ForestProperty.objects.get_or_create(user=user, name=property_name, geometry_final=casc.wkt)
        [x.delete() for x in prop1.feature_set()]
        prop1.save()

        print "Importing stands..."
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
