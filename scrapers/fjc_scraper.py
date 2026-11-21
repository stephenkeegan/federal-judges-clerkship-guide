import re
import time
import urllib.parse
import urllib.request

import pandas as pd


def fetch(name):
    url = "https://www.fjc.gov/history/judges/search?name=" + urllib.parse.quote(name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        # extract text content
        text = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        # find judge-specific snippet
        idx = text.lower().find(name.lower())
        snippet = text[idx:idx+400] if idx>=0 else text[:400]
        return snippet
    except Exception:
        return None

def main():
    df = pd.concat([pd.read_csv("final_district.csv"), pd.read_csv("final_appeals.csv")], ignore_index=True)
    rows = []
    for _, r in df.iterrows():
        name = r["Judge"]
        bio = fetch(name)
        rows.append({"Judge": name, "FJC Bio": bio})
        time.sleep(0.3)
    pd.DataFrame(rows).drop_duplicates("Judge").to_csv("fjc_data.csv", index=False)
    print("saved fjc_data.csv")

if __name__ == "__main__":
    main()
