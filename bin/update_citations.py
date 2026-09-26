#!/usr/bin/env python3
"""Refresh _data/citations.yml with citation counts from Semantic Scholar.

Reads the arXiv ids out of _bibliography/papers.bib, asks Semantic Scholar for
each paper's citation count and writes them to _data/citations.yml. Counts that
cannot be fetched (rate limit, unknown paper) keep their previous value, so a
failed run never blanks the numbers already on the site.

Set S2_API_KEY for higher rate limits (https://www.semanticscholar.org/product/api).
Run from the repository root:  python3 bin/update_citations.py
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timezone, datetime

BIB = "_bibliography/papers.bib"
OUT = "_data/citations.yml"
API = "https://api.semanticscholar.org/graph/v1/paper/arXiv:{}?fields=citationCount,title"
DELAY = 4.0          # seconds between papers; the unauthenticated API is strict
ATTEMPTS = 4


def arxiv_ids(path):
    """Every arxiv id in the bibliography, in file order."""
    return re.findall(r"^\s*arxiv\s*=\s*\{([^}]+)\}", open(path, encoding="utf-8").read(), re.M | re.I)


def previous(path):
    """The counts from the last run, so a failed fetch can fall back to them."""
    if not os.path.exists(path):
        return {}
    counts, in_counts = {}, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("counts:"):
            in_counts = True
            continue
        m = re.match(r'\s+"([^"]+)":\s*(\d+)', line)
        if in_counts and m:
            counts[m.group(1)] = int(m.group(2))
    return counts


def fetch(arxiv_id, key):
    headers = {"User-Agent": "liuyanchen1015.github.io citation updater"}
    if key:
        headers["x-api-key"] = key
    for attempt in range(1, ATTEMPTS + 1):
        try:
            req = urllib.request.Request(API.format(arxiv_id), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            if "citationCount" in data:
                return data["citationCount"], data.get("title", "")
            return None, data.get("message", "no citationCount in response")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < ATTEMPTS:
                wait = DELAY * 2 ** attempt
                print(f"    rate limited, retrying in {wait:.0f}s")
                time.sleep(wait)
                continue
            return None, f"HTTP {e.code}"
        except Exception as e:  # network hiccup
            if attempt < ATTEMPTS:
                time.sleep(DELAY * attempt)
                continue
            return None, str(e)[:60]
    return None, "gave up"


def main():
    key = os.environ.get("S2_API_KEY")
    ids, old = arxiv_ids(BIB), previous(OUT)
    counts, failed = {}, []
    for i, arxiv_id in enumerate(ids):
        count, note = fetch(arxiv_id, key)
        if count is None:
            failed.append(f"{arxiv_id} ({note})")
            if arxiv_id in old:
                counts[arxiv_id] = old[arxiv_id]
            print(f"  {arxiv_id}: failed - {note}" + (f", keeping {old[arxiv_id]}" if arxiv_id in old else ""))
        else:
            counts[arxiv_id] = count
            print(f"  {arxiv_id}: {count} ({note[:50]})")
        if i < len(ids) - 1:
            time.sleep(DELAY)

    if not counts:
        print("no counts at all, leaving the file alone")
        return 1

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Citation counts from Semantic Scholar - do not edit by hand.\n")
        f.write("# Refreshed by bin/update_citations.py (weekly, see .github/workflows/citations.yml).\n")
        f.write(f"updated: {datetime.now(timezone.utc).date().isoformat()}\n")
        f.write("counts:\n")
        for arxiv_id in ids:
            if arxiv_id in counts:
                f.write(f'  "{arxiv_id}": {counts[arxiv_id]}\n')
    print(f"wrote {OUT}: {len(counts)}/{len(ids)} papers" + (f", failed: {', '.join(failed)}" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
