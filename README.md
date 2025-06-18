# LinkedIn Job Scraper Documentation

## Purpose

This project is designed to scrape LinkedIn for job-related data, specifically targeting company names, company sizes, and decision-maker information. It leverages Selenium for scraping LinkedIn job listings and company pages, and the Google Custom Search API to identify decision makers. The final output is a consolidated CSV file containing all collected data.

## Project Structure

The project is modular, with each script handling a specific task:

- `main.py`: The entry point that coordinates the workflow by calling each module in sequence.
- `get_company_names_1.py`: Scrapes company names from LinkedIn job listings based on user-defined filters.
- `get_company_size_data_2.py`: Extracts company size data from LinkedIn company pages.
- `get_decision_makers_with_google_search_api_3.py`: Queries the Google Custom Search API to find decision makers’ LinkedIn profiles.
- `generate_final_output_4.py`: Merges all collected data into a single CSV file.

## How It Works

1. **Login to LinkedIn**

   - Selenium automates browser login using user-provided credentials (username and password).
   - Handles two-factor authentication prompts if enabled.

2. **Scrape Company Names**

   - Applies filters such as location (e.g., "United States"), job title (e.g., "Software Engineer"), date posted (e.g., "Past 24 hours"), industry (e.g., "Technology"), and experience level (e.g., "Entry level").
   - Scrapes company names from the resulting job listings, storing them in a CSV.

3. **Get Company Size Data**

   - For each company name, navigates to its LinkedIn company page (e.g., `linkedin.com/company/[company-name]`).
   - Extracts size data (e.g., "51-200 employees") from the "About" section and saves it to a separate CSV.

4. **Find Decision Makers**

   - Uses the Google Custom Search API to search for LinkedIn profiles of decision makers (e.g., "site:linkedin.com/in/ \[industry\] 'CEO' | 'CTO' | 'Director'").
   - Industry-specific titles are predefined in the script (e.g., "VP of Engineering" for tech).
   - Stores names, titles, and profile URLs in a CSV.

5. **Generate Final Output**

   - Combines data from all previous steps into a single CSV, including columns like company name, size, decision maker name, title, LinkedIn profile URL, and original job posting link.

## Setup

- **Dependencies**:

  - Install Python packages via `pip`: `selenium`, `pandas`, `requests`, `webdriver-manager` (for managing browser drivers).
  - Example: `pip install selenium pandas requests webdriver-manager`.

- **Credentials**:

  - Store LinkedIn username and password, plus Google API key and Custom Search Engine ID, in environment variables (e.g., `.env` file):

    ```
    LINKEDIN_USERNAME=your_email@example.com
    LINKEDIN_PASSWORD=your_password
    ```

- **Search Filters**:

  - Edit `main.py` to set filters like location, job title, and company size range.

- **Decision Maker Titles**:

  - Customize titles in `get_decision_makers_with_google_search_api_3.py` based on target industries.

## Output

- **Intermediate CSVs**: Each step generates a CSV in subfolders under `scraped_data/` (e.g., `scraped_data/1_company_names/`).
- **Final CSV**: A merged file (e.g., `final_output.csv`) in `scraped_data/4_final_output/`, with all data structured for easy analysis.

## Notes

- **Anti-Scraping Measures**:
  - Random delays (e.g., 2-5 seconds) and mouse-like navigation are implemented to mimic human behavior and avoid LinkedIn bans.
- **API Limits**:
  - The Google Custom Search API has a free tier limit (100 queries/day). Monitor usage or upgrade for larger projects.
- **Potential Issues**:
  - LinkedIn may block accounts for excessive scraping; use cautiously.
  - Missing data (e.g., private company pages) may result in incomplete rows.

## Running the Project

1. Ensure dependencies are installed and credentials are configured.
2. Run `python main.py` from the project root.
3. Check `scraped_data/` for output files after completion.

## Future Work

- Add IP rotation (e.g., via proxies) to improve scraping reliability and avoid detection.
- Expand filters to include more job attributes (e.g., remote vs. on-site).
