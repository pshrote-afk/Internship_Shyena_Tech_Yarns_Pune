import json
import os
import time
import random
import pandas as pd
from datetime import datetime
import requests
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from dotenv import load_dotenv
import re
from urllib.parse import quote_plus, urljoin
import logging
import asyncio

from crawl4ai import LLMConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_decision_makers_google_api(json_file_path, decision_maker_titles, max_results_per_search,
                                            api_csv_path):
    """
    Scrape LinkedIn for decision makers using Google Search API and Crawl4AI v0.6.0.

    Args:
        json_file_path (str): Path to JSON file containing companies organized by employee count
        decision_maker_titles (list): List of decision maker titles to search for
        max_results_per_search (int): Maximum number of results to extract per search (default: 5)
        api_csv_path (str): Path to CSV file containing API keys

    Returns:
        dict: Dictionary with company names as keys and decision makers as values
    """

    # Load environment variables
    load_dotenv()

    # Configuration
    OUTPUT_DIR = "./scraped_data/4_get_decision_makers_google_api"
    PROGRESS_FILE = f"{OUTPUT_DIR}/scraping_progress.json"
    OUTPUT_FILE = f"{OUTPUT_DIR}/company_name_versus_decision_maker_name.json"
    SEARCH_DELAY_MIN = 2  # Minimum delay between searches (seconds)
    SEARCH_DELAY_MAX = 5  # Maximum delay between searches (seconds)
    CRAWL_DELAY_MIN = 3  # Minimum delay between crawls (seconds)
    CRAWL_DELAY_MAX = 7  # Maximum delay between crawls (seconds)
    DAILY_LIMIT = 100  # Google Custom Search API daily limit per key
    WARNING_THRESHOLD = 70  # Warn when API key usage hits this threshold

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load company size filter from .env
    company_size_filter = os.getenv('LINKEDIN_COMPANY_SIZE_FILTER', '[]')
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

    # Initialize API key manager
    api_manager = GoogleAPIManager(api_csv_path, DAILY_LIMIT, WARNING_THRESHOLD)

    # Initialize AsyncWebCrawler with v0.6.0 configuration
    async with AsyncWebCrawler(
            browser_type="chromium",  # Updated from crawler_type
            headless=True,
            verbose=True
    ) as crawler:
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
                        for person_data in progress_data[progress_key]:
                            name = person_data.get('name')
                            if name:
                                company_decision_makers[name] = person_data
                        continue

                    # Check if we can make API calls
                    if not api_manager.can_make_request():
                        print("All API keys have hit their daily limits. Queuing for next day...")
                        print("Please run this script tomorrow to continue processing.")
                        break

                    # Perform search
                    search_results = search_linkedin_profiles_google_api(
                        api_manager, title, company_name, max_results_per_search
                    )

                    if not search_results:
                        print(f"    No LinkedIn profiles found for {title} at {company_name}")
                        progress_data[progress_key] = []
                        save_progress(PROGRESS_FILE, progress_data)
                        continue

                    # Scrape each LinkedIn profile
                    scraped_profiles = []
                    for linkedin_url in search_results:
                        print(f"    Scraping profile: {linkedin_url}")

                        # Human-like delay before crawling
                        delay = random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX)
                        print(f"    Waiting {delay:.1f} seconds before crawling...")
                        time.sleep(delay)

                        try:
                            profile_data = await scrape_linkedin_profile(crawler, linkedin_url, title, company_name)
                            if profile_data:
                                scraped_profiles.append(profile_data)
                                print(f"      Found: {profile_data['name']} - {profile_data['job_title']}")
                        except Exception as e:
                            print(f"    Error scraping {linkedin_url}: {str(e)}")
                            if "anti-bot" in str(e).lower() or "blocked" in str(e).lower():
                                print("Anti-bot measures detected. Please resolve manually and restart.")
                                input("Press Enter when ready to continue...")
                            continue

                    # Save progress for this search
                    progress_data[progress_key] = scraped_profiles
                    save_progress(PROGRESS_FILE, progress_data)

                    # Add to company results
                    for person_data in scraped_profiles:
                        name = person_data.get('name')
                        if name:
                            company_decision_makers[name] = person_data

                    # Random delay between searches
                    delay = random.uniform(SEARCH_DELAY_MIN, SEARCH_DELAY_MAX)
                    print(f"    Waiting {delay:.1f} seconds...")
                    time.sleep(delay)

                # Save company results
                final_results[company_name] = company_decision_makers
                save_progress(OUTPUT_FILE, final_results)

                print(f"  Found {len(company_decision_makers)} decision makers for {company_name}")

                # Check if we should stop due to API limits
                if not api_manager.can_make_request():
                    print("All API keys have hit their daily limits. Stopping processing.")
                    break

        except KeyboardInterrupt:
            print("\nScraping interrupted by user. Progress saved.")
        except Exception as e:
            print(f"Error during scraping: {str(e)}")

    print(f"\nScraping completed. Results saved to {OUTPUT_FILE}")
    return final_results


