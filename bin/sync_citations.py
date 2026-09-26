#!/usr/bin/env python3
"""Sync _data/citations.yml with the citation counts on Google Scholar.

Google Scholar has no API and its terms forbid scraping, so the numbers come
through SerpApi's Scholar author endpoint: one request returns every paper on
the profile. Papers are matched to _bibliography/papers.bib by title; anything
that cannot be matched or fetched keeps the value it already had, so a bad run
never blanks the badges.

Needs SERPAPI_KEY in the environment (a repository secret in CI). Run from the
repository root:  SERPAPI_KEY=... python3 bin/sync_citations.py
"""

import difflib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BIB = "_bibliography/papers.bib"
OUT = "_data/citations.yml"
SCHOLAR_ID = "Ypagfq8AAAAJ"  # site.scholar_userid in _config.yml
ENDPOINT = "https://serpapi.com/search.json"
MATCH_THRESHOLD = 0.85  # title similarity needed to trust a match


def normalise(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def bib_entries(path):
    """[(arxiv_id, title, venue)] for every bibliography entry that has an arxiv id."""
    entries = []
    for block in re.findall(r"@\w+\{.*?\n\}", open(path, encoding="utf-8").read(), re.S):
        arxiv = re.search(r"arxiv\s*=\s*\{([^}]+)\}", block, re.I)
        title = re.search(r"title\s*=\s*\{([^}]+)\}", block, re.I)
        venue = re.search(r"venue\s*=\s*\{([^}]+)\}", block, re.I)
        if arxiv and title:
            entries.append((arxiv.group(1).strip(), title.group(1).strip(),
                            venue.group(1).strip() if venue else ""))
    return entries


def previous_counts(path):
    if not os.path.exists(path):
        return {}
    counts, seen_counts = {}, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("counts:"):
            seen_counts = True
            continue
        m = re.match(r'\s+"([^"]+)":\s*(\d+)', line)
        if seen_counts and m:
            counts[m.group(1)] = int(m.group(2))
    return counts


def scholar_articles(key):
    """Every article on the Scholar profile: [(normalised title, citations)]."""
    query = urllib.parse.urlencode({
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "num": 100,
        "api_key": key,
    })
    with urllib.request.urlopen(f"{ENDPOINT}?{query}", timeout=60) as r:
        data = json.load(r)
    if "error" in data:
        raise RuntimeError(data["error"])
    totals = {}
    for row in data.get("cited_by", {}).get("table", []):
        for name, value in row.items():
            totals[name] = value.get("all")
    articles = [(normalise(a["title"]), (a.get("cited_by") or {}).get("value") or 0)
                for a in data.get("articles", [])]
    return articles, totals


def main():
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        print("SERPAPI_KEY is not set - leaving the counts alone")
        return 0

    entries, old = bib_entries(BIB), previous_counts(OUT)
    try:
        articles, totals = scholar_articles(key)
    except Exception as e:
        print(f"could not reach Scholar: {e} - leaving the counts alone")
        return 0
    print(f"profile: {len(articles)} articles, {totals.get('citations')} citations, h-index {totals.get('h_index')}")

    counts, unmatched = {}, []
    for arxiv_id, title, _ in entries:
        want = normalise(title)
        best, score = None, 0.0
        for gs_title, cites in articles:
            s = difflib.SequenceMatcher(None, want, gs_title).ratio()
            if s > score:
                best, score = cites, s
        if best is not None and score >= MATCH_THRESHOLD:
            counts[arxiv_id] = best
            print(f"  {arxiv_id}: {best:>4}  ({score:.2f})  {title[:50]}")
        else:
            unmatched.append(title[:50])
            if arxiv_id in old:
                counts[arxiv_id] = old[arxiv_id]
            print(f"  {arxiv_id}: no match (best {score:.2f}), keeping {old.get(arxiv_id, 'nothing')}")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Citation counts shown as badges next to each publication.\n")
        f.write("# Synced from Google Scholar via SerpApi by bin/sync_citations.py\n")
        f.write("# (weekly, see .github/workflows/citations.yml). Do not edit by hand.\n")
        f.write(f"updated: {datetime.now(timezone.utc).date().isoformat()}\n")
        if totals.get("citations") is not None:
            f.write(f"total: {totals['citations']}\n")
        if totals.get("h_index") is not None:
            f.write(f"h_index: {totals['h_index']}\n")
        f.write("counts:\n")
        for arxiv_id, title, venue in entries:
            if arxiv_id in counts:
                label = f"{title.split(':')[0][:40]}" + (f" ({venue})" if venue else "")
                f.write(f'  "{arxiv_id}": {counts[arxiv_id]} # {label}\n')
    print(f"wrote {OUT}: {len(counts)}/{len(entries)} papers" + (f", unmatched: {unmatched}" if unmatched else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
