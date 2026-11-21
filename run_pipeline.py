#!/usr/bin/env python3
"""run_pipeline.py - Automated pipeline for the federal judges clerkship map.

Runs all steps in order:
1. Scrape current circuit and district judges from Wikipedia
2. Scrape presidential appointees from Wikipedia
3. Merge appointee data with current judges (incumbent filter)
4. Geocode duty stations to lat/lng
5. Parse OSCAR clerkship listings for hiring info
6. Build the interactive Folium map
7. Validate output and report coverage statistics
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime


def run_step_optional(description, command, required_csv=None):
    """Run a pipeline step. If it fails but the required CSV exists, continue."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"WARNING: Step failed: {description}")
        print(result.stderr[:500])
        if required_csv and os.path.exists(required_csv):
            print(f"OK: Using existing {required_csv}")
            return True
        print(f"SKIPPING: {description}")
        return False
    print(f"OK: {description} completed")
    return True


def validate_output():
    """Validate that all expected output files exist and have data."""
    print(f"\n{'='*60}")
    print("VALIDATION")
    print(f"{'='*60}")

    required_files = [
        "current_circuit_judges.csv",
        "current_district_judges.csv",
        "pres_appeals.csv",
        "pres_district.csv",
        "active_district.csv",
        "active_appeals.csv",
        "final_district.csv",
        "final_appeals.csv",
        "oscar_clerkship_map.html",
    ]

    all_ok = True
    for f in required_files:
        path = os.path.join(os.getcwd(), f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"OK: {f} ({size:,} bytes)")
        else:
            print(f"MISSING: {f}")
            all_ok = False

    # Check geo coverage
    import pandas as pd
    fd = pd.read_csv("final_district.csv")
    fa = pd.read_csv("final_appeals.csv")
    dist_total = len(fd)
    dist_geo = fd['lat'].notna().sum()
    circ_total = len(fa)
    circ_geo = fa['lat'].notna().sum()

    print(f"\nDistrict judges: {dist_total} | with coordinates: {dist_geo} ({100*dist_geo/dist_total:.1f}%)")
    print(f"Circuit judges:  {circ_total} | with coordinates: {circ_geo} ({100*circ_geo/circ_total:.1f}%)")

    # Check hiring data with new scraper
    from oscar_scraper import add_hiring_flags_with_freshness, load_hiring_judges
    oscar_df, posting_dates, source, ts = load_hiring_judges()
    d = add_hiring_flags_with_freshness(fd.copy(), oscar_df, posting_dates)
    a = add_hiring_flags_with_freshness(fa.copy(), oscar_df, posting_dates)
    print(f"District hiring: {int(d['Hiring'].sum())} of {len(d)}")
    print(f"Circuit hiring:  {int(a['Hiring'].sum())} of {len(a)}")
    print(f"OSCAR data source: {source}")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Federal judges clerkship map pipeline")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip Wikipedia scraping steps")
    parser.add_argument("--min-geo-coverage", type=float, default=0.8,
                        help="Minimum geocoding coverage (0-1). Inactive/senior judges "
                             "without a current duty station are legitimately unlocatable, "
                             "so the practical ceiling is below 100%%.")
    args = parser.parse_args()

    start = datetime.now()
    print(f"Pipeline started at {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if not args.skip_scrape:
        run_step_optional("Scrape current circuit judges", "python current_circuit_judges.py",
                          required_csv="current_circuit_judges.csv")
        run_step_optional("Scrape current district judges", "python current_district_judges.py",
                          required_csv="current_district_judges.csv")
        run_step_optional("Scrape presidential appointees", "python pres_appoints.py",
                          required_csv="pres_appeals.csv")

    # Step 3: Merge (required - depends on previous steps)
    run_step_optional("Merge appointee data with current judges", "python merge.py",
                      required_csv="active_district.csv")

    # Step 4: Geocode (required)
    run_step_optional("Geocode duty stations", "python add_info.py",
                      required_csv="final_district.csv")

    # Step 5: Enrich with Wikipedia (optional)
    run_step_optional("Enrich judge bios (Wikipedia)", "python -c \"import pandas as pd; from enrich_judges import enrich_df; d=pd.read_csv('final_district.csv'); a=pd.read_csv('final_appeals.csv'); d=enrich_df(d); a=enrich_df(a); d.to_csv('final_district_enriched.csv',index=False); a.to_csv('final_appeals_enriched.csv',index=False); print('done')\"",
                      required_csv="final_district_enriched.csv")

    # Step 6: Build map
    run_step_optional("Build interactive clerkship map", "python make_map.py",
                      required_csv="oscar_clerkship_map.html")

    # Step 7: Export judge data for the static web front-end (app/)
    run_step_optional("Export web front-end data", "python export_site_data.py",
                      required_csv="app/judges.json")

    # Step 8: Validate
    ok = validate_output()

    # Enforce minimum geocoding coverage
    import pandas as pd
    fd = pd.read_csv("final_district.csv")
    fa = pd.read_csv("final_appeals.csv")
    cov = min(fd['lat'].notna().mean(), fa['lat'].notna().mean())
    print(f"\nGeocoding coverage: {cov:.1%} (threshold {args.min_geo_coverage:.1%})")
    if cov < args.min_geo_coverage:
        print(f"ERROR: Geocoding coverage {cov:.1%} below threshold {args.min_geo_coverage:.1%}")
        ok = False

    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"\nPipeline finished at {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration:.1f} seconds")

    if ok:
        print("\nPipeline completed successfully!")
        print("Open oscar_clerkship_map.html in a browser to view the map.")
    else:
        print("\nPipeline completed with some issues. See above.")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
