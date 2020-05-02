from django.shortcuts import render

def get_soils_connectors():
    '''
    Land Mapper: Soils WMS connector
    '''
    from owslib.wms import WebMapService
    from owslib.wfs import WebFeatureService
    wms = WebMapService('http://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms')
    # wfs = WebFeatureService(url='https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDMWM.wfs', version='1.1.0')
    wfs = WebFeatureService(url='http://sdmdataaccess.sc.egov.usda.gov/Spatial/SDMWGS84GEOGRAPHIC.wfs', version='1.1.0')
    return (wms,wfs)

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
