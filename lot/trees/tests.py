import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry 
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from simplejson import loads
from madrona.features import *
from madrona.features.models import Feature, PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features.forms import FeatureForm
from madrona.common.utils import kml_errors, enable_sharing
from madrona.raster_stats.models import RasterDataset
from trees.models import Stand, ForestProperty, County, FVSVariant, Scenario
from trees.utils import StandImporter

cntr = GEOSGeometry('SRID=3857;POINT(-13842474.0 5280123.1)')
g1 = cntr.buffer(75)
g1.transform(settings.GEOMETRY_DB_SRID)

p1 = g1.buffer(1000)

def import_rasters():
    d = os.path.dirname(__file__)
    rast_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
        'testdata'))
    # Here we'll need to create dummy rasterdatasets for everything 
    # in the IMPUTE_RASTERS setting
    elev = RasterDataset.objects.create(name="elevation",
            filepath=os.path.join(rast_path,'elevation.tif'), type='continuous')
    aspect = RasterDataset.objects.create(name="aspect",
            filepath=os.path.join(rast_path,'aspect.tif'), type='continuous')
    cos_aspect = RasterDataset.objects.create(name="cos_aspect",
            filepath=os.path.join(rast_path,'cos_aspect.tif'), type='continuous')
    sin_aspect = RasterDataset.objects.create(name="sin_aspect",
            filepath=os.path.join(rast_path,'sin_aspect.tif'), type='continuous')
    gnn = RasterDataset.objects.create(name="gnn",
            filepath=os.path.join(rast_path,'gnn.tif'), type='categorical')
    slope = RasterDataset.objects.create(name="slope",
            filepath=os.path.join(rast_path,'slope.tif'), type='continuous')

