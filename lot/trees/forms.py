from madrona.features.forms import FeatureForm, SpatialFeatureForm
from trees.models import Stand, ForestProperty

class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand

class PropertyForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = ForestProperty
