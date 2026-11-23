#!/usr/bin/env python3
"""enrich_judges.py - Efficient Wikipedia enrichment for federal judges.

Fetches Wikipedia summaries, education, and alma mater for all judges.
Uses batched API calls (50 titles per request) instead of individual calls,
reducing ~2800 API requests to ~30 batch requests.

Strategy:
  1. Try each judge's name directly as a Wikipedia page title (batched 50 at a time).
  2. Verify the extract is about a federal judge (mentions court/judge).
  3. For unmatched judges, try the Wikipedia search API to find the correct page.
  4. Fetch infoboxes for matched pages in batches.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 15
CACHE_FILE = "enrich_cache.json"

_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        _cache = json.load(open(CACHE_FILE))
    except Exception:
        _cache = {}

# Wikipedia API allows 50 titles per query for extracts.
BATCH_SIZE = 50
# Delay between API calls (seconds). Wikipedia anonymous limit ~1 req/sec.
DELAY = 1.5
# Save progress every N batches.
SAVE_EVERY = 3


def _json_dump_cache():
    try:
        json.dump(_cache, open(CACHE_FILE, "w"))
    except Exception:
        pass


def http_get(url):
    """Fetch URL with caching and rate-limit backoff.

    Only successful responses are cached; failures (including 429s) are retried
    on the next call so rate-limited requests don't get permanently cached as None.
    """
    if url in _cache and _cache[url] is not None:
        return _cache[url]
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read().decode("utf-8", errors="replace")
            _cache[url] = data
            _json_dump_cache()
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limited - exponential backoff, do NOT cache
                wait = 3 * (attempt + 1)
                print(f"  Rate limited (429), waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  HTTP {e.code}: {url[:80]}", flush=True)
                time.sleep(1 + attempt)
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            time.sleep(1 + attempt)
    # Do NOT cache failures - let them retry on next call
    return None


def _is_judge_extract(text):
    """Check if a Wikipedia extract is about a federal judge."""
    if not text:
        return False
    lower = text.lower()
    # Must mention a court or judgeship
    indicators = [
        "district court",
        "circuit court",
        "court of appeals",
        "federal judge",
        "united states district",
        "united states court",
        "bankruptcy court",
        "judge of the",
        "u.s. district",
        "u.s. court",
    ]
    return any(ind in lower for ind in indicators)


def fetch_extracts_batch(titles):
    """Fetch extracts for up to 50 titles in a single API call.

    Returns dict: title -> extract text (or None if missing/not a judge).
    """
    if not titles:
        return {}
    valid = [t for t in titles if t]
    if not valid:
        return {}
    titles_param = "|".join(urllib.parse.quote(t) for t in valid)
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&format=json&prop=extracts&exintro=1&explaintext=1"
        f"&redirects=1&titles={titles_param}"
    )
    data = http_get(url)
    if not data:
        return {}
    result = {}
    try:
        j = json.loads(data)
        pages = j.get("query", {}).get("pages", {})
        for _pid, p in pages.items():
            title = p.get("title")
            extract = p.get("extract")
            # Skip disambiguation and missing pages
            if not title or not extract:
                result[title] = None
                continue
            if extract.strip().endswith("may refer to:"):
                result[title] = None
                continue
            # Only keep extracts that are about a federal judge
            if _is_judge_extract(extract):
                result[title] = extract
            else:
                result[title] = None
    except Exception:
        pass
    return result


def search_and_fetch(judge_name, court=""):
    """Search Wikipedia for a judge and fetch their extract.

    Used as fallback when direct title match fails.
    """
    # Search for the judge name + "judge" to improve relevance
    query = f"{judge_name} judge"
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&format=json&list=search&srsearch={urllib.parse.quote(query)}"
        f"&srlimit=5&srprop="
    )
    data = http_get(url)
    if not data:
        return None, None
    try:
        j = json.loads(data)
        for s in j.get("query", {}).get("search", []):
            title = s["title"]
            # Skip list/disambiguation pages
            if "list" in title.lower() or "disambiguation" in title.lower():
                continue
            # Fetch extract for this title
            extract = fetch_extracts_batch([title])
            if title in extract and extract[title]:
                return title, extract[title]
    except Exception:
        pass
    return None, None


def fetch_infobox_batch(titles):
    """Fetch infobox data for up to 50 titles in a single API call.

    Returns dict: title -> {field: value}.
    """
    if not titles:
        return {}
    valid = [t for t in titles if t]
    if not valid:
        return {}
    titles_param = "|".join(urllib.parse.quote(t) for t in valid)
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&format=json&prop=revisions&rvprop=content&rvslots=main"
        f"&redirects=1&titles={titles_param}"
    )
    data = http_get(url)
    if not data:
        return {}
    result = {}
    try:
        j = json.loads(data)
        pages = j.get("query", {}).get("pages", {})
        for _pid, p in pages.items():
            title = p.get("title")
            if not title:
                continue
            revisions = p.get("revisions", [])
            if not revisions:
                continue
            content = revisions[0].get("slots", {}).get("main", {}).get("*", "")
            result[title] = _parse_infobox(content)
    except Exception:
        pass
    return result


def _parse_infobox(wikitext):
    """Extract infobox fields from page wikitext."""
    fields = {}
    pattern = r"\{\{Infobox[^}]*\}\}"
    matches = re.findall(pattern, wikitext, re.DOTALL)
    for match in matches:
        for line in match.split("\n"):
            m = re.match(r"\|\s*([^=]+)\s*=\s*(.+)", line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                # Clean up wiki markup
                val = re.sub(r"\{\{[^}]*\}\}", "", val)
                val = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", val)
                val = re.sub(r"\[\[([^\]]+)\]\]", r"\1", val)
                val = re.sub(r"'''?", "", val)
                val = re.sub(r"<[^>]+>", "", val)
                val = re.sub(r"\s+", " ", val).strip()
                if key and val:
                    fields[key] = val[:500]
    return fields


def _try_name_variants(name):
    """Generate name variants to try as Wikipedia titles.

    Most judges have pages titled with their full name. For those that don't,
    try removing middle initials/names, suffixes, and fixing encoding issues.
    """
    variants = [name]
    parts = name.split()
    
    # Remove suffixes (Jr., Sr., II, III, IV)
    suffixes = {"jr.", "jr", "sr.", "sr", "ii", "iii", "iv"}
    while parts and parts[-1].lower().rstrip(".") in suffixes:
        parts = parts[:-1]
    if len(parts) != len(name.split()):
        variants.append(" ".join(parts))
    
    # Remove middle initial/name
    if len(parts) >= 3:
        # Remove middle initial (e.g., "John P. Cronan" -> "John Cronan")
        middle = parts[1]
        if len(middle) <= 2 and middle.endswith("."):
            variants.append(f"{parts[0]} {parts[-1]}")
        # Remove middle name entirely
        variants.append(f"{parts[0]} {parts[-1]}")
        # Remove middle initial AND suffix
        if len(parts) >= 4:
            variants.append(f"{parts[0]} {parts[-2]}")
    
    # Fix common encoding issues from nuke_wiki_junk (stripped accents)
    fixed = name
    replacements = {
        "Colo n": "Colón", "Marti nez": "Martínez", "Nunez": "Núñez",
        "Garcia": "García", "Rodriguez": "Rodríguez", "Fernandez": "Fernández",
        "Gonzalez": "González", "Perez": "Pérez", "Sanchez": "Sánchez",
        "Ramirez": "Ramírez", "Torres": "Torres", "Flores": "Flores",
        "Rivera": "Rivera", "Gomez": "Gómez", "Diaz": "Díaz", "Morales": "Morales",
        "Ortiz": "Ortiz", "Gutierrez": "Gutiérrez", "Chavez": "Chávez",
        "Ramos": "Ramos", "Vasquez": "Vázquez", "Castillo": "Castillo",
        "Jimenez": "Jiménez", "Mendoza": "Mendoza", "Ruiz": "Ruiz",
        "Alvarez": "Álvarez", "Romero": "Romero", "Navarro": "Navarro",
        "Pena": "Peña", "Cruz": "Cruz", "Herrera": "Herrera",
    }
    for wrong, right in replacements.items():
        if wrong in fixed:
            fixed = fixed.replace(wrong, right)
            variants.append(fixed)
    
    # Deduplicate while preserving order
    seen = set()
    result = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def _save_partial(df, summaries, matched_titles, names):
    """Save intermediate enrichment progress to the enriched CSV."""
    df = df.copy()
    df["Wikipedia Summary"] = summaries
    df["Wikipedia Title"] = matched_titles
    df["Wikipedia Found"] = [bool(s) for s in summaries]
    df.to_csv("final_district_enriched_partial.csv", index=False)


def enrich_df(df):
    """Enrich a judges DataFrame with Wikipedia summaries and infobox data."""
    names = [str(x).strip() for x in df["Judge"].tolist()]
    n = len(names)

    print(f"Fetching Wikipedia extracts for {n} judges (batched)...")
    summaries = [None] * n
    matched_titles = [None] * n

    # Step 1: Try each judge name directly as a Wikipedia title (batched).
    # Wikipedia titles for judges are almost always their full name.
    for i in range(0, n, BATCH_SIZE):
        batch_names = names[i : i + BATCH_SIZE]
        extracts = fetch_extracts_batch(batch_names)
        for j, name in enumerate(batch_names):
            idx = i + j
            if name in extracts and extracts[name]:
                summaries[idx] = extracts[name][:1000]
                matched_titles[idx] = name
        batch_num = i // BATCH_SIZE + 1
        total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE
        if batch_num % SAVE_EVERY == 0 or batch_num == total_batches:
            matched = sum(1 for s in summaries if s)
            print(f"  Batch {batch_num}/{total_batches}: {matched}/{n} matched", flush=True)
            # Save intermediate progress
            _save_partial(df, summaries, matched_titles, names)
        time.sleep(DELAY)

    matched_count = sum(1 for s in summaries if s)
    print(f"  Matched {matched_count}/{n} judges by exact name")

    # Step 2: For unmatched judges, try name variants (remove middle initial).
    unmatched_indices = [i for i, s in enumerate(summaries) if not s]
    if unmatched_indices:
        print(f"Trying name variants for {len(unmatched_indices)} unmatched judges...")
        variant_names = []
        variant_indices = []
        for idx in unmatched_indices:
            for variant in _try_name_variants(names[idx])[1:]:  # skip original
                variant_names.append(variant)
                variant_indices.append(idx)

        for i in range(0, len(variant_names), BATCH_SIZE):
            batch_vars = variant_names[i : i + BATCH_SIZE]
            extracts = fetch_extracts_batch(batch_vars)
            for j, var in enumerate(batch_vars):
                idx = variant_indices[i + j]
                if not summaries[idx] and var in extracts and extracts[var]:
                    summaries[idx] = extracts[var][:1000]
                    matched_titles[idx] = var
            time.sleep(DELAY)

        matched_count = sum(1 for s in summaries if s)
        print(f"  After variants: {matched_count}/{n} judges matched")

    # Step 3: For still-unmatched judges, use Wikipedia search API.
    still_unmatched = [i for i, s in enumerate(summaries) if not s]
    if still_unmatched:
        print(f"Searching Wikipedia for {len(still_unmatched)} remaining unmatched judges...")
        for idx in still_unmatched:
            title, extract = search_and_fetch(names[idx])
            if title and extract:
                summaries[idx] = extract[:1000]
                matched_titles[idx] = title
            time.sleep(0.5)
        matched_count = sum(1 for s in summaries if s)
        print(f"  After search: {matched_count}/{n} judges matched")

    # Step 4: Fetch infoboxes for matched judges (batched).
    print("Fetching infoboxes for matched judges...")
    matched = [(i, matched_titles[i]) for i in range(n) if matched_titles[i]]
    infoboxes = [{} for _ in range(n)]

    for i in range(0, len(matched), BATCH_SIZE):
        batch = matched[i : i + BATCH_SIZE]
        batch_titles = [t for _, t in batch]
        ib_data = fetch_infobox_batch(batch_titles)
        for idx, title in batch:
            if title in ib_data:
                infoboxes[idx] = ib_data[title]
        time.sleep(DELAY)

    # Build result DataFrame
    df = df.copy()
    df["Wikipedia Summary"] = summaries
    df["Wikipedia Title"] = matched_titles
    df["Education"] = [ib.get("Education", ib.get("Alma mater", "")) for ib in infoboxes]
    df["Alma mater"] = [ib.get("Alma mater", "") for ib in infoboxes]
    df["Wikipedia Found"] = [bool(s) for s in summaries]

    found = sum(df["Wikipedia Found"])
    print(f"Enriched {found}/{n} judges with Wikipedia data")

    return df


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("final_district_enriched.csv")
    enriched = enrich_df(df)
    enriched.to_csv("final_district_enriched.csv", index=False)
    print("Saved final_district_enriched.csv")

    df2 = pd.read_csv("final_appeals_enriched.csv")
    enriched2 = enrich_df(df2)
    enriched2.to_csv("final_appeals_enriched.csv", index=False)
    print("Saved final_appeals_enriched.csv")