class GoogleAPIManager:
    """Manages Google API keys rotation and usage tracking."""

    def __init__(self, csv_file, daily_limit, warning_threshold):
        self.csv_file = csv_file
        self.daily_limit = daily_limit
        self.warning_threshold = warning_threshold
        self.current_key_index = 0
        self.load_keys()

    def load_keys(self):
        """Load API keys from CSV file."""
        try:
            self.df = pd.read_csv(self.csv_file)
            self.update_daily_usage()
            print(f"Loaded {len(self.df)} API keys")
        except Exception as e:
            raise Exception(f"Error loading API keys: {str(e)}")

    def update_daily_usage(self):
        """Reset usage count if date has changed."""
        today = datetime.now().strftime('%Y-%m-%d')

        for idx, row in self.df.iterrows():
            if row['last_used_date'] != today:
                self.df.at[idx, 'uses'] = 0
                self.df.at[idx, 'last_used_date'] = today

        self.save_keys()

    def get_next_available_key(self):
        """Get next available API key that hasn't hit daily limit."""
        for _ in range(len(self.df)):
            current_row = self.df.iloc[self.current_key_index]

            if current_row['uses'] < self.daily_limit:
                return {
                    'api_key': current_row['api_key'],
                    'cse_id': current_row['cse_id'],
                    'index': self.current_key_index
                }

            self.current_key_index = (self.current_key_index + 1) % len(self.df)

        return None

    def increment_usage(self, key_index):
        """Increment usage count for a specific key."""
        self.df.at[key_index, 'uses'] += 1
        current_uses = self.df.at[key_index, 'uses']

        if current_uses == self.warning_threshold:
            print(f"⚠️  WARNING: API key {key_index + 1} has reached {self.warning_threshold} uses")

        if current_uses >= self.daily_limit:
            print(f"🚫 API key {key_index + 1} has hit daily limit ({self.daily_limit} uses)")

        self.save_keys()
        self.current_key_index = (key_index + 1) % len(self.df)

    def can_make_request(self):
        """Check if any API key is available."""
        return self.get_next_available_key() is not None

    def save_keys(self):
        """Save updated API key data to CSV."""
        try:
            self.df.to_csv(self.csv_file, index=False)
        except Exception as e:
            print(f"Error saving API keys: {str(e)}")


def search_linkedin_profiles_google_api(api_manager, title, company_name, max_results):
    """
    Search for LinkedIn profiles using Google Custom Search API.

    Args:
        api_manager: GoogleAPIManager instance
        title (str): Decision maker title to search for
        company_name (str): Company name to search for
        max_results (int): Maximum number of results to return

    Returns:
        list: List of LinkedIn profile URLs
    """

    # Get available API key
    key_data = api_manager.get_next_available_key()
    if not key_data:
        print("No available API keys")
        return []

    # Construct search query - modified approach for better results
    search_queries = [
        f'site:linkedin.com/in/ "{title}" "{company_name}"',
        f'site:linkedin.com/in/ "{company_name}" "{title}"',
        f'site:linkedin.com/in/ {title.replace(" ", "+")} {company_name.replace(" ", "+")}'
    ]

    all_urls = set()

    for query in search_queries:
        if len(all_urls) >= max_results:
            break

        print(f"    API query: {query}")

        # Make API request
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': key_data['api_key'],
            'cx': key_data['cse_id'],
            'q': query,
            'num': min(10, max_results * 2)  # Get extra results to filter
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            api_manager.increment_usage(key_data['index'])

            if response.status_code == 200:
                data = response.json()

                if 'items' in data:
                    for item in data['items']:
                        url = item.get('link', '')
                        if 'linkedin.com/in/' in url and url not in all_urls:
                            all_urls.add(url)
                            if len(all_urls) >= max_results:
                                break
                else:
                    print(f"    No results found for query: {query}")
            else:
                print(f"    API request failed: {response.status_code} - {response.text}")
                if response.status_code == 429:  # Rate limit
                    print("    Rate limit hit, trying next key...")
                    key_data = api_manager.get_next_available_key()
                    if not key_data:
                        break

        except Exception as e:
            print(f"    Error making API request: {str(e)}")
            continue

        # Get next key for variety
        key_data = api_manager.get_next_available_key()
        if not key_data:
            break

    return list(all_urls)[:max_results]


