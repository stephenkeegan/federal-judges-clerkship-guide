#add info
import re

import pandas as pd

from helper_functions import STATE_ABBREV, STATE_MAP

print("running add_info.py")

appeals = pd.read_csv("active_appeals.csv")
district = pd.read_csv("active_district.csv")

#add lat long from cities.csv
cities = pd.read_csv('cities.csv')
# Build lookup: city name -> list of (state, lat, lng)
city_multi_lookup = {}
for _, row in cities.iterrows():
    city = row['city']
    state = row['state']
    lat = row['lat']
    lng = row['lng']
    if city not in city_multi_lookup:
        city_multi_lookup[city] = []
    city_multi_lookup[city].append((state, lat, lng))

# Build state dominance map: city -> most common state
city_dominant_state = {}
for city, matches in city_multi_lookup.items():
    state_counts = {}
    for m in matches:
        s = m[0]
        state_counts[s] = state_counts.get(s, 0) + 1
    dominant = max(state_counts, key=state_counts.get)
    total = len(matches)
    dom_count = state_counts[dominant]
    city_dominant_state[city] = (dominant, dom_count / total if total > 0 else 0)

# Manual override: ambiguous cities where we know the federal court location
# Maps city name -> state abbreviation (used to filter city_multi_lookup)
CITY_STATE_OVERRIDE = {
    'Charlottesville': 'VA',
    'Dallas': 'TX',
    'Portland': 'OR',
    'Columbus': 'OH',
    'Birmingham': 'AL',
    'Alexandria': 'VA',
    'Atlanta': 'GA',
    'Baltimore': 'MD',
    'Boston': 'MA',
    'Brooklyn': 'NY',
    'Chicago': 'IL',
    'Cincinnati': 'OH',
    'Cleveland': 'OH',
    'Columbia': 'SC',
    'Denver': 'CO',
    'Detroit': 'MI',
    'Honolulu': 'HI',
    'Houston': 'TX',
    'Huntsville': 'AL',
    'Indianapolis': 'IN',
    'Jacksonville': 'FL',
    'Kansas City': 'MO',
    'Las Vegas': 'NV',
    'Los Angeles': 'CA',
    'Louisville': 'KY',
    'Manhattan': 'NY',
    'Memphis': 'TN',
    'Miami': 'FL',
    'Milwaukee': 'WI',
    'Minneapolis': 'MN',
    'Nashville': 'TN',
    'Newark': 'NJ',
    'New Orleans': 'LA',
    'New York': 'NY',
    'Oklahoma City': 'OK',
    'Omaha': 'NE',
    'Orlando': 'FL',
    'Philadelphia': 'PA',
    'Phoenix': 'AZ',
    'Pittsburgh': 'PA',
    'Richmond': 'VA',
    'Sacramento': 'CA',
    'Salt Lake City': 'UT',
    'San Antonio': 'TX',
    'San Diego': 'CA',
    'San Francisco': 'CA',
    'San Jose': 'CA',
    'Seattle': 'WA',
    'St. Louis': 'MO',
    'Tampa': 'FL',
    'Tucson': 'AZ',
    'Washington': 'DC',
    'Charleston': 'WV',
    'Jackson': 'MS',
    'Montgomery': 'AL',
    'Mobile': 'AL',
    'Roanoke': 'VA',
    'Scranton': 'PA',
    'Syracuse': 'NY',
    'Rochester': 'NY',
    'Albany': 'NY',
    'Trenton': 'NJ',
    'Camden': 'NJ',
    'White Plains': 'NY',
    'Hammond': 'IN',
    'Concord': 'NH',
    'Greensboro': 'NC',
    'Lexington': 'KY',
    'Aberdeen': 'SD',
    'Macon': 'GA',
    'Springfield': 'MA',
    'Oakland': 'CA',
    'Wilmington': 'DE',
    'Charlotte': 'NC',
    'Eugene': 'OR',
    'Burlington': 'VT',
    'Lafayette': 'LA',
    'Greenville': 'SC',
    'Laredo': 'TX',
    'Toledo': 'OH',
    'Harrisburg': 'PA',
    'Riverside': 'CA',
    'Hartford': 'CT',
    'Norfolk': 'VA',
    'Newport News': 'VA',
    'Winston-Salem': 'NC',
    'Providence': 'RI',
    'Buffalo': 'NY',
    'Bridgeport': 'CT',
    'Knoxville': 'TN',
    'Beaumont': 'TX',
    'Dayton': 'OH',
    'Greeneville': 'TN',
    'Bismarck': 'ND',
    'Utica': 'NY',
    'Augusta': 'GA',
    'Flint': 'MI',
    'Brownsville': 'TX',
    'Rockford': 'IL',
    'Madison': 'WI',
    'Grand Rapids': 'MI',
    'Lincoln': 'NE',
}

