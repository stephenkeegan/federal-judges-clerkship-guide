#!/usr/bin/env python3
"""Enhanced Wikipedia scraper for federal judges.

Extracts comprehensive biographical data including education, clerkships,
military service, career history, notable cases, and more.
"""

import json
import re
import time
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List

import pandas as pd


WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "judges-clerkship-guide/1.0 (https://github.com/stephenkeegan/federal-judges-clerkship-guide)"}


def fetch_json(url: str) -> Optional[Dict]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  Error: {e}")
        return None


def search_page(title: str) -> Optional[str]:
    """Search for page title, return exact title if found."""
    url = f"{WIKI_API}?action=query&format=json&list=search&srsearch={urllib.parse.quote(title)}&srlimit=5"
    data = fetch_json(url)
    if not data:
        return None
    for result in data.get("query", {}).get("search", []):
        t = result["title"]
        # Prefer pages that look like judge bios (not list pages)
        if "list" not in t.lower() and "judge" not in t.lower():
            return t
    # Fallback: first result
    results = data.get("query", {}).get("search", [])
    return results[0]["title"] if results else None


def get_page_content(title: str) -> Optional[str]:
    """Get full page wikitext content."""
    url = f"{WIKI_API}?action=parse&format=json&page={urllib.parse.quote(title)}&prop=wikitext"
    data = fetch_json(url)
    if not data:
        return None
    wikitext_obj = data.get("parse", {}).get("wikitext", {})
    # Handle both string and dict responses
    if isinstance(wikitext_obj, dict):
        return wikitext_obj.get("*", "")
    return str(wikitext_obj) if wikitext_obj else ""


def get_page_sections(title: str) -> List[Dict]:
    """Get page sections for structured extraction."""
    url = f"{WIKI_API}?action=parse&format=json&page={urllib.parse.quote(title)}&prop=sections"
    data = fetch_json(url)
    if not data:
        return []
    return data.get("parse", {}).get("sections", [])


