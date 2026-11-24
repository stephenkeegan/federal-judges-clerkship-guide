"""
Parse the Federal Court Management Statistics PDF using table extraction
to get per-district caseload profiles.

Uses pdfplumber table extraction for structured parsing.
"""

import pandas as pd
import numpy as np
import pdfplumber
import re
import json

PDF_PATH = "district_profiles.pdf"
OUTPUT_JSON = "district_caseload.json"


def parse_number(val):
    """Parse a number from a table cell, handling commas and dashes."""
    if val is None:
        return None
    val = str(val).strip()
    if val in ("", "-", "—", "N/A"):
        return None
    val = val.replace(",", "")
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return None


def extract_district_from_table(table):
    """Extract district name from the first table."""
    if not table or len(table) < 2:
        return None
    # First row, first cell has the district name
    first_row = table[0]
    if first_row and len(first_row) > 0:
        name = str(first_row[0]).strip()
        # Remove "DISTRICT OF ... 12-Month Periods Ending" suffix
        name = re.sub(r'\s*12-Month Periods Ending.*$', '', name, flags=re.IGNORECASE)
        return name
    return None


def map_district_name_to_court(name):
    """Map district name from PDF to court abbreviation."""
    if not name:
        return None

    mappings = {
        "DISTRICT OF COLUMBIA": "D.D.C.",
        "MAINE": "D. Me.",
        "MASSACHUSETTS": "D. Mass.",
        "NEW HAMPSHIRE": "D.N.H.",
        "RHODE ISLAND": "D.R.I.",
        "PUERTO RICO": "D.P.R.",
        "CONNECTICUT": "D. Conn.",
        "NEW YORK NORTHERN": "N.D.N.Y.",
        "NEW YORK EASTERN": "E.D.N.Y.",
        "NEW YORK SOUTHERN": "S.D.N.Y.",
        "NEW YORK WESTERN": "W.D.N.Y.",
        "DELAWARE": "D. Del.",
        "NEW JERSEY": "D.N.J.",
        "PENNSYLVANIA EASTERN": "E.D. Pa.",
        "PENNSYLVANIA MIDDLE": "M.D. Pa.",
        "PENNSYLVANIA WESTERN": "W.D. Pa.",
        "VIRGIN ISLANDS": "D.V.I.",
        "MARYLAND": "D. Md.",
        "VIRGINIA EASTERN": "E.D. Va.",
        "VIRGINIA WESTERN": "W.D. Va.",
        "WEST VIRGINIA NORTHERN": "N.D. W. Va.",
        "WEST VIRGINIA SOUTHERN": "S.D. W. Va.",
        "NORTH CAROLINA EASTERN": "E.D.N.C.",
        "NORTH CAROLINA MIDDLE": "M.D.N.C.",
        "NORTH CAROLINA WESTERN": "W.D.N.C.",
        "SOUTH CAROLINA": "D.S.C.",
        "GEORGIA NORTHERN": "N.D. Ga.",
        "GEORGIA MIDDLE": "M.D. Ga.",
        "GEORGIA SOUTHERN": "S.D. Ga.",
        "FLORIDA NORTHERN": "N.D. Fla.",
        "FLORIDA MIDDLE": "M.D. Fla.",
        "FLORIDA SOUTHERN": "S.D. Fla.",
        "ALABAMA NORTHERN": "N.D. Ala.",
        "ALABAMA MIDDLE": "M.D. Ala.",
        "ALABAMA SOUTHERN": "S.D. Ala.",
        "MISSISSIPPI NORTHERN": "N.D. Miss.",
        "MISSISSIPPI SOUTHERN": "S.D. Miss.",
        "LOUISIANA EASTERN": "E.D. La.",
        "LOUISIANA MIDDLE": "M.D. La.",
        "LOUISIANA WESTERN": "W.D. La.",
        "TEXAS NORTHERN": "N.D. Tex.",
        "TEXAS SOUTHERN": "S.D. Tex.",
        "TEXAS EASTERN": "E.D. Tex.",
        "TEXAS WESTERN": "W.D. Tex.",
        "ARKANSAS EASTERN": "E.D. Ark.",
        "ARKANSAS WESTERN": "W.D. Ark.",
        "MISSOURI EASTERN": "E.D. Mo.",
        "MISSOURI WESTERN": "W.D. Mo.",
        "IOWA NORTHERN": "N.D. Iowa",
        "IOWA SOUTHERN": "S.D. Iowa",
        "MINNESOTA": "D. Minn.",
        "NEBRASKA": "D. Neb.",
        "NORTH DAKOTA": "D.N.D.",
        "SOUTH DAKOTA": "D.S.D.",
        "MONTANA": "D. Mont.",
        "IDAHO": "D. Idaho",
        "NEVADA": "D. Nev.",
        "ARIZONA": "D. Ariz.",
        "ALASKA": "D. Alaska",
        "HAWAII": "D. Haw.",
        "OREGON": "D. Or.",
        "WASHINGTON EASTERN": "E.D. Wash.",
        "WASHINGTON WESTERN": "W.D. Wash.",
        "GUAM": "D. Guam",
        "NORTHERN MARIANA ISLANDS": "D. N. Mar. I.",
        "CALIFORNIA NORTHERN": "N.D. Cal.",
        "CALIFORNIA EASTERN": "E.D. Cal.",
        "CALIFORNIA CENTRAL": "C.D. Cal.",
        "CALIFORNIA SOUTHERN": "S.D. Cal.",
        "COLORADO": "D. Colo.",
        "KANSAS": "D. Kan.",
        "NEW MEXICO": "D.N.M.",
        "OKLAHOMA EASTERN": "E.D. Okla.",
        "OKLAHOMA NORTHERN": "N.D. Okla.",
        "OKLAHOMA WESTERN": "W.D. Okla.",
        "UTAH": "D. Utah",
        "WYOMING": "D. Wyo.",
        "KENTUCKY EASTERN": "E.D. Ky.",
        "KENTUCKY WESTERN": "W.D. Ky.",
        "TENNESSEE EASTERN": "E.D. Tenn.",
        "TENNESSEE MIDDLE": "M.D. Tenn.",
        "TENNESSEE WESTERN": "W.D. Tenn.",
        "OHIO NORTHERN": "N.D. Ohio",
        "OHIO SOUTHERN": "S.D. Ohio",
        "MICHIGAN EASTERN": "E.D. Mich.",
        "MICHIGAN WESTERN": "W.D. Mich.",
        "ILLINOIS NORTHERN": "N.D. Ill.",
        "ILLINOIS SOUTHERN": "S.D. Ill.",
        "ILLINOIS CENTRAL": "C.D. Ill.",
        "INDIANA NORTHERN": "N.D. Ind.",
        "INDIANA SOUTHERN": "S.D. Ind.",
        "WISCONSIN EASTERN": "E.D. Wis.",
        "WISCONSIN WESTERN": "W.D. Wis.",
    }

    name_upper = name.upper().strip()
    return mappings.get(name_upper, name_upper)


