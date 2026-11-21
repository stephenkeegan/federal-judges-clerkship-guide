# parse_oscar.py
# Extract hiring judges from the wide-format OSCAR master listings CSV
import re

import pandas as pd

from helper_functions import nuke_wiki_junk


def normalize(name):
    """Normalize a judge name for matching."""
    if not isinstance(name, str):
        return ''
    name = nuke_wiki_junk(name).lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # Remove middle initials (single letters) and suffixes
    parts = name.split()
    parts = [p for p in parts if len(p) > 1]
    name = ' '.join(parts)
    name = re.sub(r'\b(jr|sr|ii|iii|iv)\b$', '', name).strip()
    return name


def last_name(name):
    n = normalize(name)
    parts = n.split()
    return parts[-1] if parts else ''


def first_last_key(name):
    """First name + last name key, ignoring middle names/initials."""
    n = normalize(name)
    parts = n.split()
    if len(parts) < 2:
        return n
    return f"{parts[0]} {parts[-1]}"


def parse_oscar_listings(file_path="oscar_master_listings.csv"):
    """Parse the wide-format OSCAR CSV and return a DataFrame of unique hiring judges.

    Each quoted segment like "Liles Burke  U.S. District Court  Huntsville, AL"
    is a separate judge listing. We extract name, court type, duty station,
    position type, term length, and dates for every listing.
    """
    with open(file_path, encoding="utf-8", errors="replace") as f:
        raw = f.read()

    # Match quoted judge listing segments:
    #   "Judge Name  U.S. District Court  City, ST"
    pattern = r'"([^"]+?)\s{2,}(U\.S\.\s+(?:District|Court of Appeals|Bankruptcy|Federal Claims|International Trade|Tax)\s+Court)\s{2,}([^"]+)"'
    matches = re.findall(pattern, raw)

    records = []
    for name, court, duty_station in matches:
        name = nuke_wiki_junk(name).strip()
        duty_station = nuke_wiki_junk(duty_station).strip()
        records.append({
            "Judge": name,
            "Court": court,
            "Duty Station": duty_station,
            "Hiring": True,
        })

    df = pd.DataFrame(records).drop_duplicates(subset=["Judge"])

    # Now parse term info from the raw CSV rows
    # Column structure: "Judge Name  U.S. Court  City, ST",Position Type,Term Length,Start Date,End Date,Count,Source_URL,...
    # We need to match each judge listing to its term length (column index 2)
    term_map = _parse_term_info(raw)

    # Add term info to each judge
    df['Hiring Term'] = df['Judge'].apply(
        lambda name: term_map.get(name, 'N/A')
    )

    df['_name_key'] = df['Judge'].apply(normalize)
    df['_last_name'] = df['Judge'].apply(last_name)
    print(f"Parsed {len(df)} unique hiring judges from OSCAR listings")
    return df


def _parse_term_info(raw):
    """Parse term lengths from the raw OSCAR CSV text.

    The OSCAR master listings CSV is a wide, ragged export: each judge listing
    appears as a quoted segment like "Judge Name  U.S. District Court  City, ST"
    followed by the position type, then a term length, then dates. The columns
    are not consistent across rows (some omit the term length entirely), so we
    scan a short window of the comma-separated fields immediately following each
    judge segment for a value that looks like a term length.

    Returns a dict mapping judge name -> hiring term (e.g. '1 Year', '2 Years').
    Judges whose row carries no term length are simply omitted (the caller
    defaults them to 'N/A').
    """
    seg = re.compile(
        r'"([^"]+?)\s{2,}U\.S\.\s+'
        r'(?:District|Court of Appeals|Bankruptcy|Federal Claims|International Trade|Tax)\s+Court'
        r'\s{2,}([^"]+)"'
    )
    # A term length is a standalone value like "1 Year", "2 Years", "Permanent".
    term_re = re.compile(r'(?:Permanent|\d+\s*Years?|\d+\s*Months?)$', re.I)

    term_map = {}
    for match in seg.finditer(raw):
        name = match.group(1).strip()
        if name in term_map:
            continue
        # Fields following the closing quote of the judge segment.
        after = raw[match.end(): match.end() + 240]
        for field in after.split(",")[:6]:
            field = field.strip().strip('"')
            if term_re.match(field):
                term_map[name] = field
                break
    return term_map


def add_hiring_flags(judges_df, oscar_df):
    """Merge hiring info onto the judges dataframe.

    Matches by full normalized name first, then falls back to first+last
    name (ignoring middle names/initials) for cases like "John Peter Cronan"
    vs "John P. Cronan".  First+last fallback is only applied when that
    combination is unique across both datasets to avoid false positives.
    """
    judges_df = judges_df.copy()
    oscar_df = oscar_df.copy()

    judges_df['_name_key'] = judges_df['Judge'].apply(normalize)
    judges_df['_fl_key'] = judges_df['Judge'].apply(first_last_key)

    oscar_df['_name_key'] = oscar_df['Judge'].apply(normalize)
    oscar_df['_fl_key'] = oscar_df['Judge'].apply(first_last_key)

    judges_df['Hiring'] = False
    judges_df['Hiring Term'] = 'N/A'

    # 1. Match by full normalized name
    name_keys_with_hiring = set(oscar_df['_name_key'])
    oscar_name_to_term = dict(zip(
        oscar_df['_name_key'],
        oscar_df['Hiring Term'],
    ))

    mask = judges_df['_name_key'].isin(name_keys_with_hiring)
    judges_df.loc[mask, 'Hiring'] = True
    judges_df.loc[mask, 'Hiring Term'] = judges_df.loc[mask, '_name_key'].map(oscar_name_to_term)

    # 2. Fallback: match by first+last name (ignoring middle names/initials)
    #    Only where that combo is unique in both datasets to avoid false positives.
    unmatched = judges_df[judges_df['Hiring'] == False]
    judge_name_keys = set(judges_df['_name_key'])
    oscar_unmatched = oscar_df[~oscar_df['_name_key'].isin(judge_name_keys)]

    # First+last keys that appear exactly once in OSCAR (unmatched)
    fl_counts = oscar_unmatched['_fl_key'].value_counts()
    unique_fl_osc = set(fl_counts[fl_counts == 1].index)

    # First+last keys that appear exactly once in unmatched judges
    judge_fl_counts = unmatched['_fl_key'].value_counts()
    unique_fl_judge = set(judge_fl_counts[judge_fl_counts == 1].index)

    # Only match where unique on both sides
    safe_fl = unique_fl_osc & unique_fl_judge
    oscar_fl_map = {}
    for _, row in oscar_unmatched[oscar_unmatched['_fl_key'].isin(safe_fl)].iterrows():
        oscar_fl_map[row['_fl_key']] = row['Hiring Term']

    mask = (judges_df['Hiring'] == False) & (judges_df['_fl_key'].isin(oscar_fl_map))
    judges_df.loc[mask, 'Hiring'] = True
    judges_df.loc[mask, 'Hiring Term'] = judges_df.loc[mask, '_fl_key'].map(oscar_fl_map)

    # Clean up helper columns
    judges_df = judges_df.drop(columns=['_name_key', '_fl_key'])
    return judges_df


if __name__ == "__main__":
    oscar_df = parse_oscar_listings()
    print(oscar_df[['Judge', 'Hiring Term', 'Duty Station']].head(20).to_string(index=False))
