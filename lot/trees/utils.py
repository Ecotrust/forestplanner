from trees.models import Stand, ForestProperty
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.error import OGRIndexError

class StandImporter:

    def __init__(self, forest_property):
        self.forest_property = forest_property
        self.user = self.forest_property.user
        self.required_fields = ['name']
        self.optional_fields = ['domspp','rx'] # model must provide defaults!

    def _validate_field_mapping(self, layer, field_mapping):
        fields = layer.fields

        for fname in self.required_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname

            if field_mapping[fname] not in fields:
                raise Exception("field_mapping must at least provide a 'name'")

        for fname in self.optional_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname
            
        return field_mapping

    def import_ogr(self, shp_path, field_mapping={}, layer_num=0):
        ds = DataSource(shp_path)
        layer = ds[0]
        num_features = len(layer)
        field_mapping = self._validate_field_mapping(layer, field_mapping)

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

def nearest_plot(imap_domspp=None, **kwargs):
    """ 
    find the closest GNN plot in coordinate space to a given point
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

    # Construct an n-dimensional point based on the numeric attributes
    if not kwargs.keys():
        keys = ['cancov','qmdc_dom']
        querypoint = np.random.random_sample(2) * 100
    else:
        keys = kwargs.keys()
        querypoint = np.array([float(kwargs[attr]) for attr in keys])

    # We need to make sure there are no nulls
    filter_keys = ["%s__isnull" % k for k in keys]
    filter_vals = [False] * len(keys)
    filter_kwargs = dict(zip(filter_keys, filter_vals))

    # The coded/categorical data must be a match in the filter
    if not imap_domspp:
        imap_domspp = 'PSME'
    filter_kwargs['imap_domspp'] = imap_domspp

    # Get any potential plots and create an n-dim array
    plotsummaries = PlotSummary.objects.filter(**filter_kwargs)
    psar = [plot_attrs(ps, keys) for ps in plotsummaries]
    allpoints = np.array(psar) 

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

    return distance, plot
