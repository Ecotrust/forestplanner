from trees.models import Stand, ForestProperty
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.error import OGRIndexError
from django.conf import settings
from madrona.common.utils import get_logger
from hashlib import sha1
from shapely.geometry import Point, Polygon
from shapely import wkt, wkb
from shapely.ops import cascaded_union

logger = get_logger()

class StandImporter:

    def __init__(self, user):
        self.user = user
        self.required_fields = ['name']
        self.optional_fields = ['domspp','rx'] # model must provide defaults!

    def _validate_field_mapping(self, layer, field_mapping):
        fields = layer.fields
        if not field_mapping:
            field_mapping = {}

        for fname in self.required_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname

            if field_mapping[fname] not in fields:
                raise Exception("Dataset does not have a required field called '%s'" % field_mapping[fname])

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
            raise Exception("Must provide either existing forest_property OR new_property_name")

        if new_property_name:
            #print "Calculating property outline from stands..."
            stands = []
            for feature in layer:
                stands.append(wkt.loads(feature.geom.wkt))
            casc_poly = cascaded_union(stands)
            casc = Polygon(casc_poly.exterior)
            
            #print "Creating Property..."
            self.forest_property = ForestProperty.objects.create(user=self.user, name=new_property_name, geometry_final=casc.wkt)
        else: 
            self.forest_property = forest_property

        stands = []
        for feature in layer:
            stand = Stand(user=self.user, 
                    name=feature.get(field_mapping['name']), 
                    geometry_orig=feature.geom.geos)
                    #geometry_final=feature.geom.geos) 

            for fname in self.optional_fields:
                if fname in field_mapping.keys():
                    try:
                        stand.__dict__[fname] = feature.get(field_mapping[fname])
                    except OGRIndexError: 
                        pass

            stand.full_clean()
            stands.append(stand)
            del stand

        for stand in stands:
            stand.save()
            self.forest_property.add(stand)
            if pre_impute:
                tmp = stand.geojson

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

        filterqs = qs.filter(geometry_final__bboverlaps = geom_buf, geometry_final__intersects = geom_buf)
        for feat2 in filterqs:
            fid2 = feat2.pk
            if fid == fid2:
                continue
            adj[fid].append(fid2)

        if len(adj[fid]) == 0:
            adj[fid] = None

        del filterqs

    return adj

def nearest_plot(categories, numeric):
    """ 
    find the closest GNN plot in coordinate space to a given point
    * filter by categorical variables
    * construct an array of the numeric variables from potential plots
       (filtering by dom sp or other qualtitative attrs)
    * normalize array to 100
    * contruct kdtree
    * query kdtree for nearest point

    requires scipy:
        apt-get install libblas-dev liblapack-dev
        apt-get build-dep scipy
        pip install scipy
    """
    import numpy as np
    from trees.models import PlotSummary
    from scipy.spatial import KDTree

    def plot_attrs(ps, keys):
        vals = []
        for attr in keys:
            vals.append(ps.__dict__[attr])
        return vals

    if len(categories.keys()) == 0:
        raise Exception("Invalid categories dict supplied, %s" )
    if len(numeric.keys()) == 0:
        raise Exception("Invalid numeric dict supplied, %s")

    # Construct an n-dimensional point based on the remaining numeric attributes
    keys = numeric.keys()
    querypoint = np.array([float(numeric[attr]) for attr in keys])
    # We need to make sure there are no nulls
    filter_keys = ["%s__isnull" % k for k in keys]
    filter_vals = [False] * len(keys)
    filter_kwargs = dict(zip(filter_keys, filter_vals))

    # The coded/categorical data must be a match in the filter
    for cat, val in categories.iteritems():
        filter_kwargs[cat] = val

    # Get any potential plots and create an array of n-dim points
    # hashkey = ".plotsummary_" + sha1(str(filter_kwargs)).hexdigest() 
    plotsummaries = list(PlotSummary.objects.filter(**filter_kwargs))
    psar = [plot_attrs(ps, keys) for ps in plotsummaries]
    allpoints = np.array(psar) 
    candidates = len(plotsummaries)
    if candidates == 0:
        raise Exception("There are no candidate plots matching the categorical variables: %s" % categories)

    # Normalize to 100; linear scale
    multipliers = (100.0 / np.max(allpoints, axis=0))
    allpoints *= multipliers
    querypoint *= multipliers

    # Create tree and query it for nearest plot
    tree = KDTree(allpoints)
    querypoints = np.array([querypoint])
    result = tree.query(querypoints) 
    distance = result[0][0]
    plot = plotsummaries[result[1][0]]

    return distance, plot, candidates

def classify_aspect(angle):
    '''
    inspired by http://xkcd.com/cyborg.py
    '''
    if not angle:
        return ""
    angle += 22.5
    angle = int(angle/45.0)
    words=["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West", "North"]
    return words[angle]
