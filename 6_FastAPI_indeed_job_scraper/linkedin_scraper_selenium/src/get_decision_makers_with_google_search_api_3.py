import json
import os
import time
import random
import pandas as pd
from datetime import datetime
import requests
from dotenv import load_dotenv
import re
from urllib.parse import quote_plus, urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = "./scraped_data/3_get_decision_makers_google_api"
PROGRESS_FILE = f"{OUTPUT_DIR}/scraping_progress.json"
OUTPUT_FILE = f"{OUTPUT_DIR}/company_name_versus_decision_maker_name.json"
SEARCH_DELAY_MIN = 2
SEARCH_DELAY_MAX = 5
DAILY_LIMIT = 100
WARNING_THRESHOLD = 70

# Hardcoded power positions list
POWER_POSITIONS = [
    "CEO", "Chief Executive Officer", "President", "Chairman", "Founder", "Co-Founder",
    "COO", "Chief Operating Officer", "CFO", "Chief Financial Officer",
    "General Manager", "Managing Director", "Executive Director", "Senior Director",
    "Vice President", "VP", "Senior Vice President", "SVP", "Executive Vice President", "EVP",
    "Chief Technology Officer", "Chief Information Officer", "Chief Data Officer",
    "Chief Strategy Officer", "Chief Product Officer", "Chief Marketing Officer",
    "Chief Revenue Officer", "Chief Sales Officer", "Chief Innovation Officer",
    "Head of", "Global Head", "Regional Head", "Country Head", "Division Head"
]

# Former position keywords to filter out
FORMER_KEYWORDS = ["ex-", "former", "previous", "past", "retired", "formerly", "student", "intern", "freelance"]

def extract_person_name_from_title(title):
    """Extract person name from Google search result title"""
    # Remove LinkedIn suffix
    title = re.sub(r'\s*-\s*LinkedIn$', '', title, re.IGNORECASE)

    # Split by common separators and take first part
    separators = [' - ', ' | ', ' at ', ' — ']
    for sep in separators:
        if sep in title:
            name = title.split(sep)[0].strip()
            if len(name) > 2:
                return name

    # If no separator found, return cleaned title
    return title.strip()


def extract_current_job_title(title, snippet):
    """Extract current job title from title and snippet, avoiding former positions"""
    combined_text = f"{title} {snippet}".lower()

    # Check for former position keywords
    for keyword in FORMER_KEYWORDS:
        if keyword in combined_text:
            return None

    # Look for job title patterns in title first
    title_lower = title.lower()
    for pos in POWER_POSITIONS:
        if pos.lower() in title_lower:
            # Extract the job title portion
            if ' - ' in title:
                parts = title.split(' - ')
                for part in parts[1:]:  # Skip name part
                    if pos.lower() in part.lower():
                        return part.strip()
            elif ' | ' in title:
                parts = title.split(' | ')
                for part in parts[1:]:
                    if pos.lower() in part.lower():
                        return part.strip()

    # Look in snippet if not found in title
    snippet_sentences = snippet.split('.')
    for sentence in snippet_sentences:
        sentence_lower = sentence.lower()
        for pos in POWER_POSITIONS:
            if pos.lower() in sentence_lower:
                return sentence.strip()

    return None


def is_profile_relevant(search_result_item, decision_maker_titles, company_name, already_found_names):
    """
    Check if the search result represents a relevant decision maker profile
    """
    title = search_result_item.get('title', '')
    snippet = search_result_item.get('snippet', '')
    combined_text = f"{title} {snippet}".lower()

    # Check for former position keywords
    for keyword in FORMER_KEYWORDS:
        if keyword in combined_text:
            return False

    # Check exact company name match
    if company_name.lower() not in combined_text:
        return False

    # Extract person name and check if already found
    person_name = extract_person_name_from_title(title)
    if person_name.lower() in [name.lower() for name in already_found_names]:
        return False

    # Check for decision maker titles
    for dm_title in decision_maker_titles:
        if dm_title.lower() in combined_text:
            return True

    # Check for hardcoded power positions
    for power_pos in POWER_POSITIONS:
        if power_pos.lower() in combined_text:
            return True

    return False


