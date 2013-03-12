from madrona.features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from trees.models import Stand, Strata, ForestProperty, Scenario
from madrona.analysistools.widgets import SliderWidget


class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand
        exclude = ('sharing_groups', 'content_type', 'object_id', 'elevation',
                   'imputed', 'aspect', 'slope', 'cond_id', 'strata', 'cost', 'nn_savetime', 'rast_savetime')


class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty


class StrataForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Strata


class ScenarioForm(FeatureForm):
    input_rxs = forms.CharField(widget=forms.HiddenInput(), initial="{}")
    input_property = forms.ModelChoiceField(
        label="", queryset=ForestProperty.objects.all(), widget=forms.HiddenInput())
    input_target_boardfeet = forms.FloatField(
        help_text="Target an annual cut (in boardfeet) for an even flow of timber",
        label="Target Annual Cut",
        widget=SliderWidget(min=0, max=100, step=1, show_number=True))
    input_age_class = forms.FloatField(
        help_text="Optimize for target proportion of mature trees",
        label='Target Mature Age Class',
        widget=SliderWidget(min=0, max=100, step=1, show_number=True))

    class Meta(FeatureForm.Meta):
        model = Scenario
        exclude = list(FeatureForm.Meta.exclude)
        # exclude.extend(['input_property',])
        for f in model.output_fields():
            exclude.append(f.attname)


class UploadStandsForm(forms.Form):
    property_pk = forms.IntegerField(required=False)
    new_property_name = forms.CharField(required=False)
    ogrfile = forms.FileField()
