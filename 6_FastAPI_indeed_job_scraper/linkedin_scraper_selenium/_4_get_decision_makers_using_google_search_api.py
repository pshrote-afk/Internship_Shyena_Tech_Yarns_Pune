import json
import os
import time
import random
import csv
import re
from datetime import datetime
from urllib.parse import quote_plus
import requests
from dotenv import load_dotenv


def scrape_decision_makers(json_file_path, decision_maker_titles, max_results_per_search=5,
                           api_csv_path="google_api_key_and_cse_id.csv"):
    load_dotenv()

    OUTPUT_DIR = "./scraped_data/4_get_decision_makers"
    PROGRESS_FILE = f"{OUTPUT_DIR}/scraping_progress.json"
    OUTPUT_FILE = f"{OUTPUT_DIR}/company_name_versus_decision_maker_name.json"
    DELAY_MIN = 1
    DELAY_MAX = 3
    COMPANY_DELAY_MIN = 5
    COMPANY_DELAY_MAX = 10

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

    api_manager = GoogleAPIManager(api_csv_path)

    try:
        for company_idx, company_name in enumerate(filtered_companies):
            print(f"\nProcessing company {company_idx + 1}/{len(filtered_companies)}: {company_name}")

            if company_name in final_results:
                print(f"Company {company_name} already processed, skipping...")
                continue

            company_decision_makers = {}

            for title_idx, title in enumerate(decision_maker_titles):
                print(f"  Searching for {title} at {company_name}")

                progress_key = f"{company_name}_{title}"

                if progress_key in progress_data:
                    print(f"    Already processed {title} for {company_name}")
                    for name, profile_data in progress_data[progress_key].items():
                        company_decision_makers[name] = profile_data
                    continue

                if not api_manager.has_available_keys():
                    print("All API keys exhausted for today. Queuing remaining companies for next day.")
                    return final_results

                search_results = search_linkedin_profiles_api(api_manager, title, company_name, max_results_per_search)

                progress_data[progress_key] = search_results
                save_progress(PROGRESS_FILE, progress_data)

                company_decision_makers.update(search_results)

                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                print(f"    Waiting {delay:.1f} seconds...")
                time.sleep(delay)

            final_results[company_name] = company_decision_makers
            save_progress(OUTPUT_FILE, final_results)

            print(f"  Found {len(company_decision_makers)} decision makers for {company_name}")

            if company_idx < len(filtered_companies) - 1:
                company_delay = random.uniform(COMPANY_DELAY_MIN, COMPANY_DELAY_MAX)
                print(f"  Waiting {company_delay:.1f} seconds before next company...")
                time.sleep(company_delay)

    except KeyboardInterrupt:
        print("\nScraping interrupted by user. Progress saved.")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")

    print(f"\nScraping completed. Results saved to {OUTPUT_FILE}")
    return final_results


class GoogleAPIManager:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.keys_data = self.load_api_keys()
        self.current_key_index = 0
        self.today = datetime.now().strftime('%Y-%m-%d')

    def load_api_keys(self):
        keys_data = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keys_data.append({
                    'id': row['id'],
                    'api_key': row['api_key'],
                    'cse_id': row['cse_id'],
                    'uses': int(row['uses']),
                    'last_used_date': row['last_used_date']
                })
        return keys_data

    def save_api_keys(self):
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'api_key', 'cse_id', 'uses', 'last_used_date']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.keys_data)

    def get_next_available_key(self):
        for _ in range(len(self.keys_data)):
            key_data = self.keys_data[self.current_key_index]

            if key_data['last_used_date'] != self.today:
                key_data['uses'] = 0
                key_data['last_used_date'] = self.today

            if key_data['uses'] < 100:
                if key_data['uses'] >= 70:
                    print(f"WARNING: API key {key_data['id']} has reached {key_data['uses']} uses (70% of daily limit)")

                key_data['uses'] += 1
                self.save_api_keys()

                result = {
                    'api_key': key_data['api_key'],
                    'cse_id': key_data['cse_id'],
                    'id': key_data['id']
                }

                self.current_key_index = (self.current_key_index + 1) % len(self.keys_data)
                return result

            self.current_key_index = (self.current_key_index + 1) % len(self.keys_data)

        return None

    def has_available_keys(self):
        for key_data in self.keys_data:
            if key_data['last_used_date'] != self.today or key_data['uses'] < 100:
                return True
        return False


