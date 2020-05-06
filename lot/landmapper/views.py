from django.shortcuts import render
from django.conf import settings

"""
get_soils_connectors
PURPOSE: return handy owslib wms and wfs objects for the soils data sources
-   as defined in landmapper.settings.py.
-   NOTE: The WFS services for the USDA Soils Data Mart site is not properly
-   configured. The next few views handle a more manual approach to reading
-   the soils data to an ogr-understandable layer object
IN:
-   'retries': The number of retries attempted on the WFS endpoint, which is
-       shakey
OUT:
-   wms: an owslib wms object
-   wfs: an owslib wfs object
"""
def get_soils_connectors(retries=0):
    '''
    Land Mapper: Soils WMS connector
    '''
    from owslib.wms import WebMapService
    from owslib.wfs import WebFeatureService
    wms = WebMapService(settings.SOIL_WMS_URL)
    # wms = WebMapService('http://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms')
    # wfs = WebFeatureService(url='https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWM.wfs', version='1.1.0')
    try:
        wfs = WebFeatureService(url=settings.SOIL_WFS_URL, version=settings.SOIL_WFS_VERSION)
    except (ConnectionError, ConnectionResetError) as e:
        if retries < 10:
            print('failed to connect to wfs %s time(s)' % retries)
            (wms,wfs) = get_soils_connectors(retries+1)
        else:
            print("ERROR: Unable to connect to WFS Server @ %s" % settings.SOIL_WFS_URL)
            wfs = None
    except Exception as e:
        print('Unexpected error occurred: %s' % e)
        wfs = None
    return (wms,wfs)

"""
unstable_request_wrapper
PURPOSE: As mentioned above, the USDA wfs service is weak. We wrote this wrapper
-   to fail less.
IN:
-   'url': The URL being requested
-   'retries': The number of retries made on this URL
OUT:
-   contents: The html contents of the requested page
"""
def unstable_request_wrapper(url, retries=0):
    import urllib.request
    try:
        contents = urllib.request.urlopen(url)
    except ConnectionError as e:
        if retries < 10:
            print('failed [%d time(s)] to connect to %s' % (retries, url))
            contents = unstable_request_wrapper(url, retries+1)
        else:
            print("ERROR: Unable to connect to %s" % url)
    except Exception as e:
        print(e)
        print(url)
    return contents

"""
get_wms_layer_image
"""
def get_wms_layer_image(wms, layers, styles, srs, bbox, size):
    img = wms.getmap(
        # layers=['surveyareapoly'],
        layers=layers,
        styles=styles,
        # srs='EPSG:4326',
        # bbox=(-125, 36, -119, 41),
        srs=srs,
        bbox=bbox,
        size=size, # WIDTH=665&HEIGHT=892
        format='image/png',
        tansparent=True
    )
    return img

