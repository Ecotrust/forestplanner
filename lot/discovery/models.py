from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit, get_feature_by_uid
from trees.models import ForestProperty, Stand

# Create your models here.

class DiscoveryStand(FeatureCollection):
    from django.conf import settings
    lot_property = models.ForeignKey(ForestProperty, on_delete=models.CASCADE)
    lot_stand = models.ForeignKey(Stand, on_delete=models.CASCADE)
    image = models.ImageField(null=True, default=None)
