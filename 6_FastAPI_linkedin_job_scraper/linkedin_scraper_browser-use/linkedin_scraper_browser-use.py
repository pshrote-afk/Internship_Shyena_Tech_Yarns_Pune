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

load_dotenv()

# Configure logging to reduce verbose output
logging.basicConfig(level=logging.WARNING)  # Changed from INFO to WARNING
logger = logging.getLogger(__name__)

# Disable logging from third-party libraries that are too verbose
logging.getLogger('browser_use').setLevel(logging.WARNING)
logging.getLogger('langchain').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('playwright').setLevel(logging.WARNING)

# Disable specific debug loggers
for name in ['asyncio', 'websockets', 'chromium', 'browser']:
    logging.getLogger(name).setLevel(logging.ERROR)


class LinkedInJobScraper:
    def __init__(self):
        # Initialize with minimal console output
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=4000,
            verbose=False  # Disable LangChain verbose output
        )
        self.job_titles = ["Generative AI Programmer", "Data Scientist", "Machine Learning Engineer",
                           "Software Developer"]
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')

        if not self.email or not self.password:
            raise ValueError("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")

        self.scraped_jobs = []

    async def run_scraper(self):
        try:
            print("🚀 Starting LinkedIn job scraping...")
            await self.login_to_linkedin()

            for title in self.job_titles:
                print(f"🔍 Searching: {title}")
                await self.search_and_scrape_jobs(title)
                await asyncio.sleep(random.uniform(3, 6))

                if random.choice([True, False]):
                    await self.simulate_behavior()

            count = self.save_to_csv()
            print(f"\n✅ Scraped {count} jobs successfully")
            return {'total_jobs': count, 'status': 'success'}

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    async def login_to_linkedin(self):
        print("🔐 Logging into LinkedIn...")
        task = f"Go to linkedin.com/login, enter {self.email} and {self.password}, click Sign in. Return LOGIN_SUCCESS"

        # Create agent with minimal output
        agent = Agent(task=task, llm=self.llm)
        await agent.run()
        print("✓ Login completed")

    async def search_and_scrape_jobs(self, job_title):
        # Step 1: Navigate and search
        navigation_task = f"""
        1. Go to linkedin.com/jobs
        2. Search "{job_title}" in "United States"  
        3. Filter "Past week"
        4. Scroll 3 times to load jobs
        5. Return "NAVIGATION_COMPLETE" when done

        DO NOT extract any data. Just navigate and return "NAVIGATION_COMPLETE".
        """

        print("  📍 Navigating to jobs page...")
        agent = Agent(task=navigation_task, llm=self.llm)
        await agent.run()

        # Step 2: Extract only specific data with minimal context
        extraction_task = f"""
        You are now on the LinkedIn jobs page. Your ONLY task is to:

        1. Look at the job listings currently visible on the page
        2. For each job listing, find the job title and company name text. Click on job title, which will open it in nearby space.
        3. From this new opened space, return ONLY a simple list in this exact format:
           Job Title 1 | Company Name 1
           Job Title 2 | Company Name 2
           Job Title 3 | Company Name 3

        CRITICAL RULES:
        - Do NOT extract page source, HTML, JSON, or any technical data
        - Do NOT return metadata, URLs, or debugging information  
        - Do NOT scroll or navigate further
        - ONLY return the job title and company name pairs as shown above
        - If you cannot find clear job titles, return "NO_JOBS_FOUND"
        """

        print("  📝 Extracting job data...")
        extraction_agent = Agent(task=extraction_task, llm=self.llm)
        result = await extraction_agent.run()

        jobs_data = self.parse_simple_format(result, job_title)
        self.scraped_jobs.extend(jobs_data)
        print(f"  ✓ Found {len(jobs_data)} jobs")

    def parse_simple_format(self, raw_data, searched_title):
        """Parse the simple pipe-separated format"""
        try:
            text = str(raw_data).strip()
            jobs = []

            if "NO_JOBS_FOUND" in text:
                return []

            # Split by lines and process each line
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if '|' in line and len(line) > 5:  # Basic validation
                    try:
                        parts = line.split('|', 1)  # Split only on first |
                        if len(parts) == 2:
                            job_title = parts[0].strip()
                            company_name = parts[1].strip()

                            # Basic validation
                            if (job_title and company_name and
                                    len(job_title) > 2 and len(company_name) > 1 and
                                    job_title.lower() not in ['job title', 'title'] and
                                    company_name.lower() not in ['company', 'company name']):
                                jobs.append({
                                    'searched_title': searched_title,
                                    'job_title': job_title,
                                    'company_name': company_name
                                })
                    except Exception as e:
                        continue  # Skip malformed lines

            # Remove duplicates
            seen = set()
            unique_jobs = []
            for job in jobs:
                key = (job['job_title'].lower(), job['company_name'].lower())
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)

            return unique_jobs[:15]  # Limit to prevent overwhelm

        except Exception as e:
            logger.error(f"Simple format parse error: {e}")
            return []

    def extract_jobs_from_text(self, text, searched_title):
        """Fallback method to extract jobs from plain text"""
        jobs = []
        try:
            # Look for patterns like "Job Title at Company Name"
            patterns = [
                r'([A-Za-z\s]+(?:Engineer|Developer|Scientist|Analyst|Manager|Specialist|Programmer))\s+at\s+([A-Za-z\s&.,-]+)',
                r'"job_title":\s*"([^"]+)",\s*"company_name":\s*"([^"]+)"'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for job_title, company_name in matches:
                    if job_title.strip() and company_name.strip():
                        jobs.append({
                            'searched_title': searched_title,
                            'job_title': job_title.strip(),
                            'company_name': company_name.strip()
                        })

            # Remove duplicates
            seen = set()
            unique_jobs = []
            for job in jobs:
                key = (job['job_title'], job['company_name'])
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)

            return unique_jobs[:10]  # Limit to 10 jobs to avoid overwhelm

        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return []

    async def simulate_behavior(self):
        behaviors = [
            "Click Messaging, wait 3s, return to Jobs page",
            "Click Me dropdown, scroll briefly, return to Jobs page",
            "Scroll down slowly on Jobs page, then scroll back up"
        ]

        task = random.choice(behaviors)
        agent = Agent(task=task, llm=self.llm)
        await agent.run()

    def save_to_csv(self):
        if not self.scraped_jobs:
            return 0

        # Remove duplicates before saving
        seen = set()
        unique_jobs = []
        for job in self.scraped_jobs:
            key = (job['job_title'], job['company_name'])
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        with open("linkedin_jobs.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Searched Title', 'Job Title', 'Company Name'])

            for job in unique_jobs:
                writer.writerow([job['searched_title'], job['job_title'], job['company_name']])

        print(f"Saved {len(unique_jobs)} unique jobs to linkedin_jobs.csv")
        return len(unique_jobs)


async def main():
    try:
        scraper = LinkedInJobScraper()
        await scraper.run_scraper()
    except Exception as e:
        print(f"Error: {e}")


def run_scraper():
    print("=== LinkedIn Job Scraper ===")
    print("Scraping job titles and company names only")
    time.sleep(2)

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == "__main__":
    run_scraper()