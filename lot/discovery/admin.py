from django.contrib import admin
from django.forms import ModelForm
from discovery.widgets import DiscoOpenLayersWidget

# Register your models here.
from discovery.models import DiscoveryStand, ExampleStand, StandListEntry
from trees.models import FVSSpecies

admin.site.register(DiscoveryStand)

class FVSSpeciesAdmin(admin.ModelAdmin):
    search_fields = ['common', 'scientific']

# class StandListInline(admin.StackedInline):
class StandListInline(admin.TabularInline):
    model = StandListEntry
    autocomplete_fields = ['species']

class ExampleStandForm(ModelForm):
    class Meta:
        model = ExampleStand
        widgets = {
            'geometry_orig': DiscoOpenLayersWidget(),
            'geometry_final': DiscoOpenLayersWidget(),
        }
        fields = ['user', 'name', 'geometry_orig', 'image', 'splash_image', 'age']


class ExampleStandAdmin(admin.ModelAdmin):
    form = ExampleStandForm
    inlines = [
        StandListInline,
    ]

admin.site.register(FVSSpecies, FVSSpeciesAdmin)
admin.site.register(ExampleStand, ExampleStandAdmin)


# blatantly ripped off from Anatolij at https://stackoverflow.com/a/18559785/706797
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db import models


from ckeditor.widgets import CKEditorWidget

class FlatPageCustom(FlatPageAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget}
    }
    class Meta:
        fields = '__all__'

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageCustom)