# Nature of suit category labels
NATURE_OF_SUIT_LABELS = [
    "A-Social Security", "B-Personal Injury/Product Liability", "C-Prisoner Petitions",
    "D-Forfeitures and Penalties", "E-Real Property", "F-Labor Suits",
    "G-Contracts", "H-Torts (other)", "I-Intellectual Property",
    "J-Civil Rights", "K-Immigration", "L-Other Statutes",
]

CRIMINAL_OFFENSE_LABELS = [
    "A-Marijuana", "B-All Other Drugs", "C-Immigration",
    "D-Firearms and Explosives", "E-Fraud", "F-Violent Offenses",
    "G-Sex Offenses", "H-Forgery and Counterfeiting", "I-Other",
    "J-Regulatory", "K-Prohibition", "L-Other",
]


def parse_district_table(table, nature_table):
    """Parse a district's main caseload table and nature of suit table."""
    if not table or len(table) < 2:
        return None

    district_name = extract_district_from_table(table)
    if not district_name:
        return None

    court = map_district_name_to_court(district_name)
    data = {"district_name": district_name, "court": court}

    # The last data column is the most recent year (2026)
    # Column indices: 0-3 are labels, 4-9 are data (2021-2026)
    # So index 9 is 2026 data
    LATEST_COL = 9

    def get_val(row, col=LATEST_COL):
        if row and len(row) > col:
            return parse_number(row[col])
        return None

    # Parse rows by looking at label content
    for row in table:
        if not row:
            continue
        label = " ".join(str(c) for c in row[:4] if c).strip().lower()

        # Filings (overall)
        if "filings" in label and "percent" not in label and "civil" not in label and "criminal" not in label and "action" not in label:
            data["filings_total"] = get_val(row)
        elif "terminations" in label and "per judgeship" not in label:
            data["terminations_total"] = get_val(row)
        elif "pending" in label and "per judgeship" not in label and "cases" not in label:
            data["pending_total"] = get_val(row)
        elif "number of judgeships" in label:
            data["judgeships"] = get_val(row)
        elif "vacant judgeship" in label:
            data["vacant_months"] = get_val(row)
        elif "civil" in label and "filings" not in label and "per judgeship" not in label:
            # This is "Actions per Judgeship - Filings - Civil"
            data["civil_per_judgeship"] = get_val(row)
        elif "criminal" in label and "felony" in label and "filings" not in label and "disposition" not in label:
            data["criminal_per_judgeship"] = get_val(row)
        elif "supervised" in label and "release" in label:
            data["supervised_release_per_judgeship"] = get_val(row)
        elif "pending cases" in label and "²" in label:
            data["pending_per_judgeship"] = get_val(row)
        elif "weighted filings" in label:
            data["weighted_filings_per_judgeship"] = get_val(row)
        elif "terminations" in label and "per judgeship" not in label and "267" not in str(row):
            # This might be the per-judgeship terminations (different from overall)
            pass
        elif "trials completed" in label:
            data["trials_completed"] = get_val(row)
        elif "felony" in label and ("from filing" in label or "disposition" in label):
            data["median_criminal_months"] = get_val(row)
        elif "civil" in label and "²" in label and "median" in label.lower() or "civil" in label and "months" in label:
            data["median_civil_months"] = get_val(row)
        elif "from filing to trial" in label:
            data["median_civil_to_trial_months"] = get_val(row)
        elif "over 3 years" in label:
            data["civil_cases_over_3_years"] = get_val(row)

    # Parse nature of suit table
    if nature_table and len(nature_table) >= 4:
        civil_row = None
        criminal_row = None
        for row in nature_table:
            if row and len(row) > 0:
                label = str(row[0]).strip().lower()
                if label.startswith("civil"):
                    civil_row = row
                elif label.startswith("criminal"):
                    criminal_row = row

        if civil_row and len(civil_row) >= 14:
            data["civil_nature_of_suit"] = [parse_number(c) for c in civil_row[1:14]]
        if criminal_row and len(criminal_row) >= 14:
            data["criminal_offense"] = [parse_number(c) for c in criminal_row[1:14]]

    return data


