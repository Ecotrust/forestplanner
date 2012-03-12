from selenium import webdriver
import unittest

class TestSequenceFunctions(unittest.TestCase):
	def setUp(self):
		pass#
	def tearDown(self):
		self.driver.close()

	def setup_profile(self, ua):
		profile = webdriver.FirefoxProfile()
		profile.set_preference("general.useragent.override", ua)
		return webdriver.Firefox(profile)

	def test_unsupported_browser(self):
		ua = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0.2) Gecko/20100101 Firefox/10.0.2'
		self.driver = self.setup_profile(ua)
		self.driver.get("http://localhost:8000")
		self.assertIn("Your current browser is not supported", 
			self.driver.find_element_by_tag_name('h1').text)

	# def test_supported_browser(self):
	# 	ua = "Mozilla/5.0 (Windows NT 6.2; rv:9.0.1) Gecko/20100101 Firefox/9.0.1"
	# 	self.driver = self.setup_profile(ua)
	# 	self.assertRaises("WebDriverException",
	# 		self.driver.get("http://localhost:8000"))
	# 	# self.assertIn("Your current browser is not supported", 
	# 	# 	self.driver.find_element_by_tag_name('h1').text)

if __name__ == '__main__':
    unittest.main()