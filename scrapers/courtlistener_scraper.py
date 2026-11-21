import json
import time
import urllib.parse
import urllib.request

import pandas as pd


def fetch(judge):
    q = urllib.parse.quote(judge)
    url = f"https://www.courtlistener.com/api/rest/v4/opinions/?q={q}&order_by=-date_filed&page_size=5"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "judges-map/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        count = data.get("count", 0)
        results = data.get("results", [])
        recent = "; ".join([r.get("case_name","") for r in results[:3]])
        return count, recent
    except Exception:
        return None, None

def main():
    df = pd.concat([pd.read_csv("final_district.csv"), pd.read_csv("final_appeals.csv")], ignore_index=True)
    rows = []
    for _, r in df.iterrows():
        name = r["Judge"]
        count, recent = fetch(name)
        rows.append({"Judge": name, "Opinion Count": count, "Recent Opinions": recent})
        time.sleep(0.5)
    pd.DataFrame(rows).drop_duplicates("Judge").to_csv("courtlistener_data.csv", index=False)
    print("Saved courtlistener_data.csv")

if __name__ == "__main__":
    main()
