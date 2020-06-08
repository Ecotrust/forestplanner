import unittest
# from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver

# from django.test import TestCase
from django.conf import settings

class FrontendTests(unittest.TestCase):
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

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass()
    #     cls.selenium = WebDriver()
    #     cls.selenium.implicitly_wait(2)
    #
    # @classmethod
    # def tearDownClass(cls):
    #     cls.selenium.quit()
    #     super().tearDownClass()

    # def test_home(self):
    #    # TODOS:
    #    #   Header placement
    #    #   Header branding
    #    #   Header Menu Items
    #    #   ...
    #    print("hi")

    # def test_login(self):
    def test_header(self):
        # look for <header> tag
        self.browser.get('http://localhost:8000/landmapper/')
        header = self.browser.find_element_by_tag_name('header')
        print(header)
        self.assertIn('svg', header.text)

        self.fail('finish test')

        # check for logo
        # logo = self.browser.find_element_by_tag_name()

if __name__ == '__main__':
    unittest.main(warnings='ignore')
    
# class MySeleniumTests(StaticLiveServerTestCase):
#     # fixtures = ['user-data.json']
#     #
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.selenium = WebDriver()
#         cls.selenium.implicitly_wait(2)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()
#
#     # def test_login(self):
#     def test_browser(self):
#         # import ipdb; ipdb.set_trace()
#         print('get server')
#         print('URL: ""%s"' % self.live_server_url)
#         # foo = self.selenium.get(self.live_server_url)
#         # foo.title
#         # self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
#         # username_input = self.selenium.find_element_by_name("username")
#         # username_input.send_keys('myuser')
#         # password_input = self.selenium.find_element_by_name("password")
#         # password_input.send_keys('secret')
#         # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
#




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
