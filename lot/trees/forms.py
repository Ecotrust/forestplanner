from madrona.features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from trees.models import Stand, ForestProperty

class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand

class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty

class UploadStandsForm(forms.Form):
    property_pk = forms.IntegerField()
    ogrfile = forms.FileField()