# Direct coords override: cities not in cities.csv under their duty-station name
CITY_COORDS_OVERRIDE = {
    'Manhattan': (40.7082, -74.0117),  # Thurgood Marshall US Courthouse, NY
    'Winston-Salem': (36.0999, -80.2442),  # Winston-Salem, NC
    'Pittsburgh': (40.4397, -79.9964),  # Joseph F. Weis Jr. Courthouse, PA
    'Greeneville': (36.1651, -82.8316),  # Greeneville, TN
    'Richland': (46.4073, -119.2764),  # Richland, WA (E.D. Wash.)
    'Oxford': (34.3665, -89.5215),  # Oxford, MS (N.D. Miss.)
    'Benton': (33.1559, -94.2289),  # Benton, AR (W.D. Ark.)
    'Akron': (41.0814, -81.5190),  # Akron, OH (N.D. Ohio)
    'Peoria': (40.6936, -89.5890),  # Peoria, IL (C.D. Ill.)
    'Florence': (34.7998, -87.6773),  # Florence, AL (N.D. Ala.)
    'Santa Fe': (35.6870, -105.9378),  # Santa Fe, NM (D.N.M.)
    'Monroe': (32.5022, -92.1184),  # Monroe, LA (W.D. La.)
    'Sherman': (33.6357, -96.6089),  # Sherman, TX (E.D. Tex.)
    'St. George Salt Lake City': (40.7608, -111.8911),  # Salt Lake City, UT (D. Utah)
    'London': (37.1290, -84.0832),  # London, KY (E.D. Ky.)
    'Urbana': (40.1106, -88.2073),  # Urbana, IL (C.D. Ill.)
    'San Antonio, Texas': (29.4219, -98.4895),  # San Antonio, TX (W.D. Tex.)
    'Covington': (39.0828, -84.5075),  # Covington, KY (E.D. Ky.)
    'Natchez': (31.5604, -91.4033),  # Natchez, MS (S.D. Miss.)
    'St. George': (37.1049, -113.5837),  # St. George, UT (D. Utah)
    'Haga tn a': (13.4443, 144.7937),  # Hagatna, Guam (D. Guam)
    'Frankfort': (38.1998, -84.8742),  # Frankfort, KY (E.D. Ky.)
    'Martinsburg': (39.4563, -77.9638),  # Martinsburg, WV (N.D. W.Va.)
    'Grand Junction': (39.0639, -108.5507),  # Grand Junction, CO (D. Colo.)
    'Lansing': (42.7321, -84.5545),  # Lansing, MI (W.D. Mich.)
    'Marshall': (32.5449, -94.3684),  # Marshall, TX (E.D. Tex.)
    'Abingdon': (36.7079, -81.9716),  # Abingdon, VA (W.D. Va.)
    'Galveston': (29.3014, -94.7977),  # Galveston, TX (S.D. Tex.)
    'Victoria': (28.8054, -96.9972),  # Victoria, TX (S.D. Tex.)
    'Allentown': (40.6084, -75.4902),  # Allentown, PA (E.D. Pa.)
    'Wheeling': (40.0640, -80.7209),  # Wheeling, WV (N.D. W.Va.)
    'Wilkes-Barre': (41.2456, -75.8767),  # Wilkes-Barre, PA (M.D. Pa.)
    'Bangor': (44.8012, -68.7778),  # Bangor, ME (D. Me.)
    'Brunswick': (31.1496, -81.4915),  # Brunswick, GA (S.D. Ga.)
    'Rutland': (43.6106, -72.9726),  # Rutland, VT (D. Vt.)
    'Williamsport': (41.2417, -77.0016),  # Williamsport, PA (M.D. Pa.)
    'Lynchburg': (37.4138, -79.1423),  # Lynchburg, VA (W.D. Va.)
    'Fargo': (46.8772, -96.7898),  # Fargo, ND (D.N.D.)
    'Savannah': (32.0803, -81.0912),  # Savannah, GA (S.D. Ga.)
    'Saipan': (15.1129, 145.7243),  # Saipan, N. Mariana Islands (D. N. Mariana Islands)
    'McAllen': (26.2034, -98.2300),  # McAllen, TX (S.D. Tex.)
    'Huntington': (38.4152, -82.4422),  # Huntington, WV (S.D. W.Va.)
    'Texarkana': (33.4251, -94.0477),  # Texarkana, TX/AR (E.D. Tex.)
    'Washington, D.C. San Antonio, Texas': (38.8911, -77.0321),  # Washington, DC
    'Plano': (33.0198, -96.6989),  # Plano, TX (E.D. Tex.)
    'Johnstown': (40.3267, -78.9221),  # Johnstown, PA (W.D. Pa.)
    'El Dorado': (33.2066, -92.6663),  # El Dorado, AR (W.D. Ark.)
    'Billings': (45.7833, -108.5007),  # Billings, MT (D. Mont.)
    'Erie': (42.1292, -80.0851),  # Erie, PA (W.D. Pa.)
    'Bay City': (43.5945, -83.8894),  # Bay City, MI (E.D. Mich.)
    'Fayetteville': (36.0626, -94.1574),  # Fayetteville, AR (W.D. Ark.)
    'Anderson': (34.5035, -82.6897),  # Anderson, SC (D.S.C.)
    'Clarksburg Elkins': (39.2810, -80.3437),  # Clarksburg, WV (N.D. W.Va.)
    'Coeur d\'Alene': (47.6777, -116.7805),  # Coeur d'Alene, ID (D. Idaho)
    'San Juan': (18.4655, -66.1057),  # San Juan, PR (D.P.R.)
}


