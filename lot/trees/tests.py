import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry 
from django.contrib.auth.models import User
from madrona.features import *
from madrona.features.models import Feature, PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features.forms import FeatureForm
from madrona.common.utils import kml_errors, enable_sharing
from trees.models import Stand, ForestProperty

class StandTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_add_stand(self):
        g1 = GEOSGeometry('SRID=4326;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
        g1.transform(settings.GEOMETRY_DB_SRID)
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        self.stand1.save()

    def test_delete_stand(self):
        self.assertEqual(1 + 1, 2)

class RestTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.client.login(username='featuretest', password='pword')

        g1 = GEOSGeometry('SRID=4326;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
        g1.transform(settings.GEOMETRY_DB_SRID)
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        self.stand1.save()
        
    def test_rest_add_stand(self):
        self.assertEqual(1 + 1, 2)

    def test_rest_delete_stand(self):
        self.assertEqual(1 + 1, 2)

    def test_rest_defaultkml_url(self):
        link = self.stand1.options.get_link('KML')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        errors = kml_errors(response.content)
        self.assertFalse(errors,"invalid KML %s" % str(errors))
        

