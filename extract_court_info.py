"""
Extract and normalize court/district/circuit information from Wikipedia leads
and duty stations.

Fills in Court, District, and Circuit columns in the unified CSV.
"""

import pandas as pd
import numpy as np
import json
import re
from fetch_full_articles import parse_wikitext_sections, strip_wikitext_markup

WIKITEXT_CACHE = "wikitext_cache.json"


# Map full court names to standard abbreviations
COURT_ABBREVIATIONS = {
    # District courts
    "Northern District of Texas": "N.D. Tex.",
    "Southern District of Texas": "S.D. Tex.",
    "Eastern District of Texas": "E.D. Tex.",
    "Western District of Texas": "W.D. Tex.",
    "Northern District of California": "N.D. Cal.",
    "Southern District of California": "S.D. Cal.",
    "Eastern District of California": "E.D. Cal.",
    "Central District of California": "C.D. Cal.",
    "Northern District of New York": "N.D.N.Y.",
    "Southern District of New York": "S.D.N.Y.",
    "Eastern District of New York": "E.D.N.Y.",
    "Western District of New York": "W.D.N.Y.",
    "Northern District of Illinois": "N.D. Ill.",
    "Southern District of Illinois": "S.D. Ill.",
    "Central District of Illinois": "C.D. Ill.",
    "Northern District of Ohio": "N.D. Ohio",
    "Southern District of Ohio": "S.D. Ohio",
    "Northern District of Georgia": "N.D. Ga.",
    "Middle District of Georgia": "M.D. Ga.",
    "Southern District of Georgia": "S.D. Ga.",
    "Northern District of Florida": "N.D. Fla.",
    "Middle District of Florida": "M.D. Fla.",
    "Southern District of Florida": "S.D. Fla.",
    "Eastern District of Virginia": "E.D. Va.",
    "Western District of Virginia": "W.D. Va.",
    "Eastern District of Pennsylvania": "E.D. Pa.",
    "Middle District of Pennsylvania": "M.D. Pa.",
    "Western District of Pennsylvania": "W.D. Pa.",
    "Eastern District of Michigan": "E.D. Mich.",
    "Western District of Michigan": "W.D. Mich.",
    "Northern District of Iowa": "N.D. Iowa",
    "Southern District of Iowa": "S.D. Iowa",
    "Eastern District of Missouri": "E.D. Mo.",
    "Western District of Missouri": "W.D. Mo.",
    "District of Minnesota": "D. Minn.",
    "District of Nebraska": "D. Neb.",
    "District of North Dakota": "D.N.D.",
    "District of South Dakota": "D.S.D.",
    "District of Montana": "D. Mont.",
    "District of Idaho": "D. Idaho",
    "District of Nevada": "D. Nev.",
    "District of Arizona": "D. Ariz.",
    "District of Alaska": "D. Alaska",
    "District of Hawaii": "D. Haw.",
    "District of Oregon": "D. Or.",
    "Eastern District of Washington": "E.D. Wash.",
    "Western District of Washington": "W.D. Wash.",
    "District of Colorado": "D. Colo.",
    "District of Kansas": "D. Kan.",
    "District of New Mexico": "D.N.M.",
    "Eastern District of Oklahoma": "E.D. Okla.",
    "Northern District of Oklahoma": "N.D. Okla.",
    "Western District of Oklahoma": "W.D. Okla.",
    "District of Utah": "D. Utah",
    "District of Wyoming": "D. Wyo.",
    "Northern District of Alabama": "N.D. Ala.",
    "Middle District of Alabama": "M.D. Ala.",
    "Southern District of Alabama": "S.D. Ala.",
    "Northern District of Mississippi": "N.D. Miss.",
    "Southern District of Mississippi": "S.D. Miss.",
    "Eastern District of Louisiana": "E.D. La.",
    "Middle District of Louisiana": "M.D. La.",
    "Western District of Louisiana": "W.D. La.",
    "Eastern District of Arkansas": "E.D. Ark.",
    "Western District of Arkansas": "W.D. Ark.",
    "District of Puerto Rico": "D.P.R.",
    "District of District of Columbia": "D.D.C.",
    "District of Columbia": "D.D.C.",
    "Eastern District of North Carolina": "E.D.N.C.",
    "Middle District of North Carolina": "M.D.N.C.",
    "Western District of North Carolina": "W.D.N.C.",
    "District of South Carolina": "D.S.C.",
    "District of Maryland": "D. Md.",
    "District of Delaware": "D. Del.",
    "District of New Jersey": "D.N.J.",
    "District of Connecticut": "D. Conn.",
    "District of Vermont": "D. Vt.",
    "District of Maine": "D. Me.",
    "District of New Hampshire": "D.N.H.",
    "District of Rhode Island": "D.R.I.",
    "District of Massachusetts": "D. Mass.",
    "Eastern District of Kentucky": "E.D. Ky.",
    "Western District of Kentucky": "W.D. Ky.",
    "Eastern District of Tennessee": "E.D. Tenn.",
    "Middle District of Tennessee": "M.D. Tenn.",
    "Western District of Tennessee": "W.D. Tenn.",
    "Northern District of West Virginia": "N.D. W. Va.",
    "Southern District of West Virginia": "S.D. W. Va.",
    "Northern District of Indiana": "N.D. Ind.",
    "Southern District of Indiana": "S.D. Ind.",
    "Eastern District of Wisconsin": "E.D. Wis.",
    "Western District of Wisconsin": "W.D. Wis.",
    # Circuit courts
    "First Circuit": "1st Cir.",
    "Second Circuit": "2nd Cir.",
    "Third Circuit": "3rd Cir.",
    "Fourth Circuit": "4th Cir.",
    "Fifth Circuit": "5th Cir.",
    "Sixth Circuit": "6th Cir.",
    "Seventh Circuit": "7th Cir.",
    "Eighth Circuit": "8th Cir.",
    "Ninth Circuit": "9th Cir.",
    "Tenth Circuit": "10th Cir.",
    "Eleventh Circuit": "11th Cir.",
    "D.C. Circuit": "D.C. Cir.",
    "Federal Circuit": "Fed. Cir.",
}


