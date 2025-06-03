from _2_get_company_size_data import scrape_company_data

if __name__ == "__main__":
	csv_file_path = "./scraped_data/1_get_company_names/linkedin_Machine Learning_jobs_20250603_113313.csv"
	
	try:
		scrape_company_data(csv_file_path)
		print("Scraping completed successfully!")
   
	except Exception as e:
        	print(f"Scraping failed: {e}")
	

