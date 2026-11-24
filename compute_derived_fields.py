"""
Compute derived fields from existing judge data.

Fields computed:
- Age (from Born year)
- Years on bench (from Active Term start year)
- Years as chief judge (from Chief Term)
- Is chief judge (boolean)
- Is senior judge (from Senior Term or Title)
- Confirmation year (parsed from various date formats)
- Years since confirmation
- Years in private practice (from Wikipedia summary, if extractable)
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime

CURRENT_YEAR = 2026


def parse_term_year(term_str):
    """Parse start and end years from Active Term / Chief Term strings.

    Examples:
        "1983 2007" -> (1983, 2007)
        "2020 present" -> (2020, None)  # None = still active
        "1983 – 2007" -> (1983, 2007)
        "2019–present" -> (2019, None)
        "2005–2012; 2018–present" -> (2005, None)  # take earliest start, latest status
    """
    if pd.isna(term_str) or str(term_str).strip() in ("", "nan", "None"):
        return (None, None)

    term_str = str(term_str).strip()

    # Find all 4-digit years
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', term_str)
    if not years:
        return (None, None)

    years = [int(y) for y in years]
    start = min(years)

    # Check if "present" appears
    if "present" in term_str.lower():
        end = None  # still active
    else:
        end = max(years)

    return (start, end)


def compute_years_on_bench(active_term):
    """Years on bench = current_year - start_year."""
    start, end = parse_term_year(active_term)
    if start is None:
        return None
    if end is not None:
        return end - start
    return CURRENT_YEAR - start


def compute_age(born):
    """Age = current_year - born_year."""
    if pd.isna(born) or str(born).strip() in ("", "nan", "None"):
        return None
    try:
        born_year = int(float(born))
        return CURRENT_YEAR - born_year
    except (ValueError, TypeError):
        return None


def compute_years_as_chief(chief_term):
    """Years as chief judge."""
    if pd.isna(chief_term) or str(chief_term).strip() in ("", "nan", "None"):
        return None
    start, end = parse_term_year(chief_term)
    if start is None:
        return None
    if end is not None:
        return end - start
    return CURRENT_YEAR - start


def is_chief(chief_term):
    """Is this judge a chief judge?"""
    if pd.isna(chief_term) or str(chief_term).strip() in ("", "nan", "None"):
        return False
    return True


def is_senior(senior_term, title):
    """Is this judge a senior judge?"""
    if pd.notna(senior_term) and str(senior_term).strip() not in ("", "nan", "None"):
        return True
    if pd.notna(title) and "senior" in str(title).lower():
        return True
    return False


def parse_confirmation_year(conf_date):
    """Parse confirmation year from various date formats.

    Examples:
        "04-Feb-26" -> 2026
        "November 18, 2025" -> 2025
        "2019" -> 2019
        "2020" -> 2020
    """
    if pd.isna(conf_date) or str(conf_date).strip() in ("", "nan", "None"):
        return None
    conf_str = str(conf_date).strip()
    
    # Try various formats
    # "04-Feb-26" -> last 2 digits, assume 20xx
    m = re.match(r'\d{2}-[A-Za-z]{3}-(\d{2})', conf_str)
    if m:
        year = int(m.group(1))
        return 2000 + year if year < 50 else 1900 + year

    # "November 18, 2025" or "Nov 18, 2025"
    m = re.search(r'\b(19\d{2}|20\d{2})\b', conf_str)
    if m:
        return int(m.group(1))

    return None


def compute_years_since_confirmation(conf_date):
    """Years since confirmation."""
    year = parse_confirmation_year(conf_date)
    if year is None:
        return None
    return CURRENT_YEAR - year


def extract_court_type(title):
    """Determine court type from title."""
    if pd.isna(title):
        return None
    title_lower = str(title).lower()
    if "district" in title_lower or "district judge" in title_lower:
        return "district"
    if "circuit" in title_lower or "appeals" in title_lower or "appellate" in title_lower:
        return "circuit"
    if "supreme" in title_lower:
        return "supreme"
    if "bankruptcy" in title_lower:
        return "bankruptcy"
    if "magistrate" in title_lower:
        return "magistrate"
    return None


def extract_circuit(court_str):
    """Derive circuit from court abbreviation.
    
    Examples:
        "N.D. Tex." -> "5th Circuit"
        "S.D.N.Y." -> "2nd Circuit"
        "D. Alaska" -> "9th Circuit"
        "D.D.C." -> "D.C. Circuit"
    """
    if pd.isna(court_str) or str(court_str).strip() in ("", "nan", "None"):
        return None
    court = str(court_str).strip()

    # Map state/district abbreviations to circuits
    circuit_map = {
        # 1st Circuit
        "D. Me.": "1st", "D.N.H.": "1st", "D.R.I.": "1st", "D. Mass.": "1st", "D.P.R.": "1st",
        # 2nd Circuit
        "D. Conn.": "2nd", "E.D.N.Y.": "2nd", "N.D.N.Y.": "2nd", "W.D.N.Y.": "2nd", "S.D.N.Y.": "2nd", "D. Vt.": "2nd",
        # 3rd Circuit
        "D. Del.": "3rd", "D.N.J.": "3rd", "E.D. Pa.": "3rd", "M.D. Pa.": "3rd", "W.D. Pa.": "3rd", "D.V.I.": "3rd",
        # 4th Circuit
        "D. Md.": "4th", "E.D.N.C.": "4th", "M.D.N.C.": "4th", "W.D.N.C.": "4th", "D.S.C.": "4th", "E.D. Va.": "4th", "W.D. Va.": "4th", "N.D. W. Va.": "4th", "S.D. W. Va.": "4th",
        # 5th Circuit
        "E.D. La.": "5th", "M.D. La.": "5th", "W.D. La.": "5th", "N.D. Miss.": "5th", "S.D. Miss.": "5th", "E.D. Tex.": "5th", "N.D. Tex.": "5th", "S.D. Tex.": "5th", "W.D. Tex.": "5th",
        # 6th Circuit
        "E.D. Ky.": "6th", "W.D. Ky.": "6th", "E.D. Mich.": "6th", "W.D. Mich.": "6th", "N.D. Ohio": "6th", "S.D. Ohio": "6th", "E.D. Tenn.": "6th", "M.D. Tenn.": "6th", "W.D. Tenn.": "6th",
        # 7th Circuit
        "C.D. Ill.": "7th", "N.D. Ill.": "7th", "S.D. Ill.": "7th", "N.D. Ind.": "7th", "S.D. Ind.": "7th", "E.D. Wis.": "7th", "W.D. Wis.": "7th",
        # 8th Circuit
        "E.D. Ark.": "8th", "W.D. Ark.": "8th", "N.D. Iowa": "8th", "S.D. Iowa": "8th", "D. Minn.": "8th", "E.D. Mo.": "8th", "W.D. Mo.": "8th", "D. Neb.": "8th", "D.N.D.": "8th", "D.S.D.": "8th",
        # 9th Circuit
        "D. Alaska": "9th", "D. Ariz.": "9th", "D. Haw.": "9th", "D. Idaho": "9th", "D. Mont.": "9th", "D. Nev.": "9th", "D.N. Cal.": "9th", "E.D. Cal.": "9th", "C.D. Cal.": "9th", "S.D. Cal.": "9th", "D. Or.": "9th", "E.D. Wash.": "9th", "W.D. Wash.": "9th", "D. Guam": "9th", "D. N. Mar. I.": "9th",
        # 10th Circuit
        "D. Colo.": "10th", "D. Kan.": "10th", "D.N.M.": "10th", "E.D. Okla.": "10th", "N.D. Okla.": "10th", "W.D. Okla.": "10th", "D. Utah": "10th", "D. Wyo.": "10th",
        # 11th Circuit
        "M.D. Ala.": "11th", "N.D. Ala.": "11th", "S.D. Ala.": "11th", "M.D. Fla.": "11th", "N.D. Fla.": "11th", "S.D. Fla.": "11th", "N.D. Ga.": "11th", "M.D. Ga.": "11th", "S.D. Ga.": "11th",
        # D.C. Circuit
        "D.D.C.": "D.C.",
    }

    # Check exact match
    if court in circuit_map:
        return circuit_map[court] + " Circuit" if circuit_map[court] != "D.C." else "D.C. Circuit"

    # Try partial match
    for key, val in circuit_map.items():
        if key.lower() in court.lower() or court.lower() in key.lower():
            return val + " Circuit" if val != "D.C." else "D.C. Circuit"

    return None


def main():
    comp = pd.read_csv("judges_unified_comprehensive.csv")

    # Compute derived fields
    comp["Age"] = comp["Born"].apply(compute_age)
    comp["Years on Bench"] = comp["Active Term"].apply(compute_years_on_bench)
    comp["Years as Chief"] = comp["Chief Term"].apply(compute_years_as_chief)
    comp["Is Chief"] = comp["Chief Term"].apply(is_chief)
    comp["Is Senior"] = comp.apply(lambda r: is_senior(r.get("Senior Term"), r.get("Title")), axis=1)
    comp["Confirmation Year"] = comp["Confirmation Date"].apply(parse_confirmation_year)
    comp["Years Since Confirmation"] = comp["Confirmation Date"].apply(compute_years_since_confirmation)
    comp["Court Type"] = comp["Title"].apply(extract_court_type)

    # Derive circuit from court string
    if "Court" in comp.columns:
        comp["Derived Circuit"] = comp["Court"].apply(extract_circuit)
    else:
        comp["Derived Circuit"] = None

    # Fill missing Circuit column
    if "Circuit" not in comp.columns:
        comp["Circuit"] = comp["Derived Circuit"]
    else:
        comp["Circuit"] = comp["Circuit"].fillna(comp["Derived Circuit"])

    # Stats
    print("=== DERIVED FIELD COVERAGE ===")
    for col in ["Age", "Years on Bench", "Years as Chief", "Is Chief", "Is Senior", "Confirmation Year", "Years Since Confirmation", "Court Type", "Derived Circuit"]:
        non_null = comp[col].notna() & (comp[col].astype(str).str.strip() != "")
        pct = 100 * non_null.sum() / len(comp)
        print(f"  {col:25s} {non_null.sum():5d}/{len(comp)} ({pct:.1f}%)")

    print()
    print("=== SAMPLE ===")
    for name in ["Amit Mehta", "Aileen Cannon", "A. Joe Fish", "Ada Brown", "Aaron C. Peterson"]:
        row = comp[comp["Judge"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}: age={r['Age']}, years_bench={r['Years on Bench']}, chief={r['Is Chief']}, senior={r['Is Senior']}, circuit={r['Derived Circuit']}")

    # Save
    comp.to_csv("judges_unified_comprehensive.csv", index=False)
    print("\nSaved judges_unified_comprehensive.csv")


if __name__ == "__main__":
    main()