async def scrape_linkedin_profile(crawler, linkedin_url, expected_title, company_name):
    """
    Scrape LinkedIn profile using Crawl4AI v0.6.0.

    Args:
        crawler: AsyncWebCrawler instance
        linkedin_url (str): LinkedIn profile URL
        expected_title (str): Expected job title
        company_name (str): Expected company name

    Returns:
        dict: Profile data with name, job_title, linkedin_url
    """

    try:
        # Define extraction strategy with updated v0.6.0 format
        extraction_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(provider="ollama/llama2"),  # You may need to adjust this based on your setup
            schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the person"
                    },
                    "current_job_title": {
                        "type": "string",
                        "description": "Current job title/position"
                    },
                    "company": {
                        "type": "string",
                        "description": "Current company name"
                    },
                    "experience": {
                        "type": "string",
                        "description": "Brief work experience summary"
                    }
                },
                "required": ["name", "current_job_title", "company"]
            },
            instruction=f"""
            Extract the person's information from this LinkedIn profile.
            Focus on finding someone who works at "{company_name}" with a title related to "{expected_title}".
            Return the most current/recent job information.
            """
        )

        # Updated crawl method for v0.6.0
        result = await crawler.arun(
            url=linkedin_url,
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
            js_code=[
                "window.scrollTo(0, document.body.scrollHeight);"
            ],
            wait_for="css:.pv-text-details__left-panel",
            page_timeout=20000,  # Updated parameter name
            delay_before_return_html=2.0  # Updated parameter name
        )

        if result.success and result.extracted_content:
            try:
                # Handle both string and list formats for extracted content
                if isinstance(result.extracted_content, list):
                    profile_data = result.extracted_content[0] if result.extracted_content else {}
                else:
                    profile_data = json.loads(result.extracted_content) if isinstance(result.extracted_content,
                                                                                      str) else result.extracted_content

                # Validate and clean the data
                name = clean_text(profile_data.get('name', ''))
                job_title = clean_text(profile_data.get('current_job_title', ''))
                company = clean_text(profile_data.get('company', ''))

                # Basic validation
                if name and job_title and len(name) > 2 and len(job_title) > 2:
                    # Check if this profile matches our search criteria
                    if (company_name.lower() in company.lower() or
                            any(title_word.lower() in job_title.lower()
                                for title_word in expected_title.split())):
                        return {
                            'name': name,
                            'job_title': job_title,
                            'linkedin_url': linkedin_url,
                            'company': company
                        }

            except (json.JSONDecodeError, TypeError):
                # Fallback: try to extract from raw content
                return extract_from_raw_content(result.html, linkedin_url, expected_title, company_name)

        # If structured extraction fails, try raw content extraction
        if result.success and result.html:
            return extract_from_raw_content(result.html, linkedin_url, expected_title, company_name)

    except Exception as e:
        if "blocked" in str(e).lower() or "anti-bot" in str(e).lower():
            raise Exception(f"Anti-bot measures detected: {str(e)}")
        print(f"    Error crawling profile: {str(e)}")

    return None


def extract_from_raw_content(html_content, linkedin_url, expected_title, company_name):
    """
    Fallback extraction from raw HTML content.

    Args:
        html_content (str): Raw HTML content
        linkedin_url (str): LinkedIn profile URL
        expected_title (str): Expected job title
        company_name (str): Expected company name

    Returns:
        dict: Profile data or None
    """

    try:
        # Extract name (usually in title or h1 tags)
        name_patterns = [
            r'<title>([^|]+)\s*\|',
            r'<h1[^>]*>([^<]+)</h1>',
            r'data-generated-suggestion-target[^>]*>([^<]+)</span>'
        ]

        name = ""
        for pattern in name_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                name = clean_text(match.group(1))
                break

        # Extract job title and company
        job_patterns = [
            r'<div[^>]*class="[^"]*pv-text-details[^"]*"[^>]*>([^<]+)</div>',
            r'<span[^>]*class="[^"]*text-body[^"]*"[^>]*>([^<]*(?:' + '|'.join(
                ['CEO', 'CTO', 'CIO', 'VP', 'Director', 'Head', 'Manager', 'Engineer', 'Lead']
            ) + r')[^<]*)</span>',
        ]

        job_title = ""
        for pattern in job_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                potential_title = clean_text(match.group(1))
                if any(word.lower() in potential_title.lower() for word in expected_title.split()):
                    job_title = potential_title
                    break

        # Basic validation
        if name and job_title and len(name) > 2 and len(job_title) > 2:
            return {
                'name': name,
                'job_title': job_title,
                'linkedin_url': linkedin_url,
                'company': company_name  # Use expected company as fallback
            }

    except Exception as e:
        print(f"    Error in fallback extraction: {str(e)}")

    return None


def clean_text(text):
    """Clean and normalize extracted text."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove common prefixes/suffixes
    text = re.sub(r'^[-|•]\s*', '', text)
    text = re.sub(r'\s*[-|•]$', '', text)

    # Remove LinkedIn suffixes
    text = re.sub(r'\s*-\s*LinkedIn$', '', text, re.IGNORECASE)

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
        print(f"Error saving progress to {filename}: {str(e)}")


# Example usage
async def main():
    """Main function to run the scraper."""
    # Example decision maker titles
    decision_maker_titles = [
        "CTO", "CIO", "VP Engineering", "VP Delivery", "Director Engineering",
        "Director Delivery", "Director Software Engineering", "Director Data",
        "Director AI Delivery", "Head Solutions Engineering",
        "Vice President Professional Services", "Director Software Engineering",
        "Director AI Solutions", "Head AI", "Director Product Engineering"
    ]

    # API CSV path
    api_csv_path = "google_api_key_and_cse_id.csv"

    # Run the scraper
    results = await scrape_decision_makers_google_api(
        json_file_path="companies.json",
        decision_maker_titles=decision_maker_titles,
        max_results_per_search=5,
        api_csv_path=api_csv_path
    )

    print(f"Total results: {len(results)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())