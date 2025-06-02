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



    async def run_scraper(self):
        """Main scraper execution"""
        try:
            logger.info("Starting Indeed scraping process...")

            # Navigate to Indeed USA
            await self.navigate_to_indeed()

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

    async def navigate_to_indeed(self):
        """Navigate to Indeed USA homepage"""
        logger.info("Navigating to Indeed USA with Cloudflare bypass...")

        navigation_task = """
        Navigate to Indeed USA and and handle Cloudflare protection:

        1. Go to https://www.indeed.com
        2. Wait 10 seconds for any Cloudflare challenge to appear
        3. If you see a Cloudflare verification checkbox:
           - Wait for it to complete automatically (up to 30 seconds)
           - If manual verification is needed, wait for human intervention
        4. If redirected to a Cloudflare error page, try refreshing once
        5. Once on the main Indeed page, wait another 5 seconds
        6. Look for the job search interface (What/Where fields)
        7. Return "NAVIGATION_SUCCESS" only when you can see the search fields

        Take your time and wait for all protections to clear.
        """

        agent = Agent(
            task=navigation_task,
            llm=self.llm
        )

        result = await agent.run()
        await asyncio.sleep(5)
        logger.info(f"Navigation completed: {result}")
        return result

    async def search_and_extract_jobs(self, search_term):
        """Search for specific job term and extract job data"""
        logger.info(f"Searching and extracting jobs for: {search_term}")

        await asyncio.sleep(random.uniform(3, 7))

        search_task = f"""
        Search for "{search_term}" jobs on Indeed and extract job data:

        1. Wait 3 seconds before starting
        2. Clear the "What" field completely and wait 1 second
        3. Type "{search_term}" in the "What" field at slow speed
        4. Wait 2 seconds after typing
        5. Leave "Where" field blank (remove any default location)
        6. Look for "Date Posted" filter and select "Last 7 days"
        7. Wait 3 seconds before clicking Search
        8. Click Search and wait 10 seconds for results to load
        9. If you see any Cloudflare challenges, wait for them to resolve
        10. Scroll down slowly 3-4 times with 3-second pauses between scrolls
        
        If you encounter Cloudflare protection:
        - If manual verification needed, pause and wait
        - Try refreshing the page once if stuck


        For each job listing visible on the page, extract the following information:
        - Job Title (exact title as displayed)
        - Company Name
        - Location (city, state)
        - Salary (if displayed, otherwise "Not specified")
        - Job Type (Full-time, Part-time, Contract, etc. - if displayed)
        - Date Posted (if visible)

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
#
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
        jobs_file = "indeed_jobs_usa.csv"
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

        print(f"\n=== INDEED SCRAPING SUMMARY ===")
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
            await asyncio.sleep(0.1)  # Give time for cleanup
        except:
            pass


def run_scraper():
    """Entry point with proper asyncio handling for Windows"""
    print("=== Indeed Job Scraper (USA) ===")
    print("🤖 This tool will:")
    print("1. Navigate to Indeed.com (USA)")
    print("2. Search for multiple job titles:")
    for term in ["Generative AI", "Generative AI Programmer", "Data Scientist", "Machine Learning Engineer",
                 "Software Developer", "Software Engineer"]:
        print(f"   - {term}")
    print("3. Filter results to 'Last 7 days'")
    print("4. Extract job details and save to CSV")
    print("\n📋 Make sure your .env file contains:")
    print("- OPENAI_API_KEY=your_openai_api_key")
    print("\n⏳ Starting in 3 seconds...")

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