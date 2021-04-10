import os, sys

from django.test import TestCase, Client
from django.conf import settings
from selenium import webdriver

# https://selenium-python.readthedocs.io/waits.html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GeocodeTest(TestCase):
    def setUp(self):
        try:
            webdriver.DesiredCapabilities.FIREFOX["unexpectedAlertBehaviour"] = "accept"
            self.browser = webdriver.Firefox()
        except Exception as e:
            print(e)
            print("Have you installed xvfb?")
            print("Have you run `Xvfb :99 -ac &` since you last restarted?")
            print("Have you run `export DISPLAY=:99` since you last restarted?")
            sys.exit(1)

    def test_geocode_studyregion(self):
        from landmapper.views import geocode
        for teststring in ['toledo', 'glide', 'Beaver Marsh', 'John Day',
            'The Dalles', 'Dallas', 'Lakeview', 'Bend', 'North Bend', 'steens',
            'joseph', 'k falls', 'Seattle'
        ]:
            results = geocode(teststring)
            for result in results:
                result_coords = result['coords']
                self.assertTrue(result_coords[0] <= settings.STUDY_REGION['north'])
                self.assertTrue(result_coords[0] >= settings.STUDY_REGION['south'])
                self.assertTrue(result_coords[1] <= settings.STUDY_REGION['east'])
                self.assertTrue(result_coords[1] >= settings.STUDY_REGION['west'])

    def test_geocode_options_gui(self):
        # user arrives on landing page
        self.browser.get("http://localhost:8000")
        # self.browser.get("https://landmapper.ecotrust.org/")
        try:
            element = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.ID, "property-search"))
            )
        except Exception as e:
            self.browser.quit()

        # user enters 'seattle' into search bar and clicks 'Go'
        self.browser.find_element_by_id("property-search").send_keys('seattle')
        self.browser.find_element_by_id("property-search-btn").click()

        # user arrives on 'identify' page after searching for 'seattle'
        try:
            element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "btn-content-panel-back"))
            )
        except Exception as e:
            self.browser.quit()

        # user is presented with a modal of location options
        self.assertTrue(self.browser.find_element_by_id("geocode-results-options").is_displayed())
        self.assertTrue(len(self.browser.find_elements_by_class_name("geocode-search-result")) > 0)

        options_coordinates = self.browser.execute_script('''
            var option_elements = $("#geocode-results-container").children('button.geocode-search-result');
            var option_coordinates = [];
            option_elements.each(function(){
                child_coords_4326 = eval($(this).find('p.coordinates-value').html());
                option_coordinates.push(ol.proj.fromLonLat([child_coords_4326[1], child_coords_4326[0]], 'EPSG:3857'));
            });
            return option_coordinates;
        ''');

        # map is zoomed to correct zoom (???)
        zoom = self.browser.execute_script("return map.getView().getZoom()")
        self.assertEqual(zoom, 14)

        # map is centered on correct coords (first geocode hit)
        map_center = self.browser.execute_script("return map.getView().getCenter()")
        primary_center = options_coordinates[0];
        self.assertEqual(int(map_center[0]), int(primary_center[0]))
        self.assertEqual(int(map_center[1]), int(primary_center[1]))

        # pin is placed at the selected coordinates
        pin_coords =  self.browser.execute_script('''
            var overlay = map.overlays_.array_[0];
            var coords = overlay.getPosition();
            return coords;
        ''')
        self.assertEqual(int(pin_coords[0]), int(primary_center[0]))
        self.assertEqual(int(pin_coords[1]), int(primary_center[1]))

        # user selects the 2nd location option
        self.browser.find_elements_by_class_name("geocode-search-result")[1].click()

        # map is cetered on correct coords (2nd geocode hit)
        map_center = self.browser.execute_script("return map.getView().getCenter()")
        secondary_center = options_coordinates[1];
        self.assertEqual(int(map_center[0]), int(secondary_center[0]))
        self.assertEqual(int(map_center[1]), int(secondary_center[1]))

        # pin is placed at the selected coordinates
        pin_coords =  self.browser.execute_script('''
            var overlay = map.overlays_.array_[0];
            var coords = overlay.getPosition();
            return coords;
        ''')
        self.assertEqual(int(pin_coords[0]), int(secondary_center[0]))
        self.assertEqual(int(pin_coords[1]), int(secondary_center[1]))

        # user selects last location option
        self.browser.find_elements_by_class_name("geocode-search-result")[-1].click()

        # map is centered on correct coords (final geocode hit)
        map_center = self.browser.execute_script("return map.getView().getCenter()")
        ultimate_center = options_coordinates[-1];
        self.assertEqual(int(map_center[0]), int(ultimate_center[0]))
        self.assertEqual(int(map_center[1]), int(ultimate_center[1]))

        # user approves the location selection
        self.browser.find_element_by_id("geocode-results-close").click()

        # Modal is gone.
        self.assertTrue(EC.invisibility_of_element_located((By.CLASS_NAME, "geocode-search-result")))

        # pin is still placed at the selected coordinates
        map_center = self.browser.execute_script("return map.getView().getCenter()")
        pin_coords =  self.browser.execute_script('''
            var overlay = map.overlays_.array_[0];
            var coords = overlay.getPosition();
            return coords;
        ''')
        self.assertEqual(int(pin_coords[0]), int(map_center[0]))
        self.assertEqual(int(pin_coords[1]), int(map_center[1]))

        # TODO: Test user rejects all and browses map for themselves
