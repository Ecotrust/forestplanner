from django.test import TestCase
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class PdfTests(StaticLiveServerTestCase):
    """
        Open a browser
        Make API call at url /report/<str:property_id>/pdf
        Check PDF in page title
        Check PDF images are correct size
    """

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.selenium = webdriver.Firefox()
        self.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(self):
        self.selenium.quit()
        super().tearDownClass()

    def test_single_download(self):
        # New URL for single page
        # New View for single page
        # Call create_property_pdf give page as arg
        # return only page requested page
        test_property_version = 'v2'
        property_id = test_property_version + 'test_property%7C583966%7C862934'
        print('Creating property...')
        self.selenium.get("http://localhost:8000/landmapper/report/%s" % property_id)
        print('Property created')
        print('Open single steam pdf')
        self.selenium.get("http://localhost:8000/landmapper/report/%s/stream/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)
        print('Open single street pdf')
        self.selenium.get("http://localhost:8000/landmapper/report/%s/street/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)
        print('Open single aerial pdf')
        self.selenium.get("http://localhost:8000/landmapper/report/%s/aerial/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)
        print('Open single soil types pdf')
        self.selenium.get("http://localhost:8000/landmapper/report/%s/soil_types/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)

    def test_cover_map_img(self):
        test_property_version = 'v2'
        property_id = test_property_version + 'test_property%7C583966%7C862934'
        # Create new property
        print('Creating property...')
        self.selenium.get("http://localhost:8000/landmapper/report/%s" % property_id)
        print('Property created')
        # Get new alt image
        print('Getting alt property image')
        self.selenium.get("http://localhost:8000/landmapper/report/%s/%s/map" % (property_id, 'property_alt'))
        # check dimensions
        self.assertIn('509', self.selenium.title)
        self.assertIn('722', self.selenium.title)

    def test_create_pdf(self):
        test_property_version = 'v2'
        property_id = test_property_version + 'test_property%7C583966%7C862934'
        # Create report
        self.selenium.get("http://localhost:8000/landmapper/report/%s" % property_id)
        # Get pdf report
        self.selenium.get("http://localhost:8000/landmapper/report/%s/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)
