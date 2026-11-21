import json
import time
import urllib.parse
import urllib.request

import pandas as pd


def geocode(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": query, "format": "json", "limit": 1})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "judges-map/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

def main():
    for f in ["final_district.csv", "final_appeals.csv"]:
        df = pd.read_csv(f)
        lats, lngs = [], []
        for _, r in df.iterrows():
            ds = r.get("Duty Station")
            st = r.get("District") or r.get("Circuit")
            q = f"US Courthouse {ds} {st}" if pd.notna(ds) else None
            lat, lng = (None, None)
            if q:
                lat, lng = geocode(q)
                time.sleep(1)
            # fallback to existing
            if lat is None:
                lat = r.get("lat")
                lng = r.get("lng")
            lats.append(lat)
            lngs.append(lng)
        df["lat"] = lats
        df["lng"] = lngs
        df.to_csv(f, index=False)
        print("updated", f)

if __name__ == "__main__":
    main()
