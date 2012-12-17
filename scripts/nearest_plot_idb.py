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


def nearest_plot(categories, input_params, weight_dict):
    search_params = input_params.copy()
    keys = search_params.keys()

    for sp in keys:
        if sp not in ['aspect', 'geographic']:
            categories[sp+"__isnull"] = False

    EQD = 3786 # World Equidistant Cylindrical (Sphere) 
    stand_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % search_params['geographic'])
    stand_centroid.transform(EQD)

    def plot_attrs(ps, keys):
        vals = []
        for attr in keys:
            if attr == 'aspect':
                angle = angular_diff(ps.calc_aspect, input_params['aspect'])
                vals.append(angle)
                search_params['aspect'] = 0 # anglular difference to self is 0
            elif attr == 'geographic':
                plot_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % (ps.longitude_fuzz, ps.latitude_fuzz))
                plot_centroid.transform(EQD)
                distance = stand_centroid.distance(plot_centroid)
                vals.append(distance)
                search_params['geographic'] = 0 # distance to self is 0
            else:
                vals.append(ps.__dict__[attr])
        return vals

    weights = np.ones(len(keys))
    for i in range(len(keys)):
        key = keys[i]
        if key in weight_dict:
            weights[i] = weight_dict[key]

    plotsummaries = list(IdbSummary.objects.filter(**categories))
    psar = [plot_attrs(ps, keys) for ps in plotsummaries]
    querypoint = np.array([float(search_params[attr]) for attr in keys])

    rawpoints = np.array(psar) 
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
    result = tree.query(querypoints, k=5)
    distances = result[0][0]
    plots = result[1][0]

    top = zip(plots, distances)
    return [plotsummaries[t[0]] for t in top], num_candidates


def potential_minmax(categories, weight_dict):
    ps = IdbSummary.objects.filter(**categories)
    keys = [k for k in weight_dict.keys() if k not in ['aspect','geographic']] # TODO 
    args = [Min(k) for k in keys] + [Max(k) for k in keys] 
    return ps.aggregate(*args) #Min('elev_ft'), Max('elev_ft'))

if __name__ == "__main__":
 
    categories = {
        'for_type_name': 'Douglas-fir', 
        'for_type_secdry_name': 'Red alder', 
    }

    input_params = {
        'qmd_hwd_cm': 20,
        'elev_ft': 1279,
        'aspect': 45, # special case
        'geographic': (-123, 46), # special case
        'calc_slope': 15,
        'sumofba_ft2': 0,
        'avgofba_ft2_ac': 0,
        'avgofht_ft': 80,
        'avgoftpa': 20,
        'avgofdbh_in': 12,
    }

    # weighting
    # no key or 1 implies standard weighting 
    # > 1 implies more importance for that variable
    weight_dict = {
        'qmd_hwd_cm': 5,
        'elev_ft': 1,
        'aspect': 1,
        'geographic': 1,
        'calc_slope': 1,
        'sumofba_ft2': 0,
        'avgofba_ft2_ac': 0,
        'avgofht_ft': 1,
        'avgoftpa': 1,
        'avgofdbh_in': 1,
    } 

    print potential_minmax(categories, weight_dict)
    top, num_candidates = nearest_plot(categories, input_params, weight_dict)

    print "Top 5 (out of", num_candidates, "candidates)"
    for plot in top:
        plot.__dict__['aspect'] = plot.calc_aspect
        plot.__dict__['geographic'] = "%s %s" %  (plot.latitude_fuzz, plot.longitude_fuzz)
        print ' '.join([x+":"+str(plot.__dict__[x]) for x in input_params.keys()])

