import asyncio
import csv
import os
import time
import json
import re
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI
import logging

import random
from browser_use import Agent, Browser
from playwright.async_api import async_playwright

# Enhanced imports for stealth browsing
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Try to import webdriver_manager for fallback
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    logger.warning("webdriver_manager not available - fallback method may not work")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndeedScraper:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=4000
        )

        # Job search terms to iterate through
        self.job_search_terms = [
            "Generative AI",
            "Generative AI Programmer",
            "Data Scientist",
            "Machine Learning Engineer",
            "Software Developer",
            "Software Engineer"
        ]

        # Initialize storage for all job data
        self.all_jobs_data = []
        
        # Initialize undetected Chrome driver
        self.driver = None

    def setup_undetected_chrome(self):
        """Setup undetected Chrome driver with stealth configuration"""
        logger.info("Setting up undetected Chrome driver...")
        
        try:
            # Method 1: Try with undetected-chromedriver (latest approach)
            try:
                # Chrome options for stealth
                chrome_options = uc.ChromeOptions()
                
                # Basic stealth options
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Additional stealth options
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-plugins-discovery')
                chrome_options.add_argument('--disable-default-apps')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--remote-debugging-port=9222')
                
                # User agent rotation
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
                chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')

                # Try different initialization methods
                try:
                    # Method 1a: Without version specification
                    self.driver = uc.Chrome(options=chrome_options)
                except Exception as e1:
                    logger.warning(f"Method 1a failed: {e1}")
                    try:
                        # Method 1b: With explicit driver path
                        self.driver = uc.Chrome(options=chrome_options, driver_executable_path=None)
                    except Exception as e2:
                        logger.warning(f"Method 1b failed: {e2}")
                        # Method 1c: With use_subprocess=False
                        self.driver = uc.Chrome(options=chrome_options, use_subprocess=False)
                
                logger.info("Undetected Chrome initialized successfully")
                
            except Exception as uc_error:
                logger.warning(f"Undetected Chrome failed: {uc_error}")
                raise uc_error
            
            # Apply selenium-stealth if driver was created successfully
            if self.driver:
                try:
                    stealth(self.driver,
                            languages=["en-US", "en"],
                            vendor="Google Inc.",
                            platform="Win32",
                            webgl_vendor="Intel Inc.",
                            renderer="Intel Iris OpenGL Engine",
                            fix_hairline=True,
                            )
                    logger.info("Selenium-stealth applied successfully")
                except Exception as stealth_error:
                    logger.warning(f"Selenium-stealth failed: {stealth_error}")
                    # Continue without stealth if it fails
                
                # Additional JavaScript execution to hide automation indicators
                try:
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.driver.execute_script("delete navigator.__proto__.webdriver")
                except Exception as js_error:
                    logger.warning(f"JavaScript stealth injection failed: {js_error}")
                
                logger.info("Undetected Chrome driver setup completed successfully")
                return True
            
        except Exception as e:
            logger.error(f"All undetected Chrome methods failed: {e}")
            
            # Fallback Method 2: Use regular Selenium with stealth
            logger.info("Attempting fallback to regular Selenium with stealth...")
            try:
                return self.setup_regular_selenium_stealth()
            except Exception as fallback_error:
                logger.error(f"Fallback method also failed: {fallback_error}")
                return False
    
    def setup_regular_selenium_stealth(self):
        """Fallback method using regular Selenium with stealth"""
        logger.info("Setting up regular Selenium with stealth...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            # Chrome options for stealth
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins-discovery')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-gpu')
            
            # User agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Setup service with different methods
            try:
                if WEBDRIVER_MANAGER_AVAILABLE:
                    # Method 1: Use webdriver_manager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    # Method 2: Use system Chrome driver
                    self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as service_error:
                logger.warning(f"Service setup failed: {service_error}")
                # Method 3: Try without explicit service
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Apply selenium-stealth
            stealth(self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            
            # Additional stealth JavaScript
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Regular Selenium with stealth setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Regular Selenium stealth setup failed: {e}")
            return False

    def cleanup_driver(self):
        """Clean up the Chrome driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")

    async def run_scraper(self):
        """Main scraper execution with enhanced stealth"""
        try:
            logger.info("Starting Indeed scraping process with stealth mode...")
            
            # Setup undetected Chrome driver
            if not self.setup_undetected_chrome():
                raise Exception("Failed to setup stealth browser")

            # Navigate to Indeed USA with stealth
            await self.navigate_to_indeed_stealth()

            # Add extra wait after initial navigation
            await asyncio.sleep(5)

            # Iterate through each job search term with longer delays
            for i, search_term in enumerate(self.job_search_terms):
                logger.info(f"Searching for: {search_term} ({i + 1}/{len(self.job_search_terms)})")

                try:
                    jobs_data = await self.search_and_extract_jobs(search_term)
                    self.all_jobs_data.extend(jobs_data)

                    # Longer delay between searches (5-10 seconds)
                    delay = random.uniform(5, 10)
                    logger.info(f"Waiting {delay:.1f} seconds before next search...")
                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.error(f"Failed to scrape {search_term}: {e}")
                    # Continue with next search term
                    await asyncio.sleep(10)
                    continue

            # Save all collected data
            total_jobs = self.save_to_csv(self.all_jobs_data)

            logger.info("Indeed scraping completed successfully!")

            return {
                'total_jobs_scraped': total_jobs,
                'search_terms_used': len(self.job_search_terms),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            # Always cleanup the driver
            self.cleanup_driver()

    async def navigate_to_indeed_stealth(self):
        """Navigate to Indeed USA with enhanced stealth techniques"""
        logger.info("Navigating to Indeed USA with enhanced stealth mode...")

        try:
            # Random delay before navigation
            await asyncio.sleep(random.uniform(2, 5))
            
            # Navigate to Indeed
            self.driver.get("https://www.indeed.com/account/login")
            
            # Wait for page load with random delay
            await asyncio.sleep(random.uniform(5, 8))
            
            # Handle potential Cloudflare or other protections
            await self.handle_protections()

                
            # Look for search elements to confirm page loaded
            try:
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='jobs-search-keywords-input'], input[name='q'], input[id='text-input-what']"))
                )
                logger.info("Successfully found search box - navigation completed")
            except Exception as e:
                logger.warning(f"Could not find search box: {e}")
                
            # Random mouse movements to appear more human-like
            await self.simulate_human_behavior()
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def handle_protections(self):
        """Handle Cloudflare and other bot protections"""
        logger.info("Checking for bot protections...")
        
        # Wait for potential Cloudflare challenge
        await asyncio.sleep(5)
        
        # Check for common protection indicators
        page_source = self.driver.page_source.lower()
        
        if any(indicator in page_source for indicator in ['cloudflare', 'checking your browser', 'ddos protection']):
            logger.info("Bot protection detected, waiting for resolution...")
            
            # Wait longer for automatic resolution
            for i in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                if "indeed" in self.driver.title.lower():
                    logger.info("Protection bypassed successfully")
                    break
            else:
                logger.warning("Protection may not have been fully bypassed")

    async def simulate_human_behavior(self):
        """Simulate human-like behavior with random actions"""
        try:
            # Random scroll
            scroll_height = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            await asyncio.sleep(random.uniform(1, 3))
            
            # Scroll back up
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_height//2});")
            await asyncio.sleep(random.uniform(0.5, 2))
            
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {e}")

    async def search_and_extract_jobs(self, search_term):
        """Search for specific job term and extract job data with stealth"""
        logger.info(f"Searching and extracting jobs for: {search_term}")

        await asyncio.sleep(random.uniform(3, 7))

        # Enhanced task with stealth considerations
        search_task = f"""
        Search for "{search_term}" jobs on Indeed using the current browser session and extract job data:

        IMPORTANT: The browser is already open and on Indeed.com. Work with the existing session.

        1. Wait 3 seconds before starting
        2. Locate the job search input field (it might be labeled as "What", "Job title", or have data-testid)
        3. Clear the "What" field completely and wait 1 second
        4. Type "{search_term}" slowly in the "What" field (simulate human typing speed)
        5. Wait 2 seconds after typing
        6. Leave "Where" field blank or remove any default location
        7. Look for "Date Posted" filter and try to select "Last 7 days" if available
        8. Wait 3 seconds before clicking Search
        9. Click Search and wait 10 seconds for results to load
        10. Handle any additional protections or popups that appear
        11. Scroll down slowly 3-4 times with 3-second pauses between scrolls
        
        STEALTH CONSIDERATIONS:
        - Move mouse naturally between actions
        - Add random small delays between keystrokes
        - If any suspicious activity is detected, pause for 10+ seconds
        - Handle any "Are you a robot?" challenges gracefully

    

        IMPORTANT: Return ONLY a valid JSON array of objects. Each object must have these exact keys:
        "job_title", "company", "location", "salary", "job_type", "date_posted", "search_term"

        Example format:
        [
            {{
                "job_title": "Senior Data Scientist",
                "company": "Google LLC",
                "location": "Mountain View, CA",
                "salary": "$120,000 - $180,000 a year",
                "job_type": "Full-time",
                "date_posted": "2 days ago",
                "search_term": "{search_term}"
            }},
            {{
                "job_title": "Machine Learning Engineer",
                "company": "Microsoft",
                "location": "Seattle, WA", 
                "salary": "Not specified",
                "job_type": "Full-time",
                "date_posted": "1 day ago",
                "search_term": "{search_term}"
            }}
        ]

        Extract at least 20-50 job listings if available.
        Return ONLY the JSON array, no additional text or explanation.
        """

        # Create agent with the existing browser session
        agent = Agent(
            task=search_task,
            llm=self.llm
        )

        jobs_data = await agent.run()
        await asyncio.sleep(5)

        logger.info(f"Job extraction completed for {search_term}")

        # Parse the extracted data
        parsed_jobs = self.parse_extracted_data(jobs_data, search_term)
        logger.info(f"Parsed {len(parsed_jobs)} jobs for {search_term}")

        return parsed_jobs

    def parse_extracted_data(self, raw_data, search_term):
        """Parse and clean the extracted job data"""
        logger.info(f"Parsing extracted data for {search_term}, type: {type(raw_data)}")

        if raw_data is None:
            return []

        # Convert to string if not already
        data_str = str(raw_data)

        # Try multiple JSON extraction methods
        parsed_data = []

        # Method 1: Direct JSON parsing if it's already a list
        if isinstance(raw_data, list):
            # Ensure each item has the search_term field
            for item in raw_data:
                if isinstance(item, dict):
                    item['search_term'] = search_term
            return raw_data

        # Method 2: Look for JSON arrays in the string
        json_patterns = [
            r'\[[\s\S]*?\]',  # Match [ ... ] with any content including newlines
            r'\[\s*\{[\s\S]*?\}\s*\]',  # Match [{ ... }] pattern specifically
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, data_str, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the JSON string
                    cleaned_match = match.strip()

                    # Fix common JSON issues
                    cleaned_match = re.sub(r',\s*}', '}', cleaned_match)  # Remove trailing commas
                    cleaned_match = re.sub(r',\s*]', ']', cleaned_match)  # Remove trailing commas in arrays

                    parsed = json.loads(cleaned_match)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Add search_term to each job if not present
                        for job in parsed:
                            if isinstance(job, dict) and 'search_term' not in job:
                                job['search_term'] = search_term
                        logger.info(f"Successfully parsed JSON with {len(parsed)} items for {search_term}")
                        return parsed
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parse failed for pattern {pattern}: {e}")
                    continue

        # Method 3: Create mock data if parsing fails (for testing/fallback)
        logger.warning(f"Could not parse job data for {search_term}, returning empty list")
        return []

    def save_to_csv(self, all_jobs_data):
        """Save all extracted job data to CSV file"""

        logger.info(f"Saving {len(all_jobs_data)} total jobs to CSV")

        # Save all jobs to a single CSV file
        jobs_file = "indeed_jobs_usa_stealth.csv"
        with open(jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Job Title', 'Company', 'Location', 'Salary',
                'Job Type', 'Date Posted', 'Search Term'
            ])

            for job in all_jobs_data:
                if isinstance(job, dict):
                    writer.writerow([
                        job.get('job_title', 'N/A'),
                        job.get('company', 'N/A'),
                        job.get('location', 'N/A'),
                        job.get('salary', 'Not specified'),
                        job.get('job_type', 'N/A'),
                        job.get('date_posted', 'N/A'),
                        job.get('search_term', 'N/A')
                    ])

        logger.info(f"Jobs saved to {jobs_file}")

        # Print detailed summary
        total_jobs = len(all_jobs_data)

        print(f"\n=== INDEED SCRAPING SUMMARY (STEALTH MODE) ===")
        print(f"Total jobs scraped: {total_jobs}")
        print(f"Search terms used: {', '.join(self.job_search_terms)}")
        print(f"File saved: {jobs_file}")

        # Print summary by search term
        search_term_counts = {}
        for job in all_jobs_data:
            if isinstance(job, dict):
                term = job.get('search_term', 'Unknown')
                search_term_counts[term] = search_term_counts.get(term, 0) + 1

        print(f"\n=== JOBS BY SEARCH TERM ===")
        for term, count in search_term_counts.items():
            print(f"{term}: {count} jobs")

        # Print sample data if available
        if all_jobs_data:
            print(f"\nSample job: {all_jobs_data[0]}")

        return total_jobs


async def main():
    """Main execution function with proper cleanup"""
    scraper = None
    try:
        scraper = IndeedScraper()
        result = await scraper.run_scraper()

        print(f"\n🎉 Indeed scraping completed successfully!")
        print(f"📊 Results: {result}")

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n📝 Please create a .env file with:")
        print("OPENAI_API_KEY=your_openai_api_key")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Full error details:")

    finally:
        # Cleanup to avoid asyncio warnings
        try:
            if scraper:
                scraper.cleanup_driver()
            await asyncio.sleep(0.1)  # Give time for cleanup
        except:
            pass


def run_scraper():
    """Entry point with proper asyncio handling for Windows"""
    print("=== Indeed Job Scraper (USA) - STEALTH MODE ===")
    print("🤖 This enhanced tool will:")
    print("1. Use undetected Chrome driver to bypass bot detection")
    print("2. Apply selenium-stealth for additional protection")
    print("3. Navigate to Indeed.com (USA) with human-like behavior")
    print("4. Search for multiple job titles:")
    for term in ["Generative AI", "Generative AI Programmer", "Data Scientist", "Machine Learning Engineer",
                 "Software Developer", "Software Engineer"]:
        print(f"   - {term}")
    print("5. Filter results to 'Last 7 days'")
    print("6. Extract job details and save to CSV")
    print("\n📋 Requirements:")
    print("- OPENAI_API_KEY in .env file")
    print("- Chrome browser installed")
    print("- undetected-chromedriver: pip install undetected-chromedriver")
    print("- selenium-stealth: pip install selenium-stealth")
    print("\n⏳ Starting stealth mode in 3 seconds...")

    time.sleep(3)

    # Set event loop policy for Windows to avoid warnings
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    run_scraper()