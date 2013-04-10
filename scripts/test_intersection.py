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
from trees.models import Stand, Scenario, Strata, ForestProperty, SpatialConstraint, Rx, ScenarioStand
from django.contrib.auth.models import User
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry
from shapely.ops import cascaded_union
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt

cntr = GEOSGeometry('SRID=3857;POINT(-13842500.0 5280100.0)')

NUM_STANDS = 400 
geoms = []
for i in range(int(NUM_STANDS**0.5)):
    cntr.set_y(cntr.y - 150)
    for j in range(int(NUM_STANDS**0.5)):
        cntr.set_x(cntr.x + 150)
        g1 = cntr.buffer(75).envelope
        g1.transform(settings.GEOMETRY_DB_SRID)
        geoms.append(wkt.loads(g1.wkt))
    cntr.set_x(cntr.x - int(NUM_STANDS**0.5)*150)

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
#      pass

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
    response = client.post(url, {'name': 'test stand', 'geometry_orig': g.wkt})
    assert(response.status_code == 201)
    uid = json.loads(response.content)['X-Madrona-Select']
    stands.append(Stand.objects.get(id=uid.split("_")[2]))

for stand in stands:
    # for this test, just fake it!
    stand.cond_id = 1234
    stand.save()

#### Associate the stand with the property
url = "/features/forestproperty/%s/add/%s" % (prop1.uid, ','.join([x.uid for x in stands]))
response = client.post(url, {})
assert(response.status_code == 200)

######################################## THESE WILL ALL GET CREATED BY US WITH FIXTURES !!!!!
#### Create Rx
rx0, created = Rx.objects.get_or_create(internal_name="testrx", internal_desc="test Rx", variant=prop1.variant)
rx1, created = Rx.objects.get_or_create(internal_name="testrx2", internal_desc="test Rx for spatial constraints", variant=prop1.variant)
rx2, created = Rx.objects.get_or_create(internal_name="testrx3", internal_desc="another test Rx for spatial constraints", variant=prop1.variant)

#### Create spatial constraints
import random
"""
for g in geoms:
    centroid = g.centroid
    cntr = GEOSGeometry(centroid.to_wkt())
    cntr.set_x(cntr.x + random.randint(-100, 100))
    cntr.set_y(cntr.y + random.randint(-100, 100))
    cg1 = cntr.buffer(random.randint(2, 100))  # .envelope
    cg1.transform(settings.GEOMETRY_DB_SRID)
    sc1 = SpatialConstraint.objects.get_or_create(
        geom=cg1,
        default_rx=random.choice([rx1, rx2]),
        category="R1"
    )

for i in range(5):
    pt1 = random.choice(geoms)
    pt2 = random.choice(geoms)
    from shapely.geometry import LineString
    line = LineString([(pt1.centroid.x, pt1.centroid.y), (pt2.centroid.x, pt2.centroid.y)])
    # create line, buffer it
    cg1 = line.buffer(random.randint(0, 200))
    sc1 = SpatialConstraint.objects.get_or_create(
        geom=cg1.wkt,
        default_rx=random.choice([rx1, rx2]),
        category=random.choice(["R1", "R2"])
    )

cntr.set_y(cntr.y - 75)
cg1 = cntr.buffer(30)  #.envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx1,
    category="R1"
)

cntr.set_y(cntr.y + 225)
cg1 = cntr.buffer(90)  #.envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx1,
    category="R1"
)

cntr.set_y(cntr.y - 15)
cg1 = cntr.buffer(20)  #.envelope
cg1.transform(settings.GEOMETRY_DB_SRID)
sc1 = SpatialConstraint.objects.get_or_create(
    geom=cg1,
    default_rx=rx2,
    category="R2"
)
"""
######################################## END fixtures

#### Create a scenario.

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


print "Creating identity"
from trees.utils import create_scenariostands
import time
x = time.time()
scenariostands = create_scenariostands(scenario1)
print time.time() - x
print "%d scenariostands created" % scenariostands.count()
