from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit, get_feature_by_uid
from trees.models import ForestProperty, Stand

# Create your models here.

@register
class DiscoveryStand(Feature):
    from django.conf import settings
    lot_property = models.ForeignKey(ForestProperty, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, null=True, default=None)
    splash_image = models.ImageField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        from django.contrib.auth.models import User
        from django.contrib.gis import geos

        try:
            form = kwargs['form']
            geometry_final = geos.GEOSGeometry(form.data.pop('geometry_final')[0])
            if hasattr(self, 'lot_property') and not self.lot_property == None:
                self.lot_property.geometry_final = geometry_final
                self.lot_property.save()
            else:
                # stupid hack since passing form.data didn't seem to like any value for 'user'
                data = {
                    'user': User.objects.get(pk=form.data['user']),
                    'name': form.data['name'],
                    'geometry_final': geometry_final
                }
                # ForestProperty.geometry_final MUST be MultiPolygon.
                if isinstance(geometry_final, geos.Polygon):
                    data['geometry_final'] = geos.MultiPolygon(geometry_final)
                lot_property = ForestProperty(**data)
                lot_property.save()
                self.lot_property = lot_property

            property_stands = self.lot_property.feature_set(feature_classes=[Stand,])
            if len(property_stands) == 0:
                stand_dict = {
                    'geometry_orig': geometry_final,
                    'geometry_final': geometry_final,
                    'user': self.lot_property.user,
                    'name': self.lot_property.name,
                }
                prop_stand = Stand.objects.create(**stand_dict)
                prop_stand.add_to_collection(self.lot_property) # or self.lot_property.add(prop_stand)
            else:
                if len(property_stands) == 1:
                    prop_stand = property_stands[0]
                else:
                    property_stands.sort(key=lambda x: x.geometry_final.area, reverse=True)
                    prop_stand = property_stands[0]
                prop_stand.geometry_orig = geometry_final
                prop_stand.geometry_final = geometry_final
            prop_stand.save()

            self.full_clean()

            super(DiscoveryStand, self).save(*args, **kwargs)
        except ValidationError as e:
            non_field_errors = ""
            for key in e.message_dict.keys():
                non_field_errors += "%s: %s. " % (key, e.message_dict[key])
            return non_field_errors

    class Options:
        form = "discovery.forms.DiscoveryStandForm"
