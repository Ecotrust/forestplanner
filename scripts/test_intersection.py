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
from django.db import connection

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


def get_scenariostands_old(scenario):
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


def get_scenariostands(the_scenario):

    sql = """
SELECT
       geometry_final,
       cond_id,
       default_rx_id as rx_id,
       stand_id,
       constraint_id
FROM
  (SELECT z.geom AS geometry_final,
          stand_id,
          constraint_id,
          default_rx_id,
          cond_id
   FROM
     (SELECT new.geom AS geom,
             Max(orig.stand_id) AS stand_id,
             Max(orig.constraint_id) AS constraint_id
      FROM
        (SELECT id AS stand_id,
                NULL AS constraint_id,
                geometry_final AS geom
         FROM trees_stand
         UNION ALL SELECT NULL AS stand_id,
                          id AS constraint_id,
                          geom
         FROM trees_spatialconstraint) AS orig,

        (SELECT St_pointonsurface(geom) AS geom
         FROM
           (SELECT geom
            FROM St_dump(
                           (SELECT St_polygonize(the_geom) AS the_geom
                            FROM
                              (SELECT St_union(the_geom ) AS the_geom
                               FROM
                                 (SELECT St_exteriorring( geom) AS the_geom
                                  FROM
                                    (SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
                                     FROM trees_stand
                                     --
                                     WHERE id IN (%(stand_ids)s)
                                     --
                                     UNION ALL SELECT NULL AS stand_id , id AS constraint_id, geom
                                     FROM trees_spatialconstraint
                                     --
                                     WHERE id in (%(category_ids)s)
                                     --
                                     ) AS _test2_combo ) AS lines) AS noded_lines))) AS _test2_overlay) AS pt,

        (SELECT geom
         FROM St_dump(
                        (SELECT St_polygonize(the_geom) AS the_geom
                         FROM
                           (SELECT St_union(the_geom) AS the_geom
                            FROM
                              (SELECT St_exteriorring(geom) AS the_geom
                               FROM
                                 (SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
                                  FROM trees_stand
                                  --
                                  WHERE id IN (%(stand_ids)s)
                                  --
                                  UNION ALL SELECT NULL AS stand_id, id AS constraint_id, geom
                                  FROM trees_spatialconstraint
                                  --
                                  WHERE id in (%(category_ids)s)
                                  --
                                  ) AS _test2_combo ) AS lines) AS noded_lines))) AS new
      WHERE orig.geom && pt.geom
        AND new.geom && pt.geom
        AND Intersects(orig.geom, pt.geom)
        AND Intersects(new.geom, pt.geom)
      GROUP BY new.geom) AS z
   LEFT JOIN trees_stand s ON s.id = z.stand_id
   LEFT JOIN trees_spatialconstraint c ON c.id = z.constraint_id) AS _test2_unionjoin
WHERE stand_id IS NOT NULL ;
""" % {
        'category_ids': ",".join([str(int(x.id)) for x in the_scenario.constraint_set()]),
        'stand_ids': ",".join([str(int(x.id)) for x in the_scenario.stand_set()]),
    }

    # pre-clean
    ScenarioStand.objects.filter(scenario=the_scenario).delete()

    # exec query
    cursor = connection.cursor()
    cursor.execute(sql)
    print [x[0] for x in cursor.description]
    # ['geometry_final', 'cond_id', 'rx_id', 'stand_id', 'constraint_id']
    input_rxs = the_scenario.input_rxs
    print
    print input_rxs
    print
    for row in cursor.fetchall():

        print row

        the_cond_id = row[1]
        ###### TODO TOTALLY NOT COOL TO DO THIS.. NEED A COND_ID AT THIS POINT!!
        if not the_cond_id:
            the_cond_id = 432

        rx_id = row[2]
        the_rx = None
        stand_id = row[3]
        the_stand = None
        constraint_id = row[4]
        the_constraint = None

        if rx_id:
            # comes from a spatial constraint
            the_rx = Rx.objects.get(id=rx_id)
        elif stand_id:
            # comes from the scenario Rx user input
            try:
                rx_id = input_rxs[stand_id]
            except KeyError:
                rx_id = input_rxs[unicode(stand_id)]
            the_rx = Rx.objects.get(id=rx_id)

        if stand_id:
            the_stand = Stand.objects.get(id=stand_id)

        if constraint_id:
            the_constraint = SpatialConstraint.objects.get(id=constraint_id)

        ScenarioStand.objects.create(
            user=the_scenario.user,
            geometry_final=row[0],
            geometry_orig=row[0],
            cond_id=the_cond_id,
            scenario=the_scenario,
            rx=the_rx,
            stand=the_stand,
            constraint=the_constraint
        )

get_scenariostands(scenario1)
