from trees.models import Stand, ForestProperty, IdbSummary, Strata, FVSAggregate
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.error import OGRIndexError
from django.conf import settings
from madrona.common.utils import get_logger
from django.db.models import Min, Max, Avg
from shapely.ops import cascaded_union
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
from scipy.spatial import KDTree
import datetime
import math

logger = get_logger()


def datetime_to_unix(dt):
    start = datetime.datetime(year=1970, month=1, day=1)
    diff = dt - start
    try:
        total = diff.total_seconds()
    except AttributeError:
        # for the benefit of python 2.6
        total = (diff.microseconds + (diff.seconds + diff.days * 24 * 3600) * 1e6) / 1e6
    return total


class StandImporter:

    def __init__(self, user):
        self.user = user
        self.required_fields = []  # ['name']
        self.optional_fields = ['name', 'domspp', 'rx']  # model must provide defaults!

    def _validate_field_mapping(self, layer, field_mapping):
        fields = layer.fields
        if not field_mapping:
            field_mapping = {}

        for fname in self.required_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname

            if field_mapping[fname] not in fields:
                raise Exception(
                    "Dataset does not have a required field called '%s'" % field_mapping[fname])

        for fname in self.optional_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname

        return field_mapping

    def import_ogr(self, shp_path, field_mapping=None, layer_num=0,
                   forest_property=None, new_property_name=None, pre_impute=False):
        ds = DataSource(shp_path)
        layer = ds[0]
        num_features = len(layer)
        field_mapping = self._validate_field_mapping(layer, field_mapping)

        if not forest_property and not new_property_name:
            raise Exception(
                "Must provide either existing forest_property OR new_property_name")

        if new_property_name:
            # Calculating property outline from stands
            stands = []
            for feature in layer:
                stands.append(wkt.loads(feature.geom.wkt))
            casc_poly = cascaded_union(stands)

            if casc_poly.type == 'MultiPolygon':
                polys = []
                for c in casc_poly:
                    # Identify small 'slivers' or areas of empty space b/t polygons that are unintentional
                    # If they're smaller than the threshold, remove them
                    interiors = [x for x in c.interiors if Polygon(
                        x).area > settings.SLIVER_THRESHOLD]
                    polys.append(Polygon(shell=c.exterior, holes=interiors))
            elif casc_poly.type == 'Polygon':
                # Identify small 'slivers' or areas of empty space b/t polygons that are unintentional
                # If they're smaller than the threshold, remove them
                interiors = [x for x in casc_poly.interiors if Polygon(
                    x).area > settings.SLIVER_THRESHOLD]
                polys = [Polygon(shell=casc_poly.exterior, holes=interiors)]

            casc = MultiPolygon(polys)

            # Creating Property
            self.forest_property = ForestProperty.objects.create(
                user=self.user, name=new_property_name, geometry_final=casc.wkt)
        else:
            self.forest_property = forest_property

        # special case for user-inventory situation
        # if there is a condid field, it is implicitly required.
        use_condid = False
        if 'condid' in layer.fields:
            use_condid = True
            valid_condids = FVSAggregate.valid_condids()

        stands = []
        stratum = {}
        for feature in layer:
            stand = Stand(
                user=self.user,
                name=str(datetime_to_unix(datetime.datetime.now())),
                geometry_orig=feature.geom.geos)
                # geometry_final=feature.geom.geos)

            for fname in self.optional_fields:
                if fname in field_mapping.keys():
                    try:
                        stand.__dict__[fname] = feature.get(
                            field_mapping[fname])
                    except OGRIndexError:
                        pass

            # If we're doing user-inventory, each feature must contain
            # integer condids that refer to valid fvsaggregate records.
            if use_condid:
                condid = feature.get('condid')

                if condid not in valid_condids:
                    raise Exception('Error: {} is not a valid condid (check fvsaggregate table)'.format(condid))

                if condid in stratum.keys():
                    # use cached
                    strata = stratum[condid]
                else:
                    # create it
                    kwargs = condid_strata(condid, self.forest_property.uid)
                    strata = Strata(user=self.user, name=condid, **kwargs)
                    strata.save(skip_validation=True)  # no need for NN validation
                    self.forest_property.add(strata)
                    stratum[condid] = strata

                stand.cond_id = condid
                stand.locked_cond_id = condid
                stand.strata = strata

            stand.full_clean()
            stands.append(stand)
            del stand

        for stand in stands:
            stand.save()
            self.forest_property.add(stand)
            if pre_impute:
                stand.preimpute()

        return True


def condid_strata(condid, forest_property_uid=''):
    """
    Given a condition id (cond_id),
    Returns a dictionary of properties used to construct a strata
    based on the available data in fvsaggregate
    """
    # TODO
    stand_list = {
        'property': forest_property_uid,
        'classes': [
            ('N/A', 1, 1, 1),
        ]
    }
    age = 0.0
    tpa = 0.0

    return {
        'stand_list': stand_list,
        'search_tpa': tpa,
        'search_age': age
    }


