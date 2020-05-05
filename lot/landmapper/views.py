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
    except ConnectionError as e:
        if retries < 10:
            print('failed to connect to wfs %s time(s)' % retries)
            (wms,wfs) = get_soils_connectors(retries+1)
        else:
            print("ERROR: Unable to connect to WFS Server @ %s" % settings.SOIL_WFS_URL)
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
        contents = urllib.request.urlopen(url).read()
    except ConnectionError as e:
        if retries < 10:
            print('failed [%d time(s)] to connect to %s' % (retries, url))
            contents = unstable_request_wrapper(url, retries+1)
        else:
            print("ERROR: Unable to connect to %s" % url)
    except Exception as e:
        print(e)
        import ipdb; ipdb.set_trace()
        print(url)
    return contents

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
    fp.write(contents)
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
