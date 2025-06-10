import pandas as pd
import json
import os
import re
from pathlib import Path

def process_data(csv_file_path, company_size_json_path, website_json_path, decision_makers_json_path):
    
    # Extract job title from CSV filename
    csv_filename = Path(csv_file_path).name
    job_title_match = re.search(r'linkedin_(.+?)_jobs\.csv', csv_filename)
    job_title = job_title_match.group(1) if job_title_match else "Unknown"
    
    # Read CSV file
    df_jobs = pd.read_csv(csv_file_path)
    
    # Load JSON files
    with open(company_size_json_path, 'r') as f:
        company_size_data = json.load(f)
    
    with open(website_json_path, 'r') as f:
        website_data = json.load(f)
    
    with open(decision_makers_json_path, 'r') as f:
        decision_makers_data = json.load(f)
    
    # Create final output list
    final_output = []
    sr_no = 1
    
    for _, job_row in df_jobs.iterrows():
        company_name = job_row['company'].strip()
        location = job_row['location'].strip()
        linkedin_job_link = job_row['url']
        
        # Get website
        website = website_data.get(company_name, "unknown")
        
        # Get decision makers for this company
        company_contacts = decision_makers_data.get(company_name, {})
        
        if company_contacts:
            # Create row for each contact
            for contact_name, contact_info in company_contacts.items():
                row = {
                    'Sr. No.': sr_no,
                    'Company Name': company_name,
                    'Website': website,
                    'Contact Name': contact_name,
                    'Title': contact_info.get('job_title', 'unknown'),
                    'E-mail Id': '',  # Left blank as requested
                    'Office Number': '',  # Left blank as requested
                    'Mobile Number': '',  # Left blank as requested
                    'State': location,
                    'LinkedIn': contact_info.get('linkedin_url', 'unknown'),
                    'LinkedIn Job link': linkedin_job_link
                }
                final_output.append(row)
                sr_no += 1
        else:
            # No contacts found, create row with unknown contact info
            row = {
                'Sr. No.': sr_no,
                'Company Name': company_name,
                'Website': website,
                'Contact Name': 'unknown',
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
    output_dir = Path('./scraped_data/final_output')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_file = output_dir / f'final_output_{job_title}.csv'
    df_final.to_csv(output_file, index=False)
    
    print(f"Final output saved to: {output_file}")
    print(f"Total rows created: {len(df_final)}")
    
    return df_final

# Example usage:
# process_data(
#     'linkedin_Data Engineer_jobs.csv',
#     'company_size_versus_company_name.json',
#     'company_versus_website.json',
#     'company_name_versus_decision_maker_name.json'
# )