def extract_state_from_district(district_str):
    """Extract state abbreviation from a district string like 'D. Alaska', 'N.D. Tex.', 'S.D. Fla.'"""
    if not isinstance(district_str, str):
        return None
    district_str = district_str.strip()
    # Try to match state abbreviation at the end
    for abbrev in STATE_MAP:
        if district_str.endswith(abbrev):
            return abbrev
    # Try to match full state name
    for abbrev, full in STATE_MAP.items():
        if full.lower() in district_str.lower():
            return abbrev
    # Try specific patterns like "D. Alaska", "N.D. Tex."
    parts = district_str.split()
    if parts:
        last = parts[-1]
        if last in STATE_MAP:
            return last
        if last in STATE_ABBREV:
            return STATE_ABBREV[last]
    return None


def extract_state_from_circuit(circuit_str):
    """Map circuit number to a representative state (for disambiguation fallback)."""
    if not isinstance(circuit_str, str):
        return None
    circuit_str = circuit_str.strip()
    CIRCUIT_STATE = {
        'First': 'ME', 'Second': 'NY', 'Third': 'PA', 'Fourth': 'VA',
        'Fifth': 'TX', 'Sixth': 'OH', 'Seventh': 'IL', 'Eighth': 'MO',
        'Ninth': 'CA', 'Tenth': 'CO', 'Eleventh': 'FL', 'Fed. Cir.': 'DC',
        'DC Cir.': 'DC',
    }
    for key, state in CIRCUIT_STATE.items():
        if key.lower() in circuit_str.lower():
            return state
    return None


