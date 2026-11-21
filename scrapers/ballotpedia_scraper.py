import re
import time
import urllib.parse
import urllib.request

import pandas as pd


def fetch(name):
    url = "https://ballotpedia.org/" + urllib.parse.quote(name.replace(" ", "_"))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        idx = text.lower().find(name.lower())
        return text[idx:idx+500] if idx>=0 else text[:500]
    except Exception:
        return None

def main():
    df = pd.concat([pd.read_csv("final_district.csv"), pd.read_csv("final_appeals.csv")], ignore_index=True)
    rows = []
    for _, r in df.iterrows():
        rows.append({"Judge": r["Judge"], "Ballotpedia": fetch(r["Judge"])})
        time.sleep(0.5)
    pd.DataFrame(rows).drop_duplicates("Judge").to_csv("ballotpedia_data.csv", index=False)
    print("saved")

if __name__ == "__main__":
    main()