async def scrape_decision_makers_google_api(json_file_path, decision_maker_titles, max_results_per_search,
                                            api_csv_path):
    load_dotenv()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    company_size_filter = os.getenv('LINKEDIN_COMPANY_SIZE_FILTER', '[]')
    try:
        size_filter = json.loads(company_size_filter)
    except json.JSONDecodeError:
        print("Error: Invalid LINKEDIN_COMPANY_SIZE_FILTER format in .env file")
        return {}

    print(f"Company size filter: {size_filter}")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            companies_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return {}

    filtered_companies = []
    for size_category in size_filter:
        if size_category in companies_data:
            filtered_companies.extend(companies_data[size_category])

    print(f"Total companies to process: {len(filtered_companies)}")

    progress_data = load_progress(PROGRESS_FILE)
    final_results = load_progress(OUTPUT_FILE)

    api_manager = GoogleAPIManager(api_csv_path, DAILY_LIMIT, WARNING_THRESHOLD)

    try:
        for company_idx, company_name in enumerate(filtered_companies):
            print(f"\nProcessing company {company_idx + 1}/{len(filtered_companies)}: {company_name}")

            if company_name in final_results:
                print(f"Company {company_name} already processed, skipping...")
                continue

            company_decision_makers = {}
            already_found_names = []

            for title_idx, title in enumerate(decision_maker_titles):
                print(f"  Searching for {title} at {company_name}")

                progress_key = f"{company_name}_{title}"

                if progress_key in progress_data:
                    print(f"    Already processed {title} for {company_name}")
                    for person_data in progress_data[progress_key]:
                        name = person_data.get('name')
                        if name and name not in already_found_names:
                            company_decision_makers[name] = {
                                'job_title': person_data.get('job_title'),
                                'linkedin_url': person_data.get('linkedin_url')
                            }
                            already_found_names.append(name)
                    continue

                if not api_manager.can_make_request():
                    print("All API keys have hit their daily limits. Queuing for next day...")
                    print("Please run this script tomorrow to continue processing.")
                    break

                search_results = search_linkedin_profiles_google_api(
                    api_manager, title, company_name, max_results_per_search, decision_maker_titles, already_found_names
                )

                print(f"    DEBUG: search_results length: {len(search_results)}")
                for i, result in enumerate(search_results):
                    print(f"    DEBUG: Result {i}: {result}")

                if not search_results:
                    print(f"    No relevant LinkedIn profiles found for {title} at {company_name}")
                    progress_data[progress_key] = []
                    save_progress(PROGRESS_FILE, progress_data)
                    continue

                processed_profiles = []
                for result_data in search_results:
                    person_name = result_data['name']
                    if person_name not in already_found_names:
                        processed_profiles.append(result_data)
                        company_decision_makers[person_name] = {
                            'job_title': result_data['job_title'],
                            'linkedin_url': result_data['linkedin_url']
                        }
                        already_found_names.append(person_name)
                        print(f"      Found: {person_name} - {result_data['job_title']}")

                print(f"    DEBUG: processed_profiles length: {len(processed_profiles)}")
                progress_data[progress_key] = processed_profiles
                save_progress(PROGRESS_FILE, progress_data)

                delay = random.uniform(SEARCH_DELAY_MIN, SEARCH_DELAY_MAX)
                print(f"    Waiting {delay:.1f} seconds...")
                time.sleep(delay)

            final_results[company_name] = company_decision_makers
            save_progress(OUTPUT_FILE, final_results)

            print(f"  Found {len(company_decision_makers)} decision makers for {company_name}")

            if not api_manager.can_make_request():
                print("All API keys have hit their daily limits. Stopping processing.")
                break

    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress saved.")
    except Exception as e:
        print(f"Error during scraping")

    print(f"\nScraping completed. Results saved to {OUTPUT_FILE}")
    return final_results


