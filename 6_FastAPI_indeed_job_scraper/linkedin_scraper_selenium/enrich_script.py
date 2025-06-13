import pandas as pd
import sys


def merge_csv_files(csv1_path, csv2_path, output_path):
    """
    Merge CSV files by adding LinkedIn Job Link from CSV1 to CSV2
    """
    try:
        # Read CSV files
        df1 = pd.read_csv(csv1_path)
        df2 = pd.read_csv(csv2_path)

        # Clean column names (remove extra spaces)
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Create a mapping dictionary from CSV1
        company_link_map = {}
        for _, row in df1.iterrows():
            company_name = row['Company Name']
            linkedin_link = row['LinkedIn Job link']
            company_link_map[company_name] = linkedin_link

        # Add LinkedIn Job Link column to CSV2
        linkedin_links = []
        for _, row in df2.iterrows():
            company_name = row['Company Name - Cleaned']
            if company_name in company_link_map:
                linkedin_links.append(company_link_map[company_name])
            else:
                linkedin_links.append("error in combining")

        # Insert LinkedIn Job Link column at position 1 (after Research Date)
        df2.insert(1, 'LinkedIn Job Link', linkedin_links)

        # Save the merged data to new CSV
        df2.to_csv(output_path, index=False)
        print(f"Successfully merged files. Output saved to: {output_path}")

    except Exception as e:
        print(f"Error processing files: {str(e)}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python script.py <csv1_path> <csv2_path> <output_path>")
        print("Example: python script.py file1.csv file2.csv merged_output.csv")
        return

    csv1_path = sys.argv[1]
    csv2_path = sys.argv[2]
    output_path = sys.argv[3]

    merge_csv_files(csv1_path, csv2_path, output_path)


if __name__ == "__main__":
    main()