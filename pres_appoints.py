print("running pres_appoints.py")


import pandas as pd
import wikipedia as wp


def parse_page(page_title, tables):
    html = wp.page(page_title).html().encode("UTF-8")
    df_list = pd.read_html(html)
    return [df_list[t] for t in tables if t < len(df_list)]

try:
    trump_one_circuit, trump_two_circuit, trump_one_district, trump_two_district = parse_page(
        "List_of_federal_judges_appointed_by_Donald_Trump", [3,4,5,6])
    print("Trump")
except Exception:
    print("Trump parse issue")

try:
    biden_circuit, biden_district = parse_page(
        "List_of_federal_judges_appointed_by_Joe_Biden", [3,5])
    print("Biden")
except Exception:
    print("Biden parse issue")

try:
    obama_circuit, obama_district = parse_page(
        "List_of_federal_judges_appointed_by_Barack_Obama", [3,5])
    print("Obama")
except Exception:
    print("Obama parse issue")

try:
    bushw_circuit, bushw_district = parse_page(
        "List_of_federal_judges_appointed_by_George_W._Bush", [3,5])
    print("Bush W")
except Exception:
    print("Bush W parse issue")

try:
    clinton_circuit, clinton_district = parse_page(
        "List_of_federal_judges_appointed_by_Bill_Clinton", [3,5])
    print("Clinton")
except Exception:
    print("Clinton parse issue")

try:
    bushhw_circuit, bushhw_district = parse_page(
        "List_of_federal_judges_appointed_by_George_H._W._Bush", [3,5])
    print("Bush HW")
except Exception:
    print("Bush HW parse issue")

try:
    reagan_circuit, reagan_district = parse_page(
        "List_of_federal_judges_appointed_by_Ronald_Reagan", [3,5])
    print("Reagan")
except Exception:
    print("Reagan parse issue")

try:
    carter_circuit, carter_district = parse_page(
        "List_of_federal_judges_appointed_by_Jimmy_Carter", [3,5])
    print("Carter")
except Exception:
    print("Carter parse issue")

try:
    nixon_circuit, nixon_district = parse_page(
        "List_of_federal_judges_appointed_by_Richard_Nixon", [3,5])
    print("Nixon")
except Exception:
    print("Nixon parse issue")

pres_appeals = pd.concat([trump_one_circuit, trump_two_circuit, biden_circuit, obama_circuit, clinton_circuit, bushhw_circuit, bushw_circuit,reagan_circuit, nixon_circuit, carter_circuit], ignore_index=True)
pres_district = pd.concat([trump_one_district, trump_two_district, biden_district, obama_district, clinton_district, bushhw_district, bushw_district,reagan_district, nixon_district, carter_district], ignore_index=True)

pres_appeals.to_csv("pres_appeals.csv", index=False)
pres_district.to_csv("pres_district.csv", index=False)
print("Presidential appointees data saved to pres_appeals.csv and pres_district.csv")