def extract_infobox(wikitext: str) -> Dict[str, str]:
    """Extract infobox fields from wikitext."""
    fields = {}
    # Find infobox template
    pattern = r'\{\{Infobox[^}]*\}\}'
    matches = re.findall(pattern, wikitext, re.DOTALL)
    for match in matches:
        # Extract key-value pairs
        for line in match.split('\n'):
            m = re.match(r'\|\s*([^=]+)\s*=\s*(.+)', line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                # Clean up
                val = re.sub(r'\{\{[^}]*\}\}', '', val)  # Remove nested templates
                val = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', val)  # Links
                val = re.sub(r'\[\[([^\]]+)\]\]', r'\1', val)
                val = re.sub(r"'''?", '', val)  # Bold/italic
                val = re.sub(r'<[^>]+>', '', val)  # HTML tags
                if key and val:
                    fields[key] = val[:500]
    return fields


def extract_education_section(wikitext: str) -> List[Dict]:
    """Extract education information from Education/Alma mater sections."""
    education = []
    # Look for education-related sections
    sections = re.findall(r'==\s*(Education|Alma mater|Early life and education)\s*==\n(.*?)(?=\n==|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
    for heading, content in sections:
        # Parse list items
        items = re.findall(r'^\s*[\*\-]\s*(.+)$', content, re.MULTILINE)
        for item in items:
            # Clean up
            item = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', item)
            item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', item)
            item = re.sub(r"'''?", '', item)
            item = item.strip()
            if item:
                education.append({"detail": item})
    return education


def extract_clerkships_section(wikitext: str) -> List[Dict]:
    """Extract clerkship information."""
    clerkships = []
    # Look for clerkship sections
    sections = re.findall(r'==\s*(Law clerk|Clerkship|Judicial clerk)\s*==\n(.*?)(?=\n==|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
    for heading, content in sections:
        items = re.findall(r'^\s*[\*\-]\s*(.+)$', content, re.MULTILINE)
        for item in items:
            item = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', item)
            item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', item)
            item = re.sub(r"'''?", '', item).strip()
            if item:
                clerkships.append({"detail": item})
    return clerkships


def extract_career_section(wikitext: str) -> List[Dict]:
    """Extract career/employment history."""
    career = []
    sections = re.findall(r'==\s*(Career|Professional career|Legal career|Early career)\s*==\n(.*?)(?=\n==|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
    for heading, content in sections:
        items = re.findall(r'^\s*[\*\-]\s*(.+)$', content, re.MULTILINE)
        for item in items:
            item = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', item)
            item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', item)
            item = re.sub(r"'''?", '', item).strip()
            if item:
                career.append({"detail": item})
    return career


def extract_notable_cases(wikitext: str) -> List[Dict]:
    """Extract notable cases/opinions."""
    cases = []
    sections = re.findall(r'==\s*(Notable cases|Notable opinions|Significant cases)\s*==\n(.*?)(?=\n==|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
    for heading, content in sections:
        items = re.findall(r'^\s*[\*\-]\s*(.+)$', content, re.MULTILINE)
        for item in items:
            item = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', item)
            item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', item)
            item = re.sub(r"'''?", '', item).strip()
            if item:
                cases.append({"detail": item})
    return cases


def extract_military(wikitext: str) -> List[Dict]:
    """Extract military service."""
    military = []
    sections = re.findall(r'==\s*(Military service|Military)\s*==\n(.*?)(?=\n==|\Z)', wikitext, re.DOTALL | re.IGNORECASE)
    for heading, content in sections:
        items = re.findall(r'^\s*[\*\-]\s*(.+)$', content, re.MULTILINE)
        for item in items:
            item = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', item)
            item = re.sub(r'\[\[([^\]]+)\]\]', r'\1', item)
            item = re.sub(r"'''?", '', item).strip()
            if item:
                military.append({"detail": item})
    return military


def process_judge_wiki(judge_name: str) -> Dict[str, Any]:
    """Process a single judge through Wikipedia."""
    print(f"Processing: {judge_name}")
    
    # Search for page
    title = search_page(judge_name)
    if not title:
        return {"Judge": judge_name, "Wiki_Found": False}
    
    # Get full content
    wikitext = get_page_content(title)
    if not wikitext:
        return {"Judge": judge_name, "Wiki_Found": False, "Wiki_Title": title}
    
    time.sleep(0.2)  # Rate limit
    
    # Extract structured data
    infobox = extract_infobox(wikitext)
    education = extract_education_section(wikitext)
    clerkships = extract_clerkships_section(wikitext)
    career = extract_career_section(wikitext)
    cases = extract_notable_cases(wikitext)
    military = extract_military(wikitext)
    
    # Get summary/intro
    url = f"{WIKI_API}?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(title)}"
    data = fetch_json(url)
    summary = ""
    if data:
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            summary = p.get("extract", "")[:3000]
    
    record = {
        "Judge": judge_name,
        "Wiki_Found": True,
        "Wiki_Title": title,
        "Wiki_Summary": summary,
        "Wiki_Infobox": json.dumps(infobox),
        "Wiki_Education": json.dumps(education),
        "Wiki_Clerkships": json.dumps(clerkships),
        "Wiki_Career": json.dumps(career),
        "Wiki_Notable_Cases": json.dumps(cases),
        "Wiki_Military": json.dumps(military),
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
        record = process_judge_wiki(name)
        results.append(record)
    
    out_df = pd.DataFrame(results)
    out_df.to_csv("wikipedia_comprehensive.csv", index=False)
    print(f"Saved {len(out_df)} records to wikipedia_comprehensive.csv")
    
    found = out_df["Wiki_Found"].sum()
    print(f"Found on Wikipedia: {found} / {len(out_df)}")


if __name__ == "__main__":
    main()