import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from _2_get_company_size_data import human_type

load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')


def initialize_driver():
    # Default path if run directly
    # Configure Chrome options (headless=False as requested)
    chrome_options = webdriver.ChromeOptions()

    profile_path = os.path.abspath("./SeleniumChromeProfile")
    chrome_options.add_argument(f"user-data-dir={profile_path}")
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
    """Login to LinkedIn with credentials and handle verification if needed"""
    driver.get("https://www.linkedin.com/login")
    try:
        # Type email and password
        human_type(WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "username"))), LINKEDIN_EMAIL)
        password_field = driver.find_element(By.ID, "password")
        human_type(password_field, LINKEDIN_PASSWORD)
        password_field.send_keys(Keys.RETURN)

        print("⏳ Waiting for login to complete...")
        time.sleep(3)  # Initial wait after submitting credentials

        # Check for multiple possible post-login scenarios
        try:
            # Check for CAPTCHA or security challenge
            if "challenge" in driver.current_url.lower() or "captcha" in driver.current_url.lower():
                print("🔒 Security challenge detected. Please complete manually and press Enter to continue...")
                input()
                # Wait additional time after manual verification


            # Check for email verification or additional security steps
            if "add-phone" in driver.current_url or "checkpoint" in driver.current_url:
                print("📧 Email verification or additional security step required.")
                print("Please complete the verification manually and press Enter to continue...")
                input()
                # Wait additional time after manual verification


            # Try multiple selectors for successful login verification
            success_selectors = [
                "//nav[@aria-label='Global navigation']",
                "//nav[contains(@class, 'global-nav')]",
                "//div[@id='global-nav']",
                "//a[@href='/feed/']",
                "//span[text()='Home']"
            ]

            login_successful = False
            for selector in success_selectors:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    login_successful = True
                    break
                except TimeoutException:
                    continue

            if not login_successful:
                # Final check - if we're on feed page, consider it successful
                if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                    login_successful = True

            if login_successful:
                print("✅ Login successful!")
                return True
            else:
                print(f"❌ Login verification failed. Current URL: {driver.current_url}")
                print("Page title:", driver.title)
                return False

        except Exception as verification_error:
            print(f"⚠️ Login verification error: {verification_error}")
            print(f"Current URL: {driver.current_url}")
            return False

    except Exception as e:
        print(f"❌ Login failed: {e}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Take screenshot for debugging

        return False