def clean_duty_station(ds):
    if not isinstance(ds, str):
        return ds
    ds = ds.replace('Ft.', 'Fort').replace('St.', 'Saint').replace('Mt.', 'Mount')
    return ds.strip()


def parse_duty_station(ds):
    """Parse duty station into list of candidate city name strings and optional state."""
    if not isinstance(ds, str) or not ds.strip():
        return [], None
    ds = clean_duty_station(ds)

    state = None
    # Check for ", ST" or ", D.C." suffix
    m = re.match(r'^(.+?),\s*([A-Z]{2}|D\.C\.)$', ds)
    if m:
        city_part = m.group(1).strip()
        state_raw = m.group(2).upper()
        if state_raw == 'D.C.':
            state = 'DC'
        else:
            state = state_raw
    else:
        city_part = ds

    candidates = [city_part]
    # If multiple words, try each word individually (for multi-city stations like "Waco Austin")
    words = city_part.split()
    for word in words:
        if word not in candidates:
            candidates.append(word)
    # Try two-word combinations (for cities like "Newport News", "Salt Lake City")
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if bigram not in candidates:
            candidates.append(bigram)
    return candidates, state


def geocode_duty_station(ds, district_str=None, circuit_str=None):
    """Geocode a duty station to (lat, lng) of its duty-station city.

    Priority:
    1. Direct coords override (cities not in cities.csv under that name)
    2. State from duty station suffix (e.g. "Charlottesville, VA")
    3. State from District column
    4. State from Circuit column
    5. Manual state override map (known federal court locations)
    6. Unique city match
    7. Dominant state (>80% of matches)
    """
    if not isinstance(ds, str) or not ds.strip():
        return (None, None)

    cities_list, duty_state = parse_duty_station(ds)

    # 1. Direct coords override
    for city_name in cities_list:
        if city_name in CITY_COORDS_OVERRIDE:
            return CITY_COORDS_OVERRIDE[city_name]

    # Determine state
    state = duty_state
    if state is None and district_str is not None:
        state = extract_state_from_district(district_str)
    if state is None and circuit_str is not None:
        state = extract_state_from_circuit(circuit_str)
    if state is None:
        # Check manual override for first candidate
        for c in cities_list:
            if c in CITY_STATE_OVERRIDE:
                state = CITY_STATE_OVERRIDE[c]
                break

    # Try each city name
    for city_name in cities_list:
        if city_name not in city_multi_lookup:
            continue
        matches = city_multi_lookup[city_name]
        if state is not None:
            state_matches = [m for m in matches if m[0] == state]
            if state_matches:
                return (state_matches[0][1], state_matches[0][2])
        else:
            if len(matches) == 1:
                return (matches[0][1], matches[0][2])
            # Fallback: dominant state if >80%
            if city_name in city_dominant_state:
                dom_state, dom_pct = city_dominant_state[city_name]
                if dom_pct > 0.8:
                    dom_matches = [m for m in matches if m[0] == dom_state]
                    if dom_matches:
                        return (dom_matches[0][1], dom_matches[0][2])

    return (None, None)


def geocode_judges(district_df, appeals_df):
    """Add lat/lng columns to district and appeals judge DataFrames."""
    lat_lng = district.apply(
        lambda row: pd.Series(geocode_duty_station(
            row['Duty Station'],
            row.get('District'),
            None
        )), axis=1)
    district['lat'] = lat_lng[0]
    district['lng'] = lat_lng[1]

    lat_lng = appeals.apply(
        lambda row: pd.Series(geocode_duty_station(
            row['Duty Station'],
            None,
            row.get('Circuit')
        )), axis=1)
    appeals['lat'] = lat_lng[0]
    appeals['lng'] = lat_lng[1]
    return district, appeals


def main():
    district = pd.read_csv("active_district.csv")
    appeals = pd.read_csv("active_appeals.csv")
    district, appeals = geocode_judges(district, appeals)

    district.to_csv("final_district.csv", index=False)
    appeals.to_csv("final_appeals.csv", index=False)

    print("Added lat/long info from cities.csv and saved to final_district.csv and final_appeals.csv")


if __name__ == "__main__":
    main()
