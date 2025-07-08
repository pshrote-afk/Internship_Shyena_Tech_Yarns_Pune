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



# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = "pdshrote@gcoen.ac.in"
LINKEDIN_PASSWORD = "J/110950089459"

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
                if "www" in next_line:
                    website = next_line
        
        # Check for Company size keyword
        if line == "Company size":
            # Check if next line exists and contains "employees"
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if "employees" in next_line:
                    company_size = next_line
    
    return website, company_size

def random_delay(min=1, max=3):
    """Random delay between actions"""
    time.sleep(random.uniform(min, max))


def human_type(element, text):
    """Type text with human-like delays"""
    for char in text:
        element.send_keys(char)
        

def login_to_linkedin(driver):
    """Login to LinkedIn with credentials"""
    driver.get("https://www.linkedin.com/login")
    try:
        human_type(WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "username"))), LINKEDIN_EMAIL)
        password_field = driver.find_element(By.ID, "password")
        human_type(password_field, LINKEDIN_PASSWORD)
        password_field.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.url_contains("feed"))
        print("Login successful")
    except Exception as e:
        print(f"Login failed")
        raise


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
            
            # Print all About section data
            try:
                about_section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//section[contains(@class,'about')]")))
                print("\nAbout Section Data:")
                print("------------------")
                # Print all visible text in the about section
                print(about_section.text)
                print("------------------\n")
                website, company_size = extract_website_and_company_size_info(about_section.text)
                print(website)
                print(company_size)
            except Exception as e:
                print(f"Could not extract full About section")
                
        except Exception as e:
            print(f"About tab not found for {company_name}")
            raise



        # Mark as processed
        processed_companies.add(company_name)
        save_progress()

    except Exception as e:
        print(f"Error processing {company_name}:")



        raise
    finally:
        # Return to home page
        try:
            driver.get("https://www.linkedin.com/feed/")
            random_delay(2, 4)
        except Exception:
            pass


def scrape_company_data(csv_file_path):
    """Main function to scrape company data"""
    # Load any existing progress
    
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

    try:
        # Read company names from CSV

        # Login to LinkedIn
        login_to_linkedin(driver)

        # Process companies
        company_name = "inflow federal"
        process_company(driver,company_name)

        print("\nProcessing complete. Final results saved.")

        # Clean up progress file after successful completion
    finally:
        driver.quit()


# This allows the script to be run directly if needed
if __name__ == "__main__":
    # Default path if run directly
    csv_path = "./scraped_data/1_scrape_job_data/scraped_jobs.csv"
    scrape_company_data(csv_path)