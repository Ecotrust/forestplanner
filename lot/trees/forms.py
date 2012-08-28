from madrona.features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from trees.models import Stand, ForestProperty, Scenario

from django.forms.widgets import RadioSelect

class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand
        exclude = ('sharing_groups','content_type','object_id', 'domspp', 'rx')

class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty

class ScenarioForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Scenario
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)

class UploadStandsForm(forms.Form):
    property_pk = forms.IntegerField(required=False)
    new_property_name = forms.CharField(required=False)
    ogrfile = forms.FileField()
