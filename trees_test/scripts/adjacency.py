"""
adjacency.py

Determines a matrix of adjacent polygons from a polygon data source.
Output is 2-column csv listing all pairs of adjacent features.

Since shapefiles (and other OGR data sources) are not topological, adjacency is determined
by a minimum distance threshold.
"""
from django.contrib.gis.gdal import DataSource
import sys

def calc_adj(inds, outfile, threshold, fid_field=None):
    ds = DataSource(inds)
    ds2 = DataSource(inds)
    layer = ds[0]
    layer2 = ds2[0]

    outfh = open(outfile, 'w')

    for i, feat in enumerate(layer):
        print i, "of", layer.num_feat
        if fid_field == None:
            fid = feat.fid
        else:
            fid = feat[fid_field]

        #geom_orig = feat.geom
        geom_buf = feat.geom.geos.buffer(threshold)

        layer2.spatial_filter = geom_buf.extent
        for feat2 in layer2:
            if fid_field == None:
                fid2 = feat2.fid
            else:
                fid2 = feat2[fid_field]

            if fid == fid2:
                continue

            # Determine adjacency
            # Using the distance method is ~ 4X slower than buffer->intersect
            # adjacent = feat2.geom.geos.distance(geom_orig.geos) <= threshold
            adjacent = feat2.geom.geos.intersects(geom_buf)

            if adjacent:
                outfh.write("%d,%d\n" % (fid, fid2))

        outfh.flush()
        layer2.spatial_filter = None

    outfh.close()

if __name__ == "__main__":
    #calc_adj('data/MgtBasins.shp','data/adj500.txt', threshold=500)
    #calc_adj('data/MgtBasins.shp','data/adj600.txt', threshold=600)
    calc_adj(sys.argv[1],'adj.txt', threshold=10)
