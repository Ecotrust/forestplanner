from django.contrib.gis.forms.fields import GeometryField
from discovery.widgets import DiscoOpenLayersWidget

class DiscoGeometryField(GeometryField):
    widget = DiscoOpenLayersWidget
