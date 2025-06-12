import os
import csv
import json
import random
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException,
                                        NoSuchElementException)

# Constants
OUTPUT_DIR = "./scraped_data/2_get_company_size_data"

# Initialize data structures
processed_companies = set()
company_website_dict = {}
company_size_dict = {
    "1-10 employees": set(),
    "11-50 employees": set(),
    "51-200 employees": set(),
    "201-500 employees": set(),
    "501-1000 employees": set(),
    "1001-5000 employees": set(),
    "5001-10,000 employees": set(),
    "10,001+ employees": set(),
    "unknown": set()
}

# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

# my new fav function
def extract_website_and_company_size_info(about_section_text):
    """
    Extracts website and company size information from about section text.

    Args:
        about_section_text (str): The input text containing company information

    Returns:
        tuple: (website, company_size) - extracted information or "unknown" if not found
    """
    lines = about_section_text.split('\n')
    website = "unknown"
    company_size = "unknown"

    for i, line in enumerate(lines):
        line = line.strip()

        # Check for Website keyword
        if line == "Website":
            # Check if next line exists and contains "www"
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if "www" in next_line or "http" in next_line:
                    website = next_line


        if line == "Industry":
            # Check if previous, previous  line contains "Verified page"
            next_line = lines[i + 1].strip()
            next_to_next_line = lines[i + 2].strip()
            if "Company size" in next_to_next_line:
                industry = next_line



        # Check for Company size keyword
        if line == "Company size":
            # Check if next line exists and contains "employees"
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if "employees" in next_line:
                    company_size = next_line


    return website, company_size