def calculate_adjacency(qs, threshold):
    """
    Determines a matrix of adjacent polygons from a Feature queryset.
    Since the data are not topological, adjacency is determined
    by a minimum distance threshold.
    """
    features = list(qs)
    adj = {}

    for feat in features:
        fid = feat.pk
        adj[fid] = []

        geom_orig = feat.geometry_final
        geom_buf = feat.geometry_final.buffer(threshold)

        filterqs = qs.filter(
            geometry_final__bboverlaps=geom_buf, geometry_final__intersects=geom_buf)
        for feat2 in filterqs:
            fid2 = feat2.pk
            if fid == fid2:
                continue
            adj[fid].append(fid2)

        if len(adj[fid]) == 0:
            adj[fid] = None

        del filterqs

    return adj


class NoPlotMatchError(Exception):
    pass


def process_categories(categories, search_params):
    keys = search_params.keys()
    for sp in keys:
        categories[sp + "__isnull"] = False

    if 'for_type_name' not in categories:
        raise NoPlotMatchError("Must provide a primary Forest Type")

    # If secondary forest type not provided, assume NO secondary forest type
    if 'for_type_secdry_name' not in categories:
        categories['for_type_secdry_name__isnull'] = True

    return categories


def nearest_plots(categories, input_params, weight_dict, k=10):
    """
    !!!!!! DEPRECATED; DO NOT USE !!!!!!!
    ~~~~~~ use trees.plots.get_nearest_neighbors instead ~~~~~~~~
    Utility function to determine the k nearest plots in attribute space

    inputs:
      - categories: dict of categorical variables for exact filter
      - input_params: dict of numeric variables for kdtree matching
      - weight_dict: dict, weighting for each input_param. assumes 1 if not in dict.

    outputs:
      - list of k IdbSummary instances
      - total number of potential candidates
    """
    search_params = input_params.copy()
    origkeys = search_params.keys()
    keys = [x for x in origkeys if x not in ['calc_aspect', ]]  # special case
    categories = process_categories(categories, search_params)

    def plot_attrs(ps, keys):
        vals = []
        for attr in keys:
            vals.append(ps.__dict__[attr])

        # Aspect is a special case
        if 'calc_aspect' in origkeys:
            angle = angular_diff(ps.calc_aspect, input_params['calc_aspect'])
            vals.append(angle)
            search_params['_aspect'] = 0  # anglular difference to self is 0

        return vals

    plotsum_qs = IdbSummary.objects.filter(**categories)
    plotsummaries = list(plotsum_qs)
    ps_attr_list = [plot_attrs(ps, keys) for ps in plotsummaries]

    # include our special case
    if 'calc_aspect' in origkeys:
        keys.append('_aspect')

    num_candidates = len(plotsummaries)
    if num_candidates == 0:
        raise NoPlotMatchError(
            "There are no candidate plots matching the categorical variables: %s" % categories)

    weights = np.ones(len(keys))
    for i in range(len(keys)):
        key = keys[i]
        if key in weight_dict:
            weights[i] = weight_dict[key]

    querypoint = np.array([float(search_params[attr]) for attr in keys])

    rawpoints = np.array(ps_attr_list)

    # Normalize to max of 100; linear scale
    high = 100.0
    low = 0.0
    mins = np.min(rawpoints, axis=0)
    maxs = np.max(rawpoints, axis=0)
    rng = maxs - mins
    scaled_points = high - (((high - low) * (maxs - rawpoints)) / rng)
    scaled_querypoint = high - (((high - low) * (maxs - querypoint)) / rng)
    scaled_querypoint[np.isinf(
        scaled_querypoint)] = high  # replace all infinite values with high val

    # Apply weights
    # and guard against any nans due to zero range or other
    scaled_points = np.nan_to_num(scaled_points * weights)
    scaled_querypoint = np.nan_to_num(scaled_querypoint * weights)

    # Create tree and query it for nearest plot
    tree = KDTree(scaled_points)
    querypoints = np.array([scaled_querypoint])
    result = tree.query(querypoints, k=k)
    distances = result[0][0]
    plots = result[1][0]

    top = zip(plots, distances)
    ps = []

    xs = [100 * x for x in weights if x > 0]
    squares = [x * x for x in xs]
    max_dist = math.sqrt(sum(squares))  # the real max
    for t in top:
        if np.isinf(t[1]):
            continue
        try:
            p = plotsummaries[t[0]]
        except IndexError:
            continue

        p.__dict__['_kdtree_distance'] = t[1]
        # certainty of 0 -> distance is furthest possible
        # certainty of 1 -> the point matches exactly
        # sqrt of ratio taken to exagerate small diffs
        p.__dict__['_certainty'] = 1.0 - ((t[1] / max_dist) ** 0.5)
        ps.append(p)

    return ps, num_candidates