# Circuit mapping from district court abbreviations
DISTRICT_TO_CIRCUIT = {
    # 1st Circuit
    "D. Me.": "1st", "D.N.H.": "1st", "D.R.I.": "1st", "D. Mass.": "1st", "D.P.R.": "1st",
    # 2nd Circuit
    "D. Conn.": "2nd", "E.D.N.Y.": "2nd", "N.D.N.Y.": "2nd", "W.D.N.Y.": "2nd", "S.D.N.Y.": "2nd", "D. Vt.": "2nd",
    # 3rd Circuit
    "D. Del.": "3rd", "D.N.J.": "3rd", "E.D. Pa.": "3rd", "M.D. Pa.": "3rd", "W.D. Pa.": "3rd",
    # 4th Circuit
    "D. Md.": "4th", "E.D.N.C.": "4th", "M.D.N.C.": "4th", "W.D.N.C.": "4th", "D.S.C.": "4th",
    "E.D. Va.": "4th", "W.D. Va.": "4th", "N.D. W. Va.": "4th", "S.D. W. Va.": "4th",
    # 5th Circuit
    "E.D. La.": "5th", "M.D. La.": "5th", "W.D. La.": "5th", "N.D. Miss.": "5th", "S.D. Miss.": "5th",
    "E.D. Tex.": "5th", "N.D. Tex.": "5th", "S.D. Tex.": "5th", "W.D. Tex.": "5th",
    # 6th Circuit
    "E.D. Ky.": "6th", "W.D. Ky.": "6th", "E.D. Mich.": "6th", "W.D. Mich.": "6th",
    "N.D. Ohio": "6th", "S.D. Ohio": "6th", "E.D. Tenn.": "6th", "M.D. Tenn.": "6th", "W.D. Tenn.": "6th",
    # 7th Circuit
    "C.D. Ill.": "7th", "N.D. Ill.": "7th", "S.D. Ill.": "7th", "N.D. Ind.": "7th", "S.D. Ind.": "7th",
    "E.D. Wis.": "7th", "W.D. Wis.": "7th",
    # 8th Circuit
    "E.D. Ark.": "8th", "W.D. Ark.": "8th", "N.D. Iowa": "8th", "S.D. Iowa": "8th", "D. Minn.": "8th",
    "E.D. Mo.": "8th", "W.D. Mo.": "8th", "D. Neb.": "8th", "D.N.D.": "8th", "D.S.D.": "8th",
    # 9th Circuit
    "D. Alaska": "9th", "D. Ariz.": "9th", "D. Haw.": "9th", "D. Idaho": "9th", "D. Mont.": "9th",
    "D. Nev.": "9th", "N.D. Cal.": "9th", "E.D. Cal.": "9th", "C.D. Cal.": "9th", "S.D. Cal.": "9th",
    "D. Or.": "9th", "E.D. Wash.": "9th", "W.D. Wash.": "9th",
    # 10th Circuit
    "D. Colo.": "10th", "D. Kan.": "10th", "D.N.M.": "10th", "E.D. Okla.": "10th",
    "N.D. Okla.": "10th", "W.D. Okla.": "10th", "D. Utah": "10th", "D. Wyo.": "10th",
    # 11th Circuit
    "M.D. Ala.": "11th", "N.D. Ala.": "11th", "S.D. Ala.": "11th", "M.D. Fla.": "11th",
    "N.D. Fla.": "11th", "S.D. Fla.": "11th", "N.D. Ga.": "11th", "M.D. Ga.": "11th", "S.D. Ga.": "11th",
    # D.C. Circuit
    "D.D.C.": "D.C.",
}


