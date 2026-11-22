#!/usr/bin/env python3
"""Merge all scraped data sources into a unified comprehensive judge dataset.

Combines:
- Pipeline base data (final_district_enriched.csv, final_appeals_enriched.csv)
- CourtListener comprehensive data
- Wikipedia comprehensive data  
- FJC comprehensive data
- OSCAR hiring data
"""

import json
import re
import pandas as pd


# Party derivation from helper_functions
PARTY_MAP = {
    'Trump': 'Republican',
    'Biden': 'Democrat',
    'Obama': 'Democrat',
    'George W. Bush': 'Republican',
    'G.W. Bush': 'Republican',
    'George_H._W._Bush': 'Republican',
    'G.H.W. Bush': 'Republican',
    'Bush HW': 'Republican',
    'Bush W': 'Republican',
    'Clinton': 'Democrat',
    'Clinton / G.W. Bush': 'Republican',
    'Reagan': 'Republican',
    'Carter': 'Democrat',
    'Nixon': 'Republican',
    'Kennedy': 'Democrat',
    'Lyndon B. Johnson': 'Democrat',
    'Johnson': 'Democrat',
    'Eisenhower': 'Republican',
    'Ford': 'Republican',
    'Harding': 'Republican',
    'Coolidge': 'Republican',
    'Hoover': 'Republican',
    'Roosevelt': 'Democrat',
    'Truman': 'Democrat',
}

def derive_party(appointed_by):
    """Map 'Appointed By' text to a political party."""
    if not isinstance(appointed_by, str):
        return 'Other'
    for pres, party in PARTY_MAP.items():
        if pres.lower() in appointed_by.lower():
            return party
    return 'Other'


def load_all_sources():
    """Load all CSV data sources."""
    sources = {}
    
    # Base pipeline data
    sources["district"] = pd.read_csv("final_district_enriched.csv")
    sources["appeals"] = pd.read_csv("final_appeals_enriched.csv")
    print(f"Base: {len(sources['district'])} district, {len(sources['appeals'])} appeals judges")
    
    # CourtListener
    try:
        sources["cl"] = pd.read_csv("courtlistener_comprehensive.csv")
        print(f"CourtListener: {len(sources['cl'])} records")
    except FileNotFoundError:
        sources["cl"] = pd.DataFrame()
        print("CourtListener: not found")
    
    # Wikipedia
    try:
        sources["wiki"] = pd.read_csv("wikipedia_comprehensive.csv")
        print(f"Wikipedia: {len(sources['wiki'])} records")
    except FileNotFoundError:
        sources["wiki"] = pd.DataFrame()
        print("Wikipedia: not found")
    
    # FJC
    try:
        sources["fjc"] = pd.read_csv("fjc_comprehensive.csv")
        print(f"FJC: {len(sources['fjc'])} records")
    except FileNotFoundError:
        sources["fjc"] = pd.DataFrame()
        print("FJC: not found")
    
    # OSCAR hiring (from existing pipeline)
    try:
        sources["oscar"] = pd.read_csv("oscar_master_listings.csv")
        print(f"OSCAR: raw listings loaded")
    except FileNotFoundError:
        sources["oscar"] = pd.DataFrame()
        print("OSCAR: not found")
    
    # Ballotpedia
    try:
        sources["ballotpedia"] = pd.read_csv("ballotpedia_data.csv")
        print(f"Ballotpedia: {len(sources['ballotpedia'])} records")
    except FileNotFoundError:
        sources["ballotpedia"] = pd.DataFrame()
        print("Ballotpedia: not found")
    
    # Justia
    try:
        sources["justia"] = pd.read_csv("justia_data.csv")
        print(f"Justia: {len(sources['justia'])} records")
    except FileNotFoundError:
        sources["justia"] = pd.DataFrame()
        print("Justia: not found")
    
    # Google Scholar
    try:
        sources["gscholar"] = pd.read_csv("gscholar_data.csv")
        print(f"Google Scholar: {len(sources['gscholar'])} records")
    except FileNotFoundError:
        sources["gscholar"] = pd.DataFrame()
        print("Google Scholar: not found")
    
    return sources


