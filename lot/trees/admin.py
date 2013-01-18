from trees.models import *
from django.contrib import admin
 
class PlotLookupAdmin(admin.ModelAdmin):
    list_display = ('name', 'attr', 'units', 'weight', 'type')

admin.site.register(PlotLookup, PlotLookupAdmin)
