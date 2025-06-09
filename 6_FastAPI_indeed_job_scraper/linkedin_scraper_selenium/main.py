import asyncio
from driver_initialize_and_login import initialize_driver,login_to_linkedin
#from _1_get_company_names import sth
from _2_get_company_size_data import scrape_company_data
from _3_get_decision_makers_google_search_api_crawl4ai import scrape_decision_makers_google_api


if __name__ == "__main__":
#	driver = initialize_driver()
#	login_to_linkedin(driver)

	#Part 1 - get company names

	#Part 2 - get company size data
#	csv_file_path = "./scraped_data/1_get_company_names/linkedin_Machine Learning_jobs_20250603_113313.csv"
#
#	try:
#		scrape_company_data(driver,csv_file_path)
#		print("Scraping completed successfully!")
 #
#	except Exception as e:
#		print(f"Scraping failed")
#	
#	driver.quit()

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