def normalize_judge_name(name: str) -> str:
    """Normalize judge name for matching."""
    if not isinstance(name, str):
        return ""
    name = name.strip()
    # Remove titles, suffixes
    name = re.sub(r'^(Hon\.|Judge|Justice|Magistrate|Bankruptcy)\s+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(Jr\.|Sr\.|II|III|IV)$', '', name, flags=re.IGNORECASE)
    # Normalize whitespace and punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def merge_on_name(df_base: pd.DataFrame, df_new: pd.DataFrame, prefix: str, 
                   base_name_col: str = "Judge", new_name_col: str = "Judge") -> pd.DataFrame:
    """Merge new data onto base using normalized name matching."""
    if df_new.empty:
        return df_base
    
    # Create normalized name columns
    df_base = df_base.copy()
    df_new = df_new.copy()
    
    df_base["_norm_name"] = df_base[base_name_col].apply(normalize_judge_name)
    df_new["_norm_name"] = df_new[new_name_col].apply(normalize_judge_name)
    
    # Drop duplicate columns from new (except Judge and _norm_name)
    new_cols = [c for c in df_new.columns if c not in df_base.columns or c in ["Judge", "_norm_name"]]
    df_new_subset = df_new[new_cols]
    
    # Merge
    merged = df_base.merge(df_new_subset, on="_norm_name", how="left", suffixes=("", f"_{prefix}"))
    
    # Clean up
    merged = merged.drop(columns=["_norm_name"])
    
    return merged


