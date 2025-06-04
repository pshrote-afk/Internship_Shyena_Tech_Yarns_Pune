import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from _2_get_company_size_data import human_type

load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

def initialize_driver():
	# Default path if run directly
	# Configure Chrome options (headless=False as requested)
	chrome_options = webdriver.ChromeOptions()

	chrome_options.add_argument("--start-maximized")
	chrome_options.add_argument("--disable-blink-features=AutomationControlled")
	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
	chrome_options.add_experimental_option('useAutomationExtension', False)
	chrome_options.add_argument(
		"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
	# Add these to reduce detection and improve speed
	chrome_options.add_argument("--disable-web-security")
	chrome_options.add_argument("--allow-running-insecure-content")
	chrome_options.add_argument("--no-sandbox")
	chrome_options.add_argument("--disable-dev-shm-usage")

	driver = webdriver.Chrome(options=chrome_options)
	return driver

def login_to_linkedin(driver):
    """Login to LinkedIn with credentials"""
    driver.get("https://www.linkedin.com/login")
    try:
        human_type(WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "username"))), LINKEDIN_EMAIL)
        password_field = driver.find_element(By.ID, "password")
        human_type(password_field, LINKEDIN_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        WebDriverWait(driver, 20).until(EC.url_contains("feed"))
        print("Login successful")
    except Exception as e:
        print(f"Login failed")
        raise
