from django.shortcuts import render

def get_soils_connector():
    '''
    Land Mapper: Soils WMS connector
    '''
    from owslib.wms import WebMapService
    wms = WebMapService('https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms')
    return wms

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
