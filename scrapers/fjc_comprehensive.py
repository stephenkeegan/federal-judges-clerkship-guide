#!/usr/bin/env python3
"""FJC Biographical Directory scraper for federal judges.

The Federal Judicial Center (fjc.gov) maintains the authoritative biographical
directory of Article III judges. This scraper extracts comprehensive data.
"""

import re
import time
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List

import pandas as pd


BASE_URL = "https://www.fjc.gov"
SEARCH_URL = f"{BASE_URL}/history/judges/search"
HEADERS = {"User-Agent": "judges-clerkship-guide/1.0 (https://github.com/stephenkeegan/federal-judges-clerkship-guide)"}


def fetch_html(url: str) -> Optional[str]:
    """Fetch HTML content with error handling."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error: {e}")
        return None


def search_judge(judge_name: str) -> Optional[str]:
    """Search FJC for judge, return detail page URL if found."""
    params = urllib.parse.urlencode({"name": judge_name})
    url = f"{SEARCH_URL}?{params}"
    html = fetch_html(url)
    if not html:
        return None
    
    # Look for judge link in results
    # Pattern: /history/judges/<id>
    matches = re.findall(r'href="(/history/judges/\d+)"', html)
    if matches:
        return f"{BASE_URL}{matches[0]}"
    return None


def extract_bio_page(html: str) -> Dict[str, Any]:
    """Extract structured data from FJC judge bio page."""
    data = {}
    
    # Clean HTML
    text = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Extract key fields using patterns
    patterns = {
        "FJC_Born": r'Born[:\s]+([^,\n]+)',
        "FJC_Died": r'Died[:\s]+([^,\n]+)',
        "FJC_Birth_Place": r'Birth Place[:\s]+([^,\n]+)',
        "FJC_Education": r'Education[:\s]+([^,\n]+(?:\n[^,\n]+)*)',
        "FJC_Federal_Judicial_Service": r'Federal Judicial Service[:\s]+([^,\n]+(?:\n[^,\n]+)*)',
        "FJC_Professional_Career": r'Professional Career[:\s]+([^,\n]+(?:\n[^,\n]+)*)',
        "FJC_Clerkships": r'Law Clerk[:\s]+([^,\n]+(?:\n[^,\n]+)*)',
        "FJC_Military": r'Military Service[:\s]+([^,\n]+(?:\n[^,\n]+)*)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r'\s+', ' ', val)
            data[key] = val[:2000]
    
    # Also try to extract from structured definition lists
    dl_matches = re.findall(r'<dt[^>]*>([^<]+)</dt>\s*<dd[^>]*>([^<]*)</dd>', html)
    for dt, dd in dl_matches:
        key = dt.strip().replace(' ', '_').replace('-', '_')
        val = dd.strip()
        if val:
            data[f"FJC_{key}"] = val[:2000]
    
    return data


def process_judge_fjc(judge_name: str) -> Dict[str, Any]:
    """Process a single judge through FJC directory."""
    print(f"Processing: {judge_name}")
    
    # Search for judge
    detail_url = search_judge(judge_name)
    if not detail_url:
        return {"Judge": judge_name, "FJC_Found": False}
    
    # Fetch detail page
    html = fetch_html(detail_url)
    if not html:
        return {"Judge": judge_name, "FJC_Found": False, "FJC_URL": detail_url}
    
    time.sleep(0.3)  # Rate limit
    
    # Extract data
    bio_data = extract_bio_page(html)
    
    record = {
        "Judge": judge_name,
        "FJC_Found": True,
        "FJC_URL": detail_url,
    }
    record.update(bio_data)
    
    return record


def main():
    # Load judge list
    df_district = pd.read_csv("final_district_enriched.csv")
    df_appeals = pd.read_csv("final_appeals_enriched.csv")
    df = pd.concat([df_district, df_appeals], ignore_index=True)
    
    print(f"Total judges to process: {len(df)}")
    
    results = []
    for _, row in df.iterrows():
        name = row["Judge"]
        record = process_judge_fjc(name)
        results.append(record)
    
    out_df = pd.DataFrame(results)
    out_df.to_csv("fjc_comprehensive.csv", index=False)
    print(f"Saved {len(out_df)} records to fjc_comprehensive.csv")
    
    found = out_df["FJC_Found"].sum()
    print(f"Found on FJC: {found} / {len(out_df)}")


if __name__ == "__main__":
    main()