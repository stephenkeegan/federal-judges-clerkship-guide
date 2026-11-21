import re
import time
import urllib.parse
import urllib.request

import pandas as pd


def fetch(name):
    url = "https://scholar.google.com/scholar?q=" + urllib.parse.quote(f'"{name}"')
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        m = re.search(r'About ([\d,]+) results', html)
        return m.group(1) if m else None
    except Exception:
        return None

def main():
    df = pd.concat([pd.read_csv("final_district.csv"), pd.read_csv("final_appeals.csv")], ignore_index=True)
    rows = []
    for _, r in df.iterrows():
        rows.append({"Judge": r["Judge"], "Scholar Results": fetch(r["Judge"])})
        time.sleep(5)
    pd.DataFrame(rows).drop_duplicates("Judge").to_csv("gscholar_data.csv", index=False)
    print("saved")

if __name__ == "__main__":
    main()