def extract_oscar_hiring(oscar_raw: pd.DataFrame) -> pd.DataFrame:
    """Parse OSCAR raw listings to extract hiring info per judge."""
    import io
    import csv
    import re
    
    hiring_records = []
    
    with open("oscar_master_listings.csv", "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    
    # Parse using the same logic as parse_oscar.py
    pattern = r'"([^"]+?)\s{2,}U\.S\.\s+(?:District|Court of Appeals|Bankruptcy|Federal Claims|International Trade|Tax)\s+Court\s{2,}([^"]+)"'
    matches = re.findall(pattern, raw)
    
    for name, duty_station in matches:
        name = name.strip()
        hiring_records.append({
            "Judge": name,
            "OSCAR_Duty_Station": duty_station.strip(),
            "OSCAR_Hiring": True,
        })
    
    # Also extract term info from the CSV rows
    reader = csv.reader(io.StringIO(raw))
    term_map = {}
    for row in reader:
        if len(row) < 3:
            continue
        col0 = row[0].strip().strip('"')
        if not col0 or '  U.S.' not in col0:
            continue
        parts = col0.split('  ')
        if len(parts) < 3:
            continue
        judge_name = parts[0].strip()
        term = row[2].strip() if len(row) > 2 else 'N/A'
        if judge_name not in term_map:
            term_map[judge_name] = term
    
    # Add terms
    for record in hiring_records:
        record["OSCAR_Term"] = term_map.get(record["Judge"], "N/A")
    
    return pd.DataFrame(hiring_records).drop_duplicates(subset=["Judge"])


def main():
    print("Loading all data sources...")
    sources = load_all_sources()
    
    # Extract OSCAR hiring data
    print("Extracting OSCAR hiring data...")
    oscar_hiring = extract_oscar_hiring(sources.get("oscar", pd.DataFrame()))
    print(f"OSCAR hiring records: {len(oscar_hiring)}")
    
    # Start with base data
    df_district = sources["district"].copy()
    df_appeals = sources["appeals"].copy()
    
    # Standardize column names
    df_district = df_district.rename(columns={
        "Court [Note 2]": "Court",
    })
    df_appeals = df_appeals.rename(columns={
        "Circuit": "Court",
    })
    
    df_base = pd.concat([df_district, df_appeals], ignore_index=True)
    print(f"Base judges: {len(df_base)}")
    
    # Derive Party from Appointed By
    df_base["Party"] = df_base["Appointed By"].apply(derive_party)
    
    # Add Hiring status from pipeline's existing data (if available)
    # Check if we have Hiring data in enriched CSVs
    if "Hiring" not in df_base.columns:
        df_base["Hiring"] = False
        df_base["Hiring Term"] = "N/A"
    
    # Merge CourtListener
    if not sources["cl"].empty:
        print("Merging CourtListener data...")
        df_base = merge_on_name(df_base, sources["cl"], "CL")
    
    # Merge Wikipedia
    if not sources["wiki"].empty:
        print("Merging Wikipedia data...")
        df_base = merge_on_name(df_base, sources["wiki"], "Wiki")
    
    # Merge FJC
    if not sources["fjc"].empty:
        print("Merging FJC data...")
        df_base = merge_on_name(df_base, sources["fjc"], "FJC")
    
    # Merge OSCAR hiring
    if not oscar_hiring.empty:
        print("Merging OSCAR hiring data...")
        df_base = merge_on_name(df_base, oscar_hiring, "OSCAR")
    
    # Merge Ballotpedia
    if "ballotpedia" in sources and not sources["ballotpedia"].empty:
        print("Merging Ballotpedia data...")
        df_base = merge_on_name(df_base, sources["ballotpedia"], "BP")
    
    # Merge Justia
    if "justia" in sources and not sources["justia"].empty:
        print("Merging Justia data...")
        df_base = merge_on_name(df_base, sources["justia"], "JU")
    
    # Merge Google Scholar
    if "gscholar" in sources and not sources["gscholar"].empty:
        print("Merging Google Scholar data...")
        df_base = merge_on_name(df_base, sources["gscholar"], "GS")
    
    # Ensure key columns exist
    key_cols = [
        "Judge", "Title", "Court", "Circuit", "District", "Duty Station",
        "Appointed By", "Born", "lat", "lng", "Party", "Hiring", "Hiring Term",
        "Wiki_Summary", "Wiki_Education", "Wiki_Clerkships", "Wiki_Career",
        "CL_Opinion_Count", "CL_Clerkships", "CL_Education", "CL_Bio",
        "FJC_Education", "FJC_Clerkships", "FJC_Federal_Judicial_Service",
        "FJC_Professional_Career", "OSCAR_Hiring", "OSCAR_Term",
        "BP_Ballotpedia", "JU_Justia Results", "GS_Scholar Results",
    ]
    
    for col in key_cols:
        if col not in df_base.columns:
            df_base[col] = ""
    
    # Also ensure source tracking columns
    for col in ["Wiki_Title", "Wiki_Found", "CL_Found", "FJC_Found", "FJC_URL"]:
        if col not in df_base.columns:
            df_base[col] = ""
    
    # Fill OSCAR_Hiring from merge
    if "OSCAR_Hiring" in df_base.columns:
        df_base["OSCAR_Hiring"] = df_base["OSCAR_Hiring"].fillna(False)
    
    # Reorder columns - put key info first
    first_cols = [
        "Judge", "Title", "Court", "Circuit", "District", "Duty Station",
        "Appointed By", "Born", "lat", "lng", "Party",
        "Hiring", "Hiring Term", "OSCAR_Hiring", "OSCAR_Term",
        "Wiki_Summary", "Wiki_Title", "Wiki_Found",
        "CL_Found", "CL_Opinion_Count",
        "FJC_Found", "FJC_URL",
        "BP_Ballotpedia", "JU_Justia Results", "GS_Scholar Results",
    ]
    
    # Only include first_cols that actually exist
    first_cols = [c for c in first_cols if c in df_base.columns]
    other_cols = [c for c in df_base.columns if c not in first_cols]
    df_base = df_base[first_cols + other_cols]
    
    # Save unified dataset
    output_path = "judges_unified_comprehensive.csv"
    df_base.to_csv(output_path, index=False)
    print(f"\nSaved unified dataset: {output_path}")
    print(f"Total judges: {len(df_base)}")
    print(f"Columns: {len(df_base.columns)}")
    
    # Also save a lean version for the web app
    lean_cols = [
        "Judge", "Title", "Court", "Circuit", "District", "Duty Station",
        "Appointed By", "Born", "lat", "lng", "Party",
        "Hiring", "Hiring Term", "OSCAR_Hiring", "OSCAR_Term",
        "Wiki_Summary", "Wiki_Title", "Wiki_Found",
        "CL_Found", "CL_Opinion_Count",
        "FJC_Found", "FJC_URL",
    ]
    lean_df = df_base[lean_cols].copy()
    lean_df.to_csv("judges_unified_lean.csv", index=False)
    print(f"Saved lean dataset: judges_unified_lean.csv")
    
    # Print coverage stats
    print(f"\nCoverage:")
    for col in ["Wiki_Found", "CL_Found", "FJC_Found", "OSCAR_Hiring"]:
        if col in df_base.columns:
            found = df_base[col].sum() if df_base[col].dtype == bool else (df_base[col] != "").sum()
            print(f"  {col}: {int(found)} / {len(df_base)}")


if __name__ == "__main__":
    import re
    main()