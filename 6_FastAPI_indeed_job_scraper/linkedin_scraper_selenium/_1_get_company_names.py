import os
import time
import csv
import random
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# Load environment variables
load_dotenv()
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
    raise ValueError("Missing credentials in .env file!")


def initialize_driver():
    """Initialize Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # Add these to reduce detection and improve speed
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login_to_linkedin(driver):
    """Log in to LinkedIn using credentials from .env."""
    try:
        print("🔐 Starting login process...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)

        # Wait for and fill email field
        email_field = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.clear()
        email_field.send_keys(LINKEDIN_EMAIL)
        time.sleep(0.5)

        # Fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(LINKEDIN_PASSWORD)
        time.sleep(0.5)

        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        print("⏳ Waiting for login to complete...")
        time.sleep(3)

        # Check for multiple possible post-login scenarios
        try:
            # Check for CAPTCHA or security challenge
            if "challenge" in driver.current_url.lower() or "captcha" in driver.current_url.lower():
                print("🔒 Security challenge detected. Please complete manually and press Enter to continue...")
                input()

            # Check for email verification
            if "add-phone" in driver.current_url or "checkpoint" in driver.current_url:
                print("📧 Email verification or additional security step required.")
                print("Please complete the verification manually and press Enter to continue...")
                input()

            # Try multiple selectors for successful login verification
            success_selectors = [
                "//nav[@aria-label='Global navigation']",
                "//nav[contains(@class, 'global-nav')]",
                "//div[@id='global-nav']",
                "//a[@href='/feed/']",
                "//span[text()='Home']"
            ]

            login_successful = False
            for selector in success_selectors:
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    login_successful = True
                    break
                except TimeoutException:
                    continue

            if not login_successful:
                # Final check - if we're on feed page, consider it successful
                if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                    login_successful = True

            if login_successful:
                print("✅ Login successful!")
                return True
            else:
                print(f"❌ Login verification failed. Current URL: {driver.current_url}")
                print("Page title:", driver.title)
                return False

        except Exception as verification_error:
            print(f"⚠️ Login verification error: {verification_error}")
            print(f"Current URL: {driver.current_url}")
            return False

    except Exception as e:
        print(f"❌ Login failed: {e}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Take screenshot for debugging
        try:
            driver.save_screenshot("login_error.png")
            print("📸 Screenshot saved as 'login_error.png'")
        except:
            pass

        return False


def apply_job_filters(driver, title, location, date_posted):
    """Apply filters on LinkedIn Jobs page."""
    try:
        print("🔍 Navigating to jobs page...")
        driver.get("https://www.linkedin.com/jobs")
        time.sleep(3)

        # Check if we're still logged in
        if "authwall" in driver.current_url or "login" in driver.current_url:
            print("❌ Not logged in properly. Please check credentials.")
            return False

        print(f"🎯 Searching for: {title} in {location}")

        # Enter job title with better error handling
        try:
            title_selectors = [
                "//input[contains(@id, 'jobs-search-box-keyword')]",
                "//input[@placeholder='Search jobs']",
                "//input[contains(@class, 'jobs-search-box__text-input')]"
            ]

            title_field = None
            for selector in title_selectors:
                try:
                    title_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not title_field:
                print("❌ Could not find job title search field")
                return False

            title_field.clear()
            time.sleep(0.5)
            title_field.send_keys(title)
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error entering job title: {e}")
            return False

        # Enter location with better error handling
        try:
            location_selectors = [
                "//input[contains(@id, 'jobs-search-box-location')]",
                "//input[@placeholder='City, state, or zip code']",
                "//input[contains(@class, 'jobs-search-box__text-input')][2]"
            ]

            location_field = None
            for selector in location_selectors:
                try:
                    location_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if location_field:
                location_field.clear()
                time.sleep(0.5)
                location_field.send_keys(location)
                time.sleep(1)

            # Press Enter to search
            title_field.send_keys(Keys.RETURN)
            time.sleep(3)

        except Exception as e:
            print(f"⚠️ Warning - location field error: {e}")
            # Continue without location filter

        # Apply date filter with better error handling
        try:
            print(f"📅 Applying date filter: {date_posted}")

            # Look for date filter button
            date_filter_selectors = [
                "//button[contains(@aria-label, 'Date posted filter')]",
                "//button[contains(text(), 'Date posted')]",
                "//button[@id='searchFilter_timePostedRange']"
            ]

            date_filter_button = None
            for selector in date_filter_selectors:
                try:
                    date_filter_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if date_filter_button:
                date_filter_button.click()
                time.sleep(1)

                date_options = {
                    "Past 24 hours": ["//label[@for='date-posted-r86400']", "//span[text()='Past 24 hours']"],
                    "Past week": ["//label[@for='date-posted-r604800']", "//span[text()='Past week']"],
                    "Past month": ["//label[@for='date-posted-r2592000']", "//span[text()='Past month']"]
                }

                if date_posted in date_options:
                    option_clicked = False
                    for option_selector in date_options[date_posted]:
                        try:
                            WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH, option_selector))
                            ).click()
                            option_clicked = True
                            break
                        except TimeoutException:
                            continue

                    if option_clicked:
                        time.sleep(1)
                        # Click Apply button
                        apply_selectors = [
                            "//button[contains(@aria-label, 'Apply current filter')]",
                            "//button[contains(text(), 'Apply')]",
                            "//button[@data-control-name='filter_apply']"
                        ]

                        for apply_selector in apply_selectors:
                            try:
                                WebDriverWait(driver, 2).until(
                                    EC.element_to_be_clickable((By.XPATH, apply_selector))
                                ).click()
                                break
                            except TimeoutException:
                                continue

                        time.sleep(2)

        except Exception as e:
            print(f"⚠️ Warning - date filter error: {e}")
            # Continue without date filter

        print("✅ Filters applied successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to apply filters: {e}")
        try:
            driver.save_screenshot("filter_error.png")
            print("📸 Screenshot saved as 'filter_error.png'")
        except:
            pass
        return False


def get_total_pages(driver):
    """Try to determine total number of pages available."""
    try:
        # Look for pagination info
        pagination_selectors = [
            "//li[contains(@class, 'artdeco-pagination__indicator--number')]",
            "//button[contains(@aria-label, 'Page')]",
            "//span[contains(@class, 'artdeco-pagination__pages-count')]"
        ]

        max_page = 1
        for selector in pagination_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        page_num = int(element.text.strip())
                        max_page = max(max_page, page_num)
                    except:
                        continue
                if max_page > 1:
                    break
            except:
                continue

        return max_page if max_page > 1 else None
    except:
        return None


def navigate_to_next_page(driver, current_page, max_retries=3):
    """Navigate to the next page with enhanced selector logic."""
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting to navigate to page {current_page + 1} (attempt {attempt + 1}/{max_retries})")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Enhanced selectors for pagination buttons
            next_button_selectors = [
                f"//button[@aria-label='Page {current_page + 1}']",
                f"//li[@data-test-pagination-page-btn='{current_page + 1}']//button",
                "//button[contains(@aria-label, 'Next')]",
                "//button[contains(@class, 'artdeco-pagination__button--next')]",
                "//li[contains(@class, 'artdeco-pagination__indicator--next')]//button",
                f"//button[text()='{current_page + 1}']",
                f"//a[text()='{current_page + 1}']"
            ]

            # Try each selector with extended timeout
            next_button = None
            for selector in next_button_selectors:
                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector)))
                    print(f"   ✅ Found next button with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not next_button:
                print(f"   ❌ No next button found on attempt {attempt + 1}")
                # Final attempt: look for "See more jobs" button
                if attempt == max_retries - 1:
                    try:
                        see_more = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        "//button[contains(., 'See more jobs')]")))
                        print("   🔄 Found 'See more jobs' button instead")
                        driver.execute_script("arguments[0].click();", see_more)
                        time.sleep(3)
                        return True
                    except:
                        pass
                continue

            # Click using JavaScript to avoid interception
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(1.5)

            # Verify navigation by checking URL change
            start_param = f"start={current_page * 25}"
            for _ in range(8):
                if start_param in driver.current_url:
                    print(f"   ✅ Successfully navigated to page {current_page + 1}")
                    time.sleep(random.uniform(2, 4))
                    return True
                time.sleep(1)

            print(f"   ⚠️ Page might not have loaded properly")
            return False

        except Exception as e:
            print(f"   ❌ Navigation error: {str(e)[:80]}...")
            time.sleep(3)

    print(f"   ❌ Failed to navigate to page {current_page + 1}")
    return False


def scrape_job_listings(driver, page_num=1):
    """Scrape job listings with enhanced scrolling simulation."""
    jobs = []
    try:
        print(f"📊 Scraping job listings from page {page_num}...")

        # Wait for initial load
        time.sleep(3)

        # Get initial job count
        initial_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
        print(f"📊 Initial job count on page {page_num}: {len(initial_jobs)}")

        # Find the scrollable container
        scroll_target = None
        scroll_selectors = [
            ".jobs-search-results-list",
            ".scaffold-layout__list",
            ".jobs-search-results",
            ".scaffold-layout__list-detail-inner",
            ".artdeco-list"
        ]

        for selector in scroll_selectors:
            try:
                scroll_target = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found scroll target: {selector}")
                break
            except:
                continue

        if not scroll_target:
            print("❌ Could not find scroll target, using body")
            scroll_target = driver.find_element(By.TAG_NAME, "body")

        # Enhanced scrolling simulation
        print(f"\n🖱️ Simulating enhanced scrolling behavior on page {page_num}...")


        # Focus on the scroll area
        actions = ActionChains(driver)
        actions.move_to_element(scroll_target).perform()
        time.sleep(0.5)

        max_scroll_attempts = 15  # Increased for more thorough scraping
        jobs_loaded_count = len(initial_jobs)
        no_new_jobs_streak = 0
        last_height = 0

        for scroll_attempt in range(max_scroll_attempts):
            print(f"   Scroll attempt {scroll_attempt + 1}/{max_scroll_attempts}")

            # Method 1: Scroll to bottom of the container
            driver.execute_script("""
                arguments[0].scrollTop = arguments[0].scrollHeight;
            """, scroll_target)
            time.sleep(2)

            # Method 2: Smooth scroll with JavaScript
            driver.execute_script("""
                arguments[0].scrollBy({
                    top: 2000,
                    left: 0,
                    behavior: 'smooth'
                });
            """, scroll_target)
            time.sleep(1.5)

            # Method 3: Scroll to last visible job card
            current_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
            if current_jobs:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                          current_jobs[-1])
                    time.sleep(1)
                except:
                    pass

            # Check for new jobs
            current_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
            current_count = len(current_jobs)

            if current_count > jobs_loaded_count:
                new_jobs = current_count - jobs_loaded_count
                print(f"   ✅ Loaded {new_jobs} new jobs! Total: {current_count}")
                jobs_loaded_count = current_count
                no_new_jobs_streak = 0
            else:
                no_new_jobs_streak += 1
                print(f"   ⏳ No new jobs (streak: {no_new_jobs_streak})")

                # Try different scrolling methods if stuck
                if no_new_jobs_streak >= 3:
                    print("   🚀 Trying alternative scrolling methods...")

                    # Scroll with page down key
                    actions.send_keys(Keys.PAGE_DOWN).perform()
                    time.sleep(1.5)

                    # Aggressive wheel scroll
                    driver.execute_script("""
                        arguments[0].scrollBy(0, 1500);
                    """, scroll_target)
                    time.sleep(2)

                    # Check if we've reached the end
                    new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_target)
                    if new_height == last_height:
                        print("   🔚 Reached end of scrollable area")
                        break
                    last_height = new_height

                    # Final check for new jobs
                    retry_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
                    if len(retry_jobs) > current_count:
                        jobs_loaded_count = len(retry_jobs)
                        no_new_jobs_streak = 0
                        print(f"   🎯 Alternative scrolling worked! Total: {len(retry_jobs)}")
                    elif no_new_jobs_streak >= 5:
                        print(f"   ⏹️ Stopping - no new jobs after {no_new_jobs_streak} attempts")
                        break

            # Random delay to appear more human-like
            time.sleep(random.uniform(0.5, 1.5))

        # Final count
        final_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
        print(f"\n🎯 Final job count on page {page_num}: {len(final_jobs)} (started with {len(initial_jobs)})")

        # Process all the jobs we found - scrape ALL jobs on the page
        print(f"\n🎯 Processing all {len(final_jobs)} jobs on page {page_num}...")

        for idx, job_card in enumerate(final_jobs):
            try:
                print(f"🔍 Processing job {idx + 1}/{len(final_jobs)} on page {page_num}...")

                # Scroll job into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_card)
                time.sleep(0.5)

                # Extract job URL from card BEFORE clicking
                job_url = "URL not found"
                try:
                    # Multiple possible selectors for the job link
                    url_selectors = [
                        ".job-card-list__title",  # CSS selector
                        "a.job-card-container__link",  # CSS selector
                        "a[data-tracking-control-name='public_jobs_jserp-job-search-card']",  # CSS selector
                        ".//a[contains(@class, 'job-card-list__title')]",  # XPath
                        ".//a[contains(@class, 'job-card-container__link')]",  # XPath
                    ]

                    for selector in url_selectors:
                        try:
                            # Try CSS selector first
                            if selector.startswith(".") or selector.startswith("a"):
                                link_element = job_card.find_element(By.CSS_SELECTOR, selector)
                            else:  # Then try XPath
                                link_element = job_card.find_element(By.XPATH, selector)

                            href = link_element.get_attribute('href')
                            if href:
                                job_url = href
                                # Handle relative URLs
                                if job_url.startswith('/'):
                                    job_url = f"https://www.linkedin.com{job_url}"
                                break
                        except:
                            continue
                except Exception as url_error:
                    print(f"⚠️ URL extraction error: {str(url_error)[:80]}...")

                # Click the job using JavaScript
                driver.execute_script("arguments[0].click();", job_card)
                time.sleep(1.5)

                # Extract job details
                title = ""
                company = ""

                # Get title
                title_selectors = [
                    "//h1[contains(@class, 't-24')]"
                ]

                for selector in title_selectors:
                    try:
                        title_element = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, selector)))
                        title = title_element.text.strip()
                        if title:
                            break
                    except:
                        continue

                # Get company
                company_selectors = [
                    "//div[contains(@class, 'jobs-unified-top-card__company-name')]//a"
                ]

                for selector in company_selectors:
                    try:
                        company_element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.XPATH, selector)))
                        company = company_element.text.strip()
                        if company:
                            break
                    except:
                        continue

                # Get location - NEW CODE
                location = "Location not found"
                location_selectors = [
                    "//span[contains(@class, 'jobs-unified-top-card__bullet')]",
                    "//span[contains(@class, 'jobs-unified-top-card__subtitle-item')]",
                    "//div[contains(@class, 'jobs-unified-top-card__company-name')]/following-sibling::div//li[1]",
                    "//div[contains(@class, 'jobs-unified-top-card__primary-description')]//span",
                    "//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description')]//span",
                    "//span[contains(@class, 'topcard__flavor--bullet')]"
                ]

                for selector in location_selectors:
                    try:
                        location_element = WebDriverWait(driver, 1).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        location = location_element.text.strip()
                        if location:  # Only break if we got actual text
                            break
                    except:
                        continue

                # Clean up location text
                location = location.replace('\n', ' ').replace('  ', ' ').strip()

                if title:
                    job_data = {
                        "title": title,
                        "company": company if company else "Company not found",
                        "location": location,
                        "url": job_url,
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    jobs.append(job_data)
                    print(f"✅ {title} at {company if company else 'Unknown'} in {location}")
                else:
                    print(f"⚠️ Could not get title for job {idx + 1}")

            except Exception as job_error:
                print(f"⚠️ Error processing job {idx + 1} on page {page_num}: {str(job_error)[:80]}...")
                continue

        print(f"\n📋 Page {page_num} Summary: Successfully scraped {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"❌ Scraping failed on page {page_num}: {e}")
        import traceback
        traceback.print_exc()
        return jobs


def scrape_all_pages(driver):
    """Scrape jobs from all available pages."""
    all_jobs = []
    current_page = 1
    max_page_attempts = 2  # Safety limit to prevent infinite loops. Default: 50

    print("\n" + "=" * 60)
    print("🚀 STARTING MULTI-PAGE SCRAPING")
    print("=" * 60)

    # Try to get total pages
    total_pages = get_total_pages(driver)
    if total_pages:
        print(f"📊 Detected approximately {total_pages} pages available")
    else:
        print("📊 Could not determine total pages - will scrape until no more pages")

    while current_page <= max_page_attempts:
        print(f"\n{'=' * 20} PAGE {current_page} {'=' * 20}")

        if total_pages:
            print(f"📄 Processing page {current_page} of ~{total_pages}")
        else:
            print(f"📄 Processing page {current_page}")

        # Scrape current page
        page_jobs = scrape_job_listings(driver, current_page)

        if page_jobs:
            all_jobs.extend(page_jobs)
            print(f"✅ Added {len(page_jobs)} jobs from page {current_page}")
            print(f"📊 Total jobs collected so far: {len(all_jobs)}")
        else:
            print(f"⚠️ No jobs found on page {current_page}")
            if current_page == 1:
                print("❌ No jobs found on first page. Stopping.")
                break

        # Try to navigate to next page
        print(f"\n🔄 Attempting to navigate from page {current_page} to page {current_page + 1}...")

        if navigate_to_next_page(driver, current_page):
            current_page += 1
            print(f"✅ Successfully moved to page {current_page}")
        else:
            print(f"🔚 No more pages available after page {current_page}")
            break

        # Extra safety delay between pages
        extra_delay = random.uniform(1, 3)
        print(f"⏱️ Extra safety delay: {extra_delay:.1f} seconds")
        time.sleep(extra_delay)

    print(f"\n🎉 SCRAPING COMPLETE!")
    print(f"📊 Total pages processed: {current_page}")
    print(f"📊 Total jobs collected: {len(all_jobs)}")

    return all_jobs


def save_to_csv(jobs, JOB_TITLE, filename=None):
    """Save jobs data to CSV file."""
    if not jobs:
        print("❌ No jobs to save")
        return

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = "1_get_company_names"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        filename = f"scraped_data/{folder_name}/linkedin_{JOB_TITLE}_jobs_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Updated fieldnames with location
            fieldnames = ['title', 'company', 'location', 'url', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for job in jobs:
                writer.writerow(job)

        print(f"✅ Data saved to {filename}")
        print(f"📊 Total records: {len(jobs)}")

    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")


def main():
    driver = initialize_driver()
    try:
        # User-defined search parameters
        LOCATION = "United States"
        JOB_TITLE = "Machine Learning"
        DATE_POSTED = "Past week"  # Options: "Past 24 hours", "Past week", "Past month"

        print("🚀 Starting LinkedIn Job Scraper with Pagination...")
        print(f"🎯 Searching for: {JOB_TITLE}")
        print(f"📍 Location: {LOCATION}")
        print(f"📅 Date filter: {DATE_POSTED}")
        print("-" * 50)

        # Execute steps
        if not login_to_linkedin(driver):
            print("❌ Login failed. Exiting...")
            return

        time.sleep(2)

        if not apply_job_filters(driver, JOB_TITLE, LOCATION, DATE_POSTED):
            print("❌ Filter application failed. Exiting...")
            return

        # Scrape all pages
        all_jobs = scrape_all_pages(driver)

        # Save all jobs to single CSV
        save_to_csv(all_jobs, JOB_TITLE)

        # Print final results
        print("\n" + "=" * 60)
        print("📊 FINAL SCRAPING SUMMARY")
        print("=" * 60)

        if all_jobs:
            print(f"✅ Successfully scraped {len(all_jobs)} jobs across multiple pages")

            # Show sample of jobs
            print(f"\n📋 Sample of scraped jobs (showing first 10):")
            for idx, job in enumerate(all_jobs[:10], 1):
                print(f"{idx:2d}. {job['title']}")
                print(f"    🏢 {job['company']}")
                print(f"    📍 {job['location']}")
                print(f"    🔗 {job['url']}")
                print()

            if len(all_jobs) > 10:
                print(f"... and {len(all_jobs) - 10} more jobs")
        else:
            print("❌ No jobs found. This could be due to:")
            print("   • LinkedIn's anti-bot measures")
            print("   • Changed page structure")
            print("   • Network connectivity issues")
            print("   • Invalid search parameters")

        print(f"\n🎯 Total jobs scraped: {len(all_jobs)}")

    except Exception as main_error:
        print(f"❌ Main execution error: {main_error}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()