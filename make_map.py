# Builds interactive Folium map of federal judges with hiring/OSCAR info.
import math
import re
from datetime import datetime

import folium
import pandas as pd
from folium.plugins import MarkerCluster

from helper_functions import STATE_MAP, derive_party
from oscar_scraper import add_hiring_flags_with_freshness, freshness_color, load_hiring_judges


def clean_data(file_path):
    df = pd.read_csv(file_path).dropna(subset=['lat', 'lng'])
    return df.drop_duplicates(subset=['Judge'])


def years_of_service(row):
    """Compute approximate years of service on bench."""
    now = datetime.now().year
    for col in ('Began active service', 'Began active service[3]', 'Began active service[7]'):
        val = row.get(col)
        if isinstance(val, str):
            m = re.search(r'\b(1[7-9]\d\d|20\d\d)\b', val)
            if m:
                start_year = int(m.group(1))
                if 1789 <= start_year <= now:
                    return now - start_year
    return None


def color_for(party):
    if party == 'Republican':
        return 'red'
    if party == 'Democrat':
        return 'blue'
    return 'gray'


def marker_for(hiring, freshness='N/A'):
    if hiring:
        fcolor = freshness_color(freshness)
        return dict(radius=9, color=fcolor, fill_color=fcolor, fill_opacity=0.9, weight=2)
    return dict(radius=6, color=None, fill_color=None, fill_opacity=0.7, weight=1)


COURTHOUSE_COORDS_FALLBACK = {
    'New York': (40.7082, -74.0117),
    'Manhattan': (40.7082, -74.0117),
    'Washington': (38.8911, -77.0321),
    'Washington, D.C.': (38.8911, -77.0321),
    'Los Angeles': (34.0537, -118.2433),
    'Chicago': (41.8795, -87.6324),
    'Boston': (42.3572, -71.0555),
    'Philadelphia': (39.9496, -75.1503),
    'San Francisco': (37.7793, -122.4193),
    'Atlanta': (33.7515, -84.3896),
    'Miami': (25.7746, -80.1936),
    'Dallas': (32.7758, -96.7954),
    'Houston': (29.7558, -95.3633),
    'Seattle': (47.5995, -122.3334),
    'Denver': (39.7420, -104.9919),
    'Detroit': (42.3284, -83.0412),
    'Baltimore': (39.2882, -76.6125),
    'Pittsburgh': (40.4397, -79.9964),
    'St. Louis': (38.6269, -90.1983),
    'Minneapolis': (44.9785, -93.2648),
    'New Orleans': (29.9531, -90.0642),
    'Charleston': (32.7778, -79.9301),
    'Charlottesville': (38.0293, -78.4767),
    'Richmond': (37.5390, -77.4381),
    'Norfolk': (36.8468, -76.2852),
    'Alexandria': (38.8047, -77.0469),
    'Brooklyn': (40.6913, -73.9917),
    'Brooklyn, NY': (40.6913, -73.9917),
    'Buffalo': (42.8857, -78.8780),
    'Albany': (42.6501, -73.7562),
    'Syracuse': (43.0482, -76.1474),
    'Rochester': (43.1534, -77.6112),
    'White Plains': (41.0329, -73.7625),
    'Newark': (40.7324, -74.1691),
    'Camden': (39.9417, -75.1195),
    'Trenton': (40.2198, -74.7614),
    'Wilmington': (39.7442, -75.5465),
    'Cleveland': (41.4963, -81.6927),
    'Cincinnati': (39.1015, -84.5120),
    'Columbus': (39.9599, -82.9862),
    'Indianapolis': (39.7669, -86.1582),
    'Milwaukee': (43.0394, -87.9143),
    'Nashville': (36.1637, -86.7784),
    'Memphis': (35.1441, -90.0474),
    'Louisville': (38.2542, -85.7565),
    'Knoxville': (35.9606, -83.9208),
    'Greenville': (34.8497, -82.4011),
    'Spartanburg': (34.9496, -81.9332),
    'Charleston, WV': (38.3498, -81.6333),
    'Huntington': (38.4152, -82.4422),
    'Bluefield': (37.2444, -81.2236),
    'Birmingham': (33.5137, -86.8134),
    'Mobile': (30.6904, -88.0389),
    'Montgomery': (32.3742, -86.2974),
    'Huntsville': (34.7269, -86.5861),
    'Savannah': (32.0803, -81.0912),
    'Augusta': (33.4712, -81.9656),
    'Tallahassee': (30.4383, -84.2807),
    'Jacksonville': (30.3218, -81.6556),
    'Orlando': (28.5383, -81.3792),
    'Tampa': (27.9478, -82.4583),
    'Fort Lauderdale': (26.1184, -80.1433),
    'West Palm Beach': (26.7107, -80.0520),
    'Fort Myers': (26.6406, -81.8725),
    'Ocala': (29.1864, -82.1395),
    'Gainesville': (29.6516, -82.3248),
    'Panama City': (30.1595, -85.6601),
    'Pensacola': (30.4138, -87.2151),
    'Baton Rouge': (30.4495, -91.1866),
    'Shreveport': (32.5131, -93.7501),
    'Monroe': (32.5022, -92.1184),
    'Lafayette': (30.2230, -92.0193),
    'Lake Charles': (30.2256, -93.2164),
}


