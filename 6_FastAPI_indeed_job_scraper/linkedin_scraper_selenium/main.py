import asyncio
from src.driver_initialize_and_login import initialize_driver,login_to_linkedin
from src.get_company_names_1 import get_company_names
from src.get_company_size_data_2 import scrape_company_data
from src.get_decision_makers_with_google_search_api_3 import scrape_decision_makers_google_api
from src.generate_final_output_4 import process_data

if __name__ == "__main__":
	# driver = initialize_driver()
	# login_to_linkedin(driver)
	#
	# # Part 1 - get company names
	#
	LOCATION = "United States"
	JOB_TITLE = "Generative AI"
	DATE_POSTED = "Past month"  # Options: "Past 24 hours", "Past week", "Past month"
	INDUSTRY_FILTER = ["IT Services and IT Consulting","Software Development","Technology, Information and Internet"]
	max_pages_scraped = 2  # Safety limit to prevent infinite loops. Default: 50
	LINKEDIN_COMPANY_SIZE_FILTER='["10,001+ employees"]'	# "1-10 employees" OR "11-50 employees" OR "51-200 employees" OR "201-500 employees" OR "501-1000 employees" OR "1001-5000 employees" OR "5001-10,000 employees" OR "10,001+ employees" OR "unknown"
	#
	# # example:
	# # LINKEDIN_COMPANY_SIZE_FILTER='["1-10 employees", "11-50 employees", "51-200 employees"]'
	# # LINKEDIN_COMPANY_SIZE_FILTER='["51-200 employees","501-1000 employees"]'
	# # LINKEDIN_COMPANY_SIZE_FILTER='["501-1000 employees"]'
	#
	# get_company_names(driver, LOCATION, JOB_TITLE, DATE_POSTED, INDUSTRY_FILTER, max_pages_scraped)
	#
	# print("\nQuitting driver...\n")
	# driver.quit()


	# later UPDATE: sleep for 15 mins, change vpn, change linkedin account
	# Part 2 - get company size data

	# driver = initialize_driver()
	# login_to_linkedin(driver)
	csv_file_path = f"./scraped_data/1_get_company_names/linkedin_{JOB_TITLE}_jobs.csv"
	# try:
	# 	scrape_company_data(driver,JOB_TITLE, csv_file_path)
	# 	print("Scraping completed successfully!")
	#
	# except Exception as e:
	# 	print(f"Scraping failed: {str(e)}")
	#
	# print("\nQuitting driver...\n")
	# driver.quit()

	# Part 3 - get decision maker

	csv_company_file_path=f"./scraped_data/2_get_company_size_data/{JOB_TITLE}_company_website_industry_size.csv"

	decision_maker_titles = {
    "IT Services and IT Consulting": [
        "Chief Technology Officer",
        "Chief Information Officer",
        "IT Director",
        "IT Manager",
        "VP of IT",
        "Director of IT Services",
        "Solutions Architect",
        "IT Consulting Manager",
        "Head of Infrastructure",
        "Cloud Services Manager"
    ],
    "Software Development": [
        "Chief Technology Officer",
        "VP of Engineering",
        "Director of Software Development",
        "Software Development Manager",
        "Head of Product Development",
        "Technical Lead",
        "Engineering Manager",
        "Product Manager (Technical)",
        "DevOps Manager",
        "Scrum Master / Agile Coach"
    ],
    "Technology, Information and Internet": [
        "Chief Technology Officer",
        "Chief Product Officer",
        "VP of Technology",
        "Director of Engineering",
        "Head of Digital Transformation",
        "Product Manager",
        "Data Science Manager",
        "Director of Information Systems",
        "Head of Innovation",
        "Technical Program Manager"
    ],
    "unknown": [
        "CEO",
        "COO",
        "CFO",
        "President",
        "General Manager",
        "Director of Operations",
        "Business Development Manager",
        "Head of Strategy",
        "VP of Business Operations",
        "Managing Director"
    ]
}

	api_csv_path="./google_api_key_and_cse_id.csv"

	results = asyncio.run(scrape_decision_makers_google_api(JOB_TITLE,
	         LINKEDIN_COMPANY_SIZE_FILTER,
	         csv_company_file_path,
	         decision_maker_titles,
	   	 max_results_per_search=5,
	 	 api_csv_path=api_csv_path
	 	))

	# Part 4 - combine all results

	final = process_data(
	csv_file_path,
	csv_company_file_path,
	f'./scraped_data/3_get_decision_makers_google_api/{JOB_TITLE}_company_name_versus_decision_maker_name.json'
	)

	print(final)




