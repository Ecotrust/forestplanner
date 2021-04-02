import os, sys

from django.test import TestCase, Client
from django.conf import settings
# from selenium import webdriver

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

class RenderTest(TestCase):
    def setUp(self):
        # try:
        #     webdriver.DesiredCapabilities.FIREFOX["unexpectedAlertBehaviour"] = "accept"
        #     self.browser = webdriver.Firefox()
        # except Exception as e:
        #     print(e)
        #     print("Have you installed xvfb?")
        #     print("Have you run `Xvfb :99 -ac &` since you last restarted?")
        #     print("Have you run `export DISPLAY=:99` since you last restarted?")
        #     sys.exit(1)
        pass

    def test_render_basemap(self):
        # given a property, get the coordinates

        # convert those coordinates into a buffered bounding box

        # get appropriate bounding box for street maps

        # get appropriate bounding box for topo map

        # render the aerial imagery to a properly-sized .png

        # render property lines onto aerial imagery as a .png (OVERVIEW)

        # render property atop taxlots atop aerial

        # render property atop streets

        # render property atop terrain

        # render property atop streams atop aerial

        # render property atop soils atop aerial
