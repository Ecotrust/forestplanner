from django.contrib import admin
from django.forms import ModelForm, ChoiceField
from django.forms.models import BaseInlineFormSet

# Register your models here.
from discovery.widgets import DiscoOpenLayersWidget
from discovery.models import DiscoveryStand, ExampleStand, StandListEntry
from trees.models import FVSSpecies

admin.site.register(DiscoveryStand)

def StandListInlineFormFactory(species_choice_list):
    class StandListInlineForm(ModelForm):
        def __init__(self, *args, **kwargs):
            super(StandListInlineForm, self).__init__(*args, **kwargs)
            if species_choice_list:
                self.fields['species'] = ChoiceField(
                    choices=species_choice_list
                )

        class Meta:
            model = StandListEntry
            fields = '__all__'

    return StandListInlineForm

def StandListInlineFactory(species_choice_list):
    # class StandListInline(admin.StackedInline):
    class StandListInline(admin.TabularInline):
        model = StandListEntry
        # autocomplete_fields = ['species']
        form = StandListInlineFormFactory(species_choice_list)

    return StandListInline

class ExampleStandForm(ModelForm):
    class Meta:
        model = ExampleStand
        widgets = {
            # 'geometry_orig': DiscoOpenLayersWidget(),
            'geometry_final': DiscoOpenLayersWidget(),
        }
        fields = ['user', 'name', 'geometry_orig', 'geometry_final', 'image', 'splash_image', 'age']


class ExampleStandAdmin(admin.ModelAdmin):
    form = ExampleStandForm
    inlines = []

    # we define inlines with factory to create Inline class with request inside
    def change_view(self, request, object_id, form_url='', extra_context=None):
        from django.urls import resolve
        from trees.views import get_species_sizecls_json
        species_choice_list = None
        resolved = resolve(request.path_info)
        examplestand_pk_str = resolved.kwargs.pop('object_id', None)
        context = {}
        context.update(extra_context or {})
        if examplestand_pk_str:
            examplestand_pk = int(examplestand_pk_str)
            try:
                parentstand = ExampleStand.objects.get(pk=examplestand_pk)
            except Exception as e:
                parentstand = None

            if parentstand:
                variant = parentstand.variant
                choice_json = get_species_sizecls_json(variant)
                context.update({'choice_json': choice_json})
                species_choice_list = [('', '----')] + [(x['species'], x['species']) for x in choice_json]
        self.inlines = (StandListInlineFactory(species_choice_list), )
        return super(ExampleStandAdmin, self).change_view(request, object_id, form_url, context)

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
