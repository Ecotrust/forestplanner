from django.test import TestCase
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


def BypassAddressInputTest(StaticLiveServerTestCase):
    """
        Load site landing page
        Add a button to select tax lot by interacting with map
        Progress panel state
        Update panel instructions if needed
    """

    # @classmethod
    def setUp(self):
        pass
        super().setUpClass()
        self.selenium = webdriver.firefox.webdriver.WebDriver()
        self.selenium.implicitly_wait(10)

    # @classmethod
    def tearDown(self):
        self.selenium.quit()
        super().tearDownClass()


    def test_bypass_address_input(self):
        self.selenium.get("http://localhost:8000/landmapper")
        self.selenium.find_element_by_id("bypass-address-input").click()

        overlay = self.selenium.find_element_by_id("property-search-form")
        self.assertFalse(self.selenium.find_element_by_xpath('//style="visibility: hidden"'))
