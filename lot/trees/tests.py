import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry 
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from simplejson import loads
from madrona.features import *
from madrona.features.models import Feature, PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features.forms import FeatureForm
from madrona.common.utils import kml_errors, enable_sharing
from trees.models import Stand, ForestProperty

g1 = GEOSGeometry(
      'SRID=4326;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
g1.transform(settings.GEOMETRY_DB_SRID)

class StandTest(TestCase):
    ''' 
    Basic tests for adding stands
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_add_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        stand1.save()

    def test_incomplete_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        stand1.save()
        self.assertFalse(stand1.complete)
        self.assertEqual(stand1.rx, '--')
        stand1.rx = "CC"
        stand1.domspp = "DF"
        stand1.save()
        self.assertTrue(stand1.complete)

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
    '''
    Basic tests for adding/removing stands from a property
    TODO Test that date_modified reflects updates to the stands
    '''

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
        # This `prop1.add(prop2)` should fail
        self.assertRaises(AssertionError, prop1.add, prop2)


class RestTest(TestCase):
    '''
    Basic tests of the REST API 
    A bit of a dup of the features tests but more concise and specific
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.options = Stand.get_options()
        self.create_url = self.options.get_create_form()
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1, rx='CC', domspp='DF') 
        self.stand1.save()
        self.stand1_form_url = self.options.get_update_form(self.stand1.pk)
        self.stand1_url = self.stand1.get_absolute_url()
        enable_sharing()

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

    def test_get_form(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.get(self.stand1_form_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.find('My Stand'), -1)

    def test_post(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.stand1_url, {
            'name': 'My New Name', 
            'geometry_orig': self.stand1.geometry_orig.wkt,
            'rx': self.stand1.rx,
            'domspp': self.stand1.domspp
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Stand.objects.get(pk=self.stand1.pk).name, 'My New Name')

    def test_post_validation_error(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.post(self.stand1_url, {
            'name': 'Another New Name', 
            'geometry_orig': self.stand1.geometry_orig.wkt,
            'rx': 'XX', # invalid rx
            'domspp': self.stand1.domspp
        })
        self.assertEqual(response.status_code, 400)
        # Nothing should have changed
        self.assertEqual(Stand.objects.get(pk=self.stand1.pk).name, 'My Stand')

    def test_delete(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(Stand.objects.filter(pk=self.stand1.pk).count(), 1)
        response = self.client.delete(self.stand1_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Stand.objects.filter(pk=self.stand1.pk).count(), 0)
        
    def test_show(self):
        self.client.login(username='featuretest', password='pword')
        response = self.client.get(self.stand1_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.find('<title>My Stand</title>'), -1)

    def test_unauthorized(self):
        response = self.client.get(self.stand1_url)
        self.assertEqual(response.status_code, 401)

class UserPropertyListTest(TestCase):
    '''
    test web service to grab json of user's properties
    {uid:name, ..}
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_unauth(self):
        url = reverse('trees-user_property_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_jsonlist_link(self):
        self.client.login(username='featuretest', password='pword')
        url = reverse('trees-user_property_list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        self.assertEquals(plist, {})

        prop1 = ForestProperty(user=self.user, name="My Property")
        prop1.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        print response.content
        self.assertEquals(plist.items()[0][1], 'My Property')

class ManipulatorsTest(TestCase):
    '''
    test overlap/sliver manipulators
    '''
    pass

class SpatialTest(TestCase):
    '''
    Tests the spatial representations of Stands and ForestProperties
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property")
        self.prop1.save()
        self.prop1.add(self.stand1)

    def test_rest_defaultkml_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('KML')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        errors = kml_errors(response.content)
        self.assertFalse(errors,"invalid KML %s" % str(errors))

    def test_stand_json(self):
        thejson = self.stand1.geojson
        d = loads(thejson)
        self.assertEquals(d['properties']['name'], 'My Stand')

    def test_property_json(self):
        thejson = self.prop1.geojson
        d = loads(thejson)
        self.assertEquals(len(d['features']), 1)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        self.prop1.add(self.stand2)
        thejson = self.prop1.geojson
        d = loads(thejson)
        self.assertEquals(len(d['features']), 2)

    def test_stand_json_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('GeoJSON')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        
    def test_multistand_json_url(self):
        self.client.login(username='featuretest', password='pword')
        uids = [self.stand1.uid, self.stand2.uid]
        link = Stand.get_options().get_link('GeoJSON')
        url = link.reverse([self.stand1, self.stand2])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(len(d['features']), 2)
        foundit = False
        for f in d['features']:
            if f['properties']['name'] == 'My Stand2':
                foundit = True
        self.assertTrue(foundit)

    def test_property_json_url(self):
        self.prop1.add(self.stand2)
        self.client.login(username='featuretest', password='pword')
        link = self.prop1.options.get_link('Property GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(len(d['features']), 2)
        foundit = False
        for f in d['features']:
            if f['properties']['name'] == 'My Stand2':
                foundit = True
        self.assertTrue(foundit)


class ImputeTest(TestCase):
    '''
    Does this occur on model save()? Async or sync?
    Or is there another API call done? Async or sync?
    # Single raster stats on GNN
    # Async raster stats
    # Raster stats at the property level (or multiple stands)
    # test pulling useful tree data out of database
    '''
    pass

class StandImportTest(TestCase):
    '''
    TODO
    # test bad shapefiles (other geom types, bad mapping dict)
    # assert that mapped attributes are populated
    '''
    def setUp(self):
        d = os.path.dirname(__file__)
        self.shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.shp'))
        self.bad_shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_bad.shp'))
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property")
        self.prop1.save()

    def test_shp_exists(self):
        self.assertTrue(os.path.exists(self.shp_path), self.shp_path)

    def test_importer_py(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        from trees.utils import StandImporter
        s = StandImporter(self.prop1)
        s.import_ogr(self.shp_path) 

        self.assertEqual(len(Stand.objects.all()), 37)
        self.assertEqual(len(Stand.objects.filter(rx='SW',domspp='MH')), 3)
        # from the default 'name' field this time
        self.assertEqual(len(Stand.objects.filter(name='001A')), 0) 
        self.assertEqual(len(Stand.objects.filter(name='277')), 1) 
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_py_fieldmap(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        from trees.utils import StandImporter
        s = StandImporter(self.prop1)
        field_mapping = {'name': 'STAND_TEXT'}
        s.import_ogr(self.shp_path, field_mapping) 

        self.assertEqual(len(Stand.objects.all()), 37)
        self.assertEqual(len(Stand.objects.filter(rx='SW',domspp='MH')), 3)
        # from the 'STAND_TEXT' field this time
        self.assertEqual(len(Stand.objects.filter(name='001A')), 1) 
        self.assertEqual(len(Stand.objects.filter(name='277')), 0) 
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_py_bad(self):
        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

        from trees.utils import StandImporter
        s = StandImporter(self.prop1)
        with self.assertRaises(Exception):
            s.import_ogr(self.bad_shp_path)

        self.assertEqual(len(Stand.objects.all()), 0)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotEqual(response.content.find('success'), -1, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 37)

    def test_importer_http_unauth(self):
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http_badfile(self):
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_bad.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': self.prop1.pk, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 500, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 0)

    def test_importer_http_badproperty(self):
        '''
        If no property is found belonging to the user, should get a 404
        '''
        self.client.login(username='featuretest', password='pword')
        self.assertEqual(len(self.prop1.feature_set()), 0)
        d = os.path.dirname(__file__)
        ogr_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands_bad.zip'))
        f = open(ogr_path)
        url = reverse('trees-upload_stands')
        response = self.client.post(url, {'property_pk': 8675309, 'ogrfile': f})
        f.close()
        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(len(self.prop1.feature_set()), 0)
        

class GrowthYieldTest(TestCase):
    '''
    # Test via python API 
    self.prop = ForestProperty(..)
    self.prop.run_gy()

    # Test via REST API
    link = self.stand1.options.get_link('Grow')
    url = link.reverse(self.prop)
    response = self.client.post(url)
    # check that reponse is OK ("Scheduling has commenced..")
    '''
    pass

class AdjacencyTest(TestCase):
    '''
    Test that stand adjacency can be reliably determined
    self.prop = ForestProperty(..)
    adj = self.prop.adjacency 
    # @property method with caching
    # returns what? list or txt or file handle? 
    # does it also check for slivers or overlap? 

    needs fixture
    '''
    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property")
        self.prop1.save()
        self.prop1.add(self.stand1)
        self.prop1.add(self.stand2)

    def test_adjacency(self):
        adj_text = """adjacency 
        stand1, stand2
        """
        #self.assertEquals(self.prop1.adjacency, adj_text)

class SchedulerTest(TestCase):
    '''
    # Test via python API 
    self.prop.schedule()

    # Test via REST API
    link = self.stand1.options.get_link('Schedule')
    url = link.reverse(self.prop)
    response = self.client.post(url)
    # check that reponse is OK ("Scheduling has commenced..")

    cases:
    manual scheduling without proper stand attributes
    '''
    pass

class OutputsTest(TestCase):
    '''
    After GY and Scheduling, parse the tree list and 
    generate/store as json data associated with
    the stand or property as appropos

    - harvest schedule
    - yield over time
    - standing timber over time
    - carbon
    '''
    def setUp(self):
        '''
        self.prop = ForestProperty(..)
        self.prop.run_gy()
        self.prop.schedule()
        '''
        pass

    def test_yield(self):
        '''
        self.prop.generate('yield_over_time') 
        self.assertTrue(self.prop.outputs.yield['2085'] == 28000)
        '''
        pass
