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

    for json_path in glob.glob(os.path.join(thisdir, "test_plots", "*3.json")):

        if len(args) > 0:
            match = False
            for arg in args:
                if arg in json_path:
                    match = True
                    break
            if not match:
                print("\tskipping", json_path)
                continue

        print(json_path)

        txt = open(json_path, 'r').read()
        print(txt)
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

        data = json.loads(txt)

        # default is defined in plots.py
        # default weight dict
        weight_dict = None

        ps, num_candidates = get_nearest_neighbors(
            data['plot_attrs'],
            data['tree_list'],
            data['variant'],
            weight_dict,
            k=20,
            verbose=True)

        print(".... Total Candidates: ", num_candidates)
        print("")
        print("----- Top candidate")
        pseries = ps[0]
        #print(pseries)
        cond_id = pseries.name
        print("ID::", cond_id)
        print("Certainty::", pseries['_certainty'])
        print("NN Distance::", pseries['_kdtree_distance'])
        print("NONSPEC_TPA::", pseries['NONSPEC_TPA'])
        print("NONSPEC_BA::", pseries['NONSPEC_BA'])
        print("PLOT_BA::", pseries['PLOT_BA'])
        print("TOTAL_TPA::", pseries['TOTAL_TPA'])
        print("TOTAL_PCTBA::", pseries['TOTAL_PCTBA'])

        idb = IdbSummary.objects.get(cond_id=cond_id)
        print("calc_aspect::", idb.calc_aspect)
        print("elev_ft::", idb.elev_ft)
        print("latitude_fuzz::", idb.latitude_fuzz)
        print("longitude_fuzz::", idb.longitude_fuzz)
        print("calc_slope::", idb.calc_slope)
        print("stand_age::", idb.stand_age)
        print("")

        orig_treelist = data['tree_list'][:]
        matched_treelist = dict([((x[0], x[1], x[2]), 0) for x in orig_treelist])


        for tree in TreeliveSummary.objects.filter(cond_id=pseries.name):
            # print(tree)
            # import ipdb; ipdb.set_trace()
            speced = False
            for tle in orig_treelist:
                if tle[0] == tree.fia_forest_type_name and \
                   tle[1] <= tree.calc_dbh_class and \
                   tle[2] > tree.calc_dbh_class:
                    matched_treelist[(tle[0],tle[1],tle[2])] += tree.sumoftpa
                    speced = True
                    break
            if not speced:
                matched_treelist[("" + tree.fia_forest_type_name,
                    tree.calc_dbh_class, tree.calc_dbh_class)] = tree.sumoftpa

        total_expected = 0
        total_observed = 0
        for k in sorted(matched_treelist.keys()):
            v = matched_treelist[k]
            orig_treedict =  dict([((x[0], x[1], x[2]), x[3]) for x in orig_treelist])
            try:
                expected =  orig_treedict[(k[0], k[1], k[2])]
            except KeyError:
                expected = 0
            total_observed += v
            total_expected += expected
            if expected == 0:
                startd = ''
            else:
                startd = '%s to' % int(k[1])
            print("%20s" % k[0], "%5s" % startd,  "%2s" % int(k[2]), '" ', "%3s" % int(v), 'tpa', "(expected %3s)" % expected)

        # print(orig_treedict)
        print("-" * 80)
        print(' ' * 31 , "%4s" % int(total_observed), 'tpa', "(expected %4s)" % total_expected )
