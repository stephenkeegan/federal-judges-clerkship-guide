import json
import urllib.request

import pandas as pd


def main():
    # Public CourtListener people search (no API key needed for basic)
    url = "https://www.courtlistener.com/api/rest/v4/people/?name=Wilkinson&page_size=5"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "judges-map/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        print("CourtListener OK, results:", len(data.get("results", [])))
    except Exception as e:
        print("CourtListener fetch failed:", e)
    pd.DataFrame().to_csv("courtlistener_judges.csv", index=False)

if __name__ == "__main__":
    main()
