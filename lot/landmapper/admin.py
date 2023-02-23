from django.contrib import admin
from django.db import models
from .models import MenuPage, Taxlot, ForestType, PropertyRecord, Profile
from ckeditor.widgets import CKEditorWidget
from discovery.widgets import DiscoOpenLayersWidget

# Register your models here.
class MenuPageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget}
    }
    class Meta:
        fields = '__all__'

class PropertyRecordAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date_created', 'property_id')
    fieldsets = (
        ('Property Record', {
            'fields': (
                'user', 'name', 'geometry_orig', 'geometry_final', 'record_taxlots'
            )
        }),
    )

# admin.site.unregister(FlatBlock)
admin.site.register(Profile)
admin.site.register(Taxlot)
admin.site.register(MenuPage, MenuPageAdmin)
admin.site.register(ForestType)
admin.site.register(PropertyRecord, PropertyRecordAdmin)