def clean_duty_for_lookup(ds):
    """Clean a duty station string for matching against fallback coordinates."""
    if not isinstance(ds, str):
        return ds
    ds = ds.strip()
    ds = re.sub(r',\s*([A-Z]{2}|D\.C\.)$', '', ds).strip()
    for abbrev, full in STATE_MAP.items():
        ds = re.sub(r',\s*' + re.escape(full) + r'$', '', ds, flags=re.I).strip()
    ds = ds.replace('Ft.', 'Fort').replace('St.', 'Saint').replace('Mt.', 'Mount')
    ds = ds.rstrip('.,').strip()
    return ds


def geocode_fallback(row):
    duty_station = str(row.get('Duty Station', '')).strip()
    if duty_station.lower() in ('none', 'inactive', 'nan'):
        return None
    cleaned = clean_duty_for_lookup(duty_station)
    if cleaned in COURTHOUSE_COORDS_FALLBACK:
        return COURTHOUSE_COORDS_FALLBACK[cleaned]
    first_word = cleaned.split()[0] if cleaned else None
    if first_word and first_word in COURTHOUSE_COORDS_FALLBACK:
        return COURTHOUSE_COORDS_FALLBACK[first_word]
    return None


def build_map():
    # 1. Data Prep
    import os
    dist_path = "final_district_enriched.csv" if os.path.exists("final_district_enriched.csv") else "final_district.csv"
    circ_path = "final_appeals_enriched.csv" if os.path.exists("final_appeals_enriched.csv") else "final_appeals.csv"
    df_district = clean_data(dist_path)
    df_circuit = clean_data(circ_path)

    # Attach hiring flags + term info + freshness from OSCAR
    oscar_df, posting_dates, data_source, pipeline_timestamp = load_hiring_judges()

    # Load FJC data if available
    import os
    fjc_data = {}
    if os.path.exists("fjc_data.csv"):
        fdf = pd.read_csv("fjc_data.csv")
        for _, r in fdf.iterrows():
            fjc_data[str(r.get("Judge"))] = r
    # Load CourtListener opinion data if available
    cl_data = {}
    if os.path.exists("courtlistener_data.csv"):
        cldf = pd.read_csv("courtlistener_data.csv")
        for _, r in cldf.iterrows():
            cl_data[str(r.get("Judge"))] = r
    df_district = add_hiring_flags_with_freshness(df_district, oscar_df, posting_dates)
    df_circuit = add_hiring_flags_with_freshness(df_circuit, oscar_df, posting_dates)

    df_district['Party'] = df_district['Appointed By'].apply(derive_party)
    df_circuit['Party'] = df_circuit['Appointed By'].apply(derive_party)

    print(f"District judges: {len(df_district)} | hiring: {int(df_district['Hiring'].sum())}")
    print(f"Circuit judges:  {len(df_circuit)} | hiring: {int(df_circuit['Hiring'].sum())}")
    print(f"District parties: {df_district['Party'].value_counts().to_dict()}")
    print(f"Circuit parties:  {df_circuit['Party'].value_counts().to_dict()}")
    print(f"OSCAR data source: {data_source}")
    print(f"Pipeline timestamp: {pipeline_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Apply fallback coordinates only when lat/lng missing
    for df in [df_district, df_circuit]:
        for idx, row in df.iterrows():
            lat = df.at[idx, 'lat']
            lng = df.at[idx, 'lng']
            if pd.isna(lat) or pd.isna(lng):
                coord = geocode_fallback(row)
                if coord is not None:
                    df.at[idx, 'lat'] = coord[0]
                    df.at[idx, 'lng'] = coord[1]

    _used_coords = {}

    def jitter_coords(lat, lng, key):
        if key not in _used_coords:
            _used_coords[key] = 0
            return (lat, lng)
        _used_coords[key] += 1
        offset = 0.008 * _used_coords[key]
        angle = _used_coords[key] * 0.6
        return (lat + offset * math.sin(angle),
                lng + offset * math.cos(angle))

    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Esri Street Map', overlay=False, control=True, show=True,
    ).add_to(m)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; OpenStreetMap contributors &copy; CARTO',
        name='CartoDB Positron', overlay=False, control=True, show=False,
    ).add_to(m)

    def na(val):
        if pd.isna(val):
            return 'N/A'
        return val

    def format_date(val):
        if pd.isna(val) or val is None or val == 'N/A':
            return 'N/A'
        if isinstance(val, str):
            return val
        try:
            return val.strftime('%b %d, %Y')
        except Exception:
            return str(val)

    def popup_html(row):
        is_hiring = bool(row.get('Hiring', False))
        court = row.get('Court', row.get('Circuit', 'N/A'))
        if (pd.isna(court) or str(court).strip() == '' or str(court) == 'N/A') and isinstance(row.get('Court [Note 2]'), str):
            court = row['Court [Note 2]']
        if pd.isna(court) or str(court).strip() == '' or str(court) == 'N/A':
            court = str(row.get('Title', 'Judge'))

        judge_name = str(row['Judge']).replace(' ', '+')
        oscar_search = f"https://www.google.com/search?q=site:oscar.uscourts.gov+{judge_name}+clerk"
        cl_search = f"https://www.courtlistener.com/?q={judge_name}&type=r"
        oscar_home = "https://oscar.uscourts.gov"

        nom_date = na(row.get('Nomination date', 'N/A'))
        conf_vote = na(row.get('Confirmation vote', 'N/A'))
        began_service = na(row.get('Began active service', row.get('Began active service[7]', row.get('Began active service[3]', 'N/A'))))
        if began_service == 'N/A':
            import re
            summ = str(row.get('Wikipedia Summary',''))
            m = re.search(r'appointed in (\d{4})', summ)
            if m:
                began_service = m.group(1)
        title = na(row.get('Title', 'N/A'))
        born = row.get('Born', 'N/A')
        if pd.notna(born) and str(born).strip() != '':
            try:
                born = int(float(born))
            except Exception:
                pass

        hiring_term = na(row.get('Hiring Term', 'N/A'))
        cl_row = cl_data.get(str(row['Judge']), {})
        op_count = cl_row.get('Opinion Count', 'N/A') if isinstance(cl_row, dict) else cl_row.get('Opinion Count', 'N/A') if hasattr(cl_row,'get') else 'N/A'
        recent_ops = cl_row.get('Recent Opinions', 'N/A') if hasattr(cl_row,'get') else 'N/A' 
        freshness = na(row.get('Freshness', 'N/A'))
        posting_date = format_date(row.get('Posting Date', 'N/A'))
        days_since = row.get('Days Since Posting', 'N/A')
        yos = years_of_service(row)
        yos_str = yos if yos is not None else 'N/A'

        freshness_style = ""
        if freshness == 'fresh':
            freshness_style = 'color: darkgreen; font-weight: bold;'
        elif freshness == 'recent':
            freshness_style = 'color: orange; font-weight: bold;'
        elif freshness == 'stale':
            freshness_style = 'color: darkred; font-weight: bold;'

        bio = na(row.get('Biography (Wikipedia)', row.get('Biography', 'N/A')))
        off = na(row.get('Official Source / Wikipedia', row.get('Official Source', row.get('Wikipedia URL', 'N/A'))))
        if off == 'N/A':
            off_link = oscar_home
            off_text = 'OSCAR Homepage'
        else:
            off_link = str(off)
            off_text = 'Official Source / Wikipedia'

        bio_html = ''
        if bio != 'N/A':
            bio_clean = str(bio).replace('\n', '<br/>')
            bio_html = f'<hr style="margin:6px 0;"><p style="margin:4px 0; font-size:12px; line-height:1.4;"><b>About:</b> {bio_clean}</p>'

        # Unique id for this marker's tab toggle so popups don't collide.
        uid = f"pp{abs(hash(row['Judge'])) % (10**8)}"
        popup = f"""
        <div style="font-family: Arial; width: 360px; max-height: 500px; overflow-y: auto;">
            <div style="display:flex;gap:6px;margin-bottom:6px;">
                <button onclick="document.getElementById('{uid}h').style.display='block'; document.getElementById('{uid}w').style.display='none';" style="font-size:11px;">Hiring</button>
                <button onclick="document.getElementById('{uid}h').style.display='none'; document.getElementById('{uid}w').style.display='block';" style="font-size:11px;">Workload</button>
            </div>
            <div id="{uid}h">
            <h4 style="margin:0 0 6px 0;">{row['Judge']}</h4>
            <p style="margin:2px 0;"><b>Title:</b> {title}</p>
            <p style="margin:2px 0;"><b>Court:</b> {court}</p>
            <p style="margin:2px 0;"><b>Duty Station:</b> {na(row.get('Duty Station', 'N/A'))}</p>
            <p style="margin:2px 0;"><b>Appointed By:</b> {na(row.get('Appointed By', 'N/A'))}</p>
            <p style="margin:2px 0;"><b>Party:</b> {row.get('Party', 'Other')}</p>
            <p style="margin:2px 0;"><b>Born:</b> {born}</p>
            <p style="margin:2px 0;"><b>Nominated:</b> {nom_date}</p>
            <p style="margin:2px 0;"><b>Confirmation Vote:</b> {conf_vote}</p>
            <p style="margin:2px 0;"><b>Began Service:</b> {began_service}</p>
            <p style="margin:2px 0;"><b>Years of Service (approx):</b> {yos_str}</p>
            <p style="margin:2px 0;"><b>Active Term:</b> {na(row.get('Active Term', 'N/A'))}</p>
            <p style="margin:2px 0;"><b>Hiring Clerks:</b> <span style="{freshness_style}">{'YES' if is_hiring else 'No'}</span></p>
            {'<p style="margin:2px 0;"><b>Hiring Term:</b> ' + hiring_term + '</p>' if is_hiring else ''}
            {'<p style="margin:2px 0;"><b>Posted:</b> ' + posting_date + ' (' + str(days_since) + ' days ago)</p>' if is_hiring and posting_date != 'N/A' else ''}
            {bio_html}
            <p style="margin:4px 0; font-size:12px;"><b>Wikipedia Summary:</b> {na(row.get('Wikipedia Summary','N/A'))}</p>

            <p style="margin:2px 0;"><b>Education:</b> {na(row.get('Education','N/A'))}</p>
            <p style="margin:2px 0;"><b>Alma mater:</b> {na(row.get('Alma mater','N/A'))}</p>

            </div>
            <div id="{uid}w" style="display:none;">
            <p style="margin:2px 0;"><b>Opinion Count:</b> {op_count}</p>
            <p style="margin:2px 0;"><b>Recent Opinions:</b> {recent_ops}</p>
            <a href="{cl_search}" target="_blank" style="font-size:13px; color:#0066cc;">CourtListener opinions</a>
            &nbsp;|&nbsp;
            <a href="https://scholar.google.com/scholar?q={judge_name}" target="_blank" style="font-size:13px; color:#0066cc;">Google Scholar</a>
            &nbsp;|&nbsp;
            <a href="https://www.justia.com/search?q={judge_name}" target="_blank" style="font-size:13px; color:#0066cc;">Justia</a>
            </div>
            <hr style="margin:6px 0;">
            <a href="{oscar_search}" target="_blank" style="font-size:13px; color:#0066cc;">Find clerkships on OSCAR (Google)</a>
            &nbsp;|&nbsp;
            <a href="{cl_search}" target="_blank" style="font-size:13px; color:#0066cc;">CourtListener opinions</a>
            &nbsp;|&nbsp;
            <a href="https://scholar.google.com/scholar?q={judge_name}" target="_blank" style="font-size:13px; color:#0066cc;">Google Scholar</a>
            &nbsp;|&nbsp;
            <a href="https://www.justia.com/search?q={judge_name}" target="_blank" style="font-size:13px; color:#0066cc;">Justia</a>
            &nbsp;|&nbsp;
            <a href="{off_link}" target="_blank" style="font-size:13px; color:#0066cc;">{off_text}</a>
        </div>
        """
        return popup

    def add_markers(df, cluster, hiring_only=False, party=None, president=None, hiring_term=None, freshness=None, layer_tag=""):
        subset = df
        if hiring_only:
            subset = subset[subset['Hiring'] == True]
        if party is not None:
            subset = subset[subset['Party'] == party]
        if president is not None:
            subset = subset[subset['Appointed By'] == president]
        if hiring_term is not None:
            subset = subset[(subset['Hiring'] == True) & (subset['Hiring Term'] == hiring_term)]
        if freshness is not None:
            subset = subset[(subset['Hiring'] == True) & (subset['Freshness'] == freshness)]

        for idx, row in subset.iterrows():
            is_hiring = bool(row.get('Hiring', False))
            col = freshness_color(row.get('Freshness', 'N/A')) if is_hiring else color_for(row.get('Party', 'Other'))
            coord_key = f"{row['lat']:.4f}_{row['lng']:.4f}"
            jittered_lat, jittered_lng = jitter_coords(row['lat'], row['lng'], coord_key)
            folium.CircleMarker(
                location=[jittered_lat, jittered_lng], radius=marker_for(is_hiring, row.get('Freshness', 'N/A'))['radius'],
                tooltip=f"{row['Judge']} - {'Hiring' if is_hiring else 'Not hiring'}",
                popup=folium.Popup(popup_html(row), max_width=340),
                color=col, fill=True, fill_color=col,
                fill_opacity=marker_for(is_hiring, row.get('Freshness', 'N/A'))['fill_opacity'], weight=marker_for(is_hiring, row.get('Freshness', 'N/A'))['weight'],
            ).add_to(cluster)

    fg_dist_all = folium.FeatureGroup(name="District - All", show=True)
    cl_dist_all = MarkerCluster().add_to(fg_dist_all)
    add_markers(df_district, cl_dist_all, layer_tag="dist_all")
    fg_dist_all.add_to(m)

    fg_circ_all = folium.FeatureGroup(name="Circuit - All", show=True)
    cl_circ_all = MarkerCluster().add_to(fg_circ_all)
    add_markers(df_circuit, cl_circ_all, layer_tag="circ_all")
    fg_circ_all.add_to(m)

    fg_dist_hire = folium.FeatureGroup(name="District - Hiring Clerks", show=False)
    cl_dist_hire = MarkerCluster().add_to(fg_dist_hire)
    add_markers(df_district, cl_dist_hire, hiring_only=True, layer_tag="dist_hire")
    fg_dist_hire.add_to(m)

    fg_circ_hire = folium.FeatureGroup(name="Circuit - Hiring Clerks", show=False)
    cl_circ_hire = MarkerCluster().add_to(fg_circ_hire)
    add_markers(df_circuit, cl_circ_hire, hiring_only=True, layer_tag="circ_hire")
    fg_circ_hire.add_to(m)

    hiring_terms = sorted(set(
        df_district[df_district['Hiring'] == True]['Hiring Term'].dropna().unique().tolist() +
        df_circuit[df_circuit['Hiring'] == True]['Hiring Term'].dropna().unique().tolist()
    ))
    for term in hiring_terms:
        fg = folium.FeatureGroup(name=f"District - Hiring: {term}", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_district, cl, hiring_term=term, layer_tag=f"dist_hire_{term}")
        fg.add_to(m)
        fg = folium.FeatureGroup(name=f"Circuit - Hiring: {term}", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_circuit, cl, hiring_term=term, layer_tag=f"circ_hire_{term}")
        fg.add_to(m)

    for fresh in ['fresh', 'recent', 'stale']:
        fg = folium.FeatureGroup(name=f"District - Hiring ({fresh})", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_district, cl, freshness=fresh, layer_tag=f"dist_fresh_{fresh}")
        fg.add_to(m)
        fg = folium.FeatureGroup(name=f"Circuit - Hiring ({fresh})", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_circuit, cl, freshness=fresh, layer_tag=f"circ_fresh_{fresh}")
        fg.add_to(m)

    for party in ['Republican', 'Democrat', 'Other']:
        fg = folium.FeatureGroup(name=f"District - {party} Appointees", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_district, cl, party=party, layer_tag=f"dist_{party}")
        fg.add_to(m)
        fg = folium.FeatureGroup(name=f"Circuit - {party} Appointees", show=False)
        cl = MarkerCluster().add_to(fg)
        add_markers(df_circuit, cl, party=party, layer_tag=f"circ_{party}")
        fg.add_to(m)

    provenance_html = f"""
    <div style="position: fixed; bottom: 2px; left: 2px; z-index: 1000; 
        background: rgba(255,255,255,0.9); border: 1px solid #ccc; 
        padding: 6px 10px; font-size: 11px; font-family: Arial; 
        border-radius: 3px; max-width: 300px;">
        <b>Data Provenance</b><br>
        Source: {data_source}<br>
        Pipeline run: {pipeline_timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
        Judge data: Wikipedia (current + presidential appointees)<br>
        Hiring data: OSCAR (oscar.uscourts.gov)<br>
        <a href="https://oscar.uscourts.gov" target="_blank" style="font-size:10px; color:#0066cc;">View on OSCAR</a>
    </div>
    """
    legend_html = """
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
        background: rgba(255,255,255,0.95); border: 1px solid #ccc;
        padding: 10px; font-size: 12px; font-family: Arial; border-radius: 3px;">
        <b>Legend</b><br>
        <span style="color: red;">●</span> Republican &nbsp;
        <span style="color: blue;">●</span> Democrat &nbsp;
        <span style="color: gray;">●</span> Other<br>
        <span style="color: darkgreen;">●</span> Hiring (fresh, &lt;30d)&nbsp;
        <span style="color: orange;">●</span> Hiring (recent, 30-60d)&nbsp;
        <span style="color: darkred;">●</span> Hiring (stale, &gt;60d)&nbsp;
        <span style="color: gray;">●</span> Hiring (no date)<br>
        Larger dots = hiring; smaller = not hiring
    </div>
    """
    dark_mode_js = """
    <button id="darkToggle" style="position:fixed;bottom:10px;right:10px;z-index:1001;padding:6px 10px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;font-size:12px;">Dark mode</button>
    <script>
      document.getElementById('darkToggle').addEventListener('click', function(){
        document.body.classList.toggle('dark-mode');
        this.textContent = document.body.classList.contains('dark-mode') ? 'Light mode' : 'Dark mode';
      });
    </script>
    <style>
      @media (max-width: 600px) {
        .leaflet-popup-content { width: 260px !important; }
        .legend { font-size: 10px !important; }
      }
      body.dark-mode { background: #1a1a1a; color: #eee; }
      body.dark-mode .leaflet-container { background: #1a1a1a; }
    </style>
    """

    folium.LayerControl(collapsed=False).add_to(m)
    m.save("oscar_clerkship_map.html")
    print("Map saved to oscar_clerkship_map.html")


if __name__ == "__main__":
    build_map()
