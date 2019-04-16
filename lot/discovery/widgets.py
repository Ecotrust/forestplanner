from django.contrib.gis.forms.widgets import OpenLayersWidget

class DiscoOpenLayersWidget(OpenLayersWidget):
    template_name = 'discovery/admin/gis/openlayers.html'
