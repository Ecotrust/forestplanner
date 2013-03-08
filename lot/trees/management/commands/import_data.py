import os
import subprocess
from django.db import connection
from django.core.management.base import BaseCommand
from django.core.management import call_command
from trees.models import IdbSummary, TreeliveSummary, County, FVSVariant, FVSSpecies
from madrona.raster_stats.models import RasterDataset
from urllib import urlretrieve


class Command(BaseCommand):
    help = 'Download and load essential datasets'
    args = '[type]'

    def handle(self, *args, **options):

        download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "fixtures", "downloads"))
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        fixtures = [
           ('http://labs.ecotrust.org/forestplanner/data/idbsummary.json.gz', IdbSummary),
           ('http://labs.ecotrust.org/forestplanner/data/county.json.gz', County),
           ('http://labs.ecotrust.org/forestplanner/data/fvsvariant.json.gz', FVSVariant),
           ('http://labs.ecotrust.org/forestplanner/data/fvsspecies.json.gz', FVSSpecies),
        ]

        #### Step 1: Fetch data bundles
        fname = os.path.join(download_dir, "terrain_rasters.tar.gz")
        if not os.path.exists(fname):  # TODO not
            print "Getting terrain raster data"
            url = "http://labs.ecotrust.org/forestplanner/data/terrain_rasters.tar.gz"
            urlretrieve(url, filename=fname)
        else:
            print "Skipping terrain raster download; tar.gz already exists"

        fname = os.path.join(download_dir, "treelive.tab")
        if not os.path.exists(fname):  # TODO not
            print "Getting treelive data"
            url = "http://labs.ecotrust.org/forestplanner/data/treelive.tab"
            urlretrieve(url, filename=fname)
        else:
            print "Skipping treelive download; .tab already exists"

        for url, klass in fixtures:
            fname = os.path.join(download_dir, url.split("/")[-1])
            if not os.path.exists(fname):
                print "Getting %s data" % klass.__name__
                urlretrieve(url, filename=fname)
            else:
                print "Skipping %s download; already exists" % klass.__name__

        #### Step 2: Process data

        os.chdir(download_dir)
        odirname = os.path.join(download_dir, "terrain")
        # unpack
        if not os.path.exists(odirname):
            print "Unpacking terrain rasters"
            fname = os.path.join(download_dir, "terrain_rasters.tar.gz")
            subprocess.check_output(['tar', '-xzvf', fname])
        else:
            print "terrain already unpacked"

        # install
        if RasterDataset.objects.all().count() < 6:
            print "Loading RasterDataset"
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'dem_swor2/hdr.adf'), type="continuous", name="elevation")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'asp_swor/hdr.adf'), type="continuous", name="aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'cos_aspect.tif'), type="continuous", name="cos_aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'sin_aspect.tif'), type="continuous", name="sin_aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'slp_swor/hdr.adf'), type="continuous", name="slope")
            # TODO cost raster - for now just use slope
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'slp_swor/hdr.adf'), type="continuous", name="cost")
        else:
            print "Skip loading RasterDataset data"

        fname = os.path.join(download_dir, "treelive.tab")
        if TreeliveSummary.objects.all().count() == 0:
            print "Loading TreeliveSummary data"
            cursor = connection.cursor()
            cursor.execute("""COPY treelive_summary
                   (CLASS_ID, PLOT_ID, COND_ID, VARNAME,
                    FIA_FOREST_TYPE_NAME, CALC_DBH_CLASS, CALC_TREE_COUNT, SumOfTPA, AvgOfTPA,
                    SumOfBA_FT2_AC, AvgOfBA_FT2_AC, AvgOfHT_FT, AvgOfDBH_IN, AvgOfAge_BH,
                    TOTAL_BA_FT2_AC, COUNT_SPECIESSIZECLASSES, PCT_OF_TOTALBA)
                FROM '%s' WITH NULL AS ''""" % fname)
            cursor.close()
        else:
            print "Skip loading TreeliveSummary data"

        for url, klass in fixtures:
            fname = os.path.join(download_dir, url.split("/")[-1])
            if klass.objects.all().count() == 0:
                print "Loading %s data" % klass.__name__
                call_command('loaddata', fname)
            else:
                print "Skip loading %s data" % klass.__name__
