from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

from django.test import TestCase
from django.conf import settings
from django.urls import reverse

class ModelTests(TestCase):
    """
    Queries on each model in the module
        Queries return correct data
        Queries that should return no data get no data
    """

    # How to work with GEOS API in Django:
    #       https://docs.djangoproject.com/en/2.2/ref/contrib/gis/geos/

    def create_test_user():
        from django.contrib.auth.models import User
        if User.objects.all().count() < 1:
            User.objects.get_or_create(username='test_user')

    def create_taxlot_records(self):
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import GEOSGeometry

        # from django.contrib.auth.models import User
        ModelTests.create_test_user()

        if Taxlot.objects.all().count() < 1:
            from django.contrib.auth.models import User
            test_user = User.objects.get(username='test_user')

            ### Create Taxlots
            # ZOOM TO: 44.085, -122.900
            # Taxlot NE of Eugene:
            poly_1 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681279.3108 5478566.238799997, -13680721.1384 5478574.5858, -13680722.0809 5478015.218999997, -13681279.9385 5478006.679099999, -13681838.8572 5477998.089199997, -13681837.4829 5478557.857699998, -13681279.3108 5478566.238799997)))', srid=3857)
            # Adjacent taxlot to the north
            poly_2 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681278.5741 5479125.020800002, -13680719.8309 5479133.516500004, -13680721.1384 5478574.5858, -13681279.3108 5478566.238799997, -13681837.4829 5478557.857699998, -13681837.3172 5479116.491499998, -13681278.5741 5479125.020800002)))', srid=3857)
            # Nearby, non-adjacent taxlot
            poly_3 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13679606.0781 5478590.317100003, -13679607.5092 5478031.919799998, -13680164.0094 5478023.597900003, -13680163.6087 5478582.451800004, -13679606.0781 5478590.317100003)))', srid=3857)
            # Adjacent taxlot to the south
            poly_4 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681279.9385 5478006.679099999, -13680722.0809 5478015.218999997, -13680723.1572 5477455.464900002, -13681280.5667 5477446.9441, -13681840.2315 5477438.354400001, -13681838.8572 5477998.089199997, -13681279.9385 5478006.679099999)))', srid=3857)
            # nearby 'tall' ratio taxlot
            poly_5 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13679588.897 5484177.156499997, -13679587.9734 5483615.298299998, -13679587.051 5483053.471600004, -13680143.9512 5483045.795699999, -13680148.3177 5483612.898599997, -13680152.6443 5484174.773000002, -13679588.897 5484177.156499997)))', srid=3857)
            # far away taxlot in Bend, OR
            poly_6 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13497350.5573 5466642.792599998, -13497362.4181 5466097.011299998, -13496818.6803 5466089.796300001, -13496841.6402 5464979.914999999, -13496842.3361 5464962.954899997, -13496847.8271 5464938.125299998, -13496854.4567 5464922.439199999, -13496862.9991 5464907.7971, -13496873.457 5464894.491099998, -13496885.6206 5464882.735399999, -13496899.281 5464872.796899997, -13496915.9134 5464864.078699999, -13497186.7509 5464756.381200001, -13497218.3726 5464744.583499998, -13497243.0659 5464738.578500003, -13497276.6577 5464734.244800001, -13497303.3047 5464733.873199999, -13497301.1837 5464709.457099997, -13497267.3398 5464709.203500003, -13497233.7491 5464713.643200003, -13497201.257 5464722.689599998, -13497177.6548 5464732.478600003, -13496906.2013 5464842.197300002, -13496890.8283 5464849.816299997, -13496870.23 5464864.486199997, -13496857.8543 5464876.191, -13496845.093 5464892.1175, -13496855.5253 5464422.189599998, -13497398.8988 5464424.464199997, -13497956.0209 5464426.768299997, -13498311.1495 5464428.221500002, -13498513.3548 5464429.037199996, -13498506.7787 5464988.822300002, -13498499.9906 5465548.669100001, -13498493.2115 5466109.637100004, -13498492.3651 5466109.618199997, -13498489.4617 5466373.697999999, -13498485.0185 5466373.632200003, -13498483.1133 5466256.362300001, -13498150.3055 5466368.762400001, -13497931.1132 5466365.570900001, -13497935.5942 5466652.810099997, -13497910.2055 5466652.561800003, -13497629.6409 5466647.688199997, -13497473.0662 5466644.93, -13497350.5573 5466642.792599998)))', srid=3857)

            tl1 = Taxlot.objects.create(user=test_user, geometry_orig=poly_1, name='test_mid_wide')
            tl2 = Taxlot.objects.create(user=test_user, geometry_orig=poly_2, name='test_top_wide')
            tl3 = Taxlot.objects.create(user=test_user, geometry_orig=poly_3, name='test_small_detached')
            tl4 = Taxlot.objects.create(user=test_user, geometry_orig=poly_4, name='test_bottom_wide')
            tl5 = Taxlot.objects.create(user=test_user, geometry_orig=poly_5, name='test_solo_tall')
            tl6 = Taxlot.objects.create(user=test_user, geometry_orig=poly_6, name='test_bend_lot')

    def test_taxlot(self):
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import GEOSGeometry

        self.create_taxlot_records()

        #Create taxlot instances
        tl1 = Taxlot.objects.get(name='test_mid_wide')
        tl2 = Taxlot.objects.get(name='test_top_wide')
        tl3 = Taxlot.objects.get(name='test_small_detached')
        tl4 = Taxlot.objects.get(name='test_bottom_wide')
        tl5 = Taxlot.objects.get(name='test_solo_tall')

        click_1 = 'SRID=4326;POINT( -122.903 44.083 )'          #Note, it doesn't appear to matter if we give GEOSGeoms or just WKT.
        click_2 = GEOSGeometry('SRID=4326;POINT( -122.902 44.087 )')
        click_3 = GEOSGeometry('SRID=4326;POINT( -122.888 44.083 )')
        click_4 = GEOSGeometry('SRID=4326;POINT( -123 45 )')

        # Test intersection
        taxlot_1 = Taxlot.objects.get(geometry_orig__contains=click_1)
        taxlot_2 = Taxlot.objects.get(geometry_orig__contains=click_2)
        taxlot_3 = Taxlot.objects.get(geometry_orig__contains=click_3)
        self.assertEqual(taxlot_1.pk, tl1.pk)
        self.assertEqual(taxlot_2.pk, tl2.pk)
        self.assertEqual(taxlot_3.pk, tl3.pk)
        self.assertNotEqual(taxlot_1.pk, tl2.pk)
        self.assertEqual(len(Taxlot.objects.filter(geometry_orig__contains=click_4)), 0)

        #TODO: test any model methods for attributes and types returned

    def test_menu_page(self):
        from landmapper.models import MenuPage

        menu_title = "Menu Item"
        # Courtesy of rikeripsum.com
        menu_text = "The game's not big enough unless it scares you a little. \
        Your head is not an artifact! Our neural pathways have become \
        accustomed to your sensory input patterns. Commander William Riker of \
        the Starship Enterprise. What? We're not at all alike! What's a \
        knock-out like you doing in a computer-generated gin joint like this? \
        Not if I weaken first. Mr. Worf, you sound like a man who's asking his \
        friend if he can start dating his sister. For an android with no \
        feelings, he sure managed to evoke them in others."
        menu_content = "<h1>%s</h1><p>%s</p>" % (menu_title, menu_text)

        MenuPage.objects.create(name='Menu', content=menu_content, order=0)

        hipster_title = "Hipster"
        # courtesy of https://hipsum.co/
        hipster_textP1 = "Fam id messenger bag forage, nisi lomo edison bulb \
        ipsum lo-fi kitsch street art kinfolk sriracha irony nulla. Raclette \
        fanny pack meditation, lomo heirloom farm-to-table wayfarers shaman \
        dolore roof party trust fund disrupt laboris anim kogi. Taxidermy \
        organic nostrud blue bottle activated charcoal minim, gluten-free \
        slow-carb XOXO photo booth cornhole keffiyeh elit. Cold-pressed \
        cornhole waistcoat snackwave hexagon. Banh mi subway tile viral ennui, \
        duis irure poutine proident flexitarian fam direct trade sint roof \
        party. Try-hard artisan pork belly chillwave. Quis activated charcoal \
        mustache cornhole excepteur nostrud godard."
        hipster_textP2 = "Id neutra literally four dollar toast ea, franzen \
        irony food truck venmo. Pour-over copper mug cold-pressed, yr YOLO \
        sartorial tousled pug tacos mustache hashtag. Health goth vinyl \
        chillwave williamsburg cardigan kickstarter tofu normcore duis hoodie \
        shaman neutra cred tumblr church-key. Af authentic craft beer, \
        letterpress deep v intelligentsia slow-carb synth 90's. Activated \
        charcoal organic blue bottle aliqua in dolore."
        hipster_content = "<h1>%s</h1><p>%s</p><p>%s</p>" % (
            hipster_title,
            hipster_textP1,
            hipster_textP2
        )

        MenuPage.objects.create(name=hipster_title, content=hipster_content, order=1, staff_only=True)

        self.assertEqual(len(MenuPage.objects.all()), 2)
        non_staff = MenuPage.objects.get(staff_only=False)
        self.assertTrue('gin joint' in non_staff.content)
        staff_only = MenuPage.objects.get(staff_only=True)
        self.assertTrue('Banh mi' in staff_only.content)

        # TODO: test this in Front-End

    def test_forest_type(self):
        from landmapper.models import ForestType

        ForestType.objects.create(name='Foo')

        self.assertEqual(len(ForestType.objects.all()), 1)

        # TODO: test everything about ForestType once it's a thing

