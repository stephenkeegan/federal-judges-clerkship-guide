import json
import urllib.parse
import urllib.request


def geocode(city, state=None):
    q = city if not state else f"{city}, {state}"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
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
    print("Nominatim geocoder ready")

if __name__ == "__main__":
    main()