def search_linkedin_profiles_api(api_manager, title, company_name, max_results):
    results = {}

    # Workaround 1: Use broader search terms and filter results
    search_strategies = [
        # Strategy 1: Remove quotes from company name (quotes may be too restrictive)
        f'site:linkedin.com/in/ "{title}" {company_name}',

        # Strategy 2: Use partial company name matching
        f'site:linkedin.com/in/ {title} {company_name}',

        # Strategy 3: Search by keywords instead of exact phrases
        f'site:linkedin.com/in/ {title.replace("-", " ").replace("VP", "Vice President")} {company_name}',

        # Strategy 4: Use common title variations
        f'site:linkedin.com/in/ {get_title_variations(title)} {company_name}',

        # Strategy 5: Broader search with company domain (if available)
        f'site:linkedin.com/in/ {title} {get_company_domain(company_name)}',
    ]

    for strategy_idx, search_query in enumerate(search_strategies):
        if len(results) >= max_results:
            break

        try:
            key_info = api_manager.get_next_available_key()
            if not key_info:
                print(f"    No available API keys for search")
                break

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': key_info['api_key'],
                'cx': key_info['cse_id'],
                'q': search_query,
                'num': 10,  # Always get max results to filter
                'dateRestrict': 'y5'  # Limit to last 5 years for fresher results
            }

            print(f"    Strategy {strategy_idx + 1} - Query: {search_query}")

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'items' not in data:
                print(f"    No results found for strategy {strategy_idx + 1}")
                continue

            # Process all results and filter by relevance
            strategy_results = {}
            for item in data['items']:
                if 'linkedin.com/in/' in item.get('link', ''):
                    name, job_title, linkedin_url = extract_name_and_title_from_api_result(item, title, company_name)

                    if name and job_title:
                        # Score relevance to filter out irrelevant results
                        relevance_score = calculate_relevance(item, title, company_name)
                        if relevance_score > 0.3:  # Threshold for relevance
                            strategy_results[name] = {
                                "job_title": job_title,
                                "linkedin_url": linkedin_url,
                                "relevance_score": relevance_score
                            }

            # Add best results from this strategy
            sorted_results = sorted(strategy_results.items(), key=lambda x: x[1]['relevance_score'], reverse=True)
            for name, data in sorted_results[:max_results]:
                if name not in results:
                    results[name] = {
                        "job_title": data["job_title"],
                        "linkedin_url": data["linkedin_url"]
                    }
                    print(
                        f"      Found: {name} - {data['job_title']} - {data['linkedin_url']} (Score: {data['relevance_score']:.2f})")

                    if len(results) >= max_results:
                        break

            # If we found good results, we can stop
            if len(results) >= max_results // 2:  # At least half the desired results
                break

            # Fallback: Try general search if LinkedIn-specific search fails
            if len(results) == 0 and strategy_idx == len(search_strategies) - 1:
                print(f"    Trying fallback general search...")
                fallback_query = f'"{title}" "{company_name}" linkedin'

                params['q'] = fallback_query
                fallback_response = requests.get(url, params=params, timeout=30)
                fallback_response.raise_for_status()

                fallback_data = fallback_response.json()
                if 'items' in fallback_data:
                    for item in fallback_data['items']:
                        link = item.get('link', '')
                        if 'linkedin.com' in link:
                            name, job_title, linkedin_url = extract_name_and_title_from_api_result(item, title,
                                                                                                   company_name)
                            if name and job_title and name not in results:
                                results[name] = {
                                    "job_title": job_title,
                                    "linkedin_url": linkedin_url
                                }
                                print(f"      Fallback found: {name} - {job_title} - {linkedin_url}")
                                if len(results) >= max_results:
                                    break

        except requests.exceptions.RequestException as e:
            print(f"    API request error for strategy {strategy_idx + 1}: {str(e)}")
            continue
        except Exception as e:
            print(f"    Unexpected error for strategy {strategy_idx + 1}: {str(e)}")
            continue

    print(f"    Total extracted profiles: {len(results)}")
    return results


def get_title_variations(title):
    """Generate variations of job titles to improve search"""
    variations = [title]

    # Common replacements
    replacements = {
        'VP': 'Vice President',
        'Dir': 'Director',
        'Mgr': 'Manager',
        'Eng': 'Engineer',
        'Dev': 'Development',
        'AI': 'Artificial Intelligence',
        'IT': 'Information Technology'
    }

    title_words = title.split()
    for i, word in enumerate(title_words):
        for abbr, full in replacements.items():
            if word == abbr:
                new_title = title_words.copy()
                new_title[i] = full
                variations.append(' '.join(new_title))
            elif word == full:
                new_title = title_words.copy()
                new_title[i] = abbr
                variations.append(' '.join(new_title))

    return ' OR '.join(f'"{var}"' for var in variations[:3])  # Limit to avoid too long queries


def get_company_domain(company_name):
    """Try to guess company domain for broader search"""
    # Simple heuristic - convert company name to potential domain
    domain_guess = company_name.lower().replace(' ', '').replace('-', '')
    return f'"{domain_guess}"'


