"""Scrape sailboat listings from boat24.ch.

boat24.com (the EU site) blocks scripted clients; boat24.ch does not.
Output: data/listings_boat24.csv
"""

import html
import re
import time

from listings import fetch, save

SEARCH = "https://www.boat24.ch/chen/usedboats/?cat=1&page={offset}"
PAGE_SIZE = 20
DELAY_S = 1.5


def field(pattern, text):
    m = re.search(pattern, text, re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).strip() if m else ""


def parse_price(raw):
    """'CHF 75'000.-' -> (75000, 'CHF'); None for 'Reserved', 'Price on request', ..."""
    m = re.match(r"(CHF|EUR|€)\s*([\d']+)", raw)
    if not m:
        return None
    return int(m.group(2).replace("'", "")), m.group(1).replace("€", "EUR")


def parse_page(page):
    for card in re.split(r'<div class="blurb blurb--', page)[1:]:
        title = field(r'blurb__title">.*?>(.*?)</a>', card)
        if not title:
            continue
        dims = field(r'blurb__value">([^<]*)</span><span class="blurb__key">Dimensions', card)
        price, currency = parse_price(field(r'blurb__price">(.*?)</p>', card)) or ("", "")
        yield {
            "id": field(r'data-id="(\d+)"', card),
            "title": title,
            "category": field(r'blurb__title-header">(.*?)</p>', card),
            "loa": dims.split(" x ")[0] if " x " in dims else "",
            "year": field(r'blurb__value">(\d{4})</span><span class="blurb__key">Year', card),
            "price": price,
            "currency": currency,
            "location": re.sub(r"\s+", " ", field(r'blurb__location">(.*?)</p>', card)),
            "url": field(r'blurb__title"><a href="([^"]+)"', card),
        }


def main():
    listings = {}
    offset = 0
    while True:
        new = [l for l in parse_page(fetch(SEARCH.format(offset=offset))) if l["id"] not in listings]
        print(f"offset {offset}: {len(new)} new")
        if not new:
            break
        listings.update((l["id"], l) for l in new)
        offset += PAGE_SIZE
        time.sleep(DELAY_S)
    save("boat24", list(listings.values()))


if __name__ == "__main__":
    main()