class GoogleAPIManager:
    def __init__(self, csv_file, daily_limit, warning_threshold):
        self.csv_file = csv_file
        self.daily_limit = daily_limit
        self.warning_threshold = warning_threshold
        self.current_key_index = 0
        self.load_keys()

    def load_keys(self):
        try:
            self.df = pd.read_csv(self.csv_file)
            self.update_daily_usage()
            print(f"Loaded {len(self.df)} API keys")
        except Exception as e:
            raise Exception(f"Error loading API keys")

    def update_daily_usage(self):
        today = datetime.now().strftime('%Y-%m-%d')

        for idx, row in self.df.iterrows():
            if row['last_used_date'] != today:
                self.df.at[idx, 'uses'] = 0
                self.df.at[idx, 'last_used_date'] = today

        self.save_keys()

    def get_next_available_key(self):
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
        self.df.at[key_index, 'uses'] += 1
        current_uses = self.df.at[key_index, 'uses']

        if current_uses == self.warning_threshold:
            print("=" * 50 + "\n\n")
            print(f"⚠️  WARNING: API key {key_index + 1} has reached {self.warning_threshold} uses")
            print("\n" + "=" * 50)

        if current_uses >= self.daily_limit:
            print("=" * 50 + "\n")
            print(f"🚫 API key {key_index + 1} has hit daily limit ({self.daily_limit} uses)")
            print("\n" + "=" * 50)

        self.save_keys()
        self.current_key_index = (key_index + 1) % len(self.df)

    def can_make_request(self):
        return self.get_next_available_key() is not None

    def save_keys(self):
        try:
            self.df.to_csv(self.csv_file, index=False)
        except Exception as e:
            print(f"Error saving API keys")


def search_linkedin_profiles_google_api(api_manager, title, company_name, max_results, decision_maker_titles,
                                        already_found_names):
    key_data = api_manager.get_next_available_key()
    if not key_data:
        print("No available API keys")
        return []

    search_queries = [
        f'site:linkedin.com/in/ "{title}" AND "{company_name}"',
        f'site:linkedin.com/in/ {title.replace(" ", "+")} AND {company_name.replace(" ", "+")}'
    ]

    all_results = []

    for query in search_queries:
        if len(all_results) >= max_results:
            break

        print(f"    API query: {query}")

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': key_data['api_key'],
            'cx': key_data['cse_id'],
            'q': query,
            'num': 10  # Get first 10 google search results
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            api_manager.increment_usage(key_data['index'])

            if response.status_code == 200:
                data = response.json()

                if 'items' in data:
                    for item in data['items']:
                        # Check relevance before processing
                        if is_profile_relevant(item, decision_maker_titles, company_name, already_found_names):
                            person_name = extract_person_name_from_title(item.get('title', ''))
                            job_title = extract_current_job_title(item.get('title', ''), item.get('snippet', ''))
                            linkedin_url = item.get('link', '')

                            if person_name and job_title and 'linkedin.com/in/' in linkedin_url:
                                result_data = {
                                    'name': person_name,
                                    'job_title': job_title,
                                    'linkedin_url': linkedin_url
                                }
                                all_results.append(result_data)
                                print(f"      Relevant profile found: {person_name} - {job_title}")

                                if len(all_results) >= max_results:
                                    break
                        else:
                            print(f"      Skipped irrelevant: {item.get('title', 'N/A')}")

                    # Save progress after each search query
                    save_progress(f"{OUTPUT_DIR}/search_results_progress.json", {
                        'company': company_name,
                        'title': title,
                        'results_found': all_results
                    })
                else:
                    print(f"    No results found for query: {query}")
            else:
                print(f"    API request failed: {response.status_code} - {response.text}")
                if response.status_code == 429:
                    print("    Rate limit hit, trying next key...")
                    key_data = api_manager.get_next_available_key()
                    if not key_data:
                        break

        except Exception as e:
            print(f"    Error making API request: {str(e)}")
            continue

        key_data = api_manager.get_next_available_key()
        if not key_data:
            break

    return all_results[:max_results]


def load_progress(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Corrupted progress file {filename}, starting fresh")
        return {}


def save_progress(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving progress to {filename}")


async def main():
    decision_maker_titles = [
        "CTO", "CIO", "VP Engineering", "VP Delivery", "Director Engineering",
        "Director Delivery", "Director Software Engineering", "Director Data",
        "Director AI Delivery", "Head Solutions Engineering",
        "Vice President Professional Services", "Director Software Engineering",
        "Director AI Solutions", "Head AI", "Director Product Engineering"
    ]

    api_csv_path = "google_api_key_and_cse_id.csv"

    results = await scrape_decision_makers_google_api(
        json_file_path="companies.json",
        decision_maker_titles=decision_maker_titles,
        max_results_per_search=5,
        api_csv_path=api_csv_path
    )

    print(f"Total results: {len(results)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())