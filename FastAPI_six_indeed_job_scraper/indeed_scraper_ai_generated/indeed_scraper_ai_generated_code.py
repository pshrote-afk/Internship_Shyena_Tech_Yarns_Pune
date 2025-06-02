import asyncio
import csv
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Indeed Job Scraper", version="1.0.0")

class JobSearchRequest(BaseModel):
    job_titles: List[str] = [
        "Generative AI Programmer",
        "Data Scientist", 
        "Machine Learning Engineer",
        "Software Developer",
        "Software Engineer"
    ]
    location: str = ""  # City, State or zip code
    base_search_term: str = "Generative AI"

class JobListing(BaseModel):
    company_name: str
    job_title: str
    company_website: Optional[str] = None
    job_url: Optional[str] = None

class IndeedScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Remove for debugging
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def navigate_to_indeed(self):
        """Navigate to Indeed homepage"""
        try:
            self.driver.get("https://www.indeed.com")
            logger.info("Navigated to Indeed homepage")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error navigating to Indeed: {str(e)}")
            raise
            
    def set_date_filter(self):
        """Set date filter to last 14 days"""
        try:
            # Look for date posted dropdown
            date_dropdown = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Date posted')]"))
            )
            date_dropdown.click()
            time.sleep(1)
            
            # Select "Last 14 days" option
            last_14_days = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Last 14 days')]"))
            )
            last_14_days.click()
            logger.info("Set date filter to last 14 days")
            time.sleep(2)
            
        except TimeoutException:
            logger.warning("Could not find date filter dropdown, continuing without it")
        except Exception as e:
            logger.error(f"Error setting date filter: {str(e)}")
            
    def search_jobs(self, search_term: str, location: str = ""):
        """Search for jobs with given terms and location"""
        try:
            # Find and fill job search box
            job_search_box = self.wait.until(
                EC.presence_of_element_located((By.ID, "text-input-what"))
            )
            job_search_box.clear()
            job_search_box.send_keys(search_term)

            time.sleep(4)		

            # Find and fill location box if provided
            if location:
                location_box = self.driver.find_element(By.ID, "text-input-where")
                location_box.clear()
                location_box.send_keys(location)
            
            time.sleep(4)

            # Click search button
            search_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'yosegi-InlineWhatWhere-primaryButton')]")
            search_button.click()
            
            logger.info(f"Searched for '{search_term}' in '{location if location else 'all locations'}'")
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            raise
            
    def extract_job_listings(self, target_job_titles: List[str]) -> List[JobListing]:
        """Extract job listings that match target job titles"""
        jobs = []
        
        try:
            # Wait for results to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk]"))
            )
            
            # Get all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk]")
            logger.info(f"Found {len(job_cards)} job listings")
            
            for card in job_cards:
                try:
                    # Extract job title
                    job_title_element = card.find_element(By.CSS_SELECTOR, "h2 a span")
                    job_title = job_title_element.get_attribute("title") or job_title_element.text
                    
                    # Check if job title matches any target titles
                    if not self._is_relevant_job(job_title, target_job_titles):
                        continue
                    
                    # Extract company name
                    company_element = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']")
                    company_name = company_element.text
                    
                    # Extract job URL
                    job_link = card.find_element(By.CSS_SELECTOR, "h2 a")
                    job_url = job_link.get_attribute("href")
                    
                    # Try to get company website (this might require clicking into the job)
                    company_website = self._get_company_website(job_url)
                    
                    job = JobListing(
                        company_name=company_name,
                        job_title=job_title,
                        company_website=company_website,
                        job_url=job_url
                    )
                    
                    jobs.append(job)
                    logger.info(f"Extracted: {company_name} - {job_title}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting job from card: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting job listings: {str(e)}")
            
        return jobs
    
    def _is_relevant_job(self, job_title: str, target_titles: List[str]) -> bool:
        """Check if job title matches any of the target job titles"""
        job_title_lower = job_title.lower()
        for target in target_titles:
            target_lower = target.lower()
            # Check for partial matches and key terms
            if (target_lower in job_title_lower or 
                any(word in job_title_lower for word in target_lower.split())):
                return True
        return False
    
    def _get_company_website(self, job_url: str) -> Optional[str]:
        """Attempt to extract company website from job posting"""
        try:
            # Open job in new tab to avoid losing search results
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('');")
            new_window = self.driver.window_handles[-1]
            self.driver.switch_to.window(new_window)
            
            self.driver.get(job_url)
            time.sleep(2)
            
            # Look for company website link
            try:
                website_link = self.driver.find_element(
                    By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'indeed.com'))]"
                )
                website_url = website_link.get_attribute("href")
                
                # Close the tab and return to original
                self.driver.close()
                self.driver.switch_to.window(original_window)
                
                return website_url
                
            except NoSuchElementException:
                # Close the tab and return to original
                self.driver.close()
                self.driver.switch_to.window(original_window)
                return None
                
        except Exception as e:
            logger.warning(f"Error getting company website: {str(e)}")
            # Make sure we return to original window
            try:
                self.driver.close()
                self.driver.switch_to.window(original_window)
            except:
                pass
            return None
    
    def save_to_csv(self, jobs: List[JobListing], filename: str = None):
        """Save job listings to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"indeed_jobs_{timestamp}.csv"
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Company Name', 'Job Title', 'Company Website', 'Job URL']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for job in jobs:
                    writer.writerow({
                        'Company Name': job.company_name,
                        'Job Title': job.job_title,
                        'Company Website': job.company_website or 'N/A',
                        'Job URL': job.job_url or 'N/A'
                    })
                    
            logger.info(f"Saved {len(jobs)} jobs to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            raise
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

# FastAPI endpoints
@app.post("/scrape-jobs")
async def scrape_jobs(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """Main endpoint to scrape Indeed jobs"""
    
    scraper = IndeedScraper()
    
    try:
        # Setup and navigate
        scraper.setup_driver()
        scraper.navigate_to_indeed()
        
        # Set date filter
        scraper.set_date_filter()
        
        # Search for jobs
        scraper.search_jobs(request.base_search_term, request.location)
        
        # Extract relevant job listings
        jobs = scraper.extract_job_listings(request.job_titles)
        
        # Save to CSV
        filename = scraper.save_to_csv(jobs)
        
        return {
            "status": "success",
            "jobs_found": len(jobs),
            "csv_file": filename,
            "jobs": [job.dict() for job in jobs]
        }
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        scraper.close()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Indeed Job Scraper API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Usage example
if __name__ == "__main__":
    import uvicorn
    
    # For testing without FastAPI
    async def test_scraper():
        request = JobSearchRequest(
            location="San Francisco, CA"  # Optional: specify location
        )
        
        scraper = IndeedScraper()
        try:
            scraper.setup_driver()
            scraper.navigate_to_indeed()
            scraper.set_date_filter()
            scraper.search_jobs(request.base_search_term, request.location)
            jobs = scraper.extract_job_listings(request.job_titles)
            filename = scraper.save_to_csv(jobs)
            print(f"Scraping completed! Found {len(jobs)} jobs. Saved to {filename}")
            
        finally:
            scraper.close()
    
    # Uncomment to test directly
    # asyncio.run(test_scraper())
    
    # Run FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)