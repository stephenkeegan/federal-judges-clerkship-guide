#!/usr/bin/env python3
"""Comprehensive CourtListener scraper for federal judges.

Fetches biographical data, education, clerkships, opinions, and career history
from CourtListener's REST API v4.
"""

import json
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

import pandas as pd


BASE_URL = "https://www.courtlistener.com/api/rest/v4"
HEADERS = {"User-Agent": "judges-clerkship-guide/1.0 (https://github.com/stephenkeegan/federal-judges-clerkship-guide)"}


def fetch_json(url: str) -> Optional[Dict]:
    """Fetch JSON from URL with error handling."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # API requires auth - skip silently, will use fallback
            return None
        print(f"  HTTP Error {e.code}: {url}")
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def search_people(judge_name: str) -> List[Dict]:
    """Search CourtListener people API for judge matches."""
    q = urllib.parse.quote(judge_name)
    url = f"{BASE_URL}/people/?name={q}&page_size=10"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("results", [])


def fetch_person_detail(person_id: int) -> Optional[Dict]:
    """Fetch full person detail including bio, education, clerkships."""
    url = f"{BASE_URL}/people/{person_id}/"
    return fetch_json(url)


def fetch_opinions(judge_name: str, max_pages: int = 3) -> List[Dict]:
    """Fetch opinions authored by judge."""
    q = urllib.parse.quote(judge_name)
    all_results = []
    page = 1
    while page <= max_pages:
        url = f"{BASE_URL}/opinions/?author={q}&order_by=-date_filed&page_size=100&page={page}"
        data = fetch_json(url)
        if not data:
            break
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        if not data.get("next"):
            break
        page += 1
        time.sleep(0.2)
    return all_results


def extract_clerkships(person: Dict) -> List[Dict]:
    """Extract clerkship history from person data."""
    clerkships = []
    # CourtListener stores clerkships in 'clerkships' field
    for c in person.get("clerkships", []):
        clerkships.append({
            "court": c.get("court", ""),
            "judge": c.get("judge", ""),
            "year_start": c.get("year_start", ""),
            "year_end": c.get("year_end", ""),
            "type": c.get("type", ""),
        })
    return clerkships


def extract_education(person: Dict) -> List[Dict]:
    """Extract education history from person data."""
    education = []
    for e in person.get("education", []):
        education.append({
            "school": e.get("school", ""),
            "degree": e.get("degree", ""),
            "year": e.get("year", ""),
        })
    return education


def extract_positions(person: Dict) -> List[Dict]:
    """Extract career positions from person data."""
    positions = []
    for p in person.get("positions", []):
        positions.append({
            "title": p.get("title", ""),
            "organization": p.get("organization", ""),
            "year_start": p.get("year_start", ""),
            "year_end": p.get("year_end", ""),
        })
    return positions


def process_judge(judge_name: str, court: str = "", duty_station: str = "") -> Dict[str, Any]:
    """Process a single judge through CourtListener API."""
    print(f"Processing: {judge_name} ({court})")
    
    people = search_people(judge_name)
    if not people:
        return {"Judge": judge_name, "CL_Found": False}
    
    # Try to find best match - prefer exact name match with court alignment
    best_match = None
    for p in people:
        # Score matches
        score = 0
        p_name = p.get("name_full", "").lower()
        if judge_name.lower() in p_name or p_name in judge_name.lower():
            score += 10
        # Check if court matches
        for pos in p.get("positions", []):
            org = pos.get("organization", "").lower()
            if court.lower() in org or (duty_station and duty_station.lower() in org):
                score += 5
        if score > (best_match[1] if best_match else 0):
            best_match = (p, score)
    
    if not best_match or best_match[1] < 5:
        # No confident match
        return {"Judge": judge_name, "CL_Found": False, "CL_Match_Score": 0}
    
    person = best_match[0]
    person_id = person.get("id")
    
    # Fetch full detail
    detail = fetch_person_detail(person_id) if person_id else person
    if not detail:
        return {"Judge": judge_name, "CL_Found": False}
    
    time.sleep(0.3)  # Rate limiting
    
    # Fetch opinions
    opinions = fetch_opinions(judge_name)
    
    # Build comprehensive record
    clerkships = extract_clerkships(detail)
    education = extract_education(detail)
    positions = extract_positions(detail)
    
    record = {
        "Judge": judge_name,
        "CL_Found": True,
        "CL_Person_ID": person_id,
        "CL_Name_Full": detail.get("name_full", ""),
        "CL_Date_Birth": detail.get("date_birth", ""),
        "CL_Date_Death": detail.get("date_death", ""),
        "CL_Bio": detail.get("bio", "")[:5000] if detail.get("bio") else "",
        "CL_FJC_ID": detail.get("fjc_id", ""),
        "CL_Wikipedia": detail.get("wikipedia", ""),
        "CL_Opinion_Count": len(opinions),
        "CL_Recent_Opinion_1": opinions[0].get("case_name", "") if len(opinions) > 0 else "",
        "CL_Recent_Opinion_1_Date": opinions[0].get("date_filed", "") if len(opinions) > 0 else "",
        "CL_Recent_Opinion_2": opinions[1].get("case_name", "") if len(opinions) > 1 else "",
        "CL_Recent_Opinion_2_Date": opinions[1].get("date_filed", "") if len(opinions) > 1 else "",
        "CL_Recent_Opinion_3": opinions[2].get("case_name", "") if len(opinions) > 2 else "",
        "CL_Recent_Opinion_3_Date": opinions[2].get("date_filed", "") if len(opinions) > 2 else "",
        "CL_Clerkships": json.dumps(clerkships),
        "CL_Education": json.dumps(education),
        "CL_Positions": json.dumps(positions),
    }
    
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
        court = row.get("Court [Note 2]", "") if "Court [Note 2]" in row else row.get("Circuit", "")
        duty_station = row.get("Duty Station", "")
        
        record = process_judge(name, court, duty_station)
        results.append(record)
    
    # Save comprehensive CSV
    out_df = pd.DataFrame(results)
    out_df.to_csv("courtlistener_comprehensive.csv", index=False)
    print(f"Saved {len(out_df)} records to courtlistener_comprehensive.csv")
    
    # Summary
    found = out_df["CL_Found"].sum()
    print(f"Found on CourtListener: {found} / {len(out_df)}")


if __name__ == "__main__":
    main()