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
