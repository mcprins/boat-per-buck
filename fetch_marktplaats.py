"""Scrape sailboat listings from marktplaats.nl and 2dehands.be (same platform).

Uses the HTML listing pages' embedded __NEXT_DATA__ JSON; the JSON search API is disallowed by robots.txt.
Output: data/listings_marktplaats.csv, data/listings_2dehands.csv
"""

import json
import re
import time

from listings import fetch, save

SITES = {"marktplaats": "https://www.marktplaats.nl", "2dehands": "https://www.2dehands.be"}
CATEGORIES = ["kajuitzeilboten-en-zeiljachten", "open-zeilboten"]
PAGE_URL = "{base}/l/watersport-en-boten/{category}/p/{page}/"
PRICED = {"FIXED", "MIN_BID"}  # MIN_BID ("bieden vanaf") is in practice an asking price
# auctions list their starting bid as MIN_BID ("Het startbod is €200.000"); that's not an asking price
AUCTION = re.compile(r"veiling|geveild|startbod|auction|auktion|versteiger", re.I)
DELAY_S = 2


def year_of(title, description):
    """Any year in the title, else an explicit 'bouwjaar'/'bj.' in the description (other years there are often the engine's)."""
    m = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", title) or re.search(
        r"\b(?:bouwjaar|bj\.?)\s*:?\s*((?:19|20)\d\d)\b", description, re.I
    )
    return m.group(1) if m else ""


def parse_page(page, base):
    data = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S).group(1))
    srr = data["props"]["pageProps"]["searchRequestAndResponse"]
    rows = []
    for l in srr["listings"]:
        if l["itemId"].startswith("a"):  # commercial ads, not boats
            continue
        attrs = {a["key"]: a["value"] for a in l.get("extendedAttributes", [])}
        price = l["priceInfo"]
        description = l.get("categorySpecificDescription") or l.get("description", "")
        is_auction = AUCTION.search(l["title"] + " " + description)
        length = re.match(r"([\d.,]+) m", attrs.get("lengthMotorboatsYachts", ""))
        rows.append({
            "id": l["itemId"],
            "title": l["title"],
            "category": attrs.get("typeCabinSailboatsYachts", ""),
            "loa": length.group(1).replace(",", ".") if length else "",
            "year": year_of(l["title"], description),
            "price": price["priceCents"] // 100 if price["priceType"] in PRICED and price["priceCents"] and not is_auction else "",
            "currency": "EUR",
            "location": f'{l["location"].get("cityName", "")}, {l["location"].get("countryAbbreviation", "")}',
            "url": base + l["vipUrl"],
        })
    return rows, srr.get("maxAllowedPageNumber") or 1


def scrape(base):
    listings = {}
    for category in CATEGORIES:
        page_no, last = 1, 1
        while page_no <= last:
            rows, last = parse_page(fetch(PAGE_URL.format(base=base, category=category, page=page_no)), base)
            # paid boosts repeat across pages, so dedupe by id
            listings.update((r["id"], r) for r in rows)
            print(f"{base} {category} page {page_no}/{last}: {len(rows)} rows, {len(listings)} unique")
            page_no += 1
            time.sleep(DELAY_S)
    return list(listings.values())


def main():
    for source, base in SITES.items():
        save(source, scrape(base))


if __name__ == "__main__":
    main()