def classify_aspect(angle):
    '''
    inspired by http://xkcd.com/cyborg.py
    '''
    try:
        angle = float(angle)
    except:
        return ""

    if angle < 0:
        return "unknown"

    while angle > 360.0:
        angle = angle - 360.0
    angle += 22.5
    angle = int(angle / 45.0)

    words = ["North", "North-East", "East", "South-East",
             "South", "South-West", "West", "North-West", "North"]
    return words[angle]


def angular_diff(x, y):
    '''
    input: two angles in degrees
    output: absolute value of the angular difference in degrees
    '''
    import math
    x = math.radians(x)
    y = math.radians(y)
    return math.fabs(math.degrees(min(y - x, y - x + 2 * math.pi, y - x - 2 * math.pi, key=abs)))


def potential_minmax(categories, weight_dict, search_params):
    categories = process_categories(categories, search_params)
    ps = IdbSummary.objects.filter(**categories)
    keys = [k for k in weight_dict.keys() if not k.startswith("_")]
    args = [Min(k) for k in keys] + [Max(
        k) for k in keys] + [Avg(k) for k in keys]
    return ps.aggregate(*args)


def create_scenariostands(the_scenario):
    """
    Given a scenario, do a spatial identity between
      * Stands for this scenario
      * All SpatialConstraints chosen for this scenario
    and populate the ScenarioStands with the results

    input: scenario instance
    output: ScenarioStands queryset
    side effects: removes old ScenarioStands and populates with new shapes
    dependencies: scenario must be runnable
    """
    from trees.models import ScenarioStand, Stand, Rx, SpatialConstraint, ScenarioNotRunnable
    from django.db import connection

    if not the_scenario.is_runnable:
        raise ScenarioNotRunnable(
            "%s has stands without cond_id or is otherwise unrunnable" % the_scenario.uid)

    # Avoid use of IN?
    # Doesn't seem to improve performance much
    # orig_combo_sql = """
    #      SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
    #      FROM trees_stand
    #      WHERE content_type_id = 47 and object_id = 80

    #      UNION ALL

    #      SELECT NULL AS stand_id, sc.id AS constraint_id, geom
    #      --from trees_spatialconstraint sc
    #      FROM trees_spatialconstraint sc, trees_forestproperty fp
    #      WHERE fp.id = 80 AND fp.geometry_final && sc.geom AND category IN ('R2')
    #     """

    orig_combo_sql = """
         SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
         FROM trees_stand
         WHERE id IN (%(stand_ids)s)

         UNION ALL

         SELECT NULL AS stand_id, sc.id AS constraint_id, geom
         FROM trees_spatialconstraint sc
         WHERE sc.id IN (%(constraint_ids)s)
    """ % {
        # in case there are no constraints involved, fake a -1 id
        'constraint_ids': ",".join([str(int(x.id)) for x in the_scenario.constraint_set()] + ['-1']),
        'stand_ids': ",".join([str(int(x.id)) for x in the_scenario.stand_set()]),
    }

    # testing, above query assumed to reside in _temp_orig
    #orig_combo_sql = "SELECT * FROM _temp_orig"

    sql = """
    -- ArcGIS-style Identity
    -- similar to a global arcgis-style union but "clipped" to one of the input layers
    -- advantage to this method is that you can include polygons from multiple input tables
    -- and overlapping polygons are handled gracefuly by taking the max/min(id)
    -- see https://gist.github.com/perrygeo/5320964
    --
    -- 1. put all polygons into one table, maintaining ids for each input layer
    -- 2. deconstruct into lines and rebuild polygons
    -- 3. take points on surface
    -- 4. group by geom and aggregate original ids by point overlap
    -- 5. Join with the original tables to pull in attributes
    -- 6. query on attributes to create an Identity

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
     (SELECT proc.geom AS geom,
             Max(orig.stand_id) AS stand_id,
             Max(orig.constraint_id) AS constraint_id
      FROM
        (
        %(orig_combo_sql)s
        ) AS orig,

        (SELECT geom, St_pointonsurface(geom) as ptgeom
         FROM St_dump(
            (SELECT St_polygonize(the_geom) AS the_geom
             FROM
               (SELECT St_union(the_geom) AS the_geom
                FROM
                  (SELECT St_exteriorring(geom) AS the_geom
                   FROM
                     (
                     %(orig_combo_sql)s
                     ) AS combo
                  ) AS lines
               ) AS noded_lines
            )
        )) AS proc
      WHERE proc.ptgeom && orig.geom
      AND ST_Contains(orig.geom, proc.ptgeom)
      GROUP BY proc.geom) AS z
    LEFT JOIN trees_stand s ON s.id = z.stand_id
    LEFT JOIN trees_spatialconstraint c ON c.id = z.constraint_id) AS _unionjoin
    WHERE stand_id IS NOT NULL ;
    """ % {
        'orig_combo_sql': orig_combo_sql
    }
    print sql

    # pre-clean
    ScenarioStand.objects.filter(scenario=the_scenario).delete()

    input_rxs = the_scenario.input_rxs

    # exec query
    cursor = connection.cursor()
    cursor.execute(sql)

    # loop through output identity polygons and
    # and create corresponding ScenarioStands
    print "Looping through results..."
    for row in cursor.fetchall():

        # [x[0] for x in cursor.description]
        # ['geometry_final', 'cond_id', 'rx_id', 'stand_id', 'constraint_id']

        the_cond_id = row[1]
        if not the_cond_id:
            raise ScenarioNotRunnable(
                "%s - not all ScenarioStands have cond_id" % the_scenario.uid)

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
                try:
                    rx_id = input_rxs[unicode(stand_id)]
                except:
                    # do we raise Exception or apply a default Rx silently?
                    err = "%s not in input_rxs!" % stand_id
                    logger.error(err)
                    raise ScenarioNotRunnable(err)

            the_rx = Rx.objects.get(id=rx_id)

        if stand_id:
            the_stand = Stand.objects.get(id=stand_id)
        else:
            raise ScenarioNotRunnable(
                "%s - not all ScenarioStands have stand_id" % the_scenario.uid)

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

    return ScenarioStand.objects.filter(scenario=the_scenario)


