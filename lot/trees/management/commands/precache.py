import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from trees.models import ForestProperty, Stand, FVSVariant, ScenarioStand

class Command(BaseCommand):

    def handle(self, *args, **options):
        from trees.views import list_species_sizecls
        from django.test.client import RequestFactory

        print("Caching the species_sizecls.json responses...")
        for v in FVSVariant.objects.all():
            request = RequestFactory().get('/trees/variant/%s/species_sizecls.json' % v.id)
            list_species_sizecls(request, v.id)

        # from madrona.layer_manager.views import get_json
        # print("Caching the layer_manager response...")
        # request = RequestFactory().get('/layer_manager/layers.json')
        # get_json(request)

        print("Caching stand attrs...")
        for s in Stand.objects.all():
            s.geojson

        print("Caching forestproperty attrs...")
        for fp in ForestProperty.objects.all():
            fp.variant
            fp.location

        print("Caching scenariostand geojson...")
        for ss in ScenarioStand.objects.all():
            ss.geojson

        # print("Caching some tiles...")
        # sz = 6
        # nz = 8  # num zoom levels

        # zooms = [str(x) for x in range(sz,sz+nz)]

        # ex = [str(x) for x in settings.JS_OPTS['extent']]
        # extent = ' '.join([ex[1], ex[0], ex[3], ex[2]])

        # layers = [
        #     ('utfgrid', 'json'),
        #     ('planning_units', 'png'),
        # ]

        # tilecfg = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..','..','tile_config','tiles.cfg'))
        # for layer in layers:
        #     cmd = "tilestache-seed.py -c %s -l %s -e %s -b %s %s" % (tilecfg, layer[0], layer[1], extent, ' '.join(zooms[:-2]))
        #     print(cmd)
        #     os.popen(cmd)
