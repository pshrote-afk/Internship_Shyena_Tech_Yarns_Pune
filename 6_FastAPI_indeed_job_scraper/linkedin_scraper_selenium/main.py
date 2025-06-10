import asyncio
from src.driver_initialize_and_login import initialize_driver,login_to_linkedin
from src.get_company_names_1 import get_company_names
from src.get_company_size_data_2 import scrape_company_data
from src.get_decision_makers_with_google_search_api_3 import scrape_decision_makers_google_api


if __name__ == "__main__":
	# driver = initialize_driver()
	# login_to_linkedin(driver)
	#
	# #Part 1 - get company names
	#
	LOCATION = "United States"
	JOB_TITLE = "Data Engineer"
	DATE_POSTED = "Past week"  # Options: "Past 24 hours", "Past week", "Past month"
	# max_pages_scraped = 1  # Safety limit to prevent infinite loops. Default: 50
	#
	# get_company_names(driver, LOCATION, JOB_TITLE, DATE_POSTED, max_pages_scraped)
	#
	
	#later UPDATE: sleep for 15 mins, change vpn, change linkedin account
	#Part 2 - get company size data

	driver = initialize_driver()
	login_to_linkedin(driver)
	csv_file_path = f"./scraped_data/1_get_company_names/linkedin_{JOB_TITLE}_jobs.csv"
	try:
		scrape_company_data(driver,csv_file_path)
		print("Scraping completed successfully!")
 
	except Exception as e:
		print(f"Scraping failed: {str(e)}")

	print("\nQuitting driver...\n")
	driver.quit()

	# Part 3 - get decision maker

	
	json_file_path="./scraped_data/2_get_company_size_data/company_size_versus_company_name.json"
	
	decision_maker_titles = ["CTO", "CIO", "VP - Engineering", "VP - Delivery", "Director - Engineering", "Director - Delivery",
              "Director of Software Engineering", "Director of Data", "Director of AI Delivery",
               "Head of Solutions Engineering", "Vice President of Professional Services",
              "Director Software Engineering", "Director of AI Solutions", "Head of AI",
              "Director of Product Engineering"]
	
	api_csv_path="./google_api_key_and_cse_id.csv"
	
	results = asyncio.run(scrape_decision_makers_google_api(
	         json_file_path,
	         decision_maker_titles,
	   	 max_results_per_search=5,
	 	 api_csv_path=api_csv_path
	 	))




