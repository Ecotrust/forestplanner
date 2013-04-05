import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
import json
from trees.models import Stand, Scenario, Strata, ForestProperty, SpatialConstraint, Rx
from django.contrib.auth.models import User
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry
from shapely.ops import cascaded_union
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt

cntr = GEOSGeometry('SRID=3857;POINT(-13842400.0 5280100.0)')

NUM_STANDS = 3
geoms = []
for i in range(NUM_STANDS):
    cntr.set_x(cntr.x + 150)
    g1 = cntr.buffer(75).envelope
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

# try:
#     old = SpatialConstraint.objects.all()
#     old.delete()
# except ForestProperty.DoesNotExist:
#     pass
# try:
#     old = Rx.objects.all()
#     old.delete()
# except ForestProperty.DoesNotExist:
#     pass
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
print
print url
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
    print
    print url
    response = client.post(url, {'name': 'test stand', 'geometry_orig': g.wkt})
    assert(response.status_code == 201)
    uid = json.loads(response.content)['X-Madrona-Select']
    stands.append(Stand.objects.get(id=uid.split("_")[2]))

#### Associate the stand with the property
url = "/features/forestproperty/%s/add/%s" % (prop1.uid, ','.join([x.uid for x in stands]))
print
print url
response = client.post(url, {})
assert(response.status_code == 200)

######################################## THESE WILL ALL GET CREATED BY US WITH FIXTURES !!!!!
#### Create Rx
rx0, created = Rx.objects.get_or_create(internal_name="testrx", internal_desc="test Rx", variant=prop1.variant)
rx1, created = Rx.objects.get_or_create(internal_name="testrx2", internal_desc="test Rx for spatial constraints", variant=prop1.variant)
rx2, created = Rx.objects.get_or_create(internal_name="testrx3", internal_desc="another test Rx for spatial constraints", variant=prop1.variant)

#### Create spatial constraints
cntr.set_x(cntr.x - 75)
cntr.set_y(cntr.y - 75)
cg1 = cntr.buffer(30).envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx1,
    category="R1"
)

cntr.set_y(cntr.y - 75)
cg1 = cntr.buffer(30).envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx1,
    category="R1"
)

cntr.set_y(cntr.y + 225)
cg1 = cntr.buffer(30).envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx1,
    category="R1"
)

cntr.set_y(cntr.y - 15)
cg1 = cntr.buffer(30).envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx2,
    category="R2"
)
######################################## END

#### Create a scenario. Try to run it (should return False; not enough info)
assert(prop1.stand_summary['with_strata'] == 0)
assert(prop1.stand_summary['with_condition'] == 0)

url = "/features/scenario/form/"
print
print url
rxs = {}
for stand in stands:
    rxs[stand.id] = rx0.id
print rxs

response = client.post(url, {
    'name': "My Scenario",
    'input_target_boardfeet': 100000,
    'input_target_carbon': 1,
    'input_age_class': 1,
    'input_property': prop1.pk,
    'spatial_constraints': "R1,R2",
    'input_rxs': json.dumps(rxs),
})
#import ipdb; ipdb.set_trace()
print response.content
assert(response.status_code == 201)
uid = json.loads(response.content)['X-Madrona-Select']
scenario1 = Scenario.objects.get(id=uid.split("_")[2])


def get_scenariostands(scenario):
    print
    print "DO Intersection ========================="
    print

    working = []
    for standgr in scenario.standgeoms_rxs:
        intersects = False
        for constgr in scenario.constraintgeoms_rxs:
            #print standgr, constgr
            if standgr[0].intersects(constgr[0]):
                intersects = True
                working.append((constgr[0].intersection(standgr[0]), constgr[1]))
                working.append((constgr[0].difference(standgr[0]), standgr[1]))

        if not intersects:
            working.append(standgr)

    for w in working:
        print w[0].wkt, w[1]

            #import ipdb; ipdb.set_trace()

get_scenariostands(scenario1)
