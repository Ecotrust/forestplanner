#!/bin/env python
from __future__ import print_function
import sys
import json
from django.contrib.gis.gdal import DataSource


def validate(layer, field_map):
    # does shp have any hitherto unknown field names?
    additional = []
    for sfield in layer.fields:
        if sfield.lower() not in field_map.keys():
            additional.append(sfield)

    if len(additional) > 0:
        raise Exception(
            "{}\nThese new fields in shapefile are not recognized in field_map\n"
            "Suggested action:\n    - add to field_map.json and models.py".format(additional))

    # is shp missing any expected field names?
    missing = []
    for dfield in field_map.keys():
        if dfield not in [x.lower() for x in layer.fields]:
            missing.append(dfield)

    if len(missing) > 0:
        raise Exception(
            "{}\nThese fields are expected but missing from shapefile \n"
            "Suggested action:\n    - remove from field_map.json and models.py".format(missing))

if __name__ == '__main__':
    shp_path = sys.argv[1]
    field_map_path = sys.argv[2]

    field_map = json.loads(open(field_map_path, 'r').read())
    ds = DataSource(shp_path)
    layer = ds[0]

    validate(layer, field_map)
