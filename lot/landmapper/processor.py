from landmapper.models import MenuPage
def menus(request):
    return {'menu_items': MenuPage.objects.all().order_by('order')}