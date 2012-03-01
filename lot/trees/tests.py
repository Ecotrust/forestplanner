import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry 
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from madrona.features import *
from madrona.features.models import Feature, PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features.forms import FeatureForm
from madrona.common.utils import kml_errors, enable_sharing
from trees.models import Stand, ForestProperty

g1 = GEOSGeometry(
      'SRID=4326;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
g1.transform(settings.GEOMETRY_DB_SRID)

class StandTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_add_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        stand1.save()

    def test_delete_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1, rx="CC") 
        stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1, rx="SW") 
        stand1.save()
        stand2.save()
        self.assertEqual(len(Stand.objects.filter(rx='CC')), 1)
        self.assertEqual(len(Stand.objects.all()), 2)
        Stand.objects.filter(rx="CC").delete()
        self.assertEqual(len(Stand.objects.filter(rx='CC')), 0)
        self.assertEqual(len(Stand.objects.all()), 1)

def ForestPropertyTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()

    def test_create_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property")
        prop1.save()

    def test_add_property_to_stand(self):
        prop1 = ForestProperty(user=self.user, name="My Property")
        prop1.save()

        self.stand1.add_to_collection(prop1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand11 in self.prop1.feature_set())

        self.stand1.remove_from_collection()
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in self.prop1.feature_set())

    def test_add_stand_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property")
        prop1.save()

        prop1.add(self.stand1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand11 in self.prop1.feature_set())

        prop1.remove(self.stand1)
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in self.prop1.feature_set())

    def test_add_property_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property")
        prop2 = ForestProperty(user=self.user, name="My Property")
        prop1.save()
        prop2.save()
        # prop1.add(prop2)
        self.assertRaises(AssertionError, prop1.add, prop2)

class RestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.options = Stand.get_options()
        self.create_url = self.options.get_create_form()

    def test_submit_not_authenticated(self):
        response = self.client.post(self.create_url, 
            {'name': "My Test", 'user': 1})
        self.assertEqual(response.status_code, 401)

    def test_submit_invalid_form(self):
        old_count = Stand.objects.count()
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {'name': 'test', 
            'geometry_orig': g1.wkt,
            'rx': 'XX', # Invalid prescription
            'domspp': 'DF'})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(old_count == Stand.objects.count())
        self.assertNotEqual(
            response.content.find('XX is not one of the available choices.'), -1)

    def test_submit_valid_form(self):
        old_count = Stand.objects.count()
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.create_url, {'name': 'test', 
            'geometry_orig': g1.wkt,
            'rx': 'CC', 
            'domspp': 'DF'})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(old_count < Stand.objects.count())
        inst = Stand.objects.get(name='test')
        self.assertTrue(
            response._get_content().find(inst.get_absolute_url()) > -1)
        
class SpatialTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()

    def test_rest_defaultkml_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('KML')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        errors = kml_errors(response.content)
        self.assertFalse(errors,"invalid KML %s" % str(errors))

