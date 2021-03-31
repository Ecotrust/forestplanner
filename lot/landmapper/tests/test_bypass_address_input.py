from django.test import TestCase
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.common.by import By

def BypassAddressInputTest(TestCase):
    """
        Load site landing page
        Add a button to select tax lot by interacting with map
        Progress panel state
        Update panel instructions if needed
    """

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.vars = {}

    def tearDown(self):
        self.driver.quit()

    def test_bypass_address_input(self):
        self.driver.get("http://localhost:8000/landmapper")
        self.driver.set_window_size(2560, 1415)
        self.driver.find_element(By.ID, "bypass-address-input").click()
