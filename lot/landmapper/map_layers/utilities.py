def get_bbox_as_string(bbox):
    # """
    # PURPOSE:
    # -   if bbox is not a string of 4 coordinates ("W,S,E,N") convert
    # IN:
    # -   A bounding box description, either a string, a list, or a GEOSGeometry
    # OUT:
    # -   A string representation of the bbox in the format of "W,S,E,N"
    # """
    from django.contrib.gis.geos import Polygon, MultiPolygon

    if type(bbox) in [Polygon, MultiPolygon]:
        west = bbox.envelope.coords[0][0][0]
        south = bbox.envelope.coords[0][0][1]
        east = bbox.envelope.coords[0][2][0]
        north = bbox.envelope.coords[0][2][1]
        return "%s,%s,%s,%s" % (west, south, east, north)

    if type(bbox) in [tuple, list]:
        if len(bbox) == 1 and len(bbox[0]) == 5: # assume coords from Polygon
            west = bbox[0][0][0]
            south = bbox[0][0][1]
            east = bbox[0][2][0]
            north = bbox[0][2][1]
            return "%s,%s,%s,%s" % (west, south, east, north)
        elif len(bbox) == 1 and len(bbox[0]) == 1 and len(bbox[0][0]) == 5:   # coords from MultiPolygon
            west = bbox[0][0][0][0]
            south = bbox[0][0][0][1]
            east = bbox[0][0][2][0]
            north = bbox[0][0][2][1]
            return "%s,%s,%s,%s" % (west, south, east, north)
        elif len(bbox) == 1 and len(bbox[0]) == 1 and len(bbox[0][0]) > 5:  # Non-envelope MultiPolygon coords
            return get_bbox_as_string(Polygon( bbox[0][0] ).envelope)
        elif len(bbox) == 1 and len(bbox[0]) > 5:   # Non-envelope Polygon coords
            return get_bbox_as_string(Polygon(bbox[0]).envelope)
        elif len(bbox) == 4:    # Simple list [W,S,E,N]
            return ','.join([str(x) for x in bbox])
        elif len(bbox) == 2 and len(bbox[0]) == 2 and len(bbox[1]) == 2: # list of two sets of Point coordinates
            return ','.join([
                ','.join([str(x) for x in bbox[0]]),
                ','.join([str(x) for x in bbox[1]])
            ])

    if type(bbox) == str:
        if len(bbox.split(',')) == 4:
            return bbox

    print('ERROR: Format of BBOX unrecognized. Crossing fingers and hoping for the best...')
    return bbox

def get_bbox_as_polygon(bbox, srid=3857):
    # """
    # PURPOSE:
    # -   return a polygon bounding box from a large number of possible formats
    # IN:
    # -   bbox: (str, GEOS geom, list or tuple) any one of the bbox representations
    # -       of a bounding box supported by 'get_bbox_as_string'
    # -   ssrid: (int) the EPSG spatial reference identifier for the coordinate
    # -       system used to interpret the given coordinates
    # -       default: 3857
    # OUT:
    # -   bbox_geom: (GEOS Polygon) A GEOS Polygon feature of the provided bounding
    # -       box
    # """
    from django.contrib.gis.geos import Polygon
    # Get BBOX into consistant format
    bbox_str = get_bbox_as_string(bbox)
    # convert list into W,S,E,N components
    [west, south, east, north] = [float(x) for x in bbox_str.split(',')]
    # Format W,S,E,N into point coordinates
    polygon_input = [(west,south),(east,south),(east,north),(west,north),(west,south)]
    # Create the Polygon with the provided SRID
    bbox_geom = Polygon(polygon_input, srid=srid)
    return bbox_geom