def fake_scenariostands(the_scenario):
    """
    fake the output of create_scenariostands with NO spatial constriaints
    Basically just copy the Stands over to ScenarioStands

    side effects: removes old ScenarioStands and populates with new shapes
    dependencies: scenario must be runnable
    """
    from trees.models import ScenarioStand, Rx, ScenarioNotRunnable

    if not the_scenario.is_runnable:
        raise ScenarioNotRunnable(
            "%s has stands without cond_id or is otherwise unrunnable" % the_scenario.uid)

    # pre-clean
    ScenarioStand.objects.filter(scenario=the_scenario).delete()

    input_rxs = the_scenario.input_rxs

    for stand in the_scenario.stand_set():
        if not stand.cond_id:
            raise ScenarioNotRunnable(
                "%s - not all ScenarioStands have cond_id" % the_scenario.uid)

        # comes from the scenario Rx user input
        rx_id = None
        try:
            rx_id = input_rxs[stand.id]
        except KeyError:
            try:
                rx_id = input_rxs[unicode(stand.id)]
            except:
                err = "%s not in input_rxs!" % stand.id
                logger.error(err)
                raise ScenarioNotRunnable(err)

        the_rx = Rx.objects.get(id=rx_id)
        cond_id = stand.cond_id

        ScenarioStand.objects.create(
            user=the_scenario.user,
            geometry_final=stand.geometry_final,
            geometry_orig=stand.geometry_orig,
            cond_id=cond_id,
            scenario=the_scenario,
            rx=the_rx,
            stand=stand,
            constraint=None,
            acres=stand.acres,
            offset=0
        )

    return ScenarioStand.objects.filter(scenario=the_scenario)


def terrain_zonal(geom):
    from rasterstats import raster_stats
    from django.conf import settings
    import math
    import os

    tdir = settings.TERRAIN_DIR

    def get_raster_stats(rastername):
        raster_path = os.path.join(tdir, rastername)
        stats = raster_stats(geom.wkt, raster_path, stats="median mean sum")
        if any(val is None or math.isnan(val) for val in stats[0].values()):
            # fall back to point centroid
            stats = raster_stats(geom.centroid.wkt, raster_path, stats="median mean sum")
        return stats[0]

    elevation = aspect = slope = cost = None

    # elevation
    data = get_raster_stats('dem.tif')
    elevation = data['mean']

    # aspect
    cos = get_raster_stats('cos_aspect.tif')
    sin = get_raster_stats('sin_aspect.tif')
    result = None
    Esin = sin['sum']
    Ecos = cos['sum']
    if Ecos and Esin:
        avg_aspect_rad = math.atan2(Esin, Ecos)
        result = math.degrees(avg_aspect_rad) % 360
    aspect = result

    # slope
    data = get_raster_stats('slope.tif')
    slope = data['median']
    cost = slope

    terrain = (elevation, slope, aspect, cost)

    if any(x is None or math.isnan(x) for x in terrain):
        # fail silently so as not to distrupt NN
        terrain = (0, 0, 0, 0)
    return terrain
