from django.contrib import admin
from django.db import models
from .models import MenuPage, Taxlot, ForestType
from ckeditor.widgets import CKEditorWidget

# Register your models here.
class MenuPageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget}
    }
    class Meta:
        fields = '__all__'

# admin.site.unregister(FlatBlock)
admin.site.register(Taxlot)
admin.site.register(MenuPage, MenuPageAdmin)
admin.site.register(ForestType)
