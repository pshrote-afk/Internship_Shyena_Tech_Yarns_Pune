import asyncio
import csv
import os
import time
import json
import re
import random
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI
import logging

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

        # Get credentials from environment variables
        self.email = os.getenv('INDEED_EMAIL')

        if not self.email:
            raise ValueError("Please set INDEED_EMAIL in your .env file")

        # Job search terms
        self.job_titles = [
            "Generative AI Programmer",
            "Data Scientist",
            "Machine Learning Engineer",
            "Software Developer",
            "Software Engineer"
        ]

        # Region
        self.region = "United States"

    def random_delay(self, min_seconds=3, max_seconds=7):
        """Add random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)

    async def run_scraper(self):
        """Main scraper execution"""
        try:
            logger.info("Starting Indeed job scraping process...")

            # Step 1: Login to Indeed
            await self.login_to_indeed()

            # Step 2: Search and extract jobs for each job title
            all_jobs_data = []

            for job_title in self.job_titles:
                logger.info(f"Searching for: {job_title}")
                jobs_data = await self.search_and_extract_jobs(job_title)

                if jobs_data:
                    parsed_jobs = self.parse_job_data(jobs_data, job_title)
                    all_jobs_data.extend(parsed_jobs)
                    logger.info(f"Found {len(parsed_jobs)} jobs for {job_title}")

                # Random delay between searches
                self.random_delay(5, 10)

            # Step 3: Save data to CSV
            jobs_count = self.save_to_csv(all_jobs_data)

            logger.info("Indeed job scraping completed successfully!")

            return {
                'total_jobs_count': jobs_count,
                'job_titles_searched': len(self.job_titles),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise

    async def login_to_indeed(self):
        """Handle Indeed login with manual password input"""
        logger.info("Starting Indeed login process...")

        login_task = f"""
        I need you to login to Indeed. Here are the steps:

        1. Navigate to https://secure.indeed.com/account/login
        2. Wait for the page to load completely (5 seconds)
        3. Fill in the email field with: {self.email}
        4. Wait for manual password input - DO NOT fill password automatically
        5. Inform the user to manually enter their password
        6. Wait until the user clicks "Sign in" button manually
        7. Handle any additional verification steps (CAPTCHA, 2FA) by waiting for manual intervention
        8. Wait until you reach the Indeed home page or job search page to confirm successful login
        9. Return "LOGIN_SUCCESS" when login is completed

        Take your time and ensure successful login before proceeding.
        If any pop-ups appear, handle them appropriately or wait for manual intervention.
        """

        agent = Agent(
            task=login_task,
            llm=self.llm
        )

        result = await agent.run()
        logger.info(f"Login completed: {result}")

        # Add delay after login
        self.random_delay()
        return result

    async def search_and_extract_jobs(self, job_title):
        """Search for specific job title and extract job listings"""
        logger.info(f"Searching and extracting jobs for: {job_title}")

        search_task = f"""
        Search for "{job_title}" jobs on Indeed and extract job data:

        1. Navigate to the main Indeed search page (https://www.indeed.com/)
        2. Wait for page to load (5 seconds)
        3. In the "What" field, enter: {job_title}
        4. In the "Where" field, enter: United States
        5. Click the "Find jobs" or search button
        6. Wait for search results to load (7 seconds)
        7. Scroll down slowly through the entire page to load all job listings
        8. For each scroll, wait 4-5 seconds before the next scroll
        9. Continue scrolling until you reach the bottom of the page or no more jobs load
        10. Extract the following information for EACH visible job listing:
            - Job Title (exact title as displayed)
            - Company Name
            - Location (city, state)
            - Salary (if displayed, otherwise "Not specified")
            - Job Type (Full-time, Part-time, Contract, etc. - if displayed, otherwise "Not specified")
            - Date Posted (if visible, otherwise "Not specified")

        IMPORTANT: Return ONLY a valid JSON array of objects. Each object must have these exact keys:
        "job_title", "company", "location", "salary", "job_type", "date_posted"

        Example format (return exactly like this):
        [
            {{
                "job_title": "Senior Data Scientist",
                "company": "Google",
                "location": "Mountain View, CA",
                "salary": "$120,000 - $180,000 a year",
                "job_type": "Full-time",
                "date_posted": "Posted 2 days ago"
            }},
            {{
                "job_title": "Machine Learning Engineer",
                "company": "Microsoft",
                "location": "Seattle, WA", 
                "salary": "Not specified",
                "job_type": "Full-time",
                "date_posted": "Posted 1 week ago"
            }}
        ]

        Extract ALL visible job listings on the page.
        Return ONLY the JSON array, no additional text or explanation.
        Take your time to scroll through the entire page and extract all jobs.
        """

        agent = Agent(
            task=search_task,
            llm=self.llm
        )

        jobs_data = await agent.run()
        logger.info(f"Job extraction completed for {job_title}")

        return jobs_data

    def parse_job_data(self, raw_data, job_title_searched):
        """Parse and clean the extracted job data"""
        logger.info(f"Parsing job data for: {job_title_searched}")

        if raw_data is None:
            return []

        # Convert to string if not already
        data_str = str(raw_data)

        # Try multiple JSON extraction methods
        parsed_jobs = []

        # Method 1: Direct JSON parsing if it's already a list
        if isinstance(raw_data, list):
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
                        logger.info(f"Successfully parsed JSON with {len(parsed)} jobs for {job_title_searched}")
                        return parsed
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parse failed for pattern {pattern}: {e}")
                    continue

        # Method 3: Parse structured text line by line
        lines = data_str.split('\n')
        current_job = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for job title patterns
            if 'job_title' in line.lower() or 'title:' in line.lower():
                if current_job:
                    parsed_jobs.append(current_job)
                    current_job = {}
                current_job['job_title'] = line.split(':', 1)[-1].strip().strip('"')
                current_job['searched_for'] = job_title_searched
            elif 'company' in line.lower():
                current_job['company'] = line.split(':', 1)[-1].strip().strip('"')
            elif 'location' in line.lower():
                current_job['location'] = line.split(':', 1)[-1].strip().strip('"')
            elif 'salary' in line.lower():
                current_job['salary'] = line.split(':', 1)[-1].strip().strip('"')
            elif 'job_type' in line.lower() or 'type' in line.lower():
                current_job['job_type'] = line.split(':', 1)[-1].strip().strip('"')
            elif 'date' in line.lower() or 'posted' in line.lower():
                current_job['date_posted'] = line.split(':', 1)[-1].strip().strip('"')

        # Don't forget the last job
        if current_job:
            parsed_jobs.append(current_job)

        # Ensure all jobs have required fields
        for job in parsed_jobs:
            job.setdefault('job_title', 'Not specified')
            job.setdefault('company', 'Not specified')
            job.setdefault('location', 'Not specified')
            job.setdefault('salary', 'Not specified')
            job.setdefault('job_type', 'Not specified')
            job.setdefault('date_posted', 'Not specified')
            job.setdefault('searched_for', job_title_searched)

        logger.info(f"Parsed {len(parsed_jobs)} jobs for {job_title_searched}")
        return parsed_jobs

    def save_to_csv(self, all_jobs_data):
        """Save extracted job data to CSV file"""

        logger.info(f"Saving {len(all_jobs_data)} jobs to CSV")

        # Create filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        jobs_file = f"indeed_jobs_{timestamp}.csv"

        with open(jobs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'Job Title',
                'Company',
                'Location',
                'Salary',
                'Job Type',
                'Date Posted',
                'Searched For'
            ])

            for job in all_jobs_data:
                if isinstance(job, dict):
                    writer.writerow([
                        job.get('job_title', 'Not specified'),
                        job.get('company', 'Not specified'),
                        job.get('location', 'Not specified'),
                        job.get('salary', 'Not specified'),
                        job.get('job_type', 'Not specified'),
                        job.get('date_posted', 'Not specified'),
                        job.get('searched_for', 'Not specified')
                    ])

        logger.info(f"Jobs saved to {jobs_file}")

        # Print detailed summary
        jobs_count = len(all_jobs_data)

        print(f"\n=== INDEED SCRAPING SUMMARY ===")
        print(f"Total jobs extracted: {jobs_count}")
        print(f"Job titles searched: {', '.join(self.job_titles)}")
        print(f"File saved: {jobs_file}")

        # Print sample data if available
        if all_jobs_data:
            print(f"\nSample job listing:")
            sample_job = all_jobs_data[0]
            for key, value in sample_job.items():
                print(f"  {key}: {value}")

        # Print summary by job title
        job_counts = {}
        for job in all_jobs_data:
            searched_for = job.get('searched_for', 'Unknown')
            job_counts[searched_for] = job_counts.get(searched_for, 0) + 1

        print(f"\nJobs found by search term:")
        for job_title, count in job_counts.items():
            print(f"  {job_title}: {count} jobs")

        return jobs_count


async def main():
    """Main execution function with proper cleanup"""
    scraper = None
    try:
        scraper = IndeedScraper()
        result = await scraper.run_scraper()

        print(f"\n🎉 Indeed job scraping completed successfully!")
        print(f"📊 Results: {result}")

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n📝 Please create a .env file with:")
        print("INDEED_EMAIL=your_email@example.com")
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
    print("=== Indeed Autonomous Job Scraper ===")
    print("🤖 This tool will:")
    print("1. Login to Indeed (manual password entry required)")
    print("2. Search for the following job titles:")
    for job_title in ["Generative AI Programmer", "Data Scientist", "Machine Learning Engineer", "Software Developer",
                      "Software Engineer"]:
        print(f"   - {job_title}")
    print("3. Extract job listings from all of USA")
    print("4. Save data to timestamped CSV file")
    print("\n📋 Make sure your .env file contains:")
    print("- INDEED_EMAIL=your_email@example.com")
    print("- OPENAI_API_KEY=your_openai_api_key")
    print("\n⚠️  Note: You will need to manually enter your Indeed password during login")
    print("\n⏳ Starting in 5 seconds...")

    time.sleep(5)

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