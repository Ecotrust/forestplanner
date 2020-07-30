from django.conf import settings

def getPropertyImageLayer(property, property_specs):
    """
    PURPOSE:
    -   Given a bounding box, return an image of all intersecting taxlots cut to the specified size.
    IN:
    -   property: (object) a property record from the DB
    -   property_specs: (dict) pre-computed aspects of the property, including: bbox, width, and height.
    OUT:
    -   taxlot_image: (PIL Image object) an image of the appropriate taxlot data
    -       rendered with the appropriate styles
    """
    from django.contrib.gis.geos.collections import MultiPolygon, Polygon
    from PIL import Image, ImageDraw
    bbox = property_specs['bbox']
    width = property_specs['width']
    height = property_specs['height']

    # Create overlay image
    base_img = Image.new("RGBA", (width, height), (255,255,255,0))

    geom = property.geometry_orig
    [bbwest, bbsouth, bbeast, bbnorth] = [float(x) for x in bbox.split(',')]
    if type(geom) == Polygon:
        coords_set = (geom.coords)
    else:
        coords_set = geom.coords

    yConversion = float(height)/(bbnorth-bbsouth)
    xConversion = float(width)/(bbeast-bbwest)

    for poly in coords_set:
        for poly_coords in poly:
            polygon = ImageDraw.Draw(base_img)
            poly_px_coords = []
            for (gX, gY) in poly_coords:
                poly_px_coords.append(((gX-bbwest)*xConversion, (bbnorth-gY)*yConversion))
            polygon.polygon(poly_px_coords, outline=settings.PROPERTY_OUTLINE_COLOR)#, width=settings.PROPERTY_OUTLINE_WIDTH)

    return base_img

def getTaxlotImageLayer(property_specs):
    foo='bar'

def getAerialImageLayer(property):
    foo='bar'

def getTopoImageLayer(property_specs):
    foo='bar'

def getSoilImageLayer(property_specs):
    foo='bar'

def getStreamImageLayer(property_specs):
    foo='bar'

def getPropertyMap(property, property_specs, base_layer, lots_layer, property_layer):
    foo='bar'

def getAerialMap(property, property_specs, base_layer, property_layer):
    foo='bar'

def getStreamMap(property, property_specs, base_layer, property_layer):
    foo='bar'

def getSoilMap(property, property_specs, base_layer, soil_layer, property_layer):
    foo='bar'
