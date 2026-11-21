#!/usr/bin/env python3
"""daily_update.py - Daily refresh for the federal judges clerkship guide.

What it does:
  1. Detects whether OSCAR has published new weekly-update posts since our last
     run (by scraping the public OSCAR homepage, which lists the 6 most recent
     weekly-update blog post links).
  2. Re-runs the judge pipeline (Wikipedia current judges + presidential
     appointees) so new judges / duty-station changes are picked up daily.
  3. Re-parses the local OSCAR master listings and re-matches hiring flags.
  4. Regenerates the Folium map and the static web front-end data.
  5. Writes a run summary to `daily_run_summary.json`.

Note on OSCAR data: the actual per-judge clerkship postings on oscar.uscourts.gov
require a judiciary login; the weekly-update blog posts are listed publicly but
their full content is behind authentication. We therefore cannot fetch brand-new
postings automatically. This script detects *when new OSCAR weeks appear* so the
data can be refreshed manually (by dropping the new export into
`oscar_master_listings.csv`), and keeps everything else current daily.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime

OSCAR_HOME = "https://oscar.uscourts.gov/"
STATE_FILE = "oscar_state.json"
SUMMARY_FILE = "daily_run_summary.json"


def fetch_oscar_homepage():
    """Return the list of recent weekly-update blog post URLs from OSCAR's home."""
    try:
        req = urllib.request.Request(OSCAR_HOME, headers={"User-Agent": "Mozilla/5.0 (judges-guide daily updater)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return [], f"OSCAR fetch failed: {e}"
    links = re.findall(r"/blog_post/_1/(\d+)/", html)
    # Deduplicate, preserve order, take unique ids.
    seen = []
    for lid in links:
        if lid not in seen:
            seen.append(lid)
    return seen, None


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"last_seen_week_ids": [], "last_run": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_step(description, command):
    """Run a pipeline step; return (ok, short_output)."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    tail = (result.stdout or result.stderr or "").strip().splitlines()
    tail = "\n".join(tail[-3:]) if tail else ""
    ok = result.returncode == 0
    return ok, tail


def main():
    started = datetime.now()
    print(f"Daily update started at {started:%Y-%m-%d %H:%M:%S}")

    state = load_state()
    summary = {"started": started.isoformat(), "steps": {}, "oscar": {}}

    # 1. Detect new OSCAR weekly-update posts.
    week_ids, err = fetch_oscar_homepage()
    summary["oscar"]["error"] = err
    summary["oscar"]["recent_week_ids"] = week_ids
    if week_ids:
        last_seen = set(state.get("last_seen_week_ids", []))
        new_weeks = [w for w in week_ids if w not in last_seen]
        summary["oscar"]["new_weeks_detected"] = new_weeks
        summary["oscar"]["new_week_count"] = len(new_weeks)
        state["last_seen_week_ids"] = week_ids
        print(f"OSCAR: {len(week_ids)} recent weeks; {len(new_weeks)} new since last run")
        if new_weeks:
            print("  NOTE: New OSCAR week(s) detected but postings need manual export.")
            print(f"        Update oscar_master_listings.csv to include weeks: {new_weeks}")
    else:
        print("OSCAR: could not read homepage (offline?)")

    # 2. Re-scrape current judges from Wikipedia (daily refresh).
    ok, out = run_step("scrape_circuit", "python current_circuit_judges.py")
    summary["steps"]["scrape_circuit"] = {"ok": ok, "out": out}
    ok, out = run_step("scrape_district", "python current_district_judges.py")
    summary["steps"]["scrape_district"] = {"ok": ok, "out": out}

    # 3. Re-scrape presidential appointees (slow; only if missing).
    if not (os.path.exists("pres_appeals.csv") and os.path.exists("pres_district.csv")):
        ok, out = run_step("scrape_appoints", "python pres_appoints.py")
        summary["steps"]["scrape_appoints"] = {"ok": ok, "out": out}

    # 4. Merge + geocode + enrich + map + site data.
    steps = [
        ("merge", "python merge.py"),
        ("geocode", "python add_info.py"),
        ("enrich", (
            "python -c \"import pandas as pd; from enrich_judges import enrich_df; "
            "d=pd.read_csv('final_district.csv'); a=pd.read_csv('final_appeals.csv'); "
            "d=enrich_df(d); a=enrich_df(a); "
            "d.to_csv('final_district_enriched.csv',index=False); "
            "a.to_csv('final_appeals_enriched.csv',index=False); print('enriched')\""
        )),
        ("map", "python make_map.py"),
        ("site_data", "python export_site_data.py"),
    ]
    for name, cmd in steps:
        ok, out = run_step(name, cmd)
        summary["steps"][name] = {"ok": ok, "out": out}
        print(f"{name}: {'OK' if ok else 'FAILED'} {out.splitlines()[-1] if out else ''}")

    summary["finished"] = datetime.now().isoformat()
    summary["ok"] = all(s["ok"] for s in summary["steps"].values()) and not err
    state["last_run"] = summary["finished"]
    save_state(state)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Daily update finished at {summary['finished']}")
    print(f"Summary written to {SUMMARY_FILE}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())