def main():
    print("Parsing district profiles PDF with table extraction...")
    all_districts = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for i in range(1, len(pdf.pages)):  # Skip page 1 (national summary)
            page = pdf.pages[i]
            tables = page.extract_tables()

            if len(tables) < 2:
                continue

            # Table 0 is the combined text, Table 1 is the main caseload table
            # Table 3 is the nature of suit table
            main_table = None
            nature_table = None

            for table in tables:
                if not table or len(table) < 2:
                    continue
                first_row = table[0]
                if first_row and first_row[0]:
                    first_cell = str(first_row[0]).lower()
                    if "judicial caseload profile" in first_cell or "district of" in first_cell or "overall" in first_cell:
                        if "caseload" in first_cell:
                            main_table = table
                    if "nature of suit" in first_cell:
                        nature_table = table

            # If we couldn't find by header, try table index 1 (main) and 3 (nature)
            if not main_table and len(tables) >= 2:
                for table in tables[1:]:
                    if table and len(table) > 5 and len(table[0]) > 3:
                        # Check if it looks like a caseload table
                        for row in table:
                            if row and row[0] and "filings" in str(row[0]).lower():
                                main_table = table
                                break
                        if main_table:
                            break

            if not main_table:
                continue

            # Find nature table
            if not nature_table:
                for table in tables:
                    if table and len(table) >= 4:
                        first_cell = str(table[0][0]).lower() if table[0] else ""
                        if "nature" in first_cell or "type of" in first_cell:
                            nature_table = table
                            break

            data = parse_district_table(main_table, nature_table)
            if data and data.get("court"):
                all_districts.append(data)
                if i <= 5 or i % 10 == 0:
                    print(f"  Page {i}: {data['district_name']} -> {data['court']}")

    print(f"\nParsed {len(all_districts)} districts")

    # Save as JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_districts, f, indent=2)
    print(f"Saved {OUTPUT_JSON}")

    # Print sample
    print("\n=== SAMPLE DATA ===")
    for d in all_districts[:5]:
        print(f"  {d['district_name']} ({d['court']}):")
        for k, v in d.items():
            if k not in ("district_name", "court") and v is not None:
                if isinstance(v, list):
                    print(f"    {k}: {v[:5]}...")
                else:
                    print(f"    {k}: {v}")
        print()


if __name__ == "__main__":
    main()