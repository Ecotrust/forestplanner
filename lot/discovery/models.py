from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit, get_feature_by_uid
from trees.models import ForestProperty, Stand, FVSSpecies, County
from django.core.cache import cache
from django.conf import settings

# Create your models here.

def cachemethod(cache_key, timeout=60 * 60 * 24 * 7):
    '''
    http://djangosnippets.org/snippets/1130/
    default timeout = 1 week

    @property
    @cachemethod("SomeClass_get_some_result_%(id)s")
    '''
    def paramed_decorator(func):
        def decorated(self, *args):
            key = cache_key % self.__dict__
            res = cache.get(key)
            if res is None:
                res = func(self, *args)
                cache.set(key, res, timeout)
            return res
        return decorated
    return paramed_decorator

@register
class ExampleStand(PolygonFeature):
    image = models.ImageField(blank=True, null=True, default=None)
    splash_image = models.ImageField(blank=True, null=True, default=None)
    age = models.IntegerField()

    @property
    def acres(self):
        try:
            g2 = self.geometry_final.transform(
                settings.EQUAL_AREA_SRID, clone=True)
            area_m = g2.area
        except:
            return None
        return area_m * settings.EQUAL_AREA_ACRES_CONVERSION

    @property
    @cachemethod("ExampleStand_%(id)s_location")
    def location(self):
        '''
        Returns: (CountyName, State)
        '''
        geom = self.geometry_final
        if geom:
            counties = County.objects.filter(geom__bboverlaps=geom)
        else:
            return None

        if not geom.valid:
            geom = geom.buffer(0)
        the_size = 0
        the_county = (None, None)
        for county in counties:
            county_geom = county.geom
            if not county_geom.valid:
                county_geom = county_geom.buffer(0)
            if county_geom.intersects(geom):
                try:
                    overlap = county_geom.intersection(geom)
                except Exception as e:
                    logger.error(self.uid + ": " + str(e))
                    continue
                area = overlap.area
                if area > the_size:
                    the_size = area
                    the_county = (county.cntyname.title(), county.stname)
        return the_county

    def to_grid(self):
        from datetime import date
        out_dict = {
            'uid': self.uid,
            'getContent': '/discovery/modal_content/stand/%s/' % self.uid,
        }
        if self.image:
            out_dict['image'] = self.image.url
        else:
            out_dict['image'] = settings.DEFAULT_STAND_IMAGE
        if self.splash_image:
            out_dict['splash_image'] = self.splash_image.url
        else:
            out_dict['splash_image'] = settings.DEFAULT_STAND_SPLASH
        out_dict['labels'] = [
            {'label': 'title', 'value': self.name},
            {'label': 'Location', 'value': "%s County, %s" % self.location},
            {'label': 'Area', 'value': int(round(self.acres)), 'posttext': 'acres'},
            {'label': 'Modified', 'value': self.date_modified.strftime("%-I:%M %p, %-m/%-d/%Y")},
        ]

        return out_dict

    class Options:
        form = "trees.forms.StandForm"
        form_template = "trees/stand_form.html"
        manipulators = []

size_class_choices = (
    (0, '0" to 2"'),
    (2, '2" to 6"'),
    (6, '6" to 12"'),
    (12, '12" to 24"'),
    (24, '24" to 36"'),
    (36, '36" to 48"'),
    (48, '48" to 70"'),
    (70, 'Greater than 70"'),
)

class StandListEntry(models.Model):
    stand = models.ForeignKey(ExampleStand, on_delete="CASCADE")
    species = models.ForeignKey(FVSSpecies, on_delete="CASCADE")
    size_class = models.SmallIntegerField(choices = size_class_choices)
    tpa = models.SmallIntegerField()

@register
class DiscoveryStand(Feature):
    lot_property = models.ForeignKey(ForestProperty, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, null=True, default=None)
    splash_image = models.ImageField(blank=True, null=True, default=None)

    def get_stand(self):
        property_stands = self.lot_property.feature_set(feature_classes=[Stand,])
        if len(property_stands) == 0:
            return None
        if len(property_stands) >= 1:
            property_stands.sort(key=lambda x: x.geometry_final.area, reverse=True)
        return property_stands[0]

    def to_grid(self):
        from datetime import date
        out_dict = {
            'uid': self.uid,
            'getContent': '/discovery/modal_content/stand/%s/' % self.uid,
        }
        if self.image:
            out_dict['image'] = self.image.url
        else:
            out_dict['image'] = settings.DEFAULT_STAND_IMAGE
        if self.splash_image:
            out_dict['splash_image'] = self.splash_image.url
        else:
            out_dict['splash_image'] = settings.DEFAULT_STAND_SPLASH
        out_dict['labels'] = [
            {'label': 'title', 'value': self.name},
            {'label': 'Location', 'value': "%s County, %s" % self.lot_property.location},
            {'label': 'Area', 'value': int(round(self.lot_property.acres)), 'posttext': 'acres'},
            {'label': 'Modified', 'value': self.date_modified.strftime("%-I:%M %p, %-m/%-d/%Y")},
        ]

        return out_dict

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        from django.contrib.auth.models import User
        from django.contrib.gis import geos

        if 'form' in kwargs.keys():
            try:
                form = kwargs['form']
                if form.data['pk'] and not self.pk == int(form.data['pk']):
                    DiscoveryStand.objects.get(pk=int(form.data['pk'])).save(*args, **kwargs)
                else:
                    geometry_final = geos.GEOSGeometry(form.data.pop('geometry_final')[0])
                    if hasattr(self, 'lot_property') and not self.lot_property == None:
                        if isinstance(geometry_final, geos.MultiPolygon):
                            self.lot_property.geometry_final = geometry_final
                        else:
                            self.lot_property.geometry_final = geos.MultiPolygon(geometry_final)
                        self.lot_property.save()
                    else:
                        # stupid hack since passing form.data didn't seem to like any value for 'user'
                        data = {
                            'user': User.objects.get(pk=form.data['user']),
                            'name': form.data['name'],
                            'geometry_final': geometry_final
                        }
                        # ForestProperty.geometry_final MUST be MultiPolygon.
                        if isinstance(geometry_final, geos.MultiPolygon):
                            data['geometry_final'] = geometry_final
                        else:
                            data['geometry_final'] = geos.MultiPolygon(geometry_final)
                        lot_property = ForestProperty(**data)
                        lot_property.save()
                        self.lot_property = lot_property

                    prop_stand = self.get_stand()
                    if not prop_stand:
                        stand_dict = {
                            'geometry_orig': geometry_final,
                            'geometry_final': geometry_final,
                            'user': self.lot_property.user,
                            'name': self.lot_property.name,
                        }
                        prop_stand = Stand.objects.create(**stand_dict)
                        prop_stand.add_to_collection(self.lot_property) # or self.lot_property.add(prop_stand)
                    else:
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
        else:
            super(DiscoveryStand, self).save(*args, **kwargs)

    class Options:
        form = "discovery.forms.DiscoveryStandForm"
