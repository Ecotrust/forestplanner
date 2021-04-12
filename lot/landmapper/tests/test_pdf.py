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
        self.selenium = webdriver.firefox.webdriver.WebDriver()
        self.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(self):
        self.selenium.quit()
        super().tearDownClass()

    def test_cover_map_img(self):
        property_id = 'Demo%7C583966%7C862934'
        # New URL
        self.selenium.get("http://localhost:8000/report/%s/%s/map_alt" % (property_id, 'property'))
        # return img
        # check dimensions

        # self.assert()

    def test_create_pdf(self):
        property_id = 'Demo%7C583966%7C862934'
        self.selenium.get("http://localhost:8000/report/%s/pdf" % property_id)
        self.assertIn('pdf', self.selenium.title)