class ViewTests(TestCase):
    """
    External APIs
        soil data queries
        geocoding
        Pulling map images for server-side .PDF creation
    """

    """
    test_soils_api
    PURPOSE:
    -   Test request for soils image tile at given size, location.
    -   Test request for soils data for corresponding BBOX.
    """
    def test_soils_api(self):
        from osgeo import ogr
        from landmapper.views import get_soil_data_gml, get_soil_overlay_tile_data, get_soils_list, unstable_request_wrapper

        soils_list = get_soils_list('-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179', 'EPSG:3857') # Bend

        self.assertEqual(len(soils_list.keys()), 18)
        self.assertEqual(soils_list['W']['muname'], 'Water')
        for musym in ['61C', '157C', '62D', '155C', '155D', '58C', '72C', '36A', '28A', '27A', '65A', '156C', '38B', '85A', '18D', '36B', 'W', 'NOTCOM']:
            self.assertTrue(musym in soils_list.keys())

        print('soils')

    def test_geocoding(self):
        from landmapper.views import geocode

        coords = geocode('Mountain View, CA')

        self.assertEqual(coords, [37.389670000000024, -122.08159999999998])
        print('geocoder')

    def test_bbox_to_string(self):
        from landmapper.views import get_bbox_as_string
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import MultiPolygon, Polygon

        ModelTests.create_taxlot_records(ModelTests)

        taxlot = Taxlot.objects.all()[0]
        geom = taxlot.geometry_final

        north = geom.envelope.coords[0][2][1]
        south = geom.envelope.coords[0][0][1]
        east = geom.envelope.coords[0][2][0]
        west = geom.envelope.coords[0][0][0]

        correct_output = ','.join([str(west),str(south),str(east),str(north)])

        self.assertLess(west, east)
        self.assertLess(south, north)

        if type(geom) == Polygon:
            polygon_input = geom
            multipolygon_input = MultiPolygon([geom,])
        else:
            polygon_input = Polygon(geom.coords[0][0])
            multipolygon_input = geom

        # CASES:
        #   Polygon
        polygon_input = Polygon(((west,south),(east,south),(east,north),(west,north),(west,south)))
        self.assertEqual(correct_output, get_bbox_as_string(polygon_input))
        #   MultiPolygon
        self.assertEqual(correct_output, get_bbox_as_string(MultiPolygon([polygon_input,])))
        #   Coords from Polygon ((W,S),(E,S),(E,N),(W,N),(W,S))
        self.assertEqual(correct_output, get_bbox_as_string(polygon_input.envelope.coords))
        #   Coords from MultiPolygon (((W,S),(E,S),(E,N),(W,N),(W,S)),)
        # self.assertEqual(correct_output, get_bbox_as_string(((west,south),(east,south),(east,north),(west,north),(west,south))))
        self.assertEqual(correct_output, get_bbox_as_string(multipolygon_input.envelope.coords))
        #   Non-envelope MultiPolygon
        self.assertEqual(correct_output, get_bbox_as_string(multipolygon_input))
        self.assertEqual(correct_output, get_bbox_as_string(multipolygon_input.coords))
        #   Non-envelope Polygon
        self.assertEqual(correct_output, get_bbox_as_string(polygon_input))
        self.assertEqual(correct_output, get_bbox_as_string(polygon_input.coords))
        #   Simple list object [W,S,E,N]
        self.assertEqual(correct_output, get_bbox_as_string([west, south, east, north]))
        #   List of two sets of point coordinates [(W,S),(E,N)]
        self.assertEqual(correct_output, get_bbox_as_string([(west, south), (east, north)]))

    def test_tiles(self):
        # TODO: Tile requests
        #   basemap images
        #   streams?
        #   lots/properties?
        #   forest types?
        #   soils
        """
        get BBOX, centroid, zoom, or any other value needed to query the endpoints
        get basemap tile
        -   set
        get any overlay tiles
        stitch images together (imagemagic?)
        """
        import os
        from PIL import Image
        # from landmapper.views import get_aerial_image, image_result_to_PIL, get_soil_overlay_tile_data, merge_images, get_property_from_taxlot_selection, get_bbox_as_string, get_bbox_from_property
        from landmapper.views import get_property_from_taxlot_selection, get_soil_report_image
        # from django.contrib.gis.geos import GEOSGeometry
        from landmapper.models import Taxlot

        # from ModelTests import create_taxlot_records
        ModelTests.create_taxlot_records(ModelTests)

        # tall_property = GEOSGeometry('SRID=3857;MULTIPOLYGON (((
        tall_taxlot = Taxlot.objects.get(name='test_solo_tall')

        wide_taxlot_top = Taxlot.objects.get(name='test_top_wide')
        wide_taxlot_mid = Taxlot.objects.get(name='test_mid_wide')
        wide_taxlot_bottom = Taxlot.objects.get(name='test_bottom_wide')

        bend_taxlot = Taxlot.objects.get(name='test_bend_lot')

        wide_property = get_property_from_taxlot_selection([wide_taxlot_mid,])

        tall_property = get_property_from_taxlot_selection([tall_taxlot,])

        stacked_property = get_property_from_taxlot_selection([
            wide_taxlot_top,
            wide_taxlot_mid,
            wide_taxlot_bottom
        ])

        bend_property = get_property_from_taxlot_selection([bend_taxlot,])

        property_runs = [
            ('tall', tall_property),
            ('wide', wide_property),
            ('stacked', stacked_property),
            ('bend', bend_property)
        ]

        for property in property_runs:
            (prop_name, prop_instance) = property
            image_data = get_soil_report_image(prop_instance, debug=False)
            image_data.save(os.path.join(settings.IMAGE_TEST_DIR, '%s_soil.png' % prop_name),"PNG")

        print('tiles')


    # """
    # TEMPLATES
    #     correctly formatted context for rendering templates
    #     reporting values
    #     ForestType queries
    #     legend creation (map, forest type, soil)
    #     table creation (overview, forest type, soil)
    # """

    # Should we break up views into 'gather' and 'render' functions?
    # Perhaps the 'gather' functions are modular children - the parent requests
    #   the context and then uses that to render the template

    def test_header_gather(self):
        # TODO:
        # add menu items (done in models tests?)
        # do branding images exist?
        # is context dict correctly formatted with:
        #   correct keywords
        #   correct value types for each keyword
        #   correct values
        #   correct order (of MenuPage instances)
        print('header view')

    def test_home_view_gather(self):
        # TODO:
        #   ...
        print('home view gather')

    def test_home_page(self):
        """
            TODO:
                create variable to strore result of fetching the home page
                assert response is 200
        """
        from landmapper.views import home
        response = self.client.get(reverse(home))
        self.assertEqual(response.status_code, 200)

    def test_identify_gather(self):
        """
        Test:
            Input
        TODO:
            create var to store page request input
            check for a coords param
            check for a search string
            check for taxlot ids param
            check for property name param
        IN:
            coords
            search string
            (opt) taxlot ids
            (opt) property name
        """
        # from landmapper.views import identify
        print('test identify gather')

    def test_identify_render(self):
        """
        TEST:
            Rendered Template
        TODO:
            create variable to store result of fetching the identify page
            assert response is 200
        """
        from landmapper.views import identify
        response = self.client.get(reverse(identify))
        self.assertEqual(response.status_code, 200)

    def test_report_gather(self):
        """
        Test:
            IN
        TODO:
            create var to store page request input
            check for taxlot ids
            check for property name
        IN:
            taxlot ids
            property name
        """
        # from landmapper.views import report
        print('test report gather')

    def test_report_render(self):
        """
        TEST:
            Rendered Template
        TODO:
            create variable to store result of fetching the report page
            assert response is 200
            can a property be created
            can a report be created
            is a legend returned

        USES:
            CreateProperty, CreatePDF, ExportLayer, BuildLegend, BuildTables
        """
        from landmapper.views import report
        response = self.client.get(reverse(report))
        self.assertEqual(response.status_code, 200)

    def test_create_property(self):
        """
        TODO:
            make request to create a property with paramaters for:
                taxlot_ids[]
                property_name
            check if a madrona polygon feature is returned
        NOTES:
            should be cached
        """
        # from landmapper.views import create_property
        print('property created')

    """
    Error Handling
    """
    """
    GIS Manipulation
        convert taxlot selections into features
    """
    """
    File generation/export
        pdf report generation
            all
            forest type
            soil
        Property Shapefile
            zipping
    """
    def test_views(self):
        print("Views!")



