#!/usr/bin/env python3
import json
import re
import time
import urllib.parse
import urllib.request

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
TIMEOUT = 8

import json as _json
import os as _os

CACHE_FILE = "enrich_cache.json"
_cache = {}
if _os.path.exists(CACHE_FILE):
    try:
        _cache = _json.load(open(CACHE_FILE))
    except Exception:
        _cache = {}

def http_get(url):
    if url in _cache:
        return _cache[url]
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read().decode('utf-8', errors='replace')
            _cache[url] = data
            _json.dump(_cache, open(CACHE_FILE, 'w'))
            return data
        except Exception:
            time.sleep(1 + attempt)
    _cache[url] = None
    return None

def find_wiki_title(name):
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={urllib.parse.quote(name)}&srprop="
    data = http_get(url)
    if not data: return None
    try:
        j = json.loads(data)
        for s in j.get('query', {}).get('search', []):
            t = s['title']
            if 'list' not in t.lower():
                return t
    except Exception:
        pass
    return None

def get_infobox(title):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={urllib.parse.quote(title)}&prop=text"
    data = http_get(url)
    if not data: return {}
    try:
        j = json.loads(data)
        html = j['parse']['text']['*']
        # find infobox table
        m = re.search(r'<table[^>]*class="[^"]*infobox[^"]*".*?</table>', html, flags=re.S)
        if not m:
            m = re.search(r'<table[^>]*>.*?</table>', html, flags=re.S)
        if not m: return {}
        table = m.group(0)
        fields = {}
        for row in re.findall(r'<tr>(.*?)</tr>', table, flags=re.S):
            th = re.search(r'<th[^>]*>(.*?)</th>', row, flags=re.S)
            td = re.search(r'<td[^>]*>(.*?)</td>', row, flags=re.S)
            if th and td:
                key = re.sub(r'<[^>]+>', '', th.group(1)).strip()
                val = re.sub(r'<[^>]+>', ' ', td.group(1))
                val = re.sub(r'\s+', ' ', val).strip()
                if key and val:
                    fields[key] = val[:300]
        return fields
    except Exception:
        return {}

def get_summary(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(title)}"
    data = http_get(url)
    if not data: return None
    try:
        j = json.loads(data)
        pages = j.get('query', {}).get('pages', {})
        for pid, p in pages.items():
            ext = p.get('extract')
            if ext:
                return ext[:500]
    except Exception:
        pass
    return None

def enrich_df(df):
    # Batch Wikipedia queries to reduce rate limiting.
    names = [str(x).strip() for x in df['Judge'].tolist()]
    # Find titles via individual search (cached), then batch extracts.
    summaries = [None]*len(df)
    infoboxes = [{} for _ in df.index]
    # Step 1: resolve titles (cached)
    titles = []
    for name in names:
        titles.append(find_wiki_title(name))
    # Step 2: fetch extracts in batches of 50
    batch_size = 50
    for i in range(0, len(titles), batch_size):
        batch_titles = [t for t in titles[i:i+batch_size] if t]
        if not batch_titles:
            continue
        # fetch extracts
        url = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles=" + "|".join(urllib.parse.quote(t) for t in batch_titles)
        data = http_get(url)
        extract_map = {}
        if data:
            try:
                j = json.loads(data)
                pages = j.get('query', {}).get('pages', {})
                for pid, p in pages.items():
                    title = p.get('title')
                    extract_map[title] = p.get('extract')
            except Exception:
                pass
        for j in range(i, min(i+batch_size, len(df))):
            t = titles[j]
            if t and t in extract_map:
                ext = extract_map[t]
                summaries[j] = ext[:500] if ext else None
                ib = get_infobox(t)
                infoboxes[j] = ib
        time.sleep(1)
    df = df.copy()
    df['Wikipedia Summary'] = summaries
    for key in ['Education', 'Alma mater']:
        df[key] = [ib.get(key, '') for ib in infoboxes]
    return df