def extract_court_from_lead(lead_text):
    """Extract court abbreviation from Wikipedia lead text."""
    if not lead_text:
        return None, None

    # Check if it's a circuit judge
    circuit_match = re.search(r'United States Court of Appeals for the (\w+) Circuit', lead_text)
    if circuit_match:
        circuit_name = circuit_match.group(1)
        # Convert "First" -> "1st", etc.
        circuit_map = {
            "First": "1st Cir.", "Second": "2nd Cir.", "Third": "3rd Cir.",
            "Fourth": "4th Cir.", "Fifth": "5th Cir.", "Sixth": "6th Cir.",
            "Seventh": "7th Cir.", "Eighth": "8th Cir.", "Ninth": "9th Cir.",
            "Tenth": "10th Cir.", "Eleventh": "11th Cir.",
        }
        court = circuit_map.get(circuit_name, circuit_name + " Cir.")
        circuit = circuit_name + " Circuit"
        return court, ("circuit", circuit)

    # Check for D.C. Circuit
    if "D.C. Circuit" in lead_text or "District of Columbia Circuit" in lead_text:
        return "D.C. Cir.", ("circuit", "D.C. Circuit")

    # Check for Federal Circuit
    if "Federal Circuit" in lead_text:
        return "Fed. Cir.", ("circuit", "Federal Circuit")

    # District court: "United States District Court for the X District of Y"
    district_match = re.search(
        r'United States District Court for the\s+'
        r'(Northern|Southern|Eastern|Western|Middle|Central)?\s*'
        r'District of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        lead_text
    )
    if district_match:
        direction = district_match.group(1) or ""
        state = district_match.group(2)
        # Build full name
        if direction:
            full_name = f"{direction} District of {state}"
        else:
            full_name = f"District of {state}"

        # Handle special cases
        if state == "Columbia":
            full_name = "District of Columbia"
        if state == "Puerto Rico":
            full_name = "District of Puerto Rico"

        abbrev = COURT_ABBREVIATIONS.get(full_name)
        if abbrev:
            circuit = DISTRICT_TO_CIRCUIT.get(abbrev, "")
            circuit_str = f"{circuit} Circuit" if circuit else None
            return abbrev, ("district", circuit_str)

    # Single-district states: "District of Alaska", "District of Nevada"
    single_match = re.search(
        r'United States District Court for the\s+District of\s+([A-Z][a-z]+)',
        lead_text
    )
    if single_match:
        state = single_match.group(1)
        full_name = f"District of {state}"
        abbrev = COURT_ABBREVIATIONS.get(full_name)
        if abbrev:
            circuit = DISTRICT_TO_CIRCUIT.get(abbrev, "")
            circuit_str = f"{circuit} Circuit" if circuit else None
            return abbrev, ("district", circuit_str)

    return None, None


