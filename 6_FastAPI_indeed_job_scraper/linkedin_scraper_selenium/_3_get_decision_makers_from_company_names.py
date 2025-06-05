import json
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dotenv import load_dotenv
import re
from urllib.parse import quote_plus
import requests


def scrape_decision_makers(json_file_path, decision_maker_titles, max_results_per_search=5, proxy_list=None):
    """
    Scrape LinkedIn for decision makers from companies based on size filter.

    Args:
        json_file_path (str): Path to JSON file containing companies organized by employee count
        decision_maker_titles (list): List of decision maker titles to search for
        max_results_per_search (int): Maximum number of results to extract per search (default: 5)
        proxy_list (list): Optional list of proxy servers in format ["ip:port", "ip:port:username:password"]

    Returns:
        dict: Dictionary with company names as keys and decision makers as values
    """

    # Load environment variables
    load_dotenv()

    # Configuration
    OUTPUT_DIR = "./scraped_data/3_get_decision_makers"
    PROGRESS_FILE = f"{OUTPUT_DIR}/scraping_progress.json"
    OUTPUT_FILE = f"{OUTPUT_DIR}/company_name_versus_decision_maker_name.json"
    DELAY_MIN = 3  # Minimum delay between searches (seconds)
    DELAY_MAX = 8  # Maximum delay between searches (seconds)
    COMPANY_DELAY_MIN = 10  # Minimum delay between companies (seconds)
    COMPANY_DELAY_MAX = 20  # Maximum delay between companies (seconds)

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load company size filter from .env
    company_size_filter = os.getenv('LINKEDIN_COMPANY_SIZE_FILTER', '[]')  # get filter list, else empty list []
    try:
        size_filter = json.loads(company_size_filter)
    except json.JSONDecodeError:
        print("Error: Invalid LINKEDIN_COMPANY_SIZE_FILTER format in .env file")
        return {}

    print(f"Company size filter: {size_filter}")

    # Load input JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            companies_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return {}

    # Filter companies based on size criteria
    filtered_companies = []
    for size_category in size_filter:
        if size_category in companies_data:
            filtered_companies.extend(companies_data[size_category])

    print(f"Total companies to process: {len(filtered_companies)}")

    # Load existing progress
    progress_data = load_progress(PROGRESS_FILE)
    final_results = load_progress(OUTPUT_FILE)

    # Initialize proxy and user agent tracking
    current_proxy_index = 0
    current_ua_index = 0

    # Setup initial WebDriver
    driver = setup_driver(proxy_list, current_proxy_index if proxy_list else None, current_ua_index)

    try:
        # Process each company
        for company_idx, company_name in enumerate(filtered_companies):
            print(f"\nProcessing company {company_idx + 1}/{len(filtered_companies)}: {company_name}")

            # Skip if already processed
            if company_name in final_results:
                print(f"Company {company_name} already processed, skipping...")
                continue

            company_decision_makers = {}

            # Search for each decision maker title
            for title_idx, title in enumerate(decision_maker_titles):
                print(f"  Searching for {title} at {company_name}")

                # Create unique key for progress tracking
                progress_key = f"{company_name}_{title}"

                # Skip if already processed
                if progress_key in progress_data:
                    print(f"    Already processed {title} for {company_name}")
                    # Add to company results if not already there
                    if progress_key in progress_data:
                        for name, job_title in progress_data[progress_key].items():
                            company_decision_makers[name] = job_title
                    continue

                # Perform search
                search_results = search_linkedin_profiles(driver, title, company_name, max_results_per_search)

                # Save progress for this search
                progress_data[progress_key] = search_results
                save_progress(PROGRESS_FILE, progress_data)

                # Add to company results
                company_decision_makers.update(search_results)

                # Random delay between searches
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                print(f"    Waiting {delay:.1f} seconds...")
                time.sleep(delay)

            # Save company results
            final_results[company_name] = company_decision_makers
            save_progress(OUTPUT_FILE, final_results)

            print(f"  Found {len(company_decision_makers)} decision makers for {company_name}")

            # After processing each company, rotate proxy and user agent
            if company_idx < len(filtered_companies) - 1:  # Don't rotate after last company
                print("  Rotating proxy and user agent...")
                driver.quit()

                # Update indices for proxy and user agent rotation
                current_ua_index = (current_ua_index + 1) % len(get_user_agents())
                if proxy_list:
                    current_proxy_index = (current_proxy_index + 1) % len(proxy_list)

                # Longer delay between companies
                company_delay = random.uniform(COMPANY_DELAY_MIN, COMPANY_DELAY_MAX)
                print(f"  Waiting {company_delay:.1f} seconds before next company...")
                time.sleep(company_delay)

                # Setup new driver with rotated proxy and user agent
                driver = setup_driver(proxy_list, current_proxy_index if proxy_list else None, current_ua_index)

    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress saved.")
    except Exception as e:
        print(f"Error during scraping")
    finally:
        driver.quit()

    print(f"\nScraping completed. Results saved to {OUTPUT_FILE}")
    return final_results


