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
        time.sleep(2)  # Reduced from 3

        # Wait for and fill email field
        email_field = WebDriverWait(driver, 8).until(  # Reduced from 10
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.clear()
        email_field.send_keys(LINKEDIN_EMAIL)
        time.sleep(0.5)  # Reduced from 1

        # Fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(LINKEDIN_PASSWORD)
        time.sleep(0.5)  # Reduced from 1

        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        print("⏳ Waiting for login to complete...")
        time.sleep(3)  # Reduced from 5

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
                    WebDriverWait(driver, 3).until(  # Reduced from 5
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
        time.sleep(3)  # Reduced from 5

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
                    title_field = WebDriverWait(driver, 3).until(  # Reduced from 5
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not title_field:
                print("❌ Could not find job title search field")
                return False

            title_field.clear()
            time.sleep(0.5)  # Reduced from 1
            title_field.send_keys(title)
            time.sleep(1)  # Reduced from 2

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
                    location_field = WebDriverWait(driver, 3).until(  # Reduced from 5
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if location_field:
                location_field.clear()
                time.sleep(0.5)  # Reduced from 1
                location_field.send_keys(location)
                time.sleep(1)  # Reduced from 2

            # Press Enter to search
            title_field.send_keys(Keys.RETURN)
            time.sleep(3)  # Reduced from 5

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
                    date_filter_button = WebDriverWait(driver, 3).until(  # Reduced from 5
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if date_filter_button:
                date_filter_button.click()
                time.sleep(1)  # Reduced from 2

                date_options = {
                    "Past 24 hours": ["//label[@for='date-posted-r86400']", "//span[text()='Past 24 hours']"],
                    "Past week": ["//label[@for='date-posted-r604800']", "//span[text()='Past week']"],
                    "Past month": ["//label[@for='date-posted-r2592000']", "//span[text()='Past month']"]
                }

                if date_posted in date_options:
                    option_clicked = False
                    for option_selector in date_options[date_posted]:
                        try:
                            WebDriverWait(driver, 2).until(  # Reduced from 3
                                EC.element_to_be_clickable((By.XPATH, option_selector))
                            ).click()
                            option_clicked = True
                            break
                        except TimeoutException:
                            continue

                    if option_clicked:
                        time.sleep(1)  # Reduced from 2
                        # Click Apply button
                        apply_selectors = [
                            "//button[contains(@aria-label, 'Apply current filter')]",
                            "//button[contains(text(), 'Apply')]",
                            "//button[@data-control-name='filter_apply']"
                        ]

                        for apply_selector in apply_selectors:
                            try:
                                WebDriverWait(driver, 2).until(  # Reduced from 3
                                    EC.element_to_be_clickable((By.XPATH, apply_selector))
                                ).click()
                                break
                            except TimeoutException:
                                continue

                        time.sleep(2)  # Reduced from 3

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


def scrape_job_listings(driver):
    """Scrape job listings with enhanced scrolling simulation."""
    jobs = []
    try:
        print("📊 Scraping job listings...")

        # Wait for initial load
        time.sleep(3)

        # Get initial job count
        initial_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
        print(f"📊 Initial job count: {len(initial_jobs)}")

        # Find the scrollable container
        scroll_target = None
        scroll_selectors = [
            ".jobs-search-results-list",  # Primary container
            ".scaffold-layout__list",  # Alternative container
            ".jobs-search-results",  # Another possible container
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
        print("\n🖱️ Simulating enhanced scrolling behavior...")

        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.keys import Keys

        # Focus on the scroll area
        actions = ActionChains(driver)
        actions.move_to_element(scroll_target).perform()
        time.sleep(0.5)

        max_scroll_attempts = 10
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
        print(f"\n🎯 Final job count: {len(final_jobs)} (started with {len(initial_jobs)})")

        # If we still have few jobs, try loading more by scrolling to very bottom
        if len(final_jobs) < 15:
            print("\n🔄 Final attempt: Scroll to very bottom with longer waits...")
            for _ in range(3):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_target)
                time.sleep(3)
                loading_indicators = driver.find_elements(By.XPATH,
                                                          "//*[contains(@class, 'loading') or contains(@class, 'spinner')]")
                if loading_indicators:
                    time.sleep(5)

            final_jobs = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container')]")
            print(f"   Final count after bottom scroll: {len(final_jobs)}")

        # Process all the jobs we found
        print(f"\n🎯 Processing {min(30, len(final_jobs))} jobs...")

        for idx, job_card in enumerate(final_jobs[:30]):
            try:
                print(f"🔍 Processing job {idx + 1}/{min(30, len(final_jobs))}...")

                # Scroll job into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_card)
                time.sleep(0.5)

                # Click the job using JavaScript as it's more reliable
                driver.execute_script("arguments[0].click();", job_card)
                time.sleep(1.5)

                # Extract job details with improved selectors
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

                if title:
                    jobs.append({
                        "title": title,
                        "company": company if company else "Company not found",
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"✅ {title} at {company if company else 'Unknown'}")
                else:
                    print(f"⚠️ Could not get title for job {idx + 1}")

            except Exception as job_error:
                print(f"⚠️ Error processing job {idx + 1}: {str(job_error)[:80]}...")
                continue

        return jobs

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return jobs


def save_to_csv(jobs, filename=None):
    """Save jobs data to CSV file."""
    if not jobs:
        print("❌ No jobs to save")
        return

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_jobs_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'company', 'scraped_at']
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
        JOB_TITLE = "Human REsources"
        DATE_POSTED = "Past week"  # Options: "Past 24 hours", "Past week", "Past month"

        print("🚀 Starting LinkedIn Job Scraper...")
        print(f"🎯 Searching for: {JOB_TITLE}")
        print(f"📍 Location: {LOCATION}")
        print(f"📅 Date filter: {DATE_POSTED}")
        print("-" * 50)

        # Execute steps
        if not login_to_linkedin(driver):
            print("❌ Login failed. Exiting...")
            return

        time.sleep(2)  # Reduced from 3

        if not apply_job_filters(driver, JOB_TITLE, LOCATION, DATE_POSTED):
            print("❌ Filter application failed. Exiting...")
            return

        jobs = scrape_job_listings(driver)

        # Save to CSV
        save_to_csv(jobs)

        # Print results
        print("\n" + "=" * 60)
        print("📊 SCRAPED JOBS SUMMARY")
        print("=" * 60)

        if jobs:
            for idx, job in enumerate(jobs, 1):
                print(f"{idx:2d}. {job['title']}")
                print(f"    🏢 {job['company']}")
                print()
        else:
            print("❌ No jobs found. This could be due to:")
            print("   • LinkedIn's anti-bot measures")
            print("   • Changed page structure")
            print("   • Network connectivity issues")
            print("   • Invalid search parameters")

        print(f"Total jobs found: {len(jobs)}")

    except Exception as main_error:
        print(f"❌ Main execution error: {main_error}")
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()