def derive_court_from_duty_station(duty_station, court_hint=None):
    """Try to derive court from duty station city name."""
    from courthouse_data import COURTHOUSE_COORDS

    if pd.isna(duty_station) or not duty_station or duty_station == "inactive":
        return None, None

    station_lower = duty_station.lower().strip()

    # Look for matching court in courthouse data
    for (city, court), coords in COURTHOUSE_COORDS.items():
        if city and station_lower in city.lower() or city.lower() in station_lower:
            if court:
                circuit = DISTRICT_TO_CIRCUIT.get(court, "")
                circuit_str = f"{circuit} Circuit" if circuit else None
                return court, ("district", circuit_str)

    return None, None


def main():
    comp = pd.read_csv("judges_unified_comprehensive.csv")
    cache = json.load(open(WIKITEXT_CACHE, "r", encoding="utf-8"))

    # Ensure columns are object type
    for col in ["Court", "District", "Circuit"]:
        comp[col] = comp[col].astype(object)

    updated = 0
    for idx, row in comp.iterrows():
        changed = False

        # Try Wikipedia lead first
        title = row.get("Wiki_Title", "")
        if pd.notna(title) and str(title).strip() not in ("", "nan", "None"):
            title = str(title).strip()
            wikitext = cache.get(title, "")
            if wikitext:
                sections = parse_wikitext_sections(wikitext)
                lead = strip_wikitext_markup(sections.get("Lead", ""))
                court, court_info = extract_court_from_lead(lead)
                if court:
                    if pd.isna(row["Court"]) or str(row["Court"]).strip() in ("", "nan", "None"):
                        comp.at[idx, "Court"] = court
                        changed = True
                    if court_info:
                        court_type, circuit = court_info
                        if court_type == "circuit":
                            if pd.isna(row["Circuit"]) or str(row["Circuit"]).strip() in ("", "nan", "None"):
                                comp.at[idx, "Circuit"] = circuit
                                changed = True
                        elif court_type == "district":
                            if circuit and (pd.isna(row["Circuit"]) or str(row["Circuit"]).strip() in ("", "nan", "None")):
                                comp.at[idx, "Circuit"] = circuit
                                changed = True
                            # Also set District column
                            if pd.isna(row["District"]) or str(row["District"]).strip() in ("", "nan", "None"):
                                comp.at[idx, "District"] = court
                                changed = True

        # If still no court, try duty station
        if pd.isna(row.get("Court", None)) or str(row.get("Court", "")).strip() in ("", "nan", "None"):
            court, court_info = derive_court_from_duty_station(row.get("Duty Station"))
            if court:
                comp.at[idx, "Court"] = court
                if court_info:
                    court_type, circuit = court_info
                    if circuit and (pd.isna(row["Circuit"]) or str(row["Circuit"]).strip() in ("", "nan", "None")):
                        comp.at[idx, "Circuit"] = circuit
                changed = True

        if changed:
            updated += 1

    print(f"Updated {updated} judges with court/circuit info")

    # Coverage
    print("\n=== COURT COVERAGE ===")
    for col in ["Court", "District", "Circuit"]:
        if col in comp.columns:
            non_null = comp[col].notna() & (comp[col].astype(str).str.strip() != "")
            pct = 100 * non_null.sum() / len(comp)
            print(f"  {col:25s} {non_null.sum():5d}/{len(comp)} ({pct:.1f}%)")

    # Samples
    print("\n=== SAMPLES ===")
    for name in ["Amit Mehta", "Aileen Cannon", "A. Joe Fish", "Anne Hwang", "Aaron C. Peterson"]:
        row = comp[comp["Judge"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}: Court={r.get('Court')}, Circuit={r.get('Circuit')}, District={r.get('District')}")

    comp.to_csv("judges_unified_comprehensive.csv", index=False)
    print("\nSaved")


if __name__ == "__main__":
    main()