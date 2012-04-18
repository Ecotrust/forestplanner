from madrona.features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from trees.models import Stand, ForestProperty

from django.forms.widgets import RadioSelect

class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand
        exclude = ('sharing_groups','content_type','object_id', 'domspp')

class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty

class UploadStandsForm(forms.Form):
    property_pk = forms.IntegerField()
    ogrfile = forms.FileField()
