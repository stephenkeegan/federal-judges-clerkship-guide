#get the district judges
print("running current_district_judges.py")
import io

import pandas as pd
import wikipedia as wp

# 1. Fetch the page
page_title = "List of current United States district judges"
html_str = wp.page(page_title).html()

# 2. Read ALL tables from the page
# Wikipedia has a lot of tables, so we filter for the ones containing judge data
all_tables = pd.read_html(io.StringIO(html_str))

# This list will store our cleaned DataFrames
district_dfs = []

# 3. Process each table
for df in all_tables:
    # We only want tables that have the "Judge" and "Term of service" columns
    # We check the column levels to identify the correct tables
    if 'Judge' in str(df.columns) and 'Term of service' in str(df.columns):
        
        # --- Apply the header flattening logic ---
        df.columns = [
            f"{col[0]} {col[1]}".strip() if "Unnamed" not in col[0] else col[1]
            for col in df.columns.values
        ]
        
        district_dfs.append(df)
        district_dfs[-1] = district_dfs[-1].rename(columns={'# #': 'Number', 'Title Title': 'Title', 'Judge Judge': 'Judge',
                                'Duty station Duty station': 'Duty Station', 
                                'Born Born': 'Born', 
                                'Term of service Active': 'Active Term', 
                                'Term of service Chief': 'Chief Term', 
                                'Term of service Senior': 'Senior Term',
                                'Appointed by Appointed by': 'Appointed By'}, inplace=False)
print(f"Total District Tables Found: {len(district_dfs)}")
current_district = pd.concat(district_dfs, ignore_index=True)
csv_filename = "current_district_judges.csv"
current_district.to_csv(csv_filename, index=False)
print(f"Current district judges data saved to {csv_filename}")