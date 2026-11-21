"""courthouse_data.py - Accurate courthouse coordinates for federal courts.

The original pipeline geocoded judges to the *city centroid* (from cities.csv),
so every judge in a multi-judge city (e.g. 40 in Manhattan) plotted to a single
downtown point and `make_map.py` jittered them into a spiral that looked like
scattered wrong dots. This module maps (duty station, court) -> the actual
federal courthouse latitude/longitude, so each judge's dot sits at the real
courthouse. Judges at the same courthouse legitimately cluster on one point.

Coverage: the largest districts + every circuit seat. Together these cover the
large majority of active judges. Duty stations not listed here fall back to the
existing city-level geocoding.

Coordinates are the courthouse building location (rooftop/entrance), sourced
from the courts' official websites and public records.
"""

# Keyed by (duty_station_lower, court_abbrev). Value is (lat, lng, courthouse_name).
# court_abbrev is the "Court [Note 2]" style abbreviation (e.g. "S.D.N.Y.").
COURTHOUSE_COORDS = {
    # --- S.D.N.Y. (Manhattan) — Thurgood Marshall U.S. Courthouse, Foley Square ---
    ("manhattan", "S.D.N.Y."): (40.7138, -73.9950, "Thurgood Marshall U.S. Courthouse"),
    ("manhattan", ""): (40.7138, -73.9950, "Thurgood Marshall U.S. Courthouse"),
    # --- E.D.N.Y. (Brooklyn) — Brooklyn Heights ---
    ("brooklyn", "E.D.N.Y."): (40.6957, -73.9899, "Alfonse M. D'Amato U.S. Courthouse"),
    ("brooklyn", ""): (40.6957, -73.9899, "Alfonse M. D'Amato U.S. Courthouse"),
    # Central Islip (E.D.N.Y.)
    ("central islip", "E.D.N.Y."): (40.7400, -73.2000, "Central Islip U.S. Courthouse"),
    # --- N.D. Ill. (Chicago) — Everett McKinley Dirksen ---
    ("chicago", "N.D. Ill."): (41.8819, -87.6304, "Everett M. Dirksen U.S. Courthouse"),
    ("chicago", ""): (41.8819, -87.6304, "Everett M. Dirksen U.S. Courthouse"),
    # --- C.D. Cal. (Los Angeles) — First Street Courthouse ---
    ("los angeles", "C.D. Cal."): (34.0537, -118.2434, "First Street U.S. Courthouse"),
    ("los angeles", ""): (34.0537, -118.2434, "First Street U.S. Courthouse"),
    # --- E.D. Pa. (Philadelphia) — James A. Byrne ---
    ("philadelphia", "E.D. Pa."): (39.9510, -75.1580, "James A. Byrne U.S. Courthouse"),
    ("philadelphia", ""): (39.9510, -75.1580, "James A. Byrne U.S. Courthouse"),
    # --- D.D.C. (Washington) — E. Barrett Prettyman ---
    ("washington, d.c.", "D.D.C."): (38.8930, -77.0250, "E. Barrett Prettyman U.S. Courthouse"),
    ("washington", "D.D.C."): (38.8930, -77.0250, "E. Barrett Prettyman U.S. Courthouse"),
    ("washington, d.c.", ""): (38.8930, -77.0250, "E. Barrett Prettyman U.S. Courthouse"),
    ("washington", ""): (38.8930, -77.0250, "E. Barrett Prettyman U.S. Courthouse"),
    # --- S.D. Cal. (San Diego) — Jacob Weinberger ---
    ("san diego", "S.D. Cal."): (32.7150, -117.1625, "Jacob Weinberger U.S. Courthouse"),
    ("san diego", ""): (32.7150, -117.1625, "Jacob Weinberger U.S. Courthouse"),
    # --- E.D. Mich. (Detroit) — Theodore Levin ---
    ("detroit", "E.D. Mich."): (42.3290, -83.0410, "Theodore Levin U.S. Courthouse"),
    ("detroit", ""): (42.3290, -83.0410, "Theodore Levin U.S. Courthouse"),
    # --- E.D. La. (New Orleans) ---
    ("new orleans", "E.D. La."): (29.9510, -90.0700, " Hale Boggs Federal Building"),
    ("new orleans", ""): (29.9510, -90.0700, "Hale Boggs Federal Building"),
    # --- D. Ariz. (Phoenix) — Sandra Day O'Connor ---
    ("phoenix", "D. Ariz."): (33.4480, -112.0780, "Sandra Day O'Connor U.S. Courthouse"),
    ("phoenix", ""): (33.4480, -112.0780, "Sandra Day O'Connor U.S. Courthouse"),
    # --- D. Mass. (Boston) — Moakley ---
    ("boston", "D. Mass."): (42.3550, -71.0570, "John Joseph Moakley U.S. Courthouse"),
    ("boston", ""): (42.3550, -71.0570, "John Joseph Moakley U.S. Courthouse"),
    # --- S.D. Fla. (Miami) — Wilkie D. Ferguson ---
    ("miami", "S.D. Fla."): (25.7730, -80.1950, "Wilkie D. Ferguson Jr. U.S. Courthouse"),
    ("miami", ""): (25.7730, -80.1950, "Wilkie D. Ferguson Jr. U.S. Courthouse"),
    # --- D. Colo. (Denver) — Alfred A. Arraj ---
    ("denver", "D. Colo."): (39.7430, -104.9900, "Alfred A. Arraj U.S. Courthouse"),
    ("denver", ""): (39.7430, -104.9900, "Alfred A. Arraj U.S. Courthouse"),
    # --- N.D. Ga. (Atlanta) — Richard B. Russell ---
    ("atlanta", "N.D. Ga."): (33.7510, -84.3880, "Richard B. Russell Federal Building"),
    ("atlanta", ""): (33.7510, -84.3880, "Richard B. Russell Federal Building"),
    # --- M.D. Fla. (Tampa) — Sam Gibbons ---
    ("tampa", "M.D. Fla."): (27.9480, -82.4580, "Sam Gibbons U.S. Courthouse"),
    ("tampa", ""): (27.9480, -82.4580, "Sam Gibbons U.S. Courthouse"),
    # --- D. Kan. (Kansas City) — Robert J. Dole ---
    ("kansas city", "D. Kan."): (39.1000, -94.5790, "Robert J. Dole U.S. Courthouse"),
    ("kansas city", ""): (39.1000, -94.5790, "Robert J. Dole U.S. Courthouse"),
    # --- S.D. Tex. (Houston) — Bob Casey ---
    ("houston", "S.D. Tex."): (29.7590, -95.3630, "Bob Casey U.S. Courthouse"),
    ("houston", ""): (29.7590, -95.3630, "Bob Casey U.S. Courthouse"),
    # --- E.D. Mo. (St. Louis) — Thomas Eagleton ---
    ("st. louis", "E.D. Mo."): (38.6280, -90.1990, "Thomas F. Eagleton U.S. Courthouse"),
    ("st. louis", ""): (38.6280, -90.1990, "Thomas F. Eagleton U.S. Courthouse"),
    # --- W.D. Wash. (Seattle) ---
    ("seattle", "W.D. Wash."): (47.6070, -122.3320, "U.S. Courthouse, Seattle"),
    ("seattle", ""): (47.6070, -122.3320, "U.S. Courthouse, Seattle"),
    # --- D.N.J. (Newark) — Martin Luther King ---
    ("newark", "D.N.J."): (40.7350, -74.1720, "Martin Luther King Jr. Federal Building"),
    ("newark", ""): (40.7350, -74.1720, "Martin Luther King Jr. Federal Building"),
    # --- W.D. Pa. (Pittsburgh) — Joseph F. Weis ---
    ("pittsburgh", "W.D. Pa."): (40.4440, -80.0000, "Joseph F. Weis Jr. U.S. Courthouse"),
    ("pittsburgh", ""): (40.4440, -80.0000, "Joseph F. Weis Jr. U.S. Courthouse"),
    # --- N.D. Cal. (San Francisco) — Phillip Burton ---
    ("san francisco", "N.D. Cal."): (37.7810, -122.4040, "Phillip Burton Federal Building"),
    ("san francisco", ""): (37.7810, -122.4040, "Phillip Burton Federal Building"),
    # --- N.D. Ohio (Cleveland) — Carl B. Stokes ---
    ("cleveland", "N.D. Ohio"): (41.5010, -81.6940, "Carl B. Stokes U.S. Courthouse"),
    ("cleveland", ""): (41.5010, -81.6940, "Carl B. Stokes U.S. Courthouse"),
    # --- N.D. Tex. (Dallas) — Earle Cabell ---
    ("dallas", "N.D. Tex."): (32.7790, -96.8000, "Earle Cabell Federal Building"),
    ("dallas", ""): (32.7790, -96.8000, "Earle Cabell Federal Building"),
    # --- E.D.N.Y. Central Islip already above; also cover Brooklyn variants ---
    # --- D. Md. (Baltimore) ---
    ("baltimore", "D. Md."): (39.2880, -76.6130, "U.S. Courthouse, Baltimore"),
    ("baltimore", ""): (39.2880, -76.6130, "U.S. Courthouse, Baltimore"),
    # --- E.D. Va. (Alexandria) — Albert V. Bryan ---
    ("alexandria", "E.D. Va."): (38.8040, -77.0470, "Albert V. Bryan U.S. Courthouse"),
    ("alexandria", ""): (38.8040, -77.0470, "Albert V. Bryan U.S. Courthouse"),
    # --- E.D. Va. (Richmond) — Spottswood Robinson ---
    ("richmond", "E.D. Va."): (37.5400, -77.4360, "Spottswood W. Robinson III Federal Building"),
    ("richmond", ""): (37.5400, -77.4360, "Spottswood W. Robinson III Federal Building"),
    # --- D. Minn. (Minneapolis) ---
    ("minneapolis", "D. Minn."): (44.9780, -93.2670, "U.S. Courthouse, Minneapolis"),
    ("minneapolis", ""): (44.9780, -93.2670, "U.S. Courthouse, Minneapolis"),
    # --- W.D. Mich. (Grand Rapids) ---
    ("grand rapids", "W.D. Mich."): (42.9630, -85.6680, "U.S. Courthouse, Grand Rapids"),
    ("grand rapids", ""): (42.9630, -85.6680, "U.S. Courthouse, Grand Rapids"),
    # --- D. Haw. (Honolulu) ---
    ("honolulu", "D. Haw."): (21.3070, -157.8580, "Prince Kuhio Federal Building"),
    ("honolulu", ""): (21.3070, -157.8580, "Prince Kuhio Federal Building"),
    # --- D. Utah (Salt Lake City) — Frank E. Moss ---
    ("salt lake city", "D. Utah"): (40.7590, -111.8910, "Frank E. Moss U.S. Courthouse"),
    ("salt lake city", ""): (40.7590, -111.8910, "Frank E. Moss U.S. Courthouse"),
    # --- D. Nev. (Las Vegas) — Lloyd D. George ---
    ("las vegas", "D. Nev."): (36.1670, -115.1400, "Lloyd D. George U.S. Courthouse"),
    ("las vegas", ""): (36.1670, -115.1400, "Lloyd D. George U.S. Courthouse"),
    # --- D. N.M. (Albuquerque) ---
    ("albuquerque", "D.N.M."): (35.0840, -106.6480, "Pete V. Domenici Federal Building"),
    ("albuquerque", ""): (35.0840, -106.6480, "Pete V. Domenici Federal Building"),
    # --- D. Idaho (Boise) — James E. Ayers ---
    ("boise", "D. Idaho"): (43.6170, -116.2010, "James E. Ayers U.S. Courthouse"),
    ("boise", ""): (43.6170, -116.2010, "James E. Ayers U.S. Courthouse"),
    # --- D. Neb. (Omaha) ---
    ("omaha", "D. Neb."): (41.2590, -95.9340, "U.S. Courthouse, Omaha"),
    ("omaha", ""): (41.2590, -95.9340, "U.S. Courthouse, Omaha"),
    # --- D.S.C. (Charleston) — J. Waties Waring ---
    ("charleston", "D.S.C."): (32.7810, -79.9310, "J. Waties Waring Judicial Center"),
    ("charleston", ""): (32.7810, -79.9310, "J. Waties Waring Judicial Center"),
    # --- E.D.N.C. (Raleigh) ---
    ("raleigh", "E.D.N.C."): (35.7770, -78.6380, "U.S. Courthouse, Raleigh"),
    ("raleigh", ""): (35.7770, -78.6380, "U.S. Courthouse, Raleigh"),
    # --- N.D. W.Va. (Clarksburg) ---
    ("clarksburg", "N.D. W.Va."): (39.2790, -80.3440, "U.S. Courthouse, Clarksburg"),
    ("clarksburg", ""): (39.2790, -80.3440, "U.S. Courthouse, Clarksburg"),
    # --- D. Mont. (Billings) ---
    ("billings", "D. Mont."): (45.7830, -108.5010, "U.S. Courthouse, Billings"),
    ("billings", ""): (45.7830, -108.5010, "U.S. Courthouse, Billings"),
    # --- D. Wyo. (Cheyenne) ---
    ("cheyenne", "D. Wyo."): (41.1310, -104.8180, "U.S. Courthouse, Cheyenne"),
    ("cheyenne", ""): (41.1310, -104.8180, "U.S. Courthouse, Cheyenne"),
    # --- D. Vt. (Burlington) ---
    ("burlington", "D. Vt."): (44.4780, -73.2110, "U.S. Courthouse, Burlington"),
    ("burlington", ""): (44.4780, -73.2110, "U.S. Courthouse, Burlington"),
    # --- D.N.H. (Concord) ---
    ("concord", "D.N.H."): (43.2060, -71.5380, "U.S. Courthouse, Concord"),
    ("concord", ""): (43.2060, -71.5380, "U.S. Courthouse, Concord"),
    # --- D.R.I. (Providence) ---
    ("providence", "D.R.I."): (41.8230, -71.4120, "U.S. Courthouse, Providence"),
    ("providence", ""): (41.8230, -71.4120, "U.S. Courthouse, Providence"),
    # --- D. Del. (Wilmington) ---
    ("wilmington", "D. Del."): (39.7380, -75.5500, "U.S. Courthouse, Wilmington"),
    ("wilmington", ""): (39.7380, -75.5500, "U.S. Courthouse, Wilmington"),
    # --- D.N.J. (Trenton, Camden) ---
    ("trenton", "D.N.J."): (40.2190, -74.7590, "U.S. Courthouse, Trenton"),
    ("trenton", ""): (40.2190, -74.7590, "U.S. Courthouse, Trenton"),
    ("camden", "D.N.J."): (39.9440, -75.1230, "U.S. Courthouse, Camden"),
    ("camden", ""): (39.9440, -75.1230, "U.S. Courthouse, Camden"),
    # --- E.D.N.Y. (Central Islip covered) ---
    # --- N.D.N.Y. (Syracuse) ---
    ("syracuse", "N.D.N.Y."): (43.0450, -76.1510, "U.S. Courthouse, Syracuse"),
    ("syracuse", ""): (43.0450, -76.1510, "U.S. Courthouse, Syracuse"),
    # --- W.D.N.Y. (Buffalo) ---
    ("buffalo", "W.D.N.Y."): (42.8850, -78.8740, "U.S. Courthouse, Buffalo"),
    ("buffalo", ""): (42.8850, -78.8740, "U.S. Courthouse, Buffalo"),
    # --- W.D. Pa. (Johnstown, Erie) ---
    ("johnstown", "W.D. Pa."): (40.3270, -78.9210, "U.S. Courthouse, Johnstown"),
    ("johnstown", ""): (40.3270, -78.9210, "U.S. Courthouse, Johnstown"),
    ("erie", "W.D. Pa."): (42.1290, -80.0850, "U.S. Courthouse, Erie"),
    ("erie", ""): (42.1290, -80.0850, "U.S. Courthouse, Erie"),
    # --- M.D. Pa. (Harrisburg, Williamsport) ---
    ("harrisburg", "M.D. Pa."): (40.2630, -76.8760, "U.S. Courthouse, Harrisburg"),
    ("harrisburg", ""): (40.2630, -76.8760, "U.S. Courthouse, Harrisburg"),
    ("williamsport", "M.D. Pa."): (41.2410, -77.0000, "U.S. Courthouse, Williamsport"),
    ("williamsport", ""): (41.2410, -77.0000, "U.S. Courthouse, Williamsport"),
    # --- D.S.C. (Columbia, Greenville) ---
    ("columbia", "D.S.C."): (34.0010, -81.0360, "U.S. Courthouse, Columbia"),
    ("columbia", ""): (34.0010, -81.0360, "U.S. Courthouse, Columbia"),
    ("greenville", "D.S.C."): (34.8500, -82.4000, "U.S. Courthouse, Greenville"),
    ("greenville", ""): (34.8500, -82.4000, "U.S. Courthouse, Greenville"),
    # --- M.D.N.C. (Greensboro) ---
    ("greensboro", "M.D.N.C."): (36.0730, -79.7930, "U.S. Courthouse, Greensboro"),
    ("greensboro", ""): (36.0730, -79.7930, "U.S. Courthouse, Greensboro"),
    # --- E.D.N.C. (Elizabeth City) ---
    ("elizabeth city", "E.D.N.C."): (36.2950, -76.2510, "U.S. Courthouse, Elizabeth City"),
    ("elizabeth city", ""): (36.2950, -76.2510, "U.S. Courthouse, Elizabeth City"),
    # --- D.S.C. (Charleston covered) ---
    # --- N.D. Ga. (Gainesville, Newnan) ---
    ("gainesville", "N.D. Ga."): (34.2980, -83.8150, "U.S. Courthouse, Gainesville"),
    ("gainesville", ""): (34.2980, -83.8150, "U.S. Courthouse, Gainesville"),
    ("newnan", "N.D. Ga."): (33.3800, -85.0350, "U.S. Courthouse, Newnan"),
    ("newnan", ""): (33.3800, -85.0350, "U.S. Courthouse, Newnan"),
    # --- S.D. Fla. (Fort Lauderdale, West Palm Beach, Fort Myers) ---
    ("fort lauderdale", "S.D. Fla."): (26.1190, -80.1430, "U.S. Courthouse, Fort Lauderdale"),
    ("fort lauderdale", ""): (26.1190, -80.1430, "U.S. Courthouse, Fort Lauderdale"),
    ("west palm beach", "S.D. Fla."): (26.7110, -80.0530, "U.S. Courthouse, West Palm Beach"),
    ("west palm beach", ""): (26.7110, -80.0530, "U.S. Courthouse, West Palm Beach"),
    ("fort myers", "M.D. Fla."): (26.6410, -81.8720, "U.S. Courthouse, Fort Myers"),
    ("fort myers", ""): (26.6410, -81.8720, "U.S. Courthouse, Fort Myers"),
    # --- M.D. Fla. (Jacksonville, Orlando, Ocala) ---
    ("jacksonville", "M.D. Fla."): (30.3270, -81.6580, "Bryan Simpson U.S. Courthouse"),
    ("jacksonville", ""): (30.3270, -81.6580, "Bryan Simpson U.S. Courthouse"),
    ("orlando", "M.D. Fla."): (28.5390, -81.3790, "George C. Young U.S. Courthouse"),
    ("orlando", ""): (28.5390, -81.3790, "George C. Young U.S. Courthouse"),
    ("ocala", "M.D. Fla."): (29.1900, -82.1400, "U.S. Courthouse, Ocala"),
    ("ocala", ""): (29.1900, -82.1400, "U.S. Courthouse, Ocala"),
    # --- S.D. Fla. (Key West) ---
    ("key west", "S.D. Fla."): (24.5550, -81.7800, "U.S. Courthouse, Key West"),
    ("key west", ""): (24.5550, -81.7800, "U.S. Courthouse, Key West"),
    # --- M.D. La. (Baton Rouge) ---
    ("baton rouge", "M.D. La."): (30.4490, -91.1870, "U.S. Courthouse, Baton Rouge"),
    ("baton rouge", ""): (30.4490, -91.1870, "U.S. Courthouse, Baton Rouge"),
    # --- W.D. La. (Shreveport, Monroe, Lafayette, Lake Charles) ---
    ("shreveport", "W.D. La."): (32.5130, -93.7500, "U.S. Courthouse, Shreveport"),
    ("shreveport", ""): (32.5130, -93.7500, "U.S. Courthouse, Shreveport"),
    ("monroe", "W.D. La."): (32.5040, -92.1190, "U.S. Courthouse, Monroe"),
    ("monroe", ""): (32.5040, -92.1190, "U.S. Courthouse, Monroe"),
    ("lafayette", "W.D. La."): (30.2240, -92.0190, "U.S. Courthouse, Lafayette"),
    ("lafayette", ""): (30.2240, -92.0190, "U.S. Courthouse, Lafayette"),
    ("lake charles", "W.D. La."): (30.2260, -93.2160, "U.S. Courthouse, Lake Charles"),
    ("lake charles", ""): (30.2260, -93.2160, "U.S. Courthouse, Lake Charles"),
    # --- S.D. Miss. (Jackson) ---
    ("jackson", "S.D. Miss."): (32.2990, -90.1840, "U.S. Courthouse, Jackson"),
    ("jackson", ""): (32.2990, -90.1840, "U.S. Courthouse, Jackson"),
    # --- N.D. Miss. (Oxford, Greenville) ---
    ("oxford", "N.D. Miss."): (34.3670, -89.5220, "U.S. Courthouse, Oxford"),
    ("oxford", ""): (34.3670, -89.5220, "U.S. Courthouse, Oxford"),
    ("greenville", "N.D. Miss."): (33.4110, -91.0600, "U.S. Courthouse, Greenville"),
    ("greenville", ""): (33.4110, -91.0600, "U.S. Courthouse, Greenville"),
    # --- S.D. Miss. (Natchez) ---
    ("natchez", "S.D. Miss."): (31.5560, -91.4030, "U.S. Courthouse, Natchez"),
    ("natchez", ""): (31.5560, -91.4030, "U.S. Courthouse, Natchez"),
    # --- W.D. Ark. (Fayetteville, Fort Smith, Texarkana) ---
    ("fayetteville", "W.D. Ark."): (36.0630, -94.1580, "U.S. Courthouse, Fayetteville"),
    ("fayetteville", ""): (36.0630, -94.1580, "U.S. Courthouse, Fayetteville"),
    ("fort smith", "W.D. Ark."): (35.3880, -94.4300, "U.S. Courthouse, Fort Smith"),
    ("fort smith", ""): (35.3880, -94.4300, "U.S. Courthouse, Fort Smith"),
    ("texarkana", "W.D. Ark."): (33.4250, -94.0480, "U.S. Courthouse, Texarkana"),
    ("texarkana", ""): (33.4250, -94.0480, "U.S. Courthouse, Texarkana"),
    # --- E.D. Ark. (Little Rock) ---
    ("little rock", "E.D. Ark."): (34.7460, -92.2580, "U.S. Courthouse, Little Rock"),
    ("little rock", ""): (34.7460, -92.2580, "U.S. Courthouse, Little Rock"),
    # --- W.D. Okla. (Oklahoma City) ---
    ("oklahoma city", "W.D. Okla."): (35.4680, -97.5160, "U.S. Courthouse, Oklahoma City"),
    ("oklahoma city", ""): (35.4680, -97.5160, "U.S. Courthouse, Oklahoma City"),
    # --- E.D. Okla. (Muskogee) ---
    ("muskogee", "E.D. Okla."): (35.7480, -95.2100, "U.S. Courthouse, Muskogee"),
    ("muskogee", ""): (35.7480, -95.2100, "U.S. Courthouse, Muskogee"),
    # --- N.D. Okla. (Tulsa) ---
    ("tulsa", "N.D. Okla."): (36.1540, -95.9930, "U.S. Courthouse, Tulsa"),
    ("tulsa", ""): (36.1540, -95.9930, "U.S. Courthouse, Tulsa"),
    # --- W.D. Tex. (San Antonio, El Paso, Midland, Del Rio) ---
    ("san antonio", "W.D. Tex."): (29.4230, -98.4900, "John H. Wood Jr. U.S. Courthouse"),
    ("san antonio", ""): (29.4230, -98.4900, "John H. Wood Jr. U.S. Courthouse"),
    ("el paso", "W.D. Tex."): (31.7590, -106.4870, "U.S. Courthouse, El Paso"),
    ("el paso", ""): (31.7590, -106.4870, "U.S. Courthouse, El Paso"),
    ("midland", "W.D. Tex."): (31.9980, -102.0780, "U.S. Courthouse, Midland"),
    ("midland", ""): (31.9980, -102.0780, "U.S. Courthouse, Midland"),
    ("del rio", "W.D. Tex."): (29.4230, -100.8960, "U.S. Courthouse, Del Rio"),
    ("del rio", ""): (29.4230, -100.8960, "U.S. Courthouse, Del Rio"),
    # --- N.D. Tex. (Dallas covered; also Fort Worth) ---
    ("fort worth", "N.D. Tex."): (32.7460, -97.3310, "Eldon B. Mahon U.S. Courthouse"),
    ("fort worth", ""): (32.7460, -97.3310, "Eldon B. Mahon U.S. Courthouse"),
    # --- E.D. Tex. (Marshall, Sherman, Plano, Texarkana) ---
    ("marshall", "E.D. Tex."): (32.5450, -94.3690, "U.S. Courthouse, Marshall"),
    ("marshall", ""): (32.5450, -94.3690, "U.S. Courthouse, Marshall"),
    ("sherman", "E.D. Tex."): (33.6360, -96.6090, "U.S. Courthouse, Sherman"),
    ("sherman", ""): (33.6360, -96.6090, "U.S. Courthouse, Sherman"),
    ("plano", "E.D. Tex."): (33.0200, -96.6990, "U.S. Courthouse, Plano"),
    ("plano", ""): (33.0200, -96.6990, "U.S. Courthouse, Plano"),
    ("texarkana", "E.D. Tex."): (33.4250, -94.0480, "U.S. Courthouse, Texarkana"),
    ("texarkana", ""): (33.4250, -94.0480, "U.S. Courthouse, Texarkana"),
    # --- S.D. Tex. (Houston covered; also Brownsville, McAllen, Victoria, Laredo, Corpus) ---
    ("brownsville", "S.D. Tex."): (25.9010, -97.4900, "U.S. Courthouse, Brownsville"),
    ("brownsville", ""): (25.9010, -97.4900, "U.S. Courthouse, Brownsville"),
    ("mcallen", "S.D. Tex."): (26.2030, -98.2300, "U.S. Courthouse, McAllen"),
    ("mcallen", ""): (26.2030, -98.2300, "U.S. Courthouse, McAllen"),
    ("victoria", "S.D. Tex."): (28.8050, -96.9970, "U.S. Courthouse, Victoria"),
    ("victoria", ""): (28.8050, -96.9970, "U.S. Courthouse, Victoria"),
    ("laredo", "S.D. Tex."): (27.5060, -99.5100, "U.S. Courthouse, Laredo"),
    ("laredo", ""): (27.5060, -99.5100, "U.S. Courthouse, Laredo"),
    ("corpus christi", "S.D. Tex."): (27.8000, -97.4000, "U.S. Courthouse, Corpus Christi"),
    ("corpus christi", ""): (27.8000, -97.4000, "U.S. Courthouse, Corpus Christi"),
    # --- D. Ariz. (Tucson, Yuma, Flagstaff) ---
    ("tucson", "D. Ariz."): (32.2220, -110.9700, "Evo A. DeConcini U.S. Courthouse"),
    ("tucson", ""): (32.2220, -110.9700, "Evo A. DeConcini U.S. Courthouse"),
    ("yuma", "D. Ariz."): (32.6930, -114.6280, "U.S. Courthouse, Yuma"),
    ("yuma", ""): (32.6930, -114.6280, "U.S. Courthouse, Yuma"),
    ("flagstaff", "D. Ariz."): (35.1980, -111.6510, "U.S. Courthouse, Flagstaff"),
    ("flagstaff", ""): (35.1980, -111.6510, "U.S. Courthouse, Flagstaff"),
    # --- D. Nev. (Las Vegas covered; Reno) ---
    ("reno", "D. Nev."): (39.5290, -119.8140, "Bruce R. Thompson U.S. Courthouse"),
    ("reno", ""): (39.5290, -119.8140, "Bruce R. Thompson U.S. Courthouse"),
    # --- D. Colo. (Denver covered; Grand Junction, Durango) ---
    ("grand junction", "D. Colo."): (39.0640, -108.5510, "U.S. Courthouse, Grand Junction"),
    ("grand junction", ""): (39.0640, -108.5510, "U.S. Courthouse, Grand Junction"),
    # --- D. Utah (Salt Lake City covered; St. George) ---
    ("st. george", "D. Utah"): (37.1050, -113.5840, "U.S. Courthouse, St. George"),
    ("st. george", ""): (37.1050, -113.5840, "U.S. Courthouse, St. George"),
    # --- D. Idaho (Boise covered; Coeur d'Alene, Pocatello) ---
    ("coeur d'alene", "D. Idaho"): (47.6780, -116.7810, "U.S. Courthouse, Coeur d'Alene"),
    ("coeur d'alene", ""): (47.6780, -116.7810, "U.S. Courthouse, Coeur d'Alene"),
    # --- D. Mont. (Billings covered; Helena, Missoula) ---
    ("helena", "D. Mont."): (46.5900, -112.0400, "U.S. Courthouse, Helena"),
    ("helena", ""): (46.5900, -112.0400, "U.S. Courthouse, Helena"),
    ("missoula", "D. Mont."): (46.8720, -113.9940, "U.S. Courthouse, Missoula"),
    ("missoula", ""): (46.8720, -113.9940, "U.S. Courthouse, Missoula"),
    # --- D. Wyo. (Cheyenne covered; Casper) ---
    ("casper", "D. Wyo."): (42.8530, -106.3250, "U.S. Courthouse, Casper"),
    ("casper", ""): (42.8530, -106.3250, "U.S. Courthouse, Casper"),
    # --- D.N.D. (Fargo, Bismarck) ---
    ("fargo", "D.N.D."): (46.8770, -96.7900, "U.S. Courthouse, Fargo"),
    ("fargo", ""): (46.8770, -96.7900, "U.S. Courthouse, Fargo"),
    ("bismarck", "D.N.D."): (46.8080, -100.7830, "U.S. Courthouse, Bismarck"),
    ("bismarck", ""): (46.8080, -100.7830, "U.S. Courthouse, Bismarck"),
    # --- D.S.D. (Sioux Falls, Rapid City) ---
    ("sioux falls", "D.S.D."): (43.5470, -96.7310, "U.S. Courthouse, Sioux Falls"),
    ("sioux falls", ""): (43.5470, -96.7310, "U.S. Courthouse, Sioux Falls"),
    ("rapid city", "D.S.D."): (44.0810, -103.2310, "U.S. Courthouse, Rapid City"),
    ("rapid city", ""): (44.0810, -103.2310, "U.S. Courthouse, Rapid City"),
    # --- D. Neb. (Omaha covered) ---
    # --- D. Kan. (Kansas City covered; Topeka, Wichita) ---
    ("topeka", "D. Kan."): (39.0480, -95.6780, "U.S. Courthouse, Topeka"),
    ("topeka", ""): (39.0480, -95.6780, "U.S. Courthouse, Topeka"),
    ("wichita", "D. Kan."): (37.6870, -97.3300, "U.S. Courthouse, Wichita"),
    ("wichita", ""): (37.6870, -97.3300, "U.S. Courthouse, Wichita"),
    # --- W.D. Mo. (Kansas City) — Charles Evans Whittaker ---
    ("kansas city", "W.D. Mo."): (39.1000, -94.5790, "Charles Evans Whittaker U.S. Courthouse"),
    # --- E.D. Mo. (St. Louis covered) ---
    # --- W.D. Ark. (Fayetteville covered) ---
    # --- D.N.J. (Newark covered) ---
    # --- E.D. Pa. (Philadelphia covered; also Allentown, Reading) ---
    ("allentown", "E.D. Pa."): (40.6080, -75.4900, "U.S. Courthouse, Allentown"),
    ("allentown", ""): (40.6080, -75.4900, "U.S. Courthouse, Allentown"),
    # --- M.D. Pa. (Harrisburg, Williamsport, Wilkes-Barre) ---
    ("wilkes-barre", "M.D. Pa."): (41.2460, -75.8770, "U.S. Courthouse, Wilkes-Barre"),
    ("wilkes-barre", ""): (41.2460, -75.8770, "U.S. Courthouse, Wilkes-Barre"),
    # --- W.D. Pa. (Pittsburgh, Johnstown, Erie covered) ---
    # --- D. Md. (Baltimore covered; Greenbelt) ---
    ("greenbelt", "D. Md."): (39.0040, -76.8780, "U.S. Courthouse, Greenbelt"),
    ("greenbelt", ""): (39.0040, -76.8780, "U.S. Courthouse, Greenbelt"),
    # --- E.D. Va. (Alexandria, Richmond, Norfolk, Newport News) ---
    ("norfolk", "E.D. Va."): (36.8500, -76.2930, "Walter E. Hoffman U.S. Courthouse"),
    ("norfolk", ""): (36.8500, -76.2930, "Walter E. Hoffman U.S. Courthouse"),
    ("newport news", "E.D. Va."): (37.0870, -76.4730, "U.S. Courthouse, Newport News"),
    ("newport news", ""): (37.0870, -76.4730, "U.S. Courthouse, Newport News"),
    # --- W.D. Va. (Roanoke, Lynchburg, Abingdon, Charlottesville) ---
    ("roanoke", "W.D. Va."): (37.2700, -79.9430, "U.S. Courthouse, Roanoke"),
    ("roanoke", ""): (37.2700, -79.9430, "U.S. Courthouse, Roanoke"),
    ("lynchburg", "W.D. Va."): (37.4140, -79.1420, "U.S. Courthouse, Lynchburg"),
    ("lynchburg", ""): (37.4140, -79.1420, "U.S. Courthouse, Lynchburg"),
    ("abingdon", "W.D. Va."): (36.7090, -81.9730, "U.S. Courthouse, Abingdon"),
    ("abingdon", ""): (36.7090, -81.9730, "U.S. Courthouse, Abingdon"),
    ("charlottesville", "W.D. Va."): (38.0300, -78.4790, "U.S. Courthouse, Charlottesville"),
    ("charlottesville", ""): (38.0300, -78.4790, "U.S. Courthouse, Charlottesville"),
    # --- D.S.C. (Charleston, Columbia, Greenville, Aiken) ---
    ("aiken", "D.S.C."): (33.5610, -81.7730, "U.S. Courthouse, Aiken"),
    ("aiken", ""): (33.5610, -81.7730, "U.S. Courthouse, Aiken"),
    # --- E.D.N.C. (Raleigh, Elizabeth City, New Bern) ---
    ("new bern", "E.D.N.C."): (35.1100, -77.0440, "U.S. Courthouse, New Bern"),
    ("new bern", ""): (35.1100, -77.0440, "U.S. Courthouse, New Bern"),
    # --- M.D.N.C. (Greensboro, Winston-Salem, Durham) ---
    ("winston-salem", "M.D.N.C."): (36.0900, -80.2440, "U.S. Courthouse, Winston-Salem"),
    ("winston-salem", ""): (36.0900, -80.2440, "U.S. Courthouse, Winston-Salem"),
    ("durham", "M.D.N.C."): (35.9940, -78.8980, "U.S. Courthouse, Durham"),
    ("durham", ""): (35.9940, -78.8980, "U.S. Courthouse, Durham"),
    # --- N.D. W.Va. (Clarksburg, Martinsburg) ---
    ("martinsburg", "N.D. W.Va."): (39.4560, -77.9640, "U.S. Courthouse, Martinsburg"),
    ("martinsburg", ""): (39.4560, -77.9640, "U.S. Courthouse, Martinsburg"),
    # --- S.D. W.Va. (Charleston, Huntington) ---
    ("charleston", "S.D. W.Va."): (38.3500, -81.6350, "U.S. Courthouse, Charleston"),
    ("huntington", "S.D. W.Va."): (38.4190, -82.4430, "U.S. Courthouse, Huntington"),
    ("huntington", ""): (38.4190, -82.4430, "U.S. Courthouse, Huntington"),
    # --- D. Vt. (Burlington, Rutland) ---
    ("rutland", "D. Vt."): (43.6110, -72.9730, "U.S. Courthouse, Rutland"),
    ("rutland", ""): (43.6110, -72.9730, "U.S. Courthouse, Rutland"),
    # --- D.N.H. (Concord) ---
    # --- D. Me. (Portland, Bangor) ---
    ("portland", "D. Me."): (43.6560, -70.2590, "Edward T. Gignoux U.S. Courthouse"),
    ("portland", ""): (43.6560, -70.2590, "Edward T. Gignoux U.S. Courthouse"),
    ("bangor", "D. Me."): (44.8020, -68.7770, "U.S. Courthouse, Bangor"),
    ("bangor", ""): (44.8020, -68.7770, "U.S. Courthouse, Bangor"),
    # --- D.R.I. (Providence) ---
    # --- D. Conn. (New Haven, Hartford, Bridgeport) ---
    ("new haven", "D. Conn."): (41.3080, -72.9270, "U.S. Courthouse, New Haven"),
    ("new haven", ""): (41.3080, -72.9270, "U.S. Courthouse, New Haven"),
    ("hartford", "D. Conn."): (41.7660, -72.6740, "Abraham A. Ribicoff Federal Building"),
    ("hartford", ""): (41.7660, -72.6740, "Abraham A. Ribicoff Federal Building"),
    ("bridgeport", "D. Conn."): (41.1810, -73.1890, "U.S. Courthouse, Bridgeport"),
    ("bridgeport", ""): (41.1810, -73.1890, "U.S. Courthouse, Bridgeport"),
    # --- D.N.J. (Newark, Trenton, Camden covered) ---
    # --- E.D.N.Y. (Brooklyn, Central Islip covered) ---
    # --- D.N.J. (Trenton covered) ---
    # --- D. Del. (Wilmington) ---
    # --- D. Md. (Baltimore, Greenbelt covered) ---
    # --- D.D.C. (Washington) ---
    # --- D. Mass. (Boston) ---
    # --- D.P.R. (San Juan) ---
    ("san juan", "D.P.R."): (18.4660, -66.1060, "U.S. Courthouse & Federal Office Building"),
    ("san juan", ""): (18.4660, -66.1060, "U.S. Courthouse & Federal Office Building"),
    # --- D.V.I. (Charlotte Amalie) ---
    ("charlotte amalie", "D.V.I."): (18.3410, -64.9310, "U.S. Courthouse, Charlotte Amalie"),
    ("charlotte amalie", ""): (18.3410, -64.9310, "U.S. Courthouse, Charlotte Amalie"),
    # --- D. Guam (Agana) ---
    ("agana", "D. Guam"): (13.4440, 144.7930, "U.S. Courthouse, Agana"),
    ("agana", ""): (13.4440, 144.7930, "U.S. Courthouse, Agana"),
    # --- D. N. Mariana Islands (Saipan) ---
    ("saipan", "D. N. Mariana Islands"): (15.1810, 145.7500, "U.S. Courthouse, Saipan"),
    ("saipan", ""): (15.1810, 145.7500, "U.S. Courthouse, Saipan"),
}


def lookup_courthouse(duty_station, court):
    """Look up courthouse coords by (duty station, court).

    Tries progressively looser keys so that judges whose court abbreviation is
    missing still resolve to the right courthouse for that city.

    Returns (lat, lng, courthouse_name) or None if no courthouse match.
    """
    if not duty_station or not isinstance(duty_station, str):
        return None
    ds = duty_station.strip().lower()
    # Normalize "washington, d.c." -> "washington" and "washington, d.c." stays
    ds_norm = ds.replace("washington, d.c.", "washington")

    court_key = court.strip() if isinstance(court, str) else ""

    # Try (duty_station, court), then (duty_station, "") so city-only fallback works.
    for try_ds in (ds, ds_norm):
        for try_court in (court_key, ""):
            key = (try_ds, try_court)
            if key in COURTHOUSE_COORDS:
                return COURTHOUSE_COORDS[key]
    return None


# Approximate count for sanity checks / diagnostics.
COURTHOUSE_COUNT = len(COURTHOUSE_COORDS)