def setup_driver(proxy_list=None, proxy_index=None, ua_index=0):
    """Setup and return Chrome WebDriver with rotating proxy and user agent."""
    chrome_options = Options()

    # Basic stealth options
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Get rotating user agent
    user_agents = get_user_agents()
    selected_ua = user_agents[ua_index % len(user_agents)]
    chrome_options.add_argument(f"--user-agent={selected_ua}")

    print(f"Using User Agent: {selected_ua[:50]}...")

    # Setup proxy if provided
    if proxy_list and proxy_index is not None:
        proxy = proxy_list[proxy_index % len(proxy_list)]

        # Handle different proxy formats
        if proxy.count(':') == 1:
            # Format: ip:port
            proxy_host, proxy_port = proxy.split(':')
            chrome_options.add_argument(f'--proxy-server=http://{proxy_host}:{proxy_port}')
            print(f"Using Proxy: {proxy_host}:{proxy_port}")
        elif proxy.count(':') == 3:
            # Format: ip:port:username:password
            proxy_parts = proxy.split(':')
            proxy_host, proxy_port, username, password = proxy_parts
            chrome_options.add_argument(f'--proxy-server=http://{proxy_host}:{proxy_port}')
            # Note: Username/password authentication might need additional setup
            print(f"Using Authenticated Proxy: {proxy_host}:{proxy_port}")

    # Additional randomization
    chrome_options.add_argument(f"--window-size={random.randint(1200, 1920)},{random.randint(800, 1080)}")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Execute stealth scripts
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")

        return driver
    except Exception as e:
        print(f"Error setting up driver: {str(e)}")
        raise


def get_user_agents():
    """Return a list of realistic user agents for rotation."""
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
    ]




def search_linkedin_profiles(driver, title, company_name, max_results):
    """
    Search for LinkedIn profiles and extract names and titles.

    Args:
        driver: Selenium WebDriver instance
        title (str): Decision maker title to search for
        company_name (str): Company name to search for
        max_results (int): Maximum number of results to extract

    Returns:
        dict: Dictionary with full names as keys and job titles as values
    """
    results = {}

    try:
        # Construct search query
        search_query = f'site:linkedin.com/in/ "{title}" AND "{company_name}"'
        google_url = f"https://www.google.com/search?q={quote_plus(search_query)}"

        print(f"    Search query: {search_query}")

        # Navigate to Google search
        driver.get(google_url)

        # Wait for search results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
        )

        # Find search result elements
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")

        processed_count = 0
        for result in search_results[:max_results * 2]:  # Get more results to filter
            if processed_count >= max_results:
                break

            try:
                # Extract title and URL
                title_element = result.find_element(By.CSS_SELECTOR, "h3")
                link_element = result.find_element(By.CSS_SELECTOR, "a")

                result_title = title_element.text
                result_url = link_element.get_attribute("href")

                # Check if it's a LinkedIn profile URL
                if "linkedin.com/in/" in result_url:
                    # Extract name and job title from the result
                    name, job_title = extract_name_and_title(result_title, result)

                    if name and job_title:
                        results[name] = job_title
                        processed_count += 1
                        print(f"      Found: {name} - {job_title}")

            except (NoSuchElementException, AttributeError) as e:
                continue

        print(f"    Extracted {len(results)} profiles")

    except TimeoutException:
        print(f"    Timeout while searching for {title} at {company_name}")
    except WebDriverException as e:
        print(f"    WebDriver error")
    except Exception as e:
        print(f"    Unexpected error")

    return results


