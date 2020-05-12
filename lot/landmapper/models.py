from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature, MultiPolygonFeature
from madrona.features import register, alternate, edit, get_feature_by_uid
# from madrona.features.forms import SpatialFeatureForm

"""
    From MVC/MTV Components Doc

    Flatblock (django-flatblocks)
    #Flatpage (django-flatpages)
    MenuPage (Custom)
    Taxlot (custom)
    Property (madrona polygon-feature)
        We don't want to save these - creating them on the fly may be helpful, but we'll need to delete them immediately.
    ForestType
        will all data be aggregated to a single geometric model, or will there be a forest-type lookup to go with the feature layer?
    ReportPage (optional idea)
        Could capture "Get Help" content
        Could make any future updates/additions to the report more flexible
        Would totally %$&@ with some of the proposed views below (not good).
"""

class MenuPage(models.Model):
    name = models.CharField(max_length=255)
    order = models.SmallIntegerField(default=10)
    staff_only = models.BooleanField(default=False)
    content = models.TextField(null=True, blank=True, default=None)

    def __str__(self):
        return "%s" % self.name

@register
class Taxlot(MultiPolygonFeature):

    class Options:
        form = 'features.forms.SpatialFeatureForm'
        manipulators = []

    class Meta:
        abstract = False

class Property(MultiPolygonFeature):
    class Options:
        form = 'features.forms.SpatialFeatureForm'
        manipulators = []

    class Meta:
        abstract = False

class ForestType(models.Model):
    name = models.CharField(max_length=255)
