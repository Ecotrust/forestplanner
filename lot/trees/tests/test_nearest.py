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

if __name__ == "__main__":

    stand_list = [
        ('Douglas-fir', 5, 10, 100),

        # ('Douglas-fir', 6, 10, 110),
        # ('Red alder', 2, 6, 230),
    ]

    variant = 'PN'

    # siskyou nt forest
    site_cond = {
        'calc_aspect': 278.2,
        'elev_ft': 1338.0,
        'latitude_fuzz': 42.394,
        'longitude_fuzz': -123.882,
        'calc_slope': 59.5,
        'stand_age': 15.0
    }

    # default is defined in plots.py
    # weight_dict = {
    #     'TOTAL_PCTBA': 10,
    #     'PLOT_BA': 10,
    #     'NONSPEC_BA': 10,
    #     'NONSPEC_TPA': 10,
    #     'TOTAL_TPA': 10,
    #     'calc_slope': 0.2,
    #     'calc_aspect': 0.5,
    #     'elev_ft': 0.7,
    # }
    weight_dict = None

    ps, num_candidates = get_nearest_neighbors(
        site_cond, stand_list, variant, weight_dict, k=19)

    print
    print stand_list
    print
    print "Candidates: ", num_candidates
    print
    from trees.models import TreeliveSummary
    for pseries in ps:
        print pseries.name, pseries['_certainty']  # "BA::", pseries['PLOT_BA'], pseries['NONSPEC_TPA']
        for tree in TreeliveSummary.objects.filter(cond_id=pseries.name):
            print tree
        print
    print
