from madrona.features.forms import FeatureForm, SpatialFeatureForm
from django import forms
from trees.models import Stand, Strata, ForestProperty, Scenario, ScenarioStand, MyRx, Rx
#from madrona.analysistools.widgets import SliderWidget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
import json


class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand
        exclude = ('sharing_groups', 'content_type', 'object_id', 'elevation', 'name',
                   'imputed', 'aspect', 'slope', 'cond_id', 'strata', 'cost', 'nn_savetime', 'rast_savetime')


class ScenarioStandForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ScenarioStand


class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty


class StrataForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Strata


class HiddenJSONInput(forms.HiddenInput):
    """
    Widget that properly escapes text as JSON
    Allows the the brower to directly JSON.parse() it
    i.e. returns
        <input value="{\"key\": value}">
    instead of
        <input value="{u'key': value}">
    """
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        # Only add the 'value' attribute if a value is non-empty.
        if value != '':
            final_attrs['value'] = json.dumps(value)
        return mark_safe(u'<input%s />' % flatatt(final_attrs))


class ScenarioForm(FeatureForm):
    input_rxs = forms.CharField(widget=HiddenJSONInput(), required=False)
    spatial_constraints = forms.CharField(widget=forms.HiddenInput(), required=False)
    input_property = forms.ModelChoiceField(
        label="", queryset=ForestProperty.objects.all(), widget=forms.HiddenInput())
    #
    # Just hide the scheduler inputs until we get it hooked up
    #
    # input_target_boardfeet = forms.FloatField(
    #     help_text="Target an annual cut (in boardfeet) for an even flow of timber",
    #     label="Target Annual Cut",
    #     widget=SliderWidget(min=0, max=100, step=1, show_number=True))
    # input_age_class = forms.FloatField(
    #     help_text="Optimize for target proportion of mature trees",
    #     label='Target Mature Age Class',
    #     widget=SliderWidget(min=0, max=100, step=1, show_number=True))
    input_target_boardfeet = forms.FloatField(widget=forms.HiddenInput(),
        label="Boardfeet", initial=0, required=False)
    input_age_class = forms.FloatField(widget=forms.HiddenInput(),
        label="Age class", initial=0, required=False)
    input_target_carbon = forms.BooleanField(widget=forms.HiddenInput(),
        label="Carbon", initial=True, required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 8}),
        label="Description", required=False)

    class Meta(FeatureForm.Meta):
        model = Scenario
        exclude = list(FeatureForm.Meta.exclude) + ['output_scheduler_results']

    def __init__(self, *args, **kwargs):
        super(ScenarioForm, self).__init__(*args, **kwargs)

        # more useful error message
        for field in self.fields.values():
            field.error_messages = {'required': 'The %s field is required' % field.label}


class UploadStandsForm(forms.Form):
    property_pk = forms.IntegerField(required=False)
    new_property_name = forms.CharField(required=False)
    ogrfile = forms.FileField()


class MyRxForm(FeatureForm):
    rx_internal_name = forms.CharField(required=True)
    rx = forms.CharField(widget=forms.HiddenInput(), required=False)  # calculated from internal name

    def clean(self):
        """
        We POST the rx's internal_name but need to make a FK reference to the Rx itself
        """
        cleaned_data = self.cleaned_data
        rx_internal_name = cleaned_data.get("rx_internal_name")

        try:
            rx = Rx.objects.get(internal_name=rx_internal_name)
        except Rx.DoesNotExist:
            del cleaned_data['rx']
            raise forms.ValidationError("Rx with name '%s' not found" % rx_internal_name)

        cleaned_data['rx'] = rx
        del cleaned_data['rx_internal_name']
        return cleaned_data

    class Meta(FeatureForm.Meta):
        model = MyRx
        exclude = ('content_type', 'object_id')
