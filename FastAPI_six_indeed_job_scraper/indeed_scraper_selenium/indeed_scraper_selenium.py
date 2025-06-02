from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time,random

class IndeedScraper:
	
	def wait(self):
		time.sleep(random.uniform(1,3))
	
	def scrap(self):
		
		options = webdriver.ChromeOptions()
		driver = webdriver.Chrome(options = options)
        
		driver.get("https://in.indeed.com/?r=us")

		search_box = driver.find_element(By.ID, "text-input-what")
		search_box.send_keys("Windsor Knot")
		
		self.wait()

		search_box.send_keys(Keys.CONTROL + "a")
		time.sleep(1)
		search_box.send_keys(Keys.BACKSPACE)
		time.sleep(1)
		search_box.send_keys("G")
		time.sleep(1)
		search_box.send_keys("ene")
		time.sleep(0.2)
		search_box.send_keys("rat")
		time.sleep(0.5)
		search_box.send_keys("iv")
		time.sleep(0.5)
		search_box.send_keys("e")
		time.sleep(1)
		search_box.send_keys(" A")
		time.sleep(0.1)
		search_box.send_keys("I")
		time.sleep(1)

		search_box.send_keys(Keys.RETURN)

		time.sleep(1)

		time.sleep(20)


scraper = IndeedScraper()
scraper.scrap()

