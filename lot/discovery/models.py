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

    @property
    # @cachemethod("DiscoveryStand_%(id)s_variant")
    def variant(self):
        '''
        Returns: Closest FVS variant instance
        '''
        from trees.models import FVSVariant
        geom = self.lot_property.geometry_final.point_on_surface

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

    def get_stand_stats(self):
        total_ba = 0
        species_dict = {}
        stand = self.get_stand()
        if stand and stand.strata:
            if 'classes' in stand.strata.stand_list.keys():
                treelist = stand.strata.stand_list['classes']
                for entry in treelist:
                    species = entry[0]
                    dbh = (entry[1]+entry[2])/2
                    tpa = entry[3]
                    # BA = pi * (DBH/2)**2 / 144, which can be simplified to BA = 0.005454 * DBH**2
                    entry_ba = 0.005454 * dbh**2 * tpa
                    if species in species_dict.keys():
                        species_dict[species] += entry_ba
                    else:
                        species_dict[species] = entry_ba
                    total_ba += entry_ba
                basal_area_dict = {'total': total_ba, 'species': species_dict}
            else:
                basal_area_dict = None
            stand_tpa = stand.strata.search_tpa
        else:
            return {
                'tpa': None,
                'basal_area_dict': None,
                'forest_type': None,
                'tree_size': None,
            }

        return {
            'tpa': int(stand_tpa),
            'basal_area_dict': basal_area_dict,
            'forest_type': self.get_forest_type(basal_area_dict),
            'tree_size': self.get_tree_size(basal_area_dict['total'], stand_tpa),
        }

    def get_forest_type(self, basal_area_dict=None):
        if basal_area_dict:
            species_composition = {
                'hardwood': 0,
                'softwood': 0,
                'unknown': 0,
                'predominant': False,
                'prevalent': [],
            }

            for species in basal_area_dict['species'].keys():
                percent_ba = basal_area_dict['species'][species]/basal_area_dict['total']
                if percent_ba >= 0.75:
                    species_composition['predominant'] = species
                elif percent_ba >= 0.25:
                    species_composition['prevalent'].append(species)
                if species in settings.HARD_SOFTWOOD_LOOKUP.keys():
                    species_composition[settings.HARD_SOFTWOOD_LOOKUP[species]] += percent_ba
                else:
                    species_composition['unknown'] += percent_ba
            if species_composition['predominant']:
                forest_type = species_composition['predominant']
            elif len(species_composition['prevalent']) > 0:
                forest_type = '%s mix' % ' / '.join(species_composition['prevalent'])
            elif species_composition['hardwood'] >= species_composition['softwood'] and species_composition['hardwood'] >= species_composition['unknown']:
                forest_type = 'Hardwood mix'
            elif species_composition['softwood'] >= species_composition['hardwood'] and species_composition['softwood'] >= species_composition['unknown']:
                forest_type = 'Softwood mix'
            else:
                forest_type = 'Mix'
        else:
            forest_type = "Unknown"
        return forest_type

    def get_tree_size(self, basal_area, tpa):
        import math
        if basal_area and tpa:
            qmd = math.sqrt((basal_area/tpa)/0.005454)
            if qmd < 1:
                size_class = "Nonstocked"
            elif qmd < 5:
                size_class = "Seedling/Sapling"
            elif qmd < 10:
                size_class = "Small Tree"
            elif qmd < 15:
                size_class = "Medium Tree"
            elif qmd < 20:
                size_class = "Large Tree"
            elif qmd >= 20:
                size_class = "Very Large Tree"
            else:
                size_class = "Unknown"
        else:
            qmd = "Unknown"
            size_class = "Unknown"
        return {
            'qmd': qmd,
            'size_class': size_class
        }

    def get_page_status(self):
        page_status = {
            'uid': self.uid,
            'titles': settings.PAGE_TITLES,
            'display': False,
            'map': False,
            'collect': False,
            'profile': False,
            'outcomes': False,
            'report': False,
        }
        if self.lot_property:
            page_status['display'] = True
            page_status['map'] = True
            stand = self.get_stand()
            if stand:
                page_status['collect'] = True
                if stand.strata:
                    page_status['profile'] = True
                    page_status['outcomes'] = True
                    page_status['report'] = True
        return page_status

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

        if not self.lot_property:
            import time
            time.sleep(5)
        if self.lot_property:
            self.lot_property.create_default_discovery_scenarios()

    class Options:
        form = "discovery.forms.DiscoveryStandForm"

class DiscoveryScenario(models.Model):
    name = models.CharField(max_length=255, help_text="The name of the scenario to be created")
    description = models.TextField(blank=True, null=True, default=None, help_text='The description to be displayed in the tooltip for selecting scenarios created from this')
    show = models.BooleanField(default=False, help_text="This scenario is ready to be shown as an option for all appropriate stands")
    default = models.BooleanField(default=False, help_text="This scenario should be selected automatically for display on compare page")

    def __str__(self):
        return self.name

class DiscoveryRx(models.Model):
    from trees.models import FVSVariant, Rx
    discovery_scenario = models.ForeignKey(DiscoveryScenario, on_delete="CASCADE")
    variant = models.ForeignKey(FVSVariant, on_delete="CASCADE")
    rx = models.ForeignKey(Rx, on_delete="CASCADE")

    def __str__(self):
        return str('%s - %s - %s' % (str(self.discovery_scenario), str(self.variant), str(self.rx)))
