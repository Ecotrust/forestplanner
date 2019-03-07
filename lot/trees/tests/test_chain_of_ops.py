import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
import ipdb
import json
import time
from trees.models import Stand, Scenario, Strata, ForestProperty, ScenarioNotRunnable
from django.contrib.auth.models import User
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry
from shapely.ops import cascaded_union
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt


cntr = GEOSGeometry('SRID=3857;POINT(-13842474.0 5280123.1)')

NUM_STANDS = 2
geoms = []
for i in range(NUM_STANDS):
    cntr.set_x(cntr.x + 150)
    g1 = cntr.buffer(75)
    g1.transform(settings.GEOMETRY_DB_SRID)
    geoms.append(wkt.loads(g1.wkt))

casc_poly = cascaded_union(geoms)

if casc_poly.type == 'MultiPolygon':
    polys = []
    for c in casc_poly:
        interiors = [x for x in c.interiors if Polygon(x).area > settings.SLIVER_THRESHOLD]
        polys.append(Polygon(shell=c.exterior, holes=interiors))
elif casc_poly.type == 'Polygon':
    interiors = [x for x in casc_poly.interiors if Polygon(x).area > settings.SLIVER_THRESHOLD]
    polys = [Polygon(shell=casc_poly.exterior, holes=interiors)]

p1 = MultiPolygon(polys)

client = Client()
try:
    user = User.objects.get(username='test')
except User.DoesNotExist:
    user = User.objects.create_user('test', 'test@ecotrust.org', password='test')

client.login(username='test', password='test')

##### Step 0. Delete all test properties and related objects
try:
    old = ForestProperty.objects.filter(user=user)
    old.delete()
except ForestProperty.DoesNotExist:
    pass
try:
    old = Stand.objects.filter(user=user)
    old.delete()
except Stand.DoesNotExist:
    pass
try:
    old = Strata.objects.filter(user=user)
    old.delete()
except Strata.DoesNotExist:
    pass
try:
    old = Scenario.objects.filter(user=user)
    old.delete()
except Scenario.DoesNotExist:
    pass

##### Create the property
url = "/features/forestproperty/form/"
print("")
print(url)
response = client.post(url,
                       {
                       'name': 'test property',
                       'geometry_final': p1.wkt,  # multipolygon required
                       }
                       )
assert(response.status_code == 201)
uid = json.loads(response.content)['X-Madrona-Select']
prop1 = ForestProperty.objects.get(id=uid.split("_")[2])

#### Create the stands
url = "/features/stand/form/"
stands = []
for g in geoms:
    print("")
    print(url)
    response = client.post(url, {'name': 'test stand', 'geometry_orig': g.wkt})
    assert(response.status_code == 201)
    uid = json.loads(response.content)['X-Madrona-Select']
    stands.append(Stand.objects.get(id=uid.split("_")[2]))

#### Associate the stand with the property
url = "/features/forestproperty/%s/add/%s" % (prop1.uid, ','.join([x.uid for x in stands]))
print("")
print(url)
response = client.post(url, {})
assert(response.status_code == 200)

assert(prop1.stand_summary['total'] == NUM_STANDS)
steps = 0
while prop1.stand_summary['with_terrain'] != NUM_STANDS:
    steps += 1
    print("Waiting for terrain...")
    print(prop1.stand_summary)
    time.sleep(1)

#### Create a scenario. Try to run it (should return False; not enough info)
assert(prop1.stand_summary['with_strata'] == 0)
assert(prop1.stand_summary['with_condition'] == 0)

url = "/features/scenario/form/"
print("")
print(url)
response = client.post(url, {
    'name': "My Scenario",
    'input_target_boardfeet': 100000,
    'input_target_carbon': 1,
    'input_age_class': 1,
    'input_property': prop1.pk,
    'input_rxs': json.dumps(dict([(stand.id, 1) for stand in stands])),
})
#import ipdb; ipdb.set_trace()
print(response.content)
assert(response.status_code == 201)
uid = json.loads(response.content)['X-Madrona-Select']
scenario1 = Scenario.objects.get(id=uid.split("_")[2])
assert(scenario1.is_runnable is False)
gotit = False
try:
    scenario1.run()
except ScenarioNotRunnable:
    gotit = True
assert gotit

assert(scenario1.needs_rerun is True)

#### Change geometry
st = Stand.objects.get(id=stands[0].id)
old = st.elevation
st.geometry_final = geoms[0].buffer(10).wkt
st.save()
assert(prop1.stand_summary['with_terrain'] == NUM_STANDS - 1)
while prop1.stand_summary['with_terrain'] < NUM_STANDS:
    print("Waiting for terrain...")
    print(prop1.stand_summary)
    time.sleep(1)

st = Stand.objects.get(id=stands[0].id)
print(st.elevation, "vs old", old)
assert(st.elevation != old)

#### Step 3. Create the strata
old_count = Strata.objects.count()
url = "/features/strata/form/"
response = client.post(url,
                       {
                       'name': 'test strata',
                       'search_tpa': 160,
                       'search_age': 40,
                       'stand_list': u'{"classes":[["Red alder",5,10,50],["Douglas-fir",10,15,10]]}'
                       # see https://github.com/Ecotrust/land_owner_tools/wiki/Stand-List
                       }
                       )
