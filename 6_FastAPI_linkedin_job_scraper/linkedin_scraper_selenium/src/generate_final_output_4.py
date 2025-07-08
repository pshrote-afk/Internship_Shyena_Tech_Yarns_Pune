import pandas as pd
import json
import os
import re
from pathlib import Path


def process_data(LINKEDIN_COMPANY_SIZE_FILTER, csv_file_path, company_details_csv_path, decision_makers_json_path):
    # Extract job title from CSV filename
    csv_filename = Path(csv_file_path).name
    job_title_match = re.search(r'linkedin_(.+?)_jobs\.csv', csv_filename)
    job_title = job_title_match.group(1) if job_title_match else "Unknown"

    # Read CSV files
    df_jobs = pd.read_csv(csv_file_path)
    df_company_details = pd.read_csv(company_details_csv_path)

    # Parse LINKEDIN_COMPANY_SIZE_FILTER if it's a string
    if isinstance(LINKEDIN_COMPANY_SIZE_FILTER, str):
        import ast
        company_size_filter = ast.literal_eval(LINKEDIN_COMPANY_SIZE_FILTER)
    else:
        company_size_filter = LINKEDIN_COMPANY_SIZE_FILTER

    # Create a dictionary for quick lookup of company details
    company_details_dict = {}
    for _, row in df_company_details.iterrows():
        company_name = row['company'].strip()
        company_size = row['company_size']

        # Skip companies with empty size, but include "unknown"
        if pd.isna(company_size) or company_size == '':
            continue

        # Filter by company size
        if company_size != 'unknown' and company_size not in company_size_filter:
            continue

        company_details_dict[company_name] = {
            'website': row['website'],
            'industry': row['industry'],
            'company_size': company_size
        }

    # Load decision makers JSON file
    with open(decision_makers_json_path, 'r', encoding='utf-8') as f:
        decision_makers_data = json.load(f)

    # Create final output list
    final_output = []
    sr_no = 1

    for _, job_row in df_jobs.iterrows():
        company_name = job_row['company'].strip()
        location = job_row['location'].strip()
        linkedin_job_link = job_row['url']
        job_description = job_row['job_description']
        scraped_at = job_row['scraped_at']
        posted_on = job_row['posted_on']

        # Skip companies not in filtered company details
        if company_name not in company_details_dict:
            continue

        # Get company details (already filtered)
        company_info = company_details_dict[company_name]
        website = company_info['website']
        industry = company_info['industry']
        company_size = company_info['company_size']

        # Get decision makers for this company
        company_contacts = decision_makers_data.get(company_name, {})

        if company_contacts:
            # Create row for each contact
            for contact_name, contact_info in company_contacts.items():
                row = {
                    'Sr. No.': sr_no,
                    'Company Name': company_name,
                    'Website': website,
                    'Industry': industry,
                    'Company size': company_size,
                    'Contact': contact_name,
                    'Title': contact_info.get('job_title', 'unknown'),
                    'E-mail Id': '',  # Left blank as requested
                    'Office Number': '',  # Left blank as requested
                    'Mobile Number': '',  # Left blank as requested
                    'State': location,
                    'LinkedIn': contact_info.get('linkedin_url', 'unknown'),
                    'LinkedIn Job link': linkedin_job_link,
                    'LinkedIn Job Description': job_description,
                    'Scraped at': scraped_at,
                    'Posted on': posted_on
                }
                final_output.append(row)
                sr_no += 1
        else:
            # No contacts found, create row with unknown contact info
            row = {
                'Sr. No.': sr_no,
                'Company Name': company_name,
                'Website': website,
                'Industry': industry,
                'Company size': company_size,
                'Contact': 'unknown',
                'Title': 'unknown',
                'E-mail Id': '',  # Left blank as requested
                'Office Number': '',  # Left blank as requested
                'Mobile Number': '',  # Left blank as requested
                'State': location,
                'LinkedIn': 'unknown',
                'LinkedIn Job link': linkedin_job_link
            }
            final_output.append(row)
            sr_no += 1

    # Create DataFrame
    df_final = pd.DataFrame(final_output)

    # Create output directory if it doesn't exist
    output_dir = Path('./scraped_data/4_final_output')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    output_file = output_dir / f'final_output_{job_title}.csv'
    df_final.to_csv(output_file, index=False)

    print(f"Final output saved to: {output_file}")
    print(f"Total rows created: {len(df_final)}")

    return df_final

# Example usage:
# process_data(
#     '["51-200 employees", "201-500 employees", "501-1,000 employees"]',
#     'linkedin_Machine Learning_jobs.csv',
#     'Machine Learning_company_website_industry_size.csv',
#     'Machine Learning_company_name_versus_decision_maker_name.json'
# )