class StandTest(TestCase):
    ''' 
    Basic tests for adding stands
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_add_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        # geometry_final will be set with manipulator
        stand1.save()

    def test_incomplete_stand(self):
        stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.assertEqual(stand1.rx, '--')

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

class ForestPropertyTest(TestCase):
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
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

    def test_property_bbox(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()
        self.assertEqual(prop1.bbox, p1.extent)
        prop1.geometry_final = g1
        prop1.save()
        self.assertNotEqual(prop1.bbox, p1.extent)
        self.assertEqual(prop1.bbox, g1.extent)

    def test_add_property_to_stand(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        self.stand1.add_to_collection(prop1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand1 in prop1.feature_set())

        self.stand1.remove_from_collection()
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in prop1.feature_set())

    def test_add_stand_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        prop1.add(self.stand1)
        self.assertEqual(self.stand1.collection, prop1)
        self.assertTrue(self.stand1 in prop1.feature_set())

        prop1.remove(self.stand1)
        self.assertEqual(self.stand1.collection, None)
        self.assertTrue(self.stand1 not in prop1.feature_set())

    def test_add_property_to_property(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop2 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
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
    [{fpattrs}, ...]
    '''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_unauth(self):
        url = reverse('trees-user_property_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_jsonlist(self):
        self.client.login(username='featuretest', password='pword')
        url = reverse('trees-user_property_list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        self.assertEquals(plist['features'], [])
        self.assertEquals(plist['bbox'], settings.DEFAULT_EXTENT, plist)

        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        plist = loads(response.content)
        self.assertEquals(plist['features'][0]['properties']['name'], 'My Property')

class PropertyStandListTest(TestCase):
    '''
    test web service to grab json of user's propertie's stands
    [{stand-attrs}, ...]
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.baduser = User.objects.create_user(
            'baduser', 'baduser@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.prop1.add(self.stand1)
        enable_sharing()

    def test_unauth(self):
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_notexists(self):
        self.client.login(username='baduser', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        url = url.replace(self.prop1.uid, 'trees_forestproperty_123456789')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_baduser(self):
        self.client.login(username='baduser', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) 

    def test_jsonlist(self):
        self.client.login(username='featuretest', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        stand_list = loads(response.content)
        self.assertEquals(stand_list['features'][0]['properties']['name'], 'My Stand', stand_list)

        self.prop1.add(self.stand2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200) 
        stand_list = loads(response.content)
        names = [stand['properties']['name'] for stand in stand_list['features']]
        names.sort()
        expected_names = ['My Stand', 'My Stand2']
        expected_names.sort()
        self.assertEqual(names, expected_names)

class NearestPlotTest(TestCase):
    '''
    Tests nearest plot util function and web service
    '''
    fixtures = ['test_plotsummary', 'fvs_species_western', ]

    def test_webservice(self):
        testcases = (
                ("8853", "/trees/nearest_plot/?imap_domspp=PSME&cancov=40&stndhgt=40&sdi=100"),
                ("14093", "/trees/nearest_plot/?imap_domspp=PSME&cancov=75&stndhgt=45"),
        )
        for case in testcases:
            url = case[1]
            fcid = case[0]
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(fcid in response.content, response.content)  #TODO test json output, html output is just for testing

class ManipulatorsTest(TestCase):
    '''
    test overlap/sliver manipulators
    '''

    def setUp(self):
        '''
        A self-intersecting polyon
        '''
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.bad_ewkt = "SRID=3857;POLYGON((-13738982.554637 5741643.81587,-13748693.674233 \
                5750032.832398,-13740702.387773 5750625.1666924,-13744294.928102 \
                5751848.1591448,-13738982.554637 5741643.81587))"

    def test_clean_badgeom(self):
        self.stand1 = Stand(user=self.user, name="Bad Stand", geometry_orig=self.bad_ewkt) 
        self.stand1.save()
        self.assertTrue(self.stand1.geometry_final.valid)


class SpatialTest(TestCase):
    '''
    Tests the spatial representations of Stands and ForestProperties
    '''

    def setUp(self):
        self.client = Client()
        import_rasters()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
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
        thejson = self.stand1.geojson()
        d = loads(thejson)
        self.assertEquals(d['properties']['name'], 'My Stand')

    def test_property_json(self):
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        self.assertEquals(len(d['features']), 1)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        self.prop1.add(self.stand2)
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        self.assertEquals(len(d['features']), 2)

    def test_property_bbox(self):
        thejson = self.prop1.feature_set_geojson()
        d = loads(thejson)
        for x, y in zip(d['bbox'], self.prop1.bbox):
            self.assertAlmostEquals(x, y, places=5)

    def test_stand_json_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('GeoJSON')
        url = link.reverse(self.stand1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Stand')
        
    def test_property_json_url(self):
        self.client.login(username='featuretest', password='pword')
        link = self.stand1.options.get_link('GeoJSON')
        url = link.reverse(self.prop1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        d = loads(response.content)
        self.assertEquals(d['features'][0]['properties']['name'], 'My Property')

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

    def test_property_stands_json_url(self):
        self.prop1.add(self.stand2)
        self.client.login(username='featuretest', password='pword')
        link = self.prop1.options.get_link('Property Stands GeoJSON')
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
    Occurs automatically on model save() UNLESS you pass impute=False.
    Can also be called directly using feature._impute() though this should 
      probably be considered a semi-private method
    '''
    fixtures = ['test_plotsummary', 'fvs_species_western', ]

    def setUp(self):
        g2 = GEOSGeometry(
            'SRID=3857;POLYGON((%(x1)s %(y1)s, %(x2)s %(y1)s, %(x2)s %(y2)s, %(x1)s %(y2)s, %(x1)s %(y1)s))' % 
            {'x1': -13841975, 'y1': 5308646, 'x2': -13841703, 'y2': 5308927})
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.stand1 = Stand(user=self.user, name="My Stand", geometry_orig=g2) 
        self.stand1.save()
        self.pk1 = self.stand1.pk

        d = os.path.dirname(__file__)
        rast_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata'))
        # Here we'll need to create dummy rasterdatasets for everything 
        # in the IMPUTE_RASTERS setting
        self.elev = RasterDataset.objects.create(name="elevation",
                filepath=os.path.join(rast_path,'elevation.tif'), type='continuous')
        self.aspect = RasterDataset.objects.create(name="aspect",
                filepath=os.path.join(rast_path,'aspect.tif'), type='continuous')
        self.cos_aspect = RasterDataset.objects.create(name="cos_aspect",
                filepath=os.path.join(rast_path,'cos_aspect.tif'), type='continuous')
        self.sin_aspect = RasterDataset.objects.create(name="sin_aspect",
                filepath=os.path.join(rast_path,'sin_aspect.tif'), type='continuous')
        self.gnn = RasterDataset.objects.create(name="gnn",
                filepath=os.path.join(rast_path,'gnn.tif'), type='categorical')
        self.slope = RasterDataset.objects.create(name="slope",
                filepath=os.path.join(rast_path,'slope.tif'), type='continuous')
        self.avg_elev = 145.05799999

    def test_impute_onsave(self):
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.imputed_elevation, None)
        self.assertAlmostEqual(s1.imputed_elevation, self.avg_elev)

    def test_impute_smart_save(self):
        d = os.path.dirname(__file__)
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertNotEqual(s1.imputed_elevation, None)
        self.assertAlmostEqual(s1.imputed_elevation, self.avg_elev)
        elev_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'elevationx2.tif')) # swap raster to elevation x 2
        self.elev.filepath = elev_path
        self.elev.save()  # saving should wipe zonal stats cache
        self.assertNotEqual(s1.imputed_elevation, None)
        self.assertAlmostEqual(s1.imputed_elevation, self.avg_elev * 2, places=5) # now we should get a new elevation value  
        elev_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'elevation.tif')) # swap rasters back to normal elevation
        self.elev.filepath = elev_path
        self.elev.save()
        geom = s1.geometry_final
        s1.geometry_final = geom.buffer(0.0001) # alter geom very slightly
        s1.save()
        self.assertNotEqual(s1.imputed_elevation, None)
        self.assertAlmostEqual(s1.imputed_elevation, self.avg_elev) # back to the original elevation value

    def test_raster_not_found(self):
        self.elev.delete()
        s1 = Stand.objects.get(pk=self.pk1)
        self.assertRaises(RasterDataset.DoesNotExist, getattr, s1, 'imputed_elevation')

    def test_zonal_null(self):
        s1 = Stand.objects.get(pk=self.pk1)
        offgeom = GEOSGeometry(
            'SRID=3857;POLYGON((-120.42 34.37, -119.64 34.32, -119.63 34.12, -120.44 34.15, -120.42 34.37))')
        s1.geometry_final = offgeom # this geom should be off the elevation map
        s1.save()
        self.assertEqual(s1.imputed_elevation, None)

    def test_all_rasters(self):
        s1 = Stand.objects.get(pk=self.pk1)
        keys = ['elevation','aspect','slope','gnn']
        vals = [self.avg_elev, 1.56339412, 35.375365000, 529.0]
        kvs = zip(keys,vals)
        for rast,val in kvs:
            self.assertNotEqual(getattr(s1,"imputed_" + rast), None)
            self.assertAlmostEqual(getattr(self.stand1, "imputed_" + rast), val)

    def test_settings_fields(self):
        kys = ['elevation','aspect','slope','gnn']
        for rast in kys:
            self.assertTrue(hasattr(self.stand1, "imputed_" + rast))

    def test_plotsummary(self):
        s = self.stand1.plot_summaries
        s1 = s[0]
        self.assertEqual(s1['fortypiv'], ['Douglas Fir'], s1)


