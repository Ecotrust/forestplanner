import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################e
from trees.plots import get_nearest_neighbors
from trees.models import TreeliveSummary, IdbSummary
import glob
import json

if __name__ == "__main__":

    args = sys.argv[1:]

    for json_path in glob.glob(os.path.join(thisdir, "test_plots", "*.json")):

        if len(args) > 0:
            match = False
            for arg in args:
                if arg in json_path:
                    match = True
                    break
            if not match:
                print "\tskipping", json_path
                continue    

        print
        print "<" * 80
        print json_path

        txt = open(json_path, 'r').read()
        print txt
        # {
        #   "tree_list": [
        #     ["Douglas-fir", 2, 6, 100],
        #     ["Red alder", 2, 6, 230]
        #   ],
        #   "variant": "PN",
        #   "plot_attrs": {
        #     "calc_aspect": 278.2,
        #     "elev_ft": 1338.0,
        #     "latitude_fuzz": 42.394,
        #     "longitude_fuzz": -123.882,
        #     "calc_slope": 59.5,
        #     "stand_age": 15.0
        #   }
        # }

        print "-" * 80
        data = json.loads(txt)

        # default is defined in plots.py
        # # default weight dict
        # weight_dict = {
        #     'TOTAL_PCTBA': 10.0,
        #     'PLOT_BA': 5.0,
        #     'NONSPEC_BA': 10.0,
        #     'NONSPEC_TPA': 5.0,
        #     'TOTAL_TPA': 2.0,
        #     'stand_age': 10.0,
        #     'calc_slope': 0.5,
        #     'calc_aspect': 1.0,
        #     'elev_ft': 0.75,
        # }
        weight_dict = {
            'TOTAL_PCTBA': 10.0,
            'PLOT_BA': 5.0,
            'NONSPEC_BA': 10.0,
            'NONSPEC_TPA': 5.0,
            'TOTAL_TPA': 2.0,
            'stand_age': 25.0,
            'calc_slope': 0.5,
            'calc_aspect': 1.0,
            'elev_ft': 0.75,
        }

        ps, num_candidates = get_nearest_neighbors(
            data['plot_attrs'],
            data['tree_list'],
            data['variant'],
            weight_dict,
            k=3,
            verbose=True)

        print ".... Total Candidates: ", num_candidates
        print
        print "----- Top candidate"
        pseries = ps[0]
        cond_id = pseries.name
        print "ID::", cond_id,
        print "Certainty::", pseries['_certainty']
        print "NONSPEC_TPA::", pseries['NONSPEC_TPA']
        print "NONSPEC_BA::", pseries['NONSPEC_BA']
        print "PLOT_BA::", pseries['PLOT_BA']
        print "TOTAL_TPA::", pseries['TOTAL_TPA']
        print "TOTAL_PCTBA::", pseries['TOTAL_PCTBA']

        idb = IdbSummary.objects.get(cond_id=cond_id)
        print json.dumps({
            "calc_aspect": idb.calc_aspect,
            "elev_ft": idb.elev_ft,
            "latitude_fuzz": idb.latitude_fuzz,
            "longitude_fuzz": idb.longitude_fuzz,
            "calc_slope": idb.calc_slope,
            "stand_age": idb.stand_age
        }, indent=2)
        for tree in TreeliveSummary.objects.filter(cond_id=pseries.name):
            print tree
        print
        print ">" * 80
