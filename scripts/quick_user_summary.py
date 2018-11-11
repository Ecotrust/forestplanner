import sys
import os
appdir = '/usr/local/apps/forestplanner/lot'
sys.path.append(appdir)
os.chdir(appdir)
sitedir = '/usr/local/venv/lot/lib/python2.7/site-packages'
sys.path.append(sitedir)
import settings
from django.core.management import setup_environ
setup_environ(settings)
##############################

from trees.models import ForestProperty, Stand, County
from django.contrib.auth.models import User
from collections import defaultdict
import json

STAND_CUTOFF = 800
PROP_CUTOFF = 10000


print "Properties: ", ForestProperty.objects.all().count()
print "Stands: ", Stand.objects.all().count()
print "Users: ", User.objects.all().count()
print

print "----- Users -----------------------------------------------"
print "username,email,staff,num_properties"
for user in User.objects.all():
    numprop = user.trees_forestproperty_related.all().count()
    print ",".join(str(x) for x in [user.username, user.email, user.is_staff or user.is_superuser, numprop])
print "----------------------------------------------------"
print


acres_prop = 0 
skipped = 0
county_summary = defaultdict(float)
for fp in ForestProperty.objects.all():
    acres = fp.acres
    loc = fp.location
    if acres and acres < PROP_CUTOFF:
        acres_prop += acres
        county_summary[loc] += acres
    else:
        skipped += 1

print "Acres of mapped property: %d (%d acre max cutoff)" % (acres_prop, PROP_CUTOFF)
print "\t skipped", skipped
#print "county,state,acres"
#for county, val in county_summary.items():
#    print ",".join([str(x) for x in [county[0], county[1], int(val)]])

cdict = { "type": "FeatureCollection", "features": [] }

for county in County.objects.filter(stname__in=['OR','WA']):
    cdict['features'].append(
    { "type": "Feature",
      "geometry": json.loads(county.geom.json),
      "properties": {
        "name": county.cntyname.title(),
        "state": county.stname,
        "acres_mapped": county_summary[(county.cntyname.title(), county.stname)]
      }
     })

out_json = "/tmp/test.json"
with open(out_json, 'w') as fh:
    fh.write(json.dumps(cdict, indent=2))
print "\t... geojson written to", out_json

acres_stand = 0
skipped = 0
for s in Stand.objects.all():
    try:
        acres = s.acres
    except:
        skipped += 1
        continue
    if acres and acres < STAND_CUTOFF:
        acres_stand += acres
    else:
        skipped += 1
print "Acres of mapped stands: %d (%d acre max cutoff)" % (acres_stand, STAND_CUTOFF)
print "\t skipped", skipped
