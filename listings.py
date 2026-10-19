"""Shared helpers for the per-site listing scrapers."""

import csv
import time
import urllib.request
from pathlib import Path

UA = "boat-per-buck/0.1 (personal research script)"
DATA = Path(__file__).parent / "data"
FIELDS = ["source", "id", "title", "category", "loa", "year", "price", "currency", "location", "url"]


def fetch(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except OSError as e:
            if attempt == retries:
                raise
            wait = 10 * 2**attempt
            print(f"  {e}; retrying in {wait}s")
            time.sleep(wait)


def save(source, rows):
    """Write rows (dicts with FIELDS keys, minus 'source') to data/listings_<source>.csv."""
    # nothing found means the site blocked us or changed its layout; keep the last good file
    if not rows:
        raise SystemExit(f"no {source} listings found; keeping the previous file")
    out = DATA / f"listings_{source}.csv"
    DATA.mkdir(exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows({**r, "source": source} for r in rows)
    print(f"wrote {len(rows)} listings to {out}")


def load_all():
    rows = []
    for path in sorted(DATA.glob("listings_*.csv")):
        rows += csv.DictReader(path.open())
    return rows
