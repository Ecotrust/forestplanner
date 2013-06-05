from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest
import selenium


class Test(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://stage.forestplanner.ecotrust.org/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_(self):
        driver = self.driver
        driver.delete_all_cookies()

        driver.get(self.base_url + "/")
        driver.find_element_by_id("signin").click()
        driver.find_element_by_id("id_login").clear()
        driver.find_element_by_id("id_login").send_keys("test")
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys("test")
        driver.find_element_by_css_selector("button.btn").click()
        driver.find_element_by_xpath("(//a[contains(text(),'Manage Your Properties')])[2]").click()
        driver.find_element_by_id("input-geosearch").clear()
        driver.find_element_by_id("input-geosearch").send_keys("Oakridge, OR")
        driver.find_element_by_css_selector("div.controls > button.btn.btn-mini").click()
        driver.find_element_by_link_text("-").click()
        driver.find_element_by_link_text("-").click()
        driver.find_element_by_link_text("-").click()

        themap = driver.find_element_by_id("map")
        import ipdb; ipdb.set_trace()

        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_css_selector("button.btn.btn-success").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_146_svgRoot").click()
        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("test")
        driver.find_element_by_link_text("Create").click()
        driver.find_element_by_xpath("//div[@id='property-html']/div[4]/div/div/div[2]/div/button").click()
        driver.find_element_by_css_selector("#stands-none > div.pull-right > button.btn.btn-success").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_css_selector("div.row-fluid > div.pull-right > button.btn.btn-success").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_id("OpenLayers.Layer.Vector_317_svgRoot").click()
        driver.find_element_by_css_selector("#stand-html > div.row-fluid > div.pull-right > button.btn.btn-success").click()
        driver.find_element_by_xpath("//div[@id='stand-html']/div/div[2]/div/button").click()
        driver.find_element_by_link_text("Properties").click()
        driver.find_element_by_link_text("Define Stand Groups").click()
        driver.find_element_by_xpath("//button").click()
        driver.find_element_by_css_selector("input.span12").clear()
        driver.find_element_by_css_selector("input.span12").send_keys("test")
        driver.find_element_by_css_selector("input.input-mini").clear()
        driver.find_element_by_css_selector("input.input-mini").send_keys("200")
        driver.find_element_by_xpath("(//input[@type='text'])[4]").clear()
        driver.find_element_by_xpath("(//input[@type='text'])[4]").send_keys("25")
        driver.find_element_by_xpath("//div[3]/div/div/div[2]/div/button").click()
        driver.find_element_by_css_selector("a.select2-choice.select2-default > span").click()
        driver.find_element_by_css_selector("input.select2-input.select2-focused").clear()
        driver.find_element_by_css_selector("input.select2-input.select2-focused").send_keys("Doug")
        driver.find_element_by_xpath("(//input[@name='size-class_0'])[2]").click()
        driver.find_element_by_xpath("//div[@id='myCarousel']/div/div/div[2]/div/label[3]").click()
        driver.find_element_by_name("percentage").clear()
        driver.find_element_by_name("percentage").send_keys("100")
        driver.find_element_by_xpath("//div[@id='myCarousel']/div/div/div[3]/div/button[2]").click()
        driver.find_element_by_xpath("//div[3]/button[2]").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_189").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_178").click()
        driver.find_element_by_xpath("//div[3]/button").click()
        driver.find_element_by_link_text("properties").click()
        driver.find_element_by_xpath("//div[@id='property-html']/div[4]/div/div/div[2]/div/button").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_320").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_309").click()
        driver.find_element_by_link_text("Properties").click()
        driver.find_element_by_xpath("//div[@id='property-html']/div[4]/div/div/div[2]/div[3]/button").click()
        driver.find_element_by_xpath("//div[@id='scenario-html']/div/div/div[2]/table/tbody/tr/td/div[3]/div[4]").click()
        driver.find_element_by_xpath("//div[@id='scenario-html']/div/div/div[2]/table/tbody/tr/td/div[3]/div[3]").click()
        driver.find_element_by_xpath("//div[@id='scenario-html']/div/div/div[2]/table/tbody/tr/td/div/button[2]").click()
        driver.find_element_by_id("scenario-edit-rx-tab").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_350").click()
        driver.find_element_by_id("OpenLayers.Geometry.Polygon_339").click()
        driver.find_element_by_xpath("//div[@id='scenario-edit-rx-content']/div[3]/table/tbody/tr/td/div[2]/button[3]").click()
        driver.find_element_by_id("scenario-review-tab").click()
        driver.find_element_by_xpath("//div[@id='scenario-review-content']/div[2]/div/button").click()
        driver.find_element_by_xpath("//div[@id='scenario-html']/div/div/div[2]/header/div/button[2]").click()
        driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        driver.find_element_by_xpath("//div[@id='scenario-charts-tab-content']/div/div/ul/li[2]/a/span").click()
        driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        driver.find_element_by_css_selector("span.text").click()
        driver.find_element_by_id("scenario-maps-tab").click()
        driver.find_element_by_xpath("//div[@id='scenario-html']/div/div/div[2]/header/div/button[2]").click()
        driver.find_element_by_id("scenario-charts-tab").click()
        driver.find_element_by_id("scenario-maps-tab").click()
        driver.find_element_by_css_selector("div.span3 > div.btn-group.bootstrap-select > button.btn.dropdown-toggle").click()
        driver.find_element_by_xpath("//div[@id='scenario-maps-tab-content']/div/div/div/div/ul/li[2]/a/span").click()
        driver.find_element_by_css_selector("header.clearfix > div.btn-group.pull-right > button.btn.btn-mini").click()
        driver.find_element_by_xpath("//div[@id='property-html']/div[4]/div/div/div[2]/div[3]/button").click()

    def is_element_present(self, how, what):
        try:
                self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
                return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert.text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
