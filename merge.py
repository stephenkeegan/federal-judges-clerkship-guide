#merge the wikipedia scrapes and clean up the data
print("running merge.py")
import pandas as pd

from helper_functions import nuke_wiki_junk

pres_appeals = pd.read_csv("pres_appeals.csv")
pres_district = pd.read_csv("pres_district.csv")
pres_appeals = pres_appeals.map(nuke_wiki_junk)
pres_district = pres_district.map(nuke_wiki_junk)

pres_appeals['Confirmation vote'] = pres_appeals['Confirmation vote'].str.replace('a', ' -', regex=False)
pres_district['Confirmation vote'] = pres_district['Confirmation vote'].replace('a', ' -', regex=False)

#this step removes judges who have been nominated but not yet confirmed, which is important for the next steps
# Keep all rows where Confirmation date is NOT "a"
pres_appeals = pres_appeals[pres_appeals['Confirmation date'] != 'a']
pres_district = pres_district[pres_district['Confirmation date'] != 'a']

# 2. Convert to actual Datetime objects
# Pandas is smart enough to parse "November 18, 2021" automatically
pres_appeals['Confirmation date'] = pd.to_datetime(pres_appeals['Confirmation date'])
# 3. Format to 18-Nov-21
# %d = Day, %b = Short Month (Nov), %y = 2-digit year (21)
pres_appeals['Confirmation date'] = pres_appeals['Confirmation date'].dt.strftime('%d-%b-%y')
pres_appeals = pres_appeals.drop(columns=['Confirmation date'])

pres_district['Confirmation Date'] = pres_district['Confirmation date'].str.replace(r'\[.*?\]', '', regex=True).str.strip()
pres_district['Confirmation Date'] = pd.to_datetime(pres_district['Confirmation Date'])
pres_district['Confirmation Date'] = pres_district['Confirmation Date'].dt.strftime('%d-%b-%y')
pres_district = pres_district.drop(columns=['Confirmation date'])

current_circuit = pd.read_csv("current_circuit_judges.csv")
current_district = pd.read_csv("current_district_judges.csv")


appeals = pd.merge(pres_appeals, current_circuit, how='outer', on='Judge')
# Keep incumbent judges from pres data AND all judges from current data
# (current judges are all incumbents by definition)
pres_only_cols = ['Ended active service', 'Confirmation vote']
curr_only_cols = ['Active Term', 'Duty Station']
mask_incumbent = appeals['Ended active service'].str.contains('Incumbent', case=False, na=False)
mask_current_only = appeals[pres_only_cols].isna().all(axis=1) & appeals[curr_only_cols].notna().any(axis=1)
appeals = appeals[mask_incumbent | mask_current_only]
appeals = appeals.drop(columns=['Number', '#', 'Court [Note 1]'])

district = pd.merge(pres_district, current_district, how='outer', on='Judge')
mask_incumbent = district['Ended active service'].str.contains('Incumbent', case=False, na=False)
mask_current_only = district[pres_only_cols].isna().all(axis=1) & district[curr_only_cols].notna().any(axis=1)
district = district[mask_incumbent | mask_current_only]
district = district.drop(columns=['Number', '#'])

appeals = appeals.map(nuke_wiki_junk)
district = district.map(nuke_wiki_junk)

district['Confirmation vote'] = district['Confirmation vote'].str.replace('a', ' -', regex=False)
appeals['Ended senior status'] = appeals['Ended senior status'].replace('a', ' -', regex=False)

district.to_csv("active_district.csv", index=False)
appeals.to_csv("active_appeals.csv", index=False)

print("Merged current judges with presidential appointees data")
print("Data saved to active_district.csv and active_appeals.csv")