def extract_name_and_title(result_title, result_element):
    """
    Extract name and job title from search result.

    Args:
        result_title (str): Title text from search result
        result_element: Selenium element of the search result

    Returns:
        tuple: (name, job_title) or (None, None) if extraction fails
    """
    try:
        # Try to get description from the result
        description = ""
        try:
            desc_element = result_element.find_element(By.CSS_SELECTOR, ".VwiC3b")
            description = desc_element.text
        except NoSuchElementException:
            pass

        # Extract name (usually the first part before " - " or " | ")
        name_match = re.match(r'^([^-|]+)', result_title)
        if name_match:
            name = name_match.group(1).strip()
        else:
            name = result_title.split()[0:2]  # Take first two words as fallback
            name = " ".join(name)

        # Extract job title (look for patterns in title and description)
        job_title = ""

        # Look for job title patterns in the result title
        title_patterns = [
            r'[-|]\s*([^-|]+(?:CEO|CTO|CIO|VP|Director|Head|Manager|Engineer|Lead)[^-|]*)',
            r'[-|]\s*([^-|]*(?:Vice President|VP|Director|Head|Manager)[^-|]*)',
            r'[-|]\s*([^-|]*(?:Chief|Senior|Principal)[^-|]*)',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, result_title, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break

        # If no title found in result title, look in description
        if not job_title and description:
            desc_patterns = [
                r'((?:CEO|CTO|CIO|VP|Vice President|Director|Head|Manager|Engineer|Lead)[^.]*)',
                r'(Chief [^.]*)',
                r'(Senior [^.]*)'
            ]

            for pattern in desc_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    job_title = match.group(1).strip()
                    break

        # Clean up extracted data
        name = clean_text(name)
        job_title = clean_text(job_title)

        # Validate extracted data
        if len(name) > 3 and len(job_title) > 3:
            return name, job_title

    except Exception as e:
        print(f"      Error extracting name and title")

    return None, None


def clean_text(text):
    """Clean and normalize extracted text."""
    if not text:
        return ""

    # Remove extra whitespace and special characters
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove common prefixes/suffixes
    text = re.sub(r'^[-|•]\s*', '', text)
    text = re.sub(r'\s*[-|•]$', '', text)

    return text


def load_progress(filename):
    """Load progress from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Corrupted progress file {filename}, starting fresh")
        return {}


def save_progress(filename, data):
    """Save progress to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving progress to {filename}")


# Example usage (to be called from main.py)
if __name__ == "__main__":
    # Example decision maker titles
    decision_maker_titles = [
        "CTO", "CIO", "VP - Engineering", "VP - Delivery", "Director - Engineering",
        "Director - Delivery", "Director of Software Engineering", "Director of Data",
        "Director of AI Delivery", "Head of Solutions Engineering",
        "Vice President of Professional Services", "Director Software Engineering",
        "Director of AI Solutions", "Head of AI", "Director of Product Engineering"
    ]

    # Example proxy list (optional)
    # You can provide your own proxy list or use free proxies
    proxy_list = [
        "123.456.789.012:8080",
        "987.654.321.098:3128",
        "111.222.333.444:8080:username:password"  # With authentication
    ]

    # Or get free proxies automatically (less reliable)
    # proxy_list = get_free_proxies()

    # Example call
    results = scrape_decision_makers(
        json_file_path="companies.json",
        decision_maker_titles=decision_maker_titles,
        max_results_per_search=5,
        proxy_list=proxy_list  # Optional, pass None if you don't want to use proxies
    )

    print(f"Total results: {len(results)}")