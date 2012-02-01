from madrona.features.forms import FeatureForm, SpatialFeatureForm
from trees.models import Stand, Unit

class StandForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = Stand

class UnitForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Unit