def save_progress():
    """Save current progress to file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    progress_file = f"{OUTPUT_DIR}/progress.json"

    progress_data = {
        'processed': list(processed_companies),
        'websites': company_website_dict,
        'sizes': {k: list(v) for k, v in company_size_dict.items()}
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f, indent=2)

def load_progress():
    """Load progress from file if exists"""
    global processed_companies, company_website_dict, company_size_dict

    progress_file = f"{OUTPUT_DIR}/progress.json"
    if not os.path.exists(progress_file):
        return

    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)

        processed_companies = set(progress_data.get('processed', []))
        company_website_dict = progress_data.get('websites', {})

        # Load sizes and convert lists back to sets
        sizes = progress_data.get('sizes', {})
        for bucket in company_size_dict.keys():
            company_size_dict[bucket] = set(sizes.get(bucket, []))

    except json.JSONDecodeError:
        print("Progress file corrupted, starting fresh")


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





def get_employee_bucket(size_str):
    """Categorize employee count into buckets"""
    if not size_str or size_str.lower() == 'unknown':
        return "unknown"

    # Clean and normalize the string
    clean_str = size_str.replace(',', '').replace(' ', '').lower()

    # Remove non-numeric characters except digits, '+', and '-'
    clean_str = ''.join(c for c in clean_str if c.isdigit() or c in '+-')

    # Handle different formats
    if '-' in clean_str:
        # Handle ranges like "2-10" or "1001-5000"
        parts = clean_str.split('-')
        try:
            # Take the upper bound of the range
            max_val = int(parts[1]) if parts[1] else int(parts[0])
        except (ValueError, IndexError):
            return "unknown"
    elif '+' in clean_str:
        # Handle "10000+" cases
        try:
            max_val = int(clean_str.split('+')[0])
        except ValueError:
            return "unknown"
    else:
        # Handle single number cases
        try:
            max_val = int(clean_str)
        except ValueError:
            return "unknown"

    # Categorize based on the max value
    if max_val <= 10:
        return "1-10 employees"
    elif max_val <= 50:
        return "11-50 employees"
    elif max_val <= 200:
        return "51-200 employees"
    elif max_val <= 500:
        return "201-500 employees"
    elif max_val <= 1000:
        return "501-1000 employees"
    elif max_val <= 5000:
        return "1001-5000 employees"
    elif max_val <= 10000:
        return "5001-10,000 employees"
    elif max_val > 10000:
        return "10,001+ employees"
    return "unknown"


def process_company(driver, company_name):
    """Process a single company to extract website and size"""
    try:
        print(f"Processing: {company_name}")

        # Search for company
        try:
            search_box = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'Search')]")))
            search_box.clear()
            human_type(search_box, company_name)
            search_box.send_keys(Keys.RETURN)
            random_delay(2, 4)
        except Exception as e:
            print(f"Search failed for {company_name}")
            raise

        # Apply company filter
        try:
            company_filter = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Companies']")))
            company_filter.click()
            random_delay(1, 2)
        except Exception:
            print("Company filter not found, proceeding with results")

        # Open first result
        try:
            first_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/company/')]")))
            first_result.click()
            random_delay(2, 3)
        except Exception as e:
            print(f"No company results found for {company_name}")
            raise

        # Go to About tab
        try:
            about_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/about/')]")))
            about_tab.click()
            random_delay(2, 3)
        except Exception as e:
            print(f"About tab not found for {company_name}")
            raise

            # Print all About section data
        try:
            about_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[contains(@class,'about')]")))

            website, company_size = extract_website_and_company_size_info(about_section.text)
            print("------------------")
            print(website)
            print(company_size)
            print("------------------\n")

        except Exception as e:
            print(f"Could not extract full About section")

        except Exception as e:
            print(f"About tab not found for {company_name}")
            raise

        company_website_dict[company_name] = website

        bucket = get_employee_bucket(company_size)
        company_size_dict[bucket].add(company_name)

        # Mark as processed
        processed_companies.add(company_name)
        save_progress()

    except Exception as e:
        print(f"Error processing {company_name}: {str(e)}")
        company_website_dict[company_name] = "unknown"
        company_size_dict["unknown"].add(company_name)
        processed_companies.add(company_name)
        save_progress()
        raise
    finally:
        # Return to home page
        try:
            driver.get("https://www.linkedin.com/feed/")
            random_delay(2, 4)
        except Exception:
            pass


def scrape_company_data(driver,csv_file_path):
    """Main function to scrape company data"""
    # Load any existing progress
    load_progress()

    try:
        # Read company names from CSV
        companies = set()
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company = row['company'].strip()
                if company:  # Skip empty company names
                    companies.add(company)
        # Filter out already processed companies
        companies_to_process = [c for c in companies if c not in processed_companies]
        total_companies = len(companies_to_process)

        if not total_companies:
            print("All companies already processed.")
            return

        print(f"Found {total_companies} companies to process")

        # Login to LinkedIn


        # Process companies
        for idx, company in enumerate(companies_to_process, 1):
            print(f"\nProcessing {idx}/{total_companies}: {company}")
            try:
                process_company(driver, company)
            except Exception as e:
                print(f"Failed to process {company}: {str(e)}")
                if "CAPTCHA" in str(e) or "bot" in str(e).lower():
                    handle_captcha()
                    # Try the same company again after CAPTCHA
                    try:
                        print(f"Retrying {company} after CAPTCHA")
                        process_company(driver, company)
                    except Exception as e:
                        print(f"Still failing after CAPTCHA: {str(e)}")
                        continue

            # Periodic longer break
            if idx % 5 == 0:
                pause_time = random.uniform(15, 25)
                print(f"Taking a longer break for {pause_time:.1f} seconds...")
                time.sleep(pause_time)
            else:
                random_delay(1, 3)

        # Save final results
        website_file = f"{OUTPUT_DIR}/company_versus_website.json"
        with open(website_file, 'w') as f:
            json.dump(company_website_dict, f, indent=2)

        size_file = f"{OUTPUT_DIR}/company_size_versus_company_name.json"
        size_dict_serializable = {k: list(v) for k, v in company_size_dict.items()}
        with open(size_file, 'w') as f:
            json.dump(size_dict_serializable, f, indent=2)

        print("\nProcessing complete. Final results saved.")

        # Clean up progress file after successful completion
        progress_file = f"{OUTPUT_DIR}/progress.json"
        if os.path.exists(progress_file):
            os.remove(progress_file)

    finally:
        driver.quit()


# This allows the script to be run directly if needed
if __name__ == "__main__":
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

    csv_path = "./scraped_data/1_get_company_names/linkedin_Generative AI_jobs.csv"
    scrape_company_data(driver,csv_path)