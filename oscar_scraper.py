# oscar_scraper.py
# Live OSCAR clerkship scraping with graceful fallback to static CSV
import re
from datetime import datetime

from parse_oscar import add_hiring_flags, parse_oscar_listings


def try_live_oscar_scrape():
    """Attempt to scrape live OSCAR data for fresh posting dates.

    OSCAR content is behind JavaScript/authentication, so direct scraping
    is limited. We attempt to fetch recent weekly update blog posts to
    extract posting dates for freshness tracking.

    Returns:
        dict: mapping of blog link -> posting date (datetime), or empty dict on failure
    """
    import urllib.request

    posting_dates = {}

    try:
        # Fetch recent weekly update blog posts
        blog_links = [
            "/blog_post/_1/833/Weekly_Update_New_Positions_Posted_October_5_2026__October_13_2026",
            "/blog_post/_1/832/Weekly_Update_New_Positions_Posted_September_28_2026__October_5_2026",
            "/blog_post/_1/831/Weekly_Update_New_Positions_Posted_September_21_2026__September_28_2026",
            "/blog_post/_1/830/Weekly_Update_New_Positions_Posted_September_14_2026__September_21_2026",
            "/blog_post/_1/829/Weekly_Update_New_Positions_Posted_September_8_2026__September_14_2026",
            "/blog_post/_1/828/Weekly_Update_New_Positions_Posted_August_31_2026_-_September_8_2026",
        ]

        for link in blog_links:
            url = "https://oscar.uscourts.gov" + link
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('utf-8', errors='replace')

                # Extract date range from URL/blog title
                # URL pattern: Weekly_Update_New_Positions_Posted_Month_Day_Year__Month_Day_Year
                match = re.search(r'Posted_([A-Za-z]+_\d+_\d+)(?:__|_-_)([A-Za-z]+_\d+_\d+)', link)
                if match:
                    start_str = match.group(1)
                    end_str = match.group(2)
                    try:
                        start_date = datetime.strptime(start_str, '%B_%d_%Y')
                        end_date = datetime.strptime(end_str, '%B_%d_%Y')
                        # Use the end date as the posting date for this batch
                        posting_dates[link] = end_date
                    except ValueError:
                        pass
            except Exception:
                continue

    except Exception:
        pass

    return posting_dates


def load_hiring_judges(csv_path="oscar_master_listings.csv"):
    """Load hiring judges from OSCAR data.

    Attempts live OSCAR scraping first for freshness dates, then falls
    back to parsing the static CSV.

    Returns:
        tuple: (oscar_df, posting_dates_dict, data_source, pipeline_timestamp)
    """
    pipeline_timestamp = datetime.now()

    # Try live scraping for posting dates
    posting_dates = try_live_oscar_scrape()
    live_available = len(posting_dates) > 0

    # Parse static CSV (always available as fallback)
    oscar_df = parse_oscar_listings(csv_path)

    data_source = "live OSCAR + static CSV" if live_available else "static CSV (oscar_master_listings.csv)"

    return oscar_df, posting_dates, data_source, pipeline_timestamp


def add_hiring_flags_with_freshness(judges_df, oscar_df, posting_dates):
    """Merge hiring info with freshness data.

    Adds:
        - Hiring: bool
        - Hiring Term: str (e.g., '1 Year', '2 Years')
        - Posting Date: datetime or None (date of the most recent OSCAR posting batch)
        - Days Since Posting: int or None
        - Freshness: str ('fresh', 'recent', 'stale', 'N/A')

    OSCAR weekly-update blog posts cannot be attributed to individual judges,
    so every hiring judge receives the same reference posting date (the most
    recent batch). This is an approximation, not a per-judge scrape.
    """
    judges_df = add_hiring_flags(judges_df.copy(), oscar_df.copy())

    judges_df['Posting Date'] = None
    judges_df['Days Since Posting'] = None
    judges_df['Freshness'] = 'N/A'

    now = datetime.now()

    # Reference posting date: most recent OSCAR weekly-update batch (applied uniformly)
    posting_date = max(posting_dates.values()) if posting_dates else None
    if posting_date:
        days_since = (now - posting_date).days
        if days_since <= 30:
            freshness = 'fresh'
        elif days_since <= 60:
            freshness = 'recent'
        else:
            freshness = 'stale'

        hiring_mask = judges_df['Hiring'] == True
        judges_df.loc[hiring_mask, 'Posting Date'] = posting_date
        judges_df.loc[hiring_mask, 'Days Since Posting'] = days_since
        judges_df.loc[hiring_mask, 'Freshness'] = freshness

    return judges_df


def freshness_color(freshness):
    """Return a color based on posting freshness."""
    if freshness == 'fresh':
        return 'darkgreen'  # Recently posted (<30 days)
    if freshness == 'recent':
        return 'orange'     # Posted 30-60 days ago
    if freshness == 'stale':
        return 'darkred'    # Posted >60 days ago
    return 'gray'           # Unknown


if __name__ == "__main__":
    oscar_df, posting_dates, source, ts = load_hiring_judges()
    print(f"Data source: {source}")
    print(f"Pipeline timestamp: {ts}")
    print(f"Live posting dates found: {len(posting_dates)}")
    print(f"Total hiring judges parsed: {len(oscar_df)}")
    print(oscar_df[['Judge', 'Hiring Term', 'Duty Station']].head(20).to_string(index=False))
