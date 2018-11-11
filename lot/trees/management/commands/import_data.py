import os
import subprocess
from django.db import connection, transaction
from django.core.management.base import BaseCommand
from django.core.management import call_command
from trees.models import IdbSummary, TreeliveSummary, County, FVSVariant, FVSSpecies, ConditionVariantLookup, Rx, FVSAggregate
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
            ('http://labs.ecotrust.org/forestplanner/data/county.json.gz', County),
            ('http://labs.ecotrust.org/forestplanner/data/fvsspecies.json.gz', FVSSpecies),
            # fvs variant and rx are handled via initial_data.json fixture for trees app
            # fvsaggregate and others handled manually
            # See https://github.com/Ecotrust/forestplanner/wiki/Fixture-management
        ]

        #### Step 1: Fetch data bundles
        print
        print "Fetch data if not already existing in %s" % download_dir
        #
        # Rasters
        #
        fname = os.path.join(download_dir, "terrain_rasters.tar.gz")
        if not os.path.exists(fname):
            print "\tGetting terrain raster data"
            url = "http://labs.ecotrust.org/forestplanner/data/terrain_rasters.tar.gz"
            urlretrieve(url, filename=fname)
        else:
            print "\tSkipping terrain raster download; tar.gz already exists"

        #
        # Treelive
        #
        fname = os.path.join(download_dir, "treelive.tab")
        if not os.path.exists(fname):
            print "\tGetting treelive data"
            url = "http://labs.ecotrust.org/forestplanner/data/treelive.tab"
            urlretrieve(url, filename=fname)
        else:
            print "\tSkipping treelive download; .tab already exists"

        #
        # IdbSummary
        #
        fname = os.path.join(download_dir, "idb_summary.tsv")
        if not os.path.exists(fname):
            print "\tGetting idb_summary data"
            url = "http://labs.ecotrust.org/forestplanner/data/idb_summary.tsv"
            urlretrieve(url, filename=fname)
        else:
            print "\tSkipping idb_summary download; .tsv already exists"

        #
        # FVS Aggregate
        #
        fname = os.path.join(download_dir, "fvsaggregate.tsv.gz")
        unzipped = os.path.join(download_dir, "fvsaggregate.tsv")
        if not os.path.exists(unzipped):
            if not os.path.exists(fname):
                print "\tGetting FVS aggregate data"
                url = "http://labs.ecotrust.org/forestplanner/data/fvsaggregate.tsv.gz"
                urlretrieve(url, filename=fname)
            assert os.path.exists(fname)

            print "\tUnpacking FVS aggregate gzip file"
            subprocess.check_output(['gunzip', fname])
            assert os.path.exists(unzipped)
        else:
            print "\tSkipping fvsaggregate download; fvsaggregate.tsv already exists"

        #
        # Fixtures
        #
        for url, klass in fixtures:
            fname = os.path.join(download_dir, url.split("/")[-1])
            if not os.path.exists(fname):
                print "\tGetting %s data" % klass.__name__
                urlretrieve(url, filename=fname)
            else:
                print "\tSkipping %s download; already exists" % klass.__name__

        #### Step 2: Process data
        print
        print "Loading data if tables are empty"
        os.chdir(download_dir)
        odirname = os.path.join(download_dir, "terrain")
        # unpack
        if not os.path.exists(odirname):
            print "\tUnpacking terrain rasters"
            fname = os.path.join(download_dir, "terrain_rasters.tar.gz")
            subprocess.check_output(['tar', '-xzvf', fname])
        else:
            print "\tSkip unpacking terrain rasters; already unpacked"

        # install
        # Technically this is not necessary now that we've replaced starspan with python-rasterstats
        if RasterDataset.objects.all().count() < 6:
            print "\tLoading RasterDataset"
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'dem.tif'), type="continuous", name="elevation")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'aspect.tif'), type="continuous", name="aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'cos_aspect.tif'), type="continuous", name="cos_aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'sin_aspect.tif'), type="continuous", name="sin_aspect")
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'slope.tif'), type="continuous", name="slope")
            # TODO cost raster - for now just use slope
            RasterDataset.objects.get_or_create(filepath=os.path.join(odirname, 'slope.tif'), type="continuous", name="cost")
        else:
            print "\tSkip loading RasterDataset data"

        fname = os.path.join(download_dir, "treelive.tab")
        if TreeliveSummary.objects.all().count() == 0:
            print "\tLoading TreeliveSummary data"
            cursor = connection.cursor()
            cursor.execute("""COPY treelive_summary
                   (CLASS_ID, PLOT_ID, COND_ID, VARNAME,
                    FIA_FOREST_TYPE_NAME, CALC_DBH_CLASS, CALC_TREE_COUNT, SumOfTPA, AvgOfTPA,
                    SumOfBA_FT2_AC, AvgOfBA_FT2_AC, AvgOfHT_FT, AvgOfDBH_IN, AvgOfAge_BH,
                    TOTAL_BA_FT2_AC, COUNT_SPECIESSIZECLASSES, PCT_OF_TOTALBA)
                FROM '%s' WITH NULL AS ''""" % fname)
            transaction.commit_unless_managed()
            cursor.close()
        else:
            print "\tSkip loading TreeliveSummary data"

        fname = os.path.join(download_dir, "idb_summary.tsv")
        if IdbSummary.objects.all().count() == 0:
            print "\tLoading IdbSummary data"
            cursor = connection.cursor()
            cursor.execute("COPY idb_summary FROM '%s' WITH NULL AS ''" % fname)
            transaction.commit_unless_managed()
            cursor.close()
        else:
            print "\tSkip loading IdbSummary data"

        fname = os.path.join(download_dir, "fvsaggregate.tsv")
        if FVSAggregate.objects.all().count() == 0 and \
           ConditionVariantLookup.objects.all().count() == 0:
            print "\tLoading FVSAggregate data"
            cursor = connection.cursor()
            cursor.execute("""
                    COPY trees_fvsaggregate
                    FROM '%s'
                    WITH NULL AS ''
                """ % fname)
            transaction.commit_unless_managed()
            cursor.close()

            print "\tPopulating conditionvariantlookup table based on fvsaggregate table"
            cursor = connection.cursor()
            cursor.execute("""
                    INSERT INTO trees_conditionvariantlookup(cond_id, variant_code)
                    SELECT cond as cond_id, var as variant_code
                    FROM trees_fvsaggregate
                    GROUP BY cond, var
                """)
            transaction.commit_unless_managed()
            cursor.close()
        else:
            print "\tSkip loading FVSAggregate data"
            print "\tSkip populating conditionvariantlookup"

        for url, klass in fixtures:
            fname = os.path.join(download_dir, url.split("/")[-1])
            if klass.objects.all().count() == 0:
                print "\tLoading %s data" % klass.__name__
                call_command('loaddata', fname)
            else:
                print "\tSkip loading %s data" % klass.__name__
