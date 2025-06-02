from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options = options)

driver.get("https://www.youtube.com")


search_box = driver.find_element(By.NAME, "search_query")
search_box.send_keys("Windsor Knot")
time.sleep(1)
search_box.send_keys(Keys.CONTROL + "a")
time.sleep(1)
search_box.send_keys(Keys.BACKSPACE)
time.sleep(1)
search_box.send_keys("a")
time.sleep(1)
search_box.send_keys("P")
time.sleep(0.2)
search_box.send_keys("P")
time.sleep(0.5)
search_box.send_keys("L")
time.sleep(0.5)
search_box.send_keys("E")
time.sleep(1)

search_box.send_keys(Keys.RETURN)

time.sleep(1)

for _ in range(5):  
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(1)  

time.sleep(2)


