import os
import json
import random
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
                                        ElementClickInterceptedException)

# Constants
OUTPUT_DIR = "./scraped_data/3_get_decision_makers"

# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
LINKEDIN_COMPANY_SIZE_FILTER = json.loads(os.getenv('LINKEDIN_COMPANY_SIZE_FILTER', '[]'))


def human_type(element, text):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))
    time.sleep(0.5)


def random_delay(min=1, max=3):
    """Random delay between actions"""
    time.sleep(random.uniform(min, max))


def handle_captcha():
    """Handle CAPTCHA by waiting for manual intervention"""
    print("\nCAPTCHA detected! Please solve it manually in the browser...")
    input("Press ENTER to continue after solving CAPTCHA...")


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
        print(f"Login failed: {str(e)}")
        raise


def navigate_to_home(driver):
    """Navigate to LinkedIn home page"""
    driver.get("https://www.linkedin.com/feed/")
    random_delay(2, 4)


def search_company_employees(driver, company_name, decision_maker_titles):
    """Search for decision makers in a specific company"""
    try:
        print(f"Searching decision makers for: {company_name}")

        # Search for company name
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'Search')]")))
        search_box.clear()
        human_type(search_box, company_name)
        search_box.send_keys(Keys.RETURN)
        random_delay(2, 4)

        # Click on "People" filter to search for people
        try:
            people_filter = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='People']")))
            people_filter.click()
            random_delay(1, 2)
        except Exception:
            print("People filter not found, trying alternative approach")
            # Try alternative selector
            try:
                people_filter = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'People')]")))
                people_filter.click()
                random_delay(1, 2)
            except Exception:
                print("Could not find People filter")
                return {}

        # Click "All filters"
        try:
            all_filters = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'All filters')]")))
            all_filters.click()
            random_delay(2, 3)
        except Exception:
            print("All filters button not found")
            return {}

        # Scroll to bottom of filters modal
        try:
            filters_modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'search-reusables__filters-bar')]")))
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", filters_modal)
            random_delay(1, 2)
        except Exception:
            print("Could not scroll filters modal")

        # Find and fill title field under Keywords section
        titles_text = ", ".join(decision_maker_titles)
        try:
            # Look for title input field
            title_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Add a title']")))
            title_input.clear()
            human_type(title_input, titles_text)
            random_delay(1, 2)
        except Exception:
            try:
                # Alternative selector for title field
                title_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'title')]")))
                title_input.clear()
                human_type(title_input, titles_text)
                random_delay(1, 2)
            except Exception:
                print("Could not find title input field")
                return {}

        # Click "Show results"
        try:
            show_results = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Show') and contains(text(), 'results')]")))
            show_results.click()
            random_delay(3, 5)
        except Exception:
            print("Show results button not found")
            return {}

        # Scrape results from first 5 pages
        decision_makers = {}

        for page in range(1, 6):  # Pages 1-5
            print(f"Processing page {page} for {company_name}")

            # Wait for results to load
            random_delay(2, 4)

            try:
                # Find all result cards on current page
                result_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'entity-result__item')]")))

                for card in result_cards:
                    try:
                        # Extract name
                        name_element = card.find_element(By.XPATH, ".//span[@aria-hidden='true']")
                        full_name = name_element.text.strip()

                        # Extract title
                        title_element = card.find_element(By.XPATH,
                                                          ".//div[contains(@class, 'entity-result__primary-subtitle')]")
                        title = title_element.text.strip()

                        if full_name and title:
                            decision_makers[title] = full_name
                            print(f"Found: {title} - {full_name}")

                    except Exception as e:
                        print(f"Error extracting person data: {str(e)}")
                        continue

            except Exception as e:
                print(f"No results found on page {page}: {str(e)}")
                break

            # Try to go to next page
            if page < 5:
                try:
                    next_button = driver.find_element(By.XPATH, f"//button[@aria-label='Page {page + 1}']")
                    driver.execute_script("arguments[0].click();", next_button)
                    random_delay(3, 5)
                except Exception:
                    print(f"No next page found after page {page}")
                    break

        return decision_makers

    except Exception as e:
        print(f"Error searching for {company_name}: {str(e)}")
        return {}


def scrape_decision_makers(driver,json_file_path, decision_maker_titles):
    """Main function to scrape decision makers from companies"""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load company data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        company_data = json.load(f)

    # Filter companies based on size filter
    companies_to_process = []
    for size_filter in LINKEDIN_COMPANY_SIZE_FILTER:
        if size_filter in company_data:
            companies_to_process.extend(company_data[size_filter])

    if not companies_to_process:
        print("No companies found matching the size filter criteria")
        return

    print(f"Found {len(companies_to_process)} companies to process")



    # Initialize results dictionary
    all_decision_makers = {}

    try:
        # Login to LinkedIn
        navigate_to_home(driver)

        # Process each company
        for idx, company in enumerate(companies_to_process, 1):
            print(f"\nProcessing {idx}/{len(companies_to_process)}: {company}")

            try:
                decision_makers = search_company_employees(driver, company, decision_maker_titles)

                if decision_makers:
                    all_decision_makers[company] = decision_makers
                    print(f"Found {len(decision_makers)} decision makers for {company}")
                else:
                    print(f"No decision makers found for {company}")

                # Navigate back to home for next search
                navigate_to_home(driver)

            except Exception as e:
                print(f"Failed to process {company}: {str(e)}")
                if "CAPTCHA" in str(e) or "bot" in str(e).lower():
                    handle_captcha()
                    # Retry after CAPTCHA
                    try:
                        decision_makers = search_company_employees(driver, company, decision_maker_titles)
                        if decision_makers:
                            all_decision_makers[company] = decision_makers
                    except Exception:
                        print(f"Still failing after CAPTCHA for {company}")

                navigate_to_home(driver)
                continue

            # Periodic longer break
            if idx % 3 == 0:
                pause_time = random.uniform(20, 30)
                print(f"Taking a longer break for {pause_time:.1f} seconds...")
                time.sleep(pause_time)
            else:
                random_delay(2, 5)

        # Save results
        output_file = f"{OUTPUT_DIR}/decision_makers.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_decision_makers, f, indent=2, ensure_ascii=False)

        print(f"\nProcessing complete. Results saved to {output_file}")
        print(f"Found decision makers for {len(all_decision_makers)} companies")

    finally:
        driver.quit()

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

# Example usage
if __name__ == "__main__":
    driver = initialize_driver()
    login_to_linkedin(driver)
    # Example parameters
    json_file_path = "./scraped_data/2_get_company_size_data/company_size_versus_company_name.json"
    decision_maker_titles = ["CEO", "CTO", "Founder", "VP", "Director", "President"]

    scrape_decision_makers(driver,json_file_path, decision_maker_titles)