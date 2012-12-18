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
Lookup for field names/descriptions
create a view
Create a testing interface
Hook into "refine veg" interface
'''

##############################
import numpy as np
from django.contrib.gis.geos import GEOSGeometry
from trees.models import IdbSummary
from trees.utils import angular_diff
from scipy.spatial import KDTree
from django.db.models import Min, Max
import math


def nearest_plot(categories, input_params, weight_dict, k=5):
    search_params = input_params.copy()
    keys = search_params.keys()
    for sp in keys:
        categories[sp+"__isnull"] = False

    EQD = 3786 # World Equidistant Cylindrical (Sphere) 
    stand_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % (input_params['longitude_fuzz'], input_params['latitude_fuzz']))
    stand_centroid.transform(EQD)

    def plot_attrs(ps, keys):
        vals = []
        for attr in keys:
            vals.append(ps.__dict__[attr])

        # an additional special case
        angle = angular_diff(ps.calc_aspect, input_params['calc_aspect'])
        vals.append(angle)
        search_params['_aspect'] = 0 # anglular difference to self is 0

        # Deal with latlon, another special case
        plot_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % (ps.longitude_fuzz, ps.latitude_fuzz))
        plot_centroid.transform(EQD)
        distance = stand_centroid.distance(plot_centroid)
        vals.append(distance)
        search_params['_geographic'] = 0 # distance to self is 0
        return vals

    plotsummaries = list(IdbSummary.objects.filter(**categories))
    ps_attr_list= [plot_attrs(ps, keys) for ps in plotsummaries]
    
    # include our additional special cases
    keys.append('_aspect') 
    keys.append('_geographic')

    weights = np.ones(len(keys))
    for i in range(len(keys)):
        key = keys[i]
        if key in weight_dict:
            weights[i] = weight_dict[key]

    querypoint = np.array([float(search_params[attr]) for attr in keys])

    rawpoints = np.array(ps_attr_list) 
    num_candidates = len(plotsummaries)
    if num_candidates == 0:
        raise Exception("There are no candidate plots matching the categorical variables: %s" % categories)

    # Normalize to 100; linear scale
    multipliers = (100.0 / np.max(rawpoints, axis=0))
    # Apply weights
    multipliers = multipliers * weights
    # Apply multipliers
    allpoints = rawpoints * multipliers
    querypoint *= multipliers

    # Create tree and query it for nearest plot
    tree = KDTree(allpoints)
    querypoints = np.array([querypoint])
    result = tree.query(querypoints, k=k)
    distances = result[0][0]
    plots = result[1][0]

    top = zip(plots, distances)
    ps = []

    xs = [100 * x for x in weights if x > 0]
    squares = [x * x for x in xs]
    print squares
    print distances
    max_dist = math.sqrt(sum(squares)) # the real max 
    for t in top:
        p = plotsummaries[t[0]]
        p.__dict__['_kdtree_distance'] = t[1]
        p.__dict__['_uncertainty'] = (t[1] / max_dist) * len(squares) # increase uncertainty as the number of variables goes up?
        ps.append(p)
    return ps, num_candidates


def potential_minmax(categories, weight_dict):
    ps = IdbSummary.objects.filter(**categories)
    keys = [k for k in weight_dict.keys() if not k.startswith("_")]
    args = [Min(k) for k in keys] + [Max(k) for k in keys] 
    return ps.aggregate(*args)

if __name__ == "__main__":
 
    categories = {
        'for_type_name': 'Douglas-fir', 
        #'for_type_secdry_name': 'Red alder', 
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
    top, num_candidates = nearest_plot(categories, input_params, weight_dict, k=20)

    print weight_dict
    print 
    print '\t'.join([x.ljust(12) for x in input_params.keys()])
    print '\t'.join([str(x).ljust(12) for x in input_params.values()])
    print 


    print "Top matches (out of", num_candidates, "candidates)"
    for plot in top:
        print '\t'.join([str(plot.__dict__[x]).ljust(10) for x in input_params.keys()]), "\t", plot._kdtree_distance, "\t", plot._uncertainty
