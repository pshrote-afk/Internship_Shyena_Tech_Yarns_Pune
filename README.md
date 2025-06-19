# LinkedIn Job Scraper Documentation

## Purpose

This project is designed to scrape LinkedIn for job-related data, specifically targeting company names from job listings. The scraper uses Selenium for web automation and OpenAI's API for job description summarization. It includes intelligent filtering to only collect recent jobs and provides data extraction with pagination support.

## Project Structure

The project is modular, with each script handling a specific task:

- `main.py`: The entry point that coordinates the workflow by calling each module in sequence
- `get_company_names_1.py`: Scrapes company names and job details from LinkedIn job listings based on user-defined filters
- `get_company_size_data_2.py`: Extracts company size data from LinkedIn company pages
- `get_decision_makers_with_google_search_api_3.py`: Queries the Google Custom Search API to find decision makers' LinkedIn profiles
- `generate_final_output_4.py`: Merges all collected data into a single CSV file

## Current Implementation Features

### Enhanced Job Scraping (`get_company_names_1.py`)

- **Smart Date Filtering**: Only scrapes jobs posted after the last scraping date to avoid duplicates
- **AI-Powered Summarization**: Uses OpenAI's GPT-3.5-turbo to generate concise job description summaries
- **Multi-Page Support**: Automatically navigates through multiple pages of job listings with configurable limits
- **Enhanced Scrolling**: Simulates human-like scrolling behavior to load all job listings on each page
- **Robust Error Handling**: Multiple fallback selectors and retry mechanisms for reliable data extraction
- **Real-time CSV Saving**: Saves each job immediately to prevent data loss during long scraping sessions

### Data Collected

For each job posting, the scraper collects:
- **Job Title**: Position name
- **Company Name**: Hiring organization
- **Location**: Job location (cleaned and parsed)
- **Job URL**: Direct link to the LinkedIn job posting
- **Job Description**: AI-summarized description (max 30 words)
- **Scraped At**: Timestamp when the job was scraped
- **Posted On**: When the job was originally posted on LinkedIn

## How It Works

### 1. **Login to LinkedIn**
- Selenium automates browser login using credentials from `.env` file
- Handles multiple post-login scenarios including CAPTCHA and email verification
- Includes robust verification with multiple success indicators

### 2. **Apply Job Filters**
- **Location Filter**: Targets specific geographic areas (e.g., "United States")
- **Job Title Filter**: Searches for specific roles (e.g., "Generative AI Developer")
- **Date Posted Filter**: Options include "Past 24 hours", "Past week", "Past month"
- **Industry Filter**: Targets specific industries like:
  - IT Services and IT Consulting
  - Software Development
  - Technology, Information and Internet
- **Experience Level Filter**: Filters by experience levels:
  - Entry level
  - Associate
  - Mid-Senior level

### 3. **Enhanced Scraping Process**
- **Intelligent Scrolling**: Uses multiple scrolling methods to ensure all jobs are loaded
- **Human-like Behavior**: Random delays and mouse movements to avoid detection
- **Date-based Filtering**: Only processes jobs newer than the last scraping date
- **Real-time Processing**: Each job is processed and saved immediately
- **Pagination Support**: Automatically navigates through multiple pages with configurable limits

### 4. **AI-Enhanced Data Processing**
- **Job Description Summarization**: Uses OpenAI API to create concise, readable summaries
- **Date Parsing**: Converts relative dates ("2 days ago") to absolute timestamps
- **Data Validation**: Ensures all required fields are populated before saving

## Setup

### Environment Configuration
Create a `.env` file with the following credentials:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
```

### Configuration Variables
Edit the configurables of main.py:
```python

# In main.py
LOCATION = "United States"
JOB_TITLE = "Generative AI Developer"
DATE_POSTED = "Past week"  # Options: "Past 24 hours", "Past week", "Past month"
max_pages_scraped = 2  # Safety limit to prevent infinite loops
INDUSTRY_FILTER = ["IT Services and IT Consulting", "Software Development"]
EXPERIENCE_LEVEL_FILTER = ["Entry level", "Associate", "Mid-Senior level"]
```

Edit the configurable `last_scraping_date` at the beginning of `get_company_names_1.py`:
```
# At the beginning of get_company_names_1.py
last_scraping_date = "2025-06-15 10:20"  # Configure this for date filtering. # later take last_scraping_data from metadata table


## Output Structure

### File Organization
```
scraped_data/
├── 1_get_company_names/
│   └── linkedin_[JOB_TITLE]_jobs.csv
├── 2_get_company_size_data/
│   └── company_size_data.csv
├── 3_get_decision_makers_with_google_search_api/
│   └── decision_makers_data.csv
└── 4_generate_final_output/
    └── final_output.csv
```

### CSV Columns
- `title`: Job position title
- `company`: Company name
- `location`: Job location
- `url`: LinkedIn job posting URL
- `job_description`: AI-generated summary (max 30 words)
- `scraped_at`: Timestamp of when data was collected
- `posted_on`: When the job was posted on LinkedIn (UTC)

## Key Features

### Anti-Detection Measures
- **Random Delays**: Variable wait times between actions (0.5-4 seconds)
- **Human-like Scrolling**: Multiple scrolling methods with realistic timing
- **User Agent Spoofing**: Mimics real browser behavior
- **Action Chains**: Uses Selenium's ActionChains for mouse-like interactions


### Performance Optimizations
- **Immediate Saving**: Prevents data loss during long scraping sessions
- **Configurable Limits**: `max_pages_scraped` prevents infinite loops
- **Date Filtering**: Avoids processing old job postings

## Usage

### Basic Execution
```python
python main.py
```

### Customization
Modify the configuration variables at the bottom of the script:
- `LOCATION`: Target geographic area
- `JOB_TITLE`: Specific job role to search for
- `DATE_POSTED`: How recent jobs should be
- `max_pages_scraped`: Maximum number of pages to process
- `INDUSTRY_FILTER`: List of target industries
- `EXPERIENCE_LEVEL_FILTER`: List of experience levels

## Important Notes

### API Usage
- **OpenAI Integration**: Requires valid API key for job description summarization
- **Token Management**: Optimized prompts to minimize API costs
- **Error Handling**: Graceful fallback if AI summarization fails

### Potential Limitations
- **LinkedIn Changes**: May require updates if LinkedIn modifies their interface
- **Network Dependencies**: Requires stable internet connection for reliable operation
- **API Costs**: OpenAI API usage incurs costs based on token consumption

## Troubleshooting

### Common Issues
- **Login Failures**: Check credentials in `.env` file
- **No Jobs Found**: Verify search filters aren't too restrictive
- **Scrolling Issues**: LinkedIn interface changes may require selector updates
- **API Errors**: Ensure OpenAI API key is valid and has sufficient credits

## Future Enhancements

### Planned Improvements
- **Proxy Support**: IP rotation for improved reliability
- **Database Storage**: Direct database insertion instead of CSV files


--Paras Shrote