class StandImportTest(TestCase):
    '''
    TODO
    # test bad shapefiles (other geom types, bad mapping dict, projection)
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
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
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
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()

        d = os.path.dirname(__file__)
        self.shp_path = os.path.abspath(os.path.join(d, '..', 'fixtures', 
            'testdata', 'test_stands.shp'))
        s = StandImporter(self.prop1)
        s.import_ogr(self.shp_path) 

    def test_adjacency(self):
        '''
        stand is adjacent to 332, 336, 405 and 412
        using default threshold of 1.0
        '''
        test_stand = Stand.objects.get(name='397')
        adj_stands = [Stand.objects.get(name=str(x)) for x in [332, 336, 405, 412]]
        adj = self.prop1.adjacency()
        for adj_stand in adj_stands:
            self.assertTrue(adj_stand.pk in adj[test_stand.pk])

    def test_adjacency_threshold(self):
        '''
        stand should be within 100 meters of 425 as well
        '''
        test_stand = Stand.objects.get(name='397')
        adj_stands = [Stand.objects.get(name=str(x)) for x in [332, 336, 405, 412, 425]]
        adj = self.prop1.adjacency(100.0)
        for adj_stand in adj_stands:
            self.assertTrue(adj_stand.pk in adj[test_stand.pk])

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
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

    def test_property_files(self):
        prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        prop1.save()
        path = os.path.join(prop1.file_dir, 'test.txt')
        try:
            fh = open(path, 'w')
            fh.write("prop1")
            fh.close()
        except:
            self.fail("Could not write file to " + path)
        os.remove(path)

    def test_yield(self):
        '''
        self.prop.generate('yield_over_time') 
        self.assertTrue(self.prop.outputs.yield['2085'] == 28000)
        '''
        pass

class LocationTest(TestCase):
    fixtures = ['test_counties.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.realloc = ("Curry", "OR")

    def test_location(self):
        self.assertEqual(len(County.objects.all()), 2, "Counties fixture didn't load properly!")
        self.assertEqual(self.prop1.location, self.realloc)

    def test_bad_location(self):
        self.assertEqual(self.prop1.location, self.realloc)
        cntr = GEOSGeometry('SRID=3857;POINT(-438474.0 980123.1)') # not on the map
        g1 = cntr.buffer(75)
        g1.transform(settings.GEOMETRY_DB_SRID)
        self.prop1.geometry_final = g1 
        self.prop1.save()
        self.assertEqual(self.prop1.location, (None, None))

class VariantTest(TestCase):
    fixtures = ['test_fvs_variants.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.real = "Klamath Mountains"

    def test_variant(self):
        self.assertEqual(len(FVSVariant.objects.all()), 1, "Variant fixture didn't load properly!")
        self.assertEqual(self.prop1.variant, self.real)

    def test_bad_variant(self):
        self.assertEqual(self.prop1.variant, self.real)
        cntr = GEOSGeometry('SRID=3857;POINT(-438474.0 980123.1)') # not on the map
        g1 = cntr.buffer(75)
        g1.transform(settings.GEOMETRY_DB_SRID)
        self.prop1.geometry_final = g1 
        self.prop1.save()
        self.assertEqual(self.prop1.variant, None)

class SearchTest(TestCase):
    
    def setUp(self):
        self.searches = [
            ('Tyron Creek', 200, [-9846283, 5208475]),
            ('41.12345;-81.98765', 200, [-9126823, 5030567]),
            ('39.3 N 76.4 W', 200, [-8504809, 4764735]), 
            ('KJHASBUNCHOFNONSENSEDOIHJJDHSGF', 404, None),
        ]

    def test_no_search(self):
        url = reverse('trees-geosearch')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_search(self):
        from urllib import quote_plus
        baseurl = reverse('trees-geosearch')
        for search in self.searches:
            url = baseurl + "?search=" + quote_plus(search[0])
            response = self.client.get(url)
            self.assertEqual(response.status_code, search[1])
            c = loads(response.content)
            if c['center'] is None:
                self.assertEquals(search[2], None)
            else:
                for x, y in zip(c['center'], search[2]):
                    self.assertAlmostEquals(x, y, delta=3)  # within 3 meters of expected

class ScenarioTest(TestCase):
    '''
    TODO test invalid Rxs get rejected
    TODO test posts
    '''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            'featuretest', 'featuretest@madrona.org', password='pword')

        self.stand1 = Stand(user=self.user, name="My Stand 1", geometry_orig=g1) 
        self.stand1.save()
        self.stand2 = Stand(user=self.user, name="My Stand 2", geometry_orig=g1) 
        self.stand2.save()
        self.prop1 = ForestProperty(user=self.user, name="My Property", geometry_final=p1)
        self.prop1.save()
        self.prop1.add(self.stand1)
        self.prop1.add(self.stand2)

    def test_create_scenario(self):
        s1 = Scenario(user=self.user, name="My Scenario", 
                input_target_boardfeet=2000,
                input_target_carbon=1,
                input_rxs={self.stand1.pk: 'CC', self.stand2.pk: "SW"},
             )
        s1.save()
        self.assertEquals(Scenario.objects.get(name="My Scenario").input_target_boardfeet, 2000.0)

    def test_scenario_results(self):
        "TODO remove this hardcoded dummy data"
        s1 = Scenario(user=self.user, name="My Scenario", 
                input_target_boardfeet=2000,
                input_target_carbon=1,
                input_rxs={self.stand1.pk: 'CC', self.stand2.pk: "SW"},
             )
        s1.save()
        out = s1.output_scheduler_results
        self.assertEquals(out[1]['carbon'][2012], 5.0)


