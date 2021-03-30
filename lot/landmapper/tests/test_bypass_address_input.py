from django.test import TestCase
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

def BypassAddressInputTest(TestCase):
    """
        Load site landing page
        Add a button to select tax lot by interacting with map
        Progress panel state
        Update panel instructions if needed
    """

    def setUp(self):
        pass

    def test_bypass_address_input(self):
        from landmapper.views import identify
        address = 'Mountain View, CA'
        response = self.client.post(reverse(identify), {'q-address':address})
