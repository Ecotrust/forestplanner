import os
from django.core.management.base import BaseCommand, AppCommand
from optparse import make_option
from django.conf import settings
from django.contrib.auth.models import User
from trees.models import Stand, ForestProperty
from trees.utils import StandImporter

class Command(BaseCommand):
    help = 'Imports shapefile as stands in the demo account'
    args = '[shp_path]'

    def handle(self, shp_path, **options):
        assert os.path.exists(shp_path)

        try:
            user = User.objects.get(username='demo')
        except User.DoesNotExist:
            user = User.objects.create_user('demo', 'mperry@madrona.org', password='demo')

        prop1, created = ForestProperty.objects.get_or_create(user=user, name='Demo Property')
        [x.delete() for x in prop1.feature_set()]
        prop1.save()

        s = StandImporter(prop1)
        s.import_ogr(shp_path) 

        print "%d stands imported from %s" % (len(prop1.feature_set()), shp_path)
