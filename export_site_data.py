#!/usr/bin/env python3
"""export_site_data.py - Export judge data into a clean JSON the static site consumes.

Reads the pipeline outputs (final_district_enriched.csv, final_appeals_enriched.csv)
plus OSCAR hiring flags and writes app/judges.json. This is the bridge between the
Python scraping pipeline and the static web front-end (app/index.html).

Each judge record carries the three things a prospective clerk needs:
  1. Courthouse location (duty station + lat/lng + court)
  2. Clerk-relevant background (bio, education, party, years of service, appointment)
  3. Hiring status (whether hiring now, term length, posting freshness)
"""

import json
import os
import re
from datetime import datetime

import pandas as pd

from courthouse_data import lookup_courthouse
from helper_functions import derive_party
from oscar_scraper import add_hiring_flags_with_freshness, load_hiring_judges

APP_DIR = os.path.join(os.path.dirname(__file__), "app")


def _clean(value):
    """Normalize a raw cell into a clean string or None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
        return None
    return s


def _parse_year(value):
    """Extract a 4-digit year from a free-text date/cell."""
    s = _clean(value)
    if not s:
        return None
    m = re.search(r"\b(1[7-9]\d\d|20\d\d)\b", s)
    return int(m.group(1)) if m else None


def _years_of_service(row, now_year):
    start = _parse_year(
        _clean(row.get("Began active service"))
        or _clean(row.get("Began active service[3]"))
        or _clean(row.get("Began active service[7]"))
    )
    if start and 1789 <= start <= now_year:
        return now_year - start
    return None


def _court_from_summary(summary):
    """Extract a federal court name from a Wikipedia summary sentence."""
    if not summary:
        return None
    # Capture "United States <...> Court" plus an optional "for the X" clause,
    # stopping at the next period (sentence end).
    m = re.search(
        r"(United States (?:District|Court of Appeals|Bankruptcy) Court"
        r"(?:\s+for\s+(?:the\s+)?[^.]*?)?)\.",
        summary,
    )
    if not m:
        # Summary may end exactly at the court name (no trailing period).
        m = re.search(
            r"(United States (?:District|Court of Appeals|Bankruptcy) Court"
            r"(?:\s+for\s+(?:the\s+)?[^.]*?)?)$",
            summary,
        )
    if m:
        court = m.group(1).strip()
        # Trim trailing clauses like "since 2012" or "in 2020"
        court = re.sub(r"\s+(?:since|in|from)\b.*$", "", court)
        return court
    # Fallback: just the court type if we can't capture the district
    m = re.search(r"United States (?:District|Court of Appeals|Bankruptcy) Court", summary)
    if m:
        return m.group(0)
    return None


def _court_name(row, level):
    court = _clean(row.get("Court [Note 2]"))
    if court:
        return court
    district = _clean(row.get("District"))
    if district:
        return district
    circuit = _clean(row.get("Circuit"))
    if circuit:
        return f"{circuit} Circuit"
    # Senior judges lose their court column; recover from the bio summary.
    summary_court = _court_from_summary(_clean(row.get("Wikipedia Summary")))
    if summary_court:
        return summary_court
    return _clean(row.get("Title")) or "Federal Court"


def build_record(row, level, now_year):
    is_hiring = bool(row.get("Hiring", False))
    court = _court_name(row, level)
    yos = _years_of_service(row, now_year)

    # Prefer courthouse-accurate coordinates over the city-level geocode.
    duty_station = _clean(row.get("Duty Station"))
    courthouse = lookup_courthouse(duty_station, _clean(row.get("Court [Note 2]")) or court)
    if courthouse:
        lat, lng, courthouse_name = courthouse
    else:
        lat = float(row["lat"]) if pd.notna(row.get("lat")) else None
        lng = float(row["lng"]) if pd.notna(row.get("lng")) else None
        courthouse_name = None

    # Age
    born = _parse_year(row.get("Born"))
    age = now_year - born if born and 1789 <= born <= now_year else None

    # Years on bench
    years_bench = None
    yob = _clean(row.get("Years on Bench"))
    if yob:
        try:
            years_bench = int(float(yob))
        except (ValueError, TypeError):
            pass

    # Chief / senior flags
    is_chief = bool(row.get("Is Chief", False)) or _clean(row.get("Chief Term")) is not None
    is_senior = bool(row.get("Is Senior", False)) or (
        _clean(row.get("Senior Term")) is not None
        or "senior" in (_clean(row.get("Title")) or "").lower()
    )

    # Confirmation year
    conf_year = None
    conf_raw = _clean(row.get("Confirmation Year")) or _clean(row.get("Confirmation Date"))
    if conf_raw:
        m = re.search(r"\b(19\d\d|20\d\d)\b", str(conf_raw))
        if m:
            conf_year = int(m.group(1))

    # Education / clerkships / career from Wikipedia
    wiki_edu = _clean(row.get("Wiki_Education"))
    alma_mater = _clean(row.get("Alma mater"))
    education = wiki_edu or _clean(row.get("Education")) or alma_mater
    wiki_clerkships = _clean(row.get("Wiki_Clerkships"))
    wiki_career = _clean(row.get("Wiki_Career"))
    notable_cases = _clean(row.get("Notable Cases"))

    # Caseload metrics
    caseload = {}
    caseload_fields = {
        "district_filings": "District Filings",
        "civil_per_judgeship": "Civil Cases per Judgeship",
        "weighted_filings": "Weighted Filings per Judgeship",
        "median_civil_months": "Median Civil Disposition (months)",
        "judgeships": "Judgeships",
        "criminal_per_judgeship": "Criminal Cases per Judgeship",
        "trials_completed": "Trials Completed",
        "civil_total": "District Civil Filings",
        "criminal_total": "District Criminal Filings",
        "top_civil_types": "Top Civil Case Types",
        "top_criminal_types": "Top Criminal Case Types",
    }
    for key, col in caseload_fields.items():
        val = _clean(row.get(col))
        if val is not None:
            try:
                caseload[key] = int(float(val))
            except (ValueError, TypeError):
                caseload[key] = val

    record = {
        "judge": _clean(row.get("Judge")),
        "level": level,
        "title": _clean(row.get("Title")),
        "court": court,
        "circuit": _clean(row.get("Circuit")),
        "duty_station": duty_station,
        "courthouse": courthouse_name,
        "lat": lat,
        "lng": lng,
        "appointed_by": _clean(row.get("Appointed By")),
        "party": derive_party(row.get("Appointed By")),
        "born": born,
        "age": age,
        "years_of_service": yos,
        "years_on_bench": years_bench,
        "is_chief": is_chief,
        "is_senior": is_senior,
        "nomination_date": _clean(row.get("Nomination date")),
        "confirmation_date": _clean(row.get("Confirmation Date")),
        "confirmation_year": conf_year,
        "confirmation_vote": _clean(row.get("Confirmation vote")),
        "education": education,
        "alma_mater": alma_mater,
        "clerkships": wiki_clerkships,
        "career": wiki_career,
        "notable_cases": notable_cases,
        "wikipedia_summary": _clean(row.get("Wikipedia Summary")),
        "wikipedia_url": _clean(row.get("Official Source / Wikipedia")),
        "caseload": caseload if caseload else None,
        "hiring": is_hiring,
        "hiring_term": _clean(row.get("Hiring Term")) if is_hiring else None,
        "posting_date": str(row["Posting Date"]) if is_hiring and pd.notna(row.get("Posting Date")) else None,
        "freshness": _clean(row.get("Freshness")) if is_hiring else None,
        "scholar_url": (
            "https://scholar.google.com/scholar?q=" + re.sub(r"\s+", "+", row["Judge"])
            if _clean(row.get("Judge"))
            else None
        ),
        "oscar_search_url": (
            "https://www.google.com/search?q=site:oscar.uscourts.gov+"
            + re.sub(r"\s+", "+", row["Judge"])
            + "+clerk"
            if _clean(row.get("Judge"))
            else None
        ),
    }
    return record


def main():
    now_year = datetime.now().year

    oscar_df, posting_dates, data_source, pipeline_timestamp = load_hiring_judges()

    # Read from the unified comprehensive CSV (has all derived + extracted fields)
    unified_path = "judges_unified_comprehensive.csv"
    if not os.path.exists(unified_path):
        print(f"ERROR: {unified_path} not found")
        return

    df = pd.read_csv(unified_path)
    df = add_hiring_flags_with_freshness(df, oscar_df, posting_dates)

    # Determine level from Title or Court Type
    def _level(row):
        title = (_clean(row.get("Title")) or "").lower()
        court_type = (_clean(row.get("Court Type")) or "").lower()
        if "circuit" in title or "appeals" in title or "appellate" in title or "circuit" in court_type:
            return "circuit"
        return "district"

    df["level"] = df.apply(_level, axis=1)

    records = []
    sources = {}

    for level in ("district", "circuit"):
        level_df = df[df["level"] == level]
        # Filter to judges with coordinates (same as before)
        level_df = level_df.dropna(subset=["lat", "lng"]).drop_duplicates(subset=["Judge"])
        for _, row in level_df.iterrows():
            rec = build_record(row, level, now_year)
            if rec["judge"]:
                records.append(rec)
        sources[level] = {"rows": len(level_df), "with_coords": int(level_df["lat"].notna().sum())}

    os.makedirs(APP_DIR, exist_ok=True)
    out = {
        "generated_at": pipeline_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "oscar_source": data_source,
        "counts": {
            "total": len(records),
            "district": sum(1 for r in records if r["level"] == "district"),
            "circuit": sum(1 for r in records if r["level"] == "circuit"),
            "hiring": sum(1 for r in records if r["hiring"]),
        },
        "judges": records,
    }

    out_path = os.path.join(APP_DIR, "judges.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(records)} judges to {out_path}")
    print(
        "Counts: "
        f"{out['counts']['district']} district, "
        f"{out['counts']['circuit']} circuit, "
        f"{out['counts']['hiring']} hiring"
    )
    print(f"OSCAR source: {data_source}")


if __name__ == "__main__":
    main()