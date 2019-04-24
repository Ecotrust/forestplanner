from django import forms
from discovery.models import DiscoveryStand
from trees.forms import PropertyForm

class DiscoveryStandForm(PropertyForm):

    # name = forms.CharField(label=None,
    #                         widget=forms.TextInput(attrs={'placeholder': 'Name your stand'}))
    geometry_final = forms.CharField(widget=forms.HiddenInput)
    pk = forms.IntegerField(widget=forms.HiddenInput, required=False)


    class Meta(PropertyForm.Meta):
        model = DiscoveryStand
        fields = [
            'name',
            'user',
        ]

    def __init__(self, *args, **kwargs):
        # we don't want to do 'propertyform' validation, so skip straight to its parent.
        super(PropertyForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = ''
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['name'].widget.attrs['placeholder'] = 'Name your stand'
        self.fields['name'].help_text = 'You can edit your stand later if needed.'
        # self.fields['name'].help_text.attrs['class'] = 'form-text text-muted stand-form-help'

class ExampleStandToDiscoveryStandForm(DiscoveryStandForm):
    image = forms.ImageField(required=False)
    splash_image = forms.ImageField(required=False)

class DiscoveryStandListEntryForm(forms.Form):
    species = forms.CharField()
    size_class = forms.CharField()
    tpa = forms.FloatField()