"""
set_image_transparancy
Attribution: Thanks to cr333 and the Stack overflow community:
-   https://stackoverflow.com/a/765774/706797
"""
def set_image_transparancy(filename, rgb_val):
    from PIL import Image
    img = Image.open(filename)
    img = img.convert("RGBA")
    data = img.getdata()
    red = int(rgb_val[0])
    green = int(rgb_val[1])
    blue = int(rgb_val[2])

    newData = []
    for item in data:
        if item[0] == red and item[1] == green and item[2] == blue:
            newData.append((red, green, blue, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(filename, "PNG")


"""
get_soil_data_gml
PURPOSE: given a bounding box, SRS, and preferred version (format) of GML,
-   return an OGR layer read from the GML response (from unstable_request_wrapper)
IN:
-   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
-   srs: The Spatial Reference System used to interpret the coordinates
-       default: 'EPSG:4326'
-   format: The version of GML to use (GML2 or GML3)
-       default: 'GML3'
OUT:
-   gml: an OGR layer interpreted from the GML
"""
def get_soil_data_gml(bbox, srs='EPSG:4326',format='GML3'):
    from tempfile import NamedTemporaryFile
    from osgeo import ogr
    endpoint = settings.SOIL_WFS_URL
    request = 'SERVICE=WFS&REQUEST=GetFeature&VERSION=%s&' % settings.SOIL_WFS_VERSION
    layer = 'TYPENAME=%s&' % settings.SOIL_DATA_LAYER
    projection = 'SRSNAME=%s&' % srs
    bbox = 'BBOX=%s' % bbox
    gml = '&OUTPUTFORMAT=%s' % format
    url = "%s?%s%s%s%s%s" % (endpoint, request, layer, projection, bbox, gml)
    contents = unstable_request_wrapper(url)
    fp = NamedTemporaryFile()
    fp.write(contents.read())
    gml = ogr.Open(fp.name)
    fp.close()
    return gml

"""
get_soils_list
PURPOSE:
IN:
-   bbox: a string of comma-separated bounding-box coordinates (W,S,E,N)
-   srs: The Spatial Reference System used to interpret the coordinates
-       default: 'EPSG:4326'
-   format: The version of GML to use (GML2 or GML3)
-       default: 'GML3'
OUT:
-   gml: an OGR layer interpreted from the GML
"""
def get_soils_list(bbox, srs='EPSG:4326',format='GML3'):
    gml = get_soil_data_gml(bbox, srs, format)
    inLayer = gml.GetLayerByIndex(0)

    inLayerDefn = inLayer.GetLayerDefn()

    soils_list = {}
    inLayer.ResetReading()
    for i in range(0, inLayer.GetFeatureCount()):
        feat = inLayer.GetNextFeature()
        feat_dict = {}
        if not feat.GetField(settings.SOIL_ID_FIELD) in soils_list.keys():
            for j in range(0, inLayerDefn.GetFieldCount()):
                field_name = inLayerDefn.GetFieldDefn(j).GetName()
                if field_name in settings.SOIL_FIELDS.keys() and settings.SOIL_FIELDS[field_name]['display']:
                    feat_dict[field_name] = feat.GetField(field_name)
            soils_list[feat.GetField(settings.SOIL_ID_FIELD)] = feat_dict

    return soils_list

"""
geocode
PURPOSE: Convert a provided place name into geographic coordinates
IN:
-   search_string: (string) An address or named landmark/region
-   srs: (int) The EPSG ID for the spatial reference system in which to output coordinates
-       defaut: 4326
-   service: (string) The geocoding service to query for a result
-       default = 'arcgis'
-       other supported options: 'google'
OUT:
-   coords: a list of two coordinate elements -- [lat(y), long(x)]
-       projected in the requested coordinate system
"""
def geocode(search_string, srs=4326, service='arcgis'):
    # https://geocoder.readthedocs.io/
    import geocoder

    g = False
    # Query desired service
    if service.lower() == 'arcgis':
        g = geocoder.arcgis(search_string)
    elif service.lower() == 'google':
        if hasattr(settings, 'GOOGLE_API_KEY'):
            g = geocoder.google(search_string, key=settings.GOOGLE_API_KEY)
        else:
            print('To use Google geocoder, please configure "GOOGLE_API_KEY" in your project settings. ')
    if not g or not g.ok:
        print('Selected geocoder not available or failed. Defaulting to ArcGIS')
        g = geocoder.arcgis(search_string)

    coords = g.latlng

    # Transform coordinates if necessary
    if not srs == 4326:
        from django.contrib.gis.geos import GEOSGeometry
        if ':' in srs:
            try:
                srs = srs.split(':')[1]
            except Exception as e:
                pass
        try:
            int(srs)
        except ValueError as e:
            print('ERROR: Unable to interpret provided srs. Please provide a valid EPSG integer ID. Providing coords in EPSG:4326')
            return coords

        point = GEOSGeometry('SRID=4326;POINT (%s %s)' % (coords[1], coords[0]), srid=4326)
        point.transform(srs)
        coords = [point.coords[1], point.coords[0]]

    return coords

"""
get_aerial_image
PURPOSE: Return USGS Aerial image at the selected location of the selected size
IN:
-   bbox: (string) comma-separated W,S,E,N coordinates
-   width: (int) The number of pixels for the width of the image
-   height: (int) The number of pixels for the height of the image
-   bboxSR: (int) EPSG ID for Spatial Reference system used for input bbox coordinates
-       default: 3857
OUT:
-   image_info: (dict) {
-       image: image as raw data (bytes)
-       attribution: attribution text for proper use of imagery
-   }
"""
def get_aerial_image(bbox, width, height, bboxSR=3857):
    aerial_endpoint = 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export'
    layers = 0
    aerial_url = "%s?bbox=%s&imageSR=3857&bboxSR=%s&layers=%s&size=%s,%s&format=png&f=image" % (aerial_endpoint, bbox, bboxSR, layers, width, height)
    attribution = 'USGS The National Map: Orthoimagery. Data refreshed April, 2019.'

    image_data = unstable_request_wrapper(aerial_url)

    return {
        'image': image_data,
        'attribution': attribution
    }

# Create your views here.
def home(request):
    '''
    Land Mapper: Home Page
    '''
    # return render(request, 'landmapper/home.html', {})
    return render(request, 'landmapper/home.html', {})

def index(request):
    '''
    Land Mapper: Index Page
    '''
    return render(request, 'landmapper/base.html', {})

def identify(request):
    '''
    Land Mapper: Identify Pages
    '''
    return render(request, 'landmapper/base.html', {})

def report(request):
    '''
    Land Mapper: Report Pages
    '''
    return render(request, 'landmapper/base.html', {})

def create_property(request, taxlot_ids, property_name):
    '''
    Land Mapper: Create Property

    TODO:
        can a memory instance of feature be made as opposed to a database feature
            meta of model (ref: madrona.features) to be inherited?
            don't want this in a database
            use a class (python class) as opposed to django model class?
        add methods to class for
            creating property
            turn into shp
            CreatePDF, ExportLayer, BuildLegend, BuildTables?
        research caching approaches
            django docs
            django caching API
    '''