def calculate_relevance(item, target_title, company_name):
    """Calculate relevance score for search results"""
    title_text = item.get('title', '').lower()
    snippet_text = item.get('snippet', '').lower()
    combined_text = f"{title_text} {snippet_text}"

    score = 0.0

    # Title matching
    title_words = target_title.lower().split()
    for word in title_words:
        if len(word) > 2:  # Skip short words
            if word in combined_text:
                score += 0.3

    # Company matching
    company_words = company_name.lower().split()
    for word in company_words:
        if len(word) > 2:  # Skip short words
            if word in combined_text:
                score += 0.4

    # Exact phrase matching (bonus)
    if target_title.lower() in combined_text:
        score += 0.5
    if company_name.lower() in combined_text:
        score += 0.5

    # Penalty for irrelevant content
    irrelevant_terms = ['student', 'intern', 'former', 'ex-', 'retired', 'freelance']
    for term in irrelevant_terms:
        if term in combined_text:
            score -= 0.2

    return max(0, score)  # Ensure non-negative score


def extract_name_and_title_from_api_result(item, target_title, company_name):
    try:
        title_text = item.get('title', '')
        snippet_text = item.get('snippet', '')
        linkedin_url = item.get('link', '')

        validated_url = validate_linkedin_url(linkedin_url)

        combined_text = f"{title_text} {snippet_text}"

        name_match = re.match(r'^([^-|]+)', title_text)
        if name_match:
            name = name_match.group(1).strip()
        else:
            name_parts = title_text.split()[:2]
            name = " ".join(name_parts)

        job_title = ""

        title_patterns = [
            r'[-|]\s*([^-|]+(?:CEO|CTO|CIO|VP|Director|Head|Manager|Engineer|Lead)[^-|]*)',
            r'[-|]\s*([^-|]*(?:Vice President|VP|Director|Head|Manager)[^-|]*)',
            r'[-|]\s*([^-|]*(?:Chief|Senior|Principal)[^-|]*)',
            r'(CEO|CTO|CIO|Chief Technology Officer|Chief Information Officer)',
            r'(Vice President[^.|,]*)',
            r'(Director[^.|,]*)',
            r'(Head of[^.|,]*)',
            r'(VP[^.|,]*)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break

        if not job_title:
            job_title_keywords = ['CEO', 'CTO', 'CIO', 'VP', 'Vice President', 'Director', 'Head', 'Manager',
                                  'Engineer', 'Lead', 'Chief']
            for keyword in job_title_keywords:
                if keyword.lower() in combined_text.lower():
                    sentences = re.split(r'[.!?]', combined_text)
                    for sentence in sentences:
                        if keyword.lower() in sentence.lower() and company_name.lower() in sentence.lower():
                            job_title = sentence.strip()
                            break
                    if job_title:
                        break

        name = clean_text(name)
        job_title = clean_text(job_title)

        if len(name) > 3 and len(job_title) > 3 and not is_generic_text(name):
            return name, job_title, validated_url

    except Exception as e:
        print(f"      Error extracting name and title: {str(e)}")

    return None, None, None


def validate_linkedin_url(url):
    """Validate and clean LinkedIn URL"""
    if not url:
        return "unknown"

    try:
        # Check if it's a valid LinkedIn profile URL
        linkedin_profile_pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?(?:\?.*)?'
        if re.match(linkedin_profile_pattern, url):
            # Clean the URL by removing query parameters
            clean_url = re.sub(r'\?.*$', '', url)
            return clean_url
        else:
            return "invalid_linkedin_url"
    except Exception:
        return "error_validating_url"


def is_generic_text(text):
    """Check if text contains generic terms that shouldn't be treated as names"""
    if not text:
        return True

    generic_terms = ['linkedin', 'profile', 'profiles', 'search', 'results', 'page', 'website', 'site']
    return any(term in text.lower() for term in generic_terms)


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""

    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove leading bullets or separators
    text = re.sub(r'^[-|•]\s*', '', text)
    # Remove trailing separators
    text = re.sub(r'\s*[-|•]$', '', text)
    # Remove LinkedIn-specific suffixes
    text = re.sub(r'\s*-\s*LinkedIn.*$', '', text, flags=re.IGNORECASE)

    return text


def load_progress(filename):
    """Load progress from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Corrupted progress file {filename}, starting fresh")
        return {}


def save_progress(filename, data):
    """Save progress to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving progress to {filename}: {str(e)}")


if __name__ == "__main__":
    decision_maker_titles = [
        "CTO", "CIO", "VP - Engineering", "VP - Delivery", "Director - Engineering",
        "Director - Delivery", "Director of Software Engineering", "Director of Data",
        "Director of AI Delivery", "Head of Solutions Engineering",
        "Vice President of Professional Services", "Director Software Engineering",
        "Director of AI Solutions", "Head of AI", "Director of Product Engineering"
    ]

    results = scrape_decision_makers(
        json_file_path="companies.json",
        decision_maker_titles=decision_maker_titles,
        max_results_per_search=5,
        api_csv_path="google_api_key_and_cse_id.csv"
    )

    print(f"Total results: {len(results)}")