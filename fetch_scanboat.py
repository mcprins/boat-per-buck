"""Scrape sailboat listings from scanboat.com (Europe-wide, prices shown in EUR).

Output: data/listings_scanboat.csv
"""

import html
import re
import time

from listings import fetch, save

SEARCH = (
    "https://www.scanboat.com/en/boat-market/boats"
    "?SearchCriteria.BoatClassification=sail&SearchCriteria.CurrencyID=2"
    "&SearchCriteria.LengthWidthUnitID=1&SearchCriteria.Searched=True&page={page}"
)
DELAY_S = 2


def parse_page(page):
    for card in re.split(r'<div class="item(?: active)?\s*">', page)[1:]:
        href = re.search(r'<a href="([^"]+)"', card)
        name = re.search(r"<h2>(.*?)</h2>", card, re.S)
        if not (href and name):
            continue
        body = re.search(r'<section class="item__body">\s*<p>(.*?)</p>', card, re.S)
        body = " ".join(body.group(1).split()) if body else ""
        price_block = re.search(r'<section class="flex-2 right">(.*?)</section>', card, re.S)
        # reduced prices show old and new; the last one is current
        prices = re.findall(r"([\d,]+) EUR", price_block.group(1)) if price_block else []
        year = re.search(r"Year : (\d{4})", body)
        country = re.search(r"Country : ([^|]+)", body)
        yield {
            "id": href.group(1).rsplit("-", 1)[-1],
            "title": " ".join(html.unescape(name.group(1)).split()),
            "category": body.split("|")[0].strip(),
            "loa": "",  # only on detail pages
            "year": year.group(1) if year else "",
            "price": prices[-1].replace(",", "") if prices else "",
            "currency": "EUR" if prices else "",
            "location": country.group(1).strip() if country else "",
            "url": "https://www.scanboat.com" + href.group(1),
        }


def main():
    listings = {}
    page_no = 1
    while True:
        new = [l for l in parse_page(fetch(SEARCH.format(page=page_no))) if l["id"] not in listings]
        print(f"page {page_no}: {len(new)} new")
        if not new:
            break
        listings.update((l["id"], l) for l in new)
        page_no += 1
        time.sleep(DELAY_S)
    save("scanboat", list(listings.values()))


if __name__ == "__main__":
    main()
