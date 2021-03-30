from django.test import TestCase
from django.conf import settings

class GeocodeTest(TestCase):
    def setUp(self):
        pass

    def test_geocode_studyregion(self):
        from landmapper.views import geocode
        for teststring in ['toledo', 'glide', 'Beaver Marsh', 'John Day',
            'The Dalles', 'Dallas', 'Lakeview', 'Bend', 'North Bend', 'steens',
            'joseph', 'k falls', 'Seattle'
        ]:
            # print('TESTING: %s...\n' % teststring)
            results = geocode(teststring)
            for result in results:
                result_coords = result['coords']
                self.assertTrue(result_coords[0] <= settings.STUDY_REGION['north'])
                self.assertTrue(result_coords[0] >= settings.STUDY_REGION['south'])
                self.assertTrue(result_coords[1] <= settings.STUDY_REGION['east'])
                self.assertTrue(result_coords[1] >= settings.STUDY_REGION['west'])
