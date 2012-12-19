import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)

##############################
# TODO 
'''
create a utl
create a view
Create a testing interface
Hook into "refine veg" interface
'''
##############################
from trees.utils import potential_minmax, nearest_plots

if __name__ == "__main__":
 
    categories = {
        'for_type_name': 'Douglas-fir', 
        #'for_type_name': 'Red alder', 
    }

    input_params = {
        'age_dom': 40,
        'elev_ft': 1279,
        'calc_slope': 25,
        'calc_aspect': 225, 
        'longitude_fuzz': -123.0, 
        'latitude_fuzz': 43.0, 
    }

    # weighting
    # no key or 1 implies standard weighting 
    # > 1 implies more importance for that variable
    weight_dict = {
        # special cases
        'calc_aspect': 0, # ALWAYS ZERO
        'longitude_fuzz': 0, # ALWAYS ZERO
        'latitude_fuzz': 0, # ALWAYS ZERO
        '_geographic': 1,
        '_aspect': 1,

        # Site attrs
        'elev_ft': 1,
        'calc_slope': 1,

        # Optional
        'age_dom': 1,
    } 

    pmm = potential_minmax(categories, weight_dict)
    print pmm

    top, num_candidates = nearest_plots(categories, input_params, weight_dict, k=10)

    print weight_dict
    print 
    print '\t'.join([x.ljust(12) for x in input_params.keys()])
    print '\t'.join([str(x).ljust(12) for x in input_params.values()])
    print 

    print "Top matches (out of", num_candidates, "candidates)"
    for plot in top:
        print '\t'.join([str(plot.__dict__[x]).ljust(10) for x in input_params.keys()]), "\t", plot._kdtree_distance, "\t", plot._certainty, '\t', plot.for_type_name
