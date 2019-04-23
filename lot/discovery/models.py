from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature
from madrona.features import register, alternate, edit, get_feature_by_uid
from trees.models import ForestProperty, Stand, County
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
    content = models.TextField(null=True, blank=True, default=None)

    def __str__(self):
        return "%s" % self.name

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
    # @cachemethod("ExampleStand_%(id)s_location")
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

    @property
    # @cachemethod("ExampleStand_%(id)s_variant")
    def variant(self):
        '''
        Returns: Closest FVS variant instance
        '''
        from trees.models import FVSVariant
        geom = self.geometry_final.point_on_surface

        variants = FVSVariant.objects.all()

        min_distance = 99999999999999.0
        the_variant = None
        for variant in variants:
            variant_geom = variant.geom
            if not variant_geom.valid:
                variant_geom = variant_geom.buffer(0)
            dst = variant_geom.distance(geom)
            if dst == 0.0:
                return variant
            if dst < min_distance:
                min_distance = dst
                the_variant = variant
        return the_variant

    def to_grid(self):
        from datetime import date
        out_dict = {
            'uid': self.uid,
            'getContent': '/discovery/modal_content/example_stand/%s/' % self.uid,
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

class StandListEntry(models.Model):
    stand = models.ForeignKey(ExampleStand, on_delete="CASCADE")
    species = models.CharField(max_length=255)
    size_class = models.CharField(max_length=255)
    tpa = models.SmallIntegerField()

    # TODO: validate unique: stand + species + size_class

@register
class DiscoveryStand(Feature):
    lot_property = models.ForeignKey(ForestProperty, on_delete=models.CASCADE, null=True, blank=True, default=None)
    image = models.ImageField(blank=True, null=True, default=None)
    splash_image = models.ImageField(blank=True, null=True, default=None)

    def __str__(self):
        return self.name
        
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

    def get_new_lot_property_value(self, user, name, geometry_final):
        from django.contrib.gis import geos
        data = {
            'user': user,
            'name': name,
            'geometry_final': geometry_final
        }
        # ForestProperty.geometry_final MUST be MultiPolygon.
        if isinstance(geometry_final, geos.MultiPolygon):
            data['geometry_final'] = geometry_final
        else:
            data['geometry_final'] = geos.MultiPolygon(geometry_final)
        lot_property = ForestProperty(**data)
        lot_property.save()
        return lot_property

    def get_or_create_property_stand(self, geometry_final):
        from django.contrib.gis import geos
        try:
            if not isinstance(geometry_final, geos.Polygon):
                geometry_final = geos.Polygon(geometry_final)
        except Exception as e:
            print(e)
            pass

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

    def delete(self, *args, **kwargs):
        lot_property = None
        if self.lot_property:
            lot_property = self.lot_property
            for stand in self.lot_property.feature_set(feature_classes=[Stand,]):
                if stand.strata:
                    stand.strata.delete()
                stand.delete()
        super(DiscoveryStand, self).delete(*args, **kwargs)
        if lot_property:
            lot_property.delete()

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
                        user = User.objects.get(pk=form.data['user'])
                        name = form.data['name']
                        lot_property = self.get_new_lot_property_value(user, name, geometry_final)
                        self.lot_property = lot_property

                    self.get_or_create_property_stand(geometry_final)

            except ValidationError as e:
                non_field_errors = ""
                for key in e.message_dict.keys():
                    non_field_errors += "%s: %s. " % (key, e.message_dict[key])
                return non_field_errors
        elif 'geometry_final' in kwargs.keys():
            if not self.user and 'user' in kwargs.keys():
                self.user = kwargs.pop('user')
            if not self.name and 'name' in kwargs.keys():
                name = kwargs.pop('name')
            geometry_final = kwargs.pop('geometry_final')
            lot_property = self.get_new_lot_property_value(self.user, self.name, geometry_final)
            self.lot_property = lot_property
            self.get_or_create_property_stand(geometry_final)

        super(DiscoveryStand, self).save(*args, **kwargs)

    class Options:
        form = "discovery.forms.DiscoveryStandForm"
