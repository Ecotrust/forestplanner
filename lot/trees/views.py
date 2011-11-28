# Create your views here.
from django.http import HttpResponse
from django.contrib.gis.geos import GEOSGeometry
from trees.models import *
from itertools import izip
from django.db import connection
import json

def properties_list(request):
    parcels = Parcel.objects.all()
    apns = [{p.pk: p.apn} for p in parcels]
    response = HttpResponse(json.dumps(apns), status=200)
    response.ContentType = 'application/json'
    return response

def parcel_geojson(request, pk):
    parcels = Parcel.objects.filter(pk=pk).geojson()
    collection = """{
              "type": "FeatureCollection", 
              "features": [
                {"geometry": {
                    "type": "GeometryCollection", 
                    "geometries": [
                      %s
                    ]
                }, 
                "type": "Feature", 
                "properties": {}}
              ]
           }""" % ','.join([p.geojson for p in parcels])
    response = HttpResponse(collection, status=200)
    response.ContentType = 'application/json'
    return response
    
def stands(request):
    stands_jsons = request.POST.getlist('stands[]')
    stand_geoms = []
    for sj in stands_jsons:
        j = json.loads(sj)
        gj = j['geometry']
        stand_geom = GEOSGeometry(json.dumps(gj))
        # TODO Store stands in TreesAnalysis
        stand_geoms.append(stand_geom)

    def get_json(geom):
        return """
                {
                  "geometry": %s, 
                  "type": "Feature", 
                  "properties": {"test": "works!"}
                }
        """ % geom.geojson

    collection = """{
              "type": "FeatureCollection", 
              "features": [ %s ]
           }""" % ',\n'.join([get_json(s) for s in stand_geoms])

    response = HttpResponse(collection, status=200)
    response.ContentType = 'application/json'
    return response


def construct_stands(request):
    if not request.method == 'POST':
        return HttpResponse("Not a valid request method. Try POST.", status=405)

    edges_json = request.POST.getlist('edges[]')
    edges = []
    for ej in edges_json:
        j = json.loads(ej)
        gj = j['geometry']
        edge = GEOSGeometry(json.dumps(gj))
        edges.append(edge)
    # TODO Store edges in TreesAnalysis

    parcel_pk = int(request.POST['parcel_pk'])
    parcels = Parcel.objects.filter(pk=parcel_pk).geojson()
    parcel_polys = []
    for parcel in parcels:
        g = parcel.geom
        if g.geom_type == 'MultiPolygon':
            for sg in g:
                if sg.geom_type == 'Polygon':
                    parcel_polys.append(sg)
                else:
                    raise Exception("was expecting a polygon - got a %s" % sg.geom_type)
        elif g.geom_type == 'Polygon':
            parcel_polys.append(g)
        else:
            raise Exception("was expecting a (multi)polygon - got a %s" % sg.geom_type)

    stream_buffers = StreamBuffer.objects.filter(geom__bboverlaps=parcels.collect()).geojson()
    strbuf_polys = []
    for strbuf in stream_buffers:
        g = strbuf.geom
        if g.geom_type == 'MultiPolygon':
            for sg in g:
                if sg.geom_type == 'Polygon':
                    if sg.intersects(parcels.collect()):
                        strbuf_polys.append(sg)
                else:
                    raise Exception("was expecting a polygon - got a %s" % sg.geom_type)
        elif g.geom_type == 'Polygon':
            if g.intersects(parcels.collect()):
                strbuf_polys.append(g)
        else:
            raise Exception("was expecting a (multi)polygon - got a %s" % sg.geom_type)

    # Take the edges, and the parcel and ST_Polygonize them
    sql = """
    SELECT 
        ST_AsText(
            ST_POLYGONIZE(
                ST_Union(
                    ARRAY[
                        %s, 
                        %s
                    ]
                )
            )
        )
        AS polygon
    """ % (',\n                        '.join(["ST_GeomFromText('%s')" % e.wkt for e in edges]), 
           ',\n                        '.join(["ST_GeomFromText(ST_ExteriorRing('%s'))" % p.wkt for p in parcel_polys]), 
    )
    results = list(query_to_dicts(sql))
    newgeom = GEOSGeometry(results[0]['polygon'])
    print newgeom

    #TODO intersect with stream buffers
    #',\n                        '.join(["ST_GeomFromText(ST_ExteriorRing('%s'))" % s.wkt for s in strbuf_polys]), 
    # TODO Store polygons in TreesAnalysis

    # TODO Loop through polygons and auto-attribute them individually

    # TODO Deliver a summary of the analysis : "X stands were created with X acres of ...."

    collection = """{
              "type": "FeatureCollection", 
              "features": [
                {
                  "geometry": %s, 
                  "type": "Feature", 
                  "properties": {}
                }
              ]
           }""" % newgeom.json
    response = HttpResponse(collection, status=200)
    response.ContentType = 'application/json'
    return response
    
def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return



