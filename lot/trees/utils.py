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

def kdtree(querypoint=None):
    """ 
    find the closest one in coordinate space to a given point
    * construct an array of variables from the plot summary (filtering by dom sp or other qualtitative attrs)
    * normalize array
    * contructs kdtree
    * query kdtree for nearest point
    * ?
    requires scipy:
        apt-get install libblas-dev liblapack-dev
        apt-get build-dep scipy
        pip install scipy
    """
    import numpy as np
    from trees.models import PlotSummary
    from scipy.spatial import KDTree

    if not querypoint:
        querypoint = np.random.random_sample(2) * 100
    print querypoint

    psar = [[ps.tph_ge_3, ps.qmdc_dom] for ps in 
            PlotSummary.objects.filter(baa_ge_100__isnull=False, baa_ge_100__gt=0, bph_ge_3__isnull=False,
                tph_ge_3__isnull=False, qmdc_dom__isnull=False)[:20]]
    allpoints = np.array(psar) 
    # Normalize to 100
    multipliers = (100 / np.max(allpoints, axis=0))
    allpoints *= multipliers

    print allpoints
    tree = KDTree(allpoints)
    querypoints = np.array([querypoint])
    result = tree.query(querypoints) 
    return result[0][0], result[1][0]
    #a("Closest is point #", result[1][0], "... distance", result[0][0])
    #a("Closest point =",  allpoints[result[1][0]])

