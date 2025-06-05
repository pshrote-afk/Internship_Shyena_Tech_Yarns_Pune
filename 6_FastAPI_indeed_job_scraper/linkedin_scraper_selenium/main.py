from driver_initialize_and_login import initialize_driver,login_to_linkedin
from _2_get_company_size_data import scrape_company_data
from _3_get_decision_makers_from_company_names import scrape_decision_makers

if __name__ == "__main__":
#	driver = initialize_driver()
#	login_to_linkedin(driver)

	#Part 1

	#Part 2 - commented out while we test part 3
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

	# Part 3

	driver = initialize_driver()
	login_to_linkedin(driver)

	json_file_path="./scraped_data/2_get_company_size_data/company_size_versus_company_name.json"

	decision_maker_titles = ["CTO", "CIO", "VP - Engineering", "VP - Delivery", "Director - Engineering", "Director - Delivery",
              "Director of Software Engineering", "Director of Data", "Director of AI Delivery",
              "Head of Solutions Engineering", "Vice President of Professional Services",
              "Director Software Engineering", "Director of AI Solutions", "Head of AI",
              "Director of Product Engineering"]
	
	proxy_list = [
        "106.214.62.67",
        "103.180.210.10", ]


	results = scrape_decision_makers(
			json_file_path,
			decision_maker_titles,
			max_results_per_search=5,
			proxy_list=proxy_list)





