import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
import numpy as np
from django.contrib.gis.geos import GEOSGeometry
import math
from trees.models import IdbSummary
from scipy.spatial import KDTree
'''
    plot_id = models.BigIntegerField(null=True, blank=True)
    cond_id = models.BigIntegerField(null=True, blank=True)
    sumofba_ft2 = models.FloatField(null=True, blank=True)
    avgofba_ft2_ac = models.FloatField(null=True, blank=True)
    avgofht_ft = models.FloatField(null=True, blank=True)
    avgoftpa = models.FloatField(null=True, blank=True)
    avgofdbh_in = models.FloatField(null=True, blank=True)
    state_name = models.CharField(max_length=40, blank=True)
    county_name = models.CharField(max_length=100, blank=True)
    halfstate_name = models.CharField(max_length=100, blank=True)
    forest_name = models.CharField(max_length=510, blank=True)
    acres = models.FloatField(null=True, blank=True)
    acres_vol = models.FloatField(null=True, blank=True)
    fia_forest_type_name = models.CharField(max_length=60, blank=True)
    latitude_fuzz = models.FloatField(null=True, blank=True)
    longitude_fuzz = models.FloatField(null=True, blank=True)
    aspect_deg = models.IntegerField(null=True, blank=True)
    stdevofaspect_deg = models.FloatField(null=True, blank=True)
    firstofaspect_deg = models.IntegerField(null=True, blank=True)
    slope = models.IntegerField(null=True, blank=True)
    stdevofslope = models.FloatField(null=True, blank=True)
    avgofslope = models.FloatField(null=True, blank=True)
    elev_ft = models.IntegerField(null=True, blank=True)
    fvs_variant = models.CharField(max_length=4, blank=True)
    site_species = models.IntegerField(null=True, blank=True)
    site_index_fia = models.IntegerField(null=True, blank=True)
    plant_assoc_code = models.CharField(max_length=20, blank=True)
    countofsubplot_id = models.BigIntegerField(null=True, blank=True)
    qmd_hwd_cm = models.FloatField(null=True, blank=True)
    qmd_swd_cm = models.FloatField(null=True, blank=True)
    qmd_tot_cm = models.FloatField(null=True, blank=True)
    calc_aspect = models.IntegerField(null=True, blank=True)
    calc_slope = models.IntegerField(null=True, blank=True)
    stand_size_class = models.IntegerField(null=True, blank=True)
    site_class_fia = models.IntegerField(null=True, blank=True)
    stand_age_even_yn = models.CharField(max_length=2, blank=True)
    stand_age = models.IntegerField(null=True, blank=True)
    for_type = models.IntegerField(null=True, blank=True)
    for_type_secdry = models.IntegerField(null=True, blank=True)
    for_type_name = models.CharField(max_length=60, blank=True)
    for_type_secdry_name = models.CharField(max_length=60, blank=True)
'''
 
# TODO 
'''
Recreate idbsummary table: standard units, left join with GNN plotsummary and pull in relevant cols
Put into util function
create a view
Create a testing interface
Hook into "refine veg" interface
'''


'''
Join Query:

select plot_id, idb_plot_id, state_name, county_name from idb_summary left join sppsz_attr_all
ON idb_summary.plot_id = sppsz_attr_all.idb_plot_id where idb_plot_id is null;
'''


##############
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

search_params = input_params.copy()

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

keys = search_params.keys()
for sp in keys:
    if sp not in ['aspect', 'geographic']:
        categories[sp+"__isnull"] = False

EQD = 3786 # World Equidistant Cylindrical (Sphere) 
stand_centroid = GEOSGeometry('SRID=4326;POINT(%f %f)' % search_params['geographic'])
stand_centroid.transform(EQD)

def angular_diff(x,y):
    '''
    input: two angles in degrees
    output: absolute value of the angular difference in degrees
    '''
    x = math.radians(x)
    y = math.radians(y)
    return math.fabs(math.degrees(min(y-x, y-x+2*math.pi, y-x-2*math.pi, key=abs)))

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
candidates = len(plotsummaries)
if candidates == 0:
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

print
print input_params
print
print "Top 5 (out of", candidates, "candidates)"
top = zip(plots, distances)
for t in top:
    plotidx = t[0]
    plot = plotsummaries[plotidx]
    plot.__dict__['aspect'] = plot.calc_aspect
    plot.__dict__['geographic'] = "%s %s" %  (plot.latitude_fuzz, plot.longitude_fuzz)

    print "plot", ' '.join([x+":"+str(plot.__dict__[x]) for x in search_params.keys()]), 'distance:', t[1]
