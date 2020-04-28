from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

from django.test import TestCase
from django.conf import settings


class AnimalTestCase(TestCase):
    # def setUp(self):
    #     Animal.objects.create(name="lion", sound="roar")
    #     Animal.objects.create(name="cat", sound="meow")

    def test_animals_can_speak(self):
        print('foo')

class ModelTests(TestCase):
    """
    Queries on each model in the module
        Queries return correct data
        Queries that should return no data get no data
    """
    # How to work with GEOS API in Django: https://docs.djangoproject.com/en/2.2/ref/contrib/gis/geos/


    def test_models(self):
        print("Models!")

    def setUp(self):
        from django.contrib.auth.models import User
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import GEOSGeometry
        ### Create user
        admin = User.objects.create(username='admin')

        ### Create Taxlots
        # ZOOM TO: 44.085, -122.900
        # Taxlot NE of Eugene:
        poly_1 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681279.3108 5478566.238799997, -13680721.1384 5478574.5858, -13680722.0809 5478015.218999997, -13681279.9385 5478006.679099999, -13681838.8572 5477998.089199997, -13681837.4829 5478557.857699998, -13681279.3108 5478566.238799997)))', srid=3857)
        # Adjacent taxlot to the note
        poly_2 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681278.5741 5479125.020800002, -13680719.8309 5479133.516500004, -13680721.1384 5478574.5858, -13681279.3108 5478566.238799997, -13681837.4829 5478557.857699998, -13681837.3172 5479116.491499998, -13681278.5741 5479125.020800002)))', srid=3857)
        # Nearby, non-adjacent taxlot
        poly_3 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13679606.0781 5478590.317100003, -13679607.5092 5478031.919799998, -13680164.0094 5478023.597900003, -13680163.6087 5478582.451800004, -13679606.0781 5478590.317100003)))', srid=3857)
        # transform polies from 3857 to 4326
        poly_1.transform(4326)
        poly_2.transform(4326)
        poly_3.transform(4326)

        #Create taxlot instances
        Taxlot.objects.create(user=admin, geometry_orig=poly_1)
        Taxlot.objects.create(user=admin, geometry_orig=poly_2)
        Taxlot.objects.create(user=admin, geometry_orig=poly_3)

    def test_taxlot(self):
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import GEOSGeometry
        click_1 = 'SRID=4326;POINT( -122.903 44.083 )'          #Note, it doesn't appear to matter if we give GEOSGeoms or just WKT.
        click_2 = GEOSGeometry('SRID=4326;POINT( -122.902 44.087 )')
        click_3 = GEOSGeometry('SRID=4326;POINT( -122.888 44.083 )')

        # Test intersection
        taxlot_1 = Taxlot.objects.get(geometry_orig__contains=click_1)
        taxlot_2 = Taxlot.objects.get(geometry_orig__contains=click_2)
        taxlot_3 = Taxlot.objects.get(geometry_orig__contains=click_3)

class ViewTests(TestCase):
    """
    External APIs
        soil data queries
        geocoding
        Pulling map images for server-side .PDF creation
    Templates
        correctly formatted context for rendering templates
        reporting values
        ForestType queries
        legend creation (map, forest type, soil)
        table creation (overview, forest type, soil)
    Error Handling
    GIS Manipulation
        convert taxlot selections into features
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(2)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    # def test_login(self):
    def test_browser(self):
        print("Front End!")

class MySeleniumTests(StaticLiveServerTestCase):
    # fixtures = ['user-data.json']
    #
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(2)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    # def test_login(self):
    def test_browser(self):
        # import ipdb; ipdb.set_trace()
        print('get server')
        print('URL: ""%s"' % self.live_server_url)
        # foo = self.selenium.get(self.live_server_url)
        # foo.title
        # self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
        # username_input = self.selenium.find_element_by_name("username")
        # username_input.send_keys('myuser')
        # password_input = self.selenium.find_element_by_name("password")
        # password_input.send_keys('secret')
        # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()





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