assert(response.status_code == 201)
assert(old_count < Strata.objects.count())
uid = json.loads(response.content)['X-Madrona-Select']
print(uid)
strata1 = Strata.objects.get(id=uid.split("_")[2])

#### Step 3b. Associate the strata with the property
url = "/features/forestproperty/%s/add/%s" % (prop1.uid, strata1.uid)
response = client.post(url, {})
assert(response.status_code == 200)
assert(prop1.stand_summary['with_strata'] == 0)

#### Step 4. Add the stands to a strata
url = "/features/strata/links/add-stands/%s/" % strata1.uid
print("")
print(url)
response = client.post(url,
                       {'stands': ",".join([x.uid for x in stands])}
                       )
assert(response.status_code == 200)
print(prop1.stand_summary)
assert(prop1.stand_summary['with_strata'] == NUM_STANDS)
while not scenario1.is_runnable:
    print("Waiting for scenario to become runnable...")
    time.sleep(4)

print("We should be able to run() the scenario here.")
assert(scenario1.is_runnable is True)
scenario1.run()
i = 0
while scenario1.needs_rerun:
    if i > 5:
        print("Waiting too damn long. What's up?")
        # ipdb.set_trace()
    print("Waiting for %s results..." % scenario1.uid)
    # need to requery !
    scenario1 = Scenario.objects.get(id=scenario1.id)
    time.sleep(2)
    i += 1
print(scenario1.uid, scenario1.output_scheduler_results)

#### Step 6. Delete a stand
url = "/features/generic-links/links/delete/%s/" % stands[0].uid
print("")
print(url)
response = client.delete(url)
assert(response.status_code == 200)

scenario1 = Scenario.objects.get(id=scenario1.id)
assert(scenario1.is_runnable is True)
assert(scenario1.needs_rerun is True)
print(scenario1.uid)
scenario1.run()
while scenario1.needs_rerun:
    print("Waiting for scheduler results...")
    scenario1 = Scenario.objects.get(id=scenario1.id)
    time.sleep(2)

#### Change geometry
st = Stand.objects.get(id=stands[1].id)
old = st.elevation
st.geometry_final = geoms[1].buffer(20).wkt
st.save()  # WARNING: This may set the scenario to stale but a previously-started scenario.run() could clobber it
print(prop1.stand_summary)
while prop1.stand_summary['with_terrain'] < NUM_STANDS - 1:
    print("Waiting for terrain...")
    print(prop1.stand_summary)
    time.sleep(1)

while prop1.stand_summary['with_condition'] < NUM_STANDS - 1:
    print("Waiting for nearest...")
    print(prop1.stand_summary)
    time.sleep(1)

st = Stand.objects.get(id=stands[1].id)
assert(st.elevation != old)

assert(scenario1.is_runnable is True)
assert(scenario1.needs_rerun)
scenario1.run()
while scenario1.needs_rerun:
    print("Waiting for scenario results...")
    # need to requery !
    scenario1 = Scenario.objects.get(id=scenario1.id)
    time.sleep(2)

#### Create the stands
url = "/features/stand/form/"
print("")
print(url)
response = client.post(url, {'name': 'test stand', 'geometry_orig': geoms[0].wkt})
assert(response.status_code == 201)
uid = json.loads(response.content)['X-Madrona-Select']
stands[0] = Stand.objects.get(id=uid.split("_")[2])

url = "/features/forestproperty/%s/add/%s" % (prop1.uid, ','.join([x.uid for x in stands]))
print("")
print(url)
response = client.post(url, {})
assert(response.status_code == 200)

url = "/features/strata/links/add-stands/%s/" % strata1.uid
print("")
print(url)
response = client.post(url,
                       {'stands': ",".join([x.uid for x in stands])}
                       )
assert(response.status_code == 200)

print(prop1.stand_summary)
print(NUM_STANDS)
while prop1.stand_summary['with_condition'] < NUM_STANDS:
    print("Waiting for nearest...")
    print(prop1.stand_summary)
    time.sleep(2.5)

assert(prop1.stand_summary['total'] == NUM_STANDS)
assert(scenario1.is_runnable is False)
#  need to add a rx to the scenario.input_rx
scenario1.input_rxs = dict([(stand.id, 1) for stand in stands])
scenario1.save(rerun=False)

assert(scenario1.is_runnable is True)
assert(scenario1.needs_rerun is True)
scenario1.run()
i = 0
while scenario1.needs_rerun:
    if i > 5:
        print("Waiting too long.")
        # ipdb.set_trace()
    print("Waiting for scenario results...")
    # need to requery !
    scenario1 = Scenario.objects.get(id=scenario1.id)
    time.sleep(2)
    i += 1

#### Edit the strata
print("")
print("Edit the strata, should force re-calc of nearest neighbor")
strata1.search_tpa += 50
strata1.save()
assert(prop1.stand_summary['with_condition'] == 0)
while prop1.stand_summary['with_condition'] < NUM_STANDS:
    print("Waiting for nearest...")
    print(prop1.stand_summary)
    time.sleep(3)

#### Delete the strata
url = "/features/generic-links/links/delete/%s/" % strata1.uid
print("")
print(url)
response = client.delete(url)
assert(response.status_code == 200)

# should have no condition since strata was deleted
assert(scenario1.is_runnable is False)
assert(prop1.stand_summary['with_condition'] == 0)

print("")
