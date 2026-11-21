#helper_functions.py

import re
import unicodedata


#this will take care of the weird encoding from wikipedia and remove citations and other junk
def nuke_wiki_junk(text):
    if not isinstance(text, str):
        return text

    # 1. Normalize Unicode (Fixes \xa0, \u2013, and "strange" spaces/dashes)
    # NFKD decomposes combined characters into their base parts
    text = unicodedata.normalize("NFKD", text)

    # 2. Strip Wikipedia Citations: [1], [n 1], [edit], etc.
    text = re.sub(r'\[.*?\]', '', text)

    # 3. Clean up any remaining "mojibake" or weird symbols
    # This keeps alphanumeric, common punctuation, and spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text.strip()


# Shared state abbreviation <-> full name mapping (single source of truth)
STATE_MAP = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam',
}
STATE_ABBREV = {v: k for k, v in STATE_MAP.items()}

# Party of the president who appointed the judge -> political leaning used on the map
PARTY_MAP = {
    'Trump': 'Republican',
    'Biden': 'Democrat',
    'Obama': 'Democrat',
    'George W. Bush': 'Republican',
    'G.W. Bush': 'Republican',
    'George_H._W._Bush': 'Republican',
    'G.H.W. Bush': 'Republican',
    'Bush HW': 'Republican',
    'Bush W': 'Republican',
    'Clinton': 'Democrat',
    'Clinton / G.W. Bush': 'Republican',
    'Reagan': 'Republican',
    'Carter': 'Democrat',
    'Nixon': 'Republican',
    'Kennedy': 'Democrat',
    'Lyndon B. Johnson': 'Democrat',
    'Johnson': 'Democrat',
    'Eisenhower': 'Republican',
    'Ford': 'Republican',
    'Harding': 'Republican',
    'Coolidge': 'Republican',
    'Hoover': 'Republican',
    'Roosevelt': 'Democrat',
    'Truman': 'Democrat',
}


def derive_party(appointed_by):
    """Map 'Appointed By' text to a political party."""
    if not isinstance(appointed_by, str):
        return 'Other'
    for pres, party in PARTY_MAP.items():
        if pres.lower() in appointed_by.lower():
            return party
    return 'Other'