class FrontendTests(StaticLiveServerTestCase):
    """
    state changes
        address found
            map zoomed
                Test if specific map tiles were pulled
            state advanced
        1st taxlot selected
            state advanced
            url updated
        2nd taxlot selected
            state retained
            url updated
        property name entered
            'next' enabled
            url updated
        property name deleted
            'next' disabled
            url updated
        2nd taxlot unselected
            url updated
            state retained
        1st taxlot unselected
            url updated
            state regressed
        address cleared
            url updated
            state regressed
            map zoomed back to default
        valid input and clicking 'next' brings us to a report
    Error handling
        unknown address
        non-contiguous taxlots
    validation
        validate address prior to geocode query
        valid property names?
            1+ spaces?
            Maximum characters
            Foreign accented characters (Latin1, umlauts, etc…)
    popups
        From the header menu
        from the download button(s)
        From 'get help'
    downloads?
    """
    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass()
    #     cls.selenium = WebDriver()
    #     cls.selenium.implicitly_wait(2)
    #
    # @classmethod
    # def tearDownClass(cls):
    #     cls.selenium.quit()
    #     super().tearDownClass()

    # def test_home(self):
    #    # TODOS:
    #    #   Header placement
    #    #   Header branding
    #    #   Header Menu Items
    #    #   ...
    #    print("hi")

    # def test_login(self):
    def test_browser(self):
        print("Front End!")

# class MySeleniumTests(StaticLiveServerTestCase):
#     # fixtures = ['user-data.json']
#     #
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.selenium = WebDriver()
#         cls.selenium.implicitly_wait(2)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()
#
#     # def test_login(self):
#     def test_browser(self):
#         # import ipdb; ipdb.set_trace()
#         print('get server')
#         print('URL: ""%s"' % self.live_server_url)
#         # foo = self.selenium.get(self.live_server_url)
#         # foo.title
#         # self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
#         # username_input = self.selenium.find_element_by_name("username")
#         # username_input.send_keys('myuser')
#         # password_input = self.selenium.find_element_by_name("password")
#         # password_input.send_keys('secret')
#         # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
#




# from django.test import TestCase
#
# from selenium import webdriver
#
# # From stack overflow:
# ### https://stackoverflow.com/a/47785513
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#
# cap = DesiredCapabilities().FIREFOX
# # cap["marionette"] = False
#
# # browser = webdriver.Firefox(capabilities=cap, executable_path="/usr/local/bin/geckodriver")
#
# ### https://stackoverflow.com/questions/45692626/unable-to-load-firefox-in-selenium-webdriver-in-python
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# cap["marionette"] = True
# binary = FirefoxBinary('/usr/bin/firefox')
# print('create browser')
# browser = webdriver.Firefox(firefox_binary=binary, capabilities=cap, executable_path="/usr/local/bin/geckodriver")
#
# # browser = webdriver.Firefox()
# # browser.get('http://127.0.0.1:8000')
# print('google test')
# browser.get('http://www.google.com')
# print('pre')
# browser.get('http://0:8000')
# print(browser.title)
# assert 'Django' in browser.title
