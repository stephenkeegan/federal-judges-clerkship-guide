"""
Fetch full Wikipedia article wikitext for all judges with a Wikipedia Title.

Uses prop=revisions&rvprop=content&rvslots=main with batched titles (50 per call)
to get full article wikitext. Then parses sections to extract:
- Education (from "Education" / "Early life" sections)
- Clerkships (from "Legal career" / "Clerkship" sections)
- Career (from "Career" / "Professional career" sections)
- Notable cases (from "Notable cases" / "Judicial service" sections)
"""

import pandas as pd
import numpy as np
import json
import time
import re
from urllib.parse import quote
from enrich_judges import http_get, BATCH_SIZE

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKITEXT_CACHE = "wikitext_cache.json"


def load_cache():
    try:
        with open(WIKITEXT_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cache(cache):
    with open(WIKITEXT_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def fetch_wikitext_batch(titles, cache):
    """Fetch full wikitext for a batch of titles using prop=revisions."""
    new_titles = [t for t in titles if t not in cache]
    if not new_titles:
        return {}

    batch = new_titles[:BATCH_SIZE]
    titles_param = "|".join(quote(t, safe="") for t in batch)
    url = (
        f"{WIKI_API}?action=query&format=json"
        f"&prop=revisions&rvprop=content&rvslots=main"
        f"&redirects=1&titles={titles_param}"
    )

    data = http_get(url)
    if not data:
        return {}

    try:
        parsed = json.loads(data) if isinstance(data, str) else data
    except (json.JSONDecodeError, TypeError):
        return {}

    if "query" not in parsed:
        return {}

    results = {}
    pages = parsed["query"].get("pages", {})

    # Build normalized title map
    normalized = {}
    for n in parsed["query"].get("normalized", []):
        normalized[n["from"]] = n["to"]
    for r in parsed["query"].get("redirects", []):
        normalized[r["from"]] = r["to"]

    for page_id, page_data in pages.items():
        if "missing" in page_data:
            continue
        title = page_data.get("title", "")
        revisions = page_data.get("revisions", [])
        if not revisions:
            continue
        content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
        if content and len(content) > 100:
            results[title] = content
            cache[title] = content
            # Also cache under original input name if normalized
            for orig in batch:
                norm = normalized.get(orig, orig)
                if norm == title:
                    cache[orig] = content
                    results[orig] = content

    return results


def parse_wikitext_sections(wikitext):
    """Parse wikitext into sections by heading."""
    sections = {}
    current_section = "Lead"
    current_lines = []

    for line in wikitext.split("\n"):
        # Match section headings: == Heading == or === Subheading ===
        m = re.match(r'^(={2,})\s*(.+?)\s*\1\s*$', line)
        if m:
            # Save previous section
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


def strip_wikitext_markup(text):
    """Remove basic wikitext markup to get plain text."""
    if not text:
        return ""
    # Remove templates
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    # Remove refs
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*/>', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove wikilink markup but keep text
    text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', text)
    # Remove external links
    text = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[https?://\S+\]', '', text)
    # Remove bold/italic
    text = re.sub(r"'''?", '', text)
    # Remove categories
    text = re.sub(r'\[\[Category:[^\]]+\]\]', '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_education_from_sections(sections):
    """Extract education from education-related sections."""
    edu_keywords = ["education", "early life", "academic", "alma mater", "schooling"]
    education_parts = []

    for section_name, content in sections.items():
        for kw in edu_keywords:
            if kw in section_name.lower():
                plain = strip_wikitext_markup(content)
                if plain and len(plain) > 20:
                    education_parts.append(plain[:2000])
                break

    # Also check Lead section for education mentions
    lead = sections.get("Lead", "")
    lead_plain = strip_wikitext_markup(lead)
    if lead_plain:
        # Look for education-related sentences in lead
        for sentence in re.split(r'(?<=[.!?])\s+', lead_plain):
            if any(w in sentence.lower() for w in ["graduated", "degree", "law school", "attended", "earned", "received his", "received her", "bachelor", "J.D.", "A.B."]):
                education_parts.append(sentence.strip())

    return " | ".join(education_parts) if education_parts else None


def extract_career_from_sections(sections):
    """Extract career from career-related sections."""
    career_keywords = ["career", "professional", "legal career", "practice", "early career", "pre-judicial"]
    career_parts = []

    for section_name, content in sections.items():
        for kw in career_keywords:
            if kw in section_name.lower():
                plain = strip_wikitext_markup(content)
                if plain and len(plain) > 20:
                    career_parts.append(plain[:2000])
                break

    # Also check for clerkship mentions in legal career
    return " | ".join(career_parts) if career_parts else None


def extract_clerkships_from_sections(sections):
    """Extract clerkship info from career/legal sections."""
    clerk_keywords = ["clerk", "law clerk"]
    clerk_parts = []

    for section_name, content in sections.items():
        plain = strip_wikitext_markup(content)
        if not plain:
            continue
        for sentence in re.split(r'(?<=[.!?])\s+', plain):
            if any(w in sentence.lower() for w in clerk_keywords):
                clerk_parts.append(sentence.strip())

    return " | ".join(clerk_parts[:5]) if clerk_parts else None


def extract_cases_from_sections(sections):
    """Extract notable cases from judicial service sections."""
    case_keywords = ["notable cases", "judicial service", "notable rulings", "cases", "opinions"]
    case_parts = []

    for section_name, content in sections.items():
        for kw in case_keywords:
            if kw in section_name.lower():
                plain = strip_wikitext_markup(content)
                if plain and len(plain) > 20:
                    case_parts.append(plain[:2000])
                break

    # Also check Lead for case mentions
    lead = sections.get("Lead", "")
    lead_plain = strip_wikitext_markup(lead)
    if lead_plain:
        for sentence in re.split(r'(?<=[.!?])\s+', lead_plain):
            if any(w in sentence.lower() for w in ["presided", "ruled", "opinion", "case of", "decision"]):
                case_parts.append(sentence.strip())

    return " | ".join(case_parts) if case_parts else None


def main():
    comp = pd.read_csv("judges_unified_comprehensive.csv")
    cache = load_cache()

    wiki_titles = comp["Wiki_Title"].dropna().unique().tolist()
    wiki_titles = [t for t in wiki_titles if str(t).strip() not in ("", "nan", "None")]
    print(f"Judges with Wikipedia titles: {len(wiki_titles)}")

    to_fetch = [t for t in wiki_titles if t not in cache]
    print(f"To fetch: {len(to_fetch)}")
    print(f"Already cached: {len(wiki_titles) - len(to_fetch)}")

    if to_fetch:
        for i in range(0, len(to_fetch), BATCH_SIZE):
            batch = to_fetch[i:i + BATCH_SIZE]
            results = fetch_wikitext_batch(batch, cache)

            batch_num = i // BATCH_SIZE + 1
            total = (len(to_fetch) + BATCH_SIZE - 1) // BATCH_SIZE
            cached_count = sum(1 for t in wiki_titles if t in cache)
            print(f"  Batch {batch_num}/{total}: {cached_count}/{len(wiki_titles)} cached", flush=True)

            if batch_num % 5 == 0:
                save_cache(cache)

            time.sleep(2)

        save_cache(cache)
        print("All wikitext fetched and cached")

    # Parse and extract structured info
    print("\n=== EXTRACTING STRUCTURED INFO FROM FULL WIKITEXT ===")

    for col in ["Wiki_Education", "Alma mater", "Wiki_Clerkships", "Wiki_Career", "Notable Cases"]:
        if col not in comp.columns:
            comp[col] = None
        comp[col] = comp[col].astype(object)

    updated = 0
    for idx, row in comp.iterrows():
        title = row.get("Wiki_Title", "")
        if pd.isna(title) or str(title).strip() in ("", "nan", "None"):
            continue

        title = str(title).strip()
        wikitext = cache.get(title, "")
        if not wikitext or len(wikitext) < 100:
            continue

        sections = parse_wikitext_sections(wikitext)
        changed = False

        # Education
        edu = extract_education_from_sections(sections)
        if edu:
            comp.at[idx, "Wiki_Education"] = edu[:2000]
            changed = True

        # Clerkships
        clerks = extract_clerkships_from_sections(sections)
        if clerks:
            comp.at[idx, "Wiki_Clerkships"] = clerks[:1000]
            changed = True

        # Career
        career = extract_career_from_sections(sections)
        if career:
            comp.at[idx, "Wiki_Career"] = career[:2000]
            changed = True

        # Notable cases
        cases = extract_cases_from_sections(sections)
        if cases:
            comp.at[idx, "Notable Cases"] = cases[:2000]
            changed = True

        # Update summary with Lead section if current is too short
        current_summary = row.get("Wikipedia Summary", "")
        if pd.isna(current_summary) or len(str(current_summary)) < 150:
            lead = sections.get("Lead", "")
            lead_plain = strip_wikitext_markup(lead)
            if lead_plain and len(lead_plain) > 100:
                comp.at[idx, "Wikipedia Summary"] = lead_plain[:1000]
                changed = True

        if changed:
            updated += 1

    print(f"Updated {updated} judges with full article info")

    # Coverage
    print("\n=== EXTRACTION COVERAGE ===")
    for col in ["Wiki_Education", "Wiki_Clerkships", "Wiki_Career", "Notable Cases", "Wikipedia Summary"]:
        if col in comp.columns:
            non_null = comp[col].notna() & (comp[col].astype(str).str.strip() != "")
            pct = 100 * non_null.sum() / len(comp)
            print(f"  {col:25s} {non_null.sum():5d}/{len(comp)} ({pct:.1f}%)")

    # Samples
    print("\n=== SAMPLES ===")
    for name in ["Amit Mehta", "Aileen Cannon", "Ada Brown", "Anne Hwang", "Andrew L. Carter Jr."]:
        row = comp[comp["Judge"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}:")
            for col in ["Wiki_Education", "Wiki_Clerkships", "Wiki_Career", "Notable Cases"]:
                val = r.get(col)
                if pd.notna(val) and str(val).strip() not in ("", "nan", "None"):
                    print(f"    {col}: {str(val)[:200]}")

    comp.to_csv("judges_unified_comprehensive.csv", index=False)
    print("\nSaved judges_unified_comprehensive.csv")


if __name__ == "__main__":
    main()