"""Scrape sailing yacht listings from Apollo Duck (UK/EU, prices in GBP/EUR/USD).

Output: data/listings_apolloduck.csv
"""

import html
import re
import time

from listings import fetch, save

BASE = "https://yachts.apolloduck.com"
SEARCH = BASE + "/listings.phtml?next={offset}&sort=0&limit={limit}"
PAGE_SIZE = 50
DELAY_S = 2
CURRENCIES = {"£": "GBP", "€": "EUR", "US$": "USD"}
FEET_TO_M = 0.3048


def spec(label, panel):
    m = re.search(rf'{label}:</td>\s*<td class="_PanelSpecData">(.*?)</td>', panel, re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).split()) if m else ""


def parse_length(raw):
    """'8m' / '9.85m' / "33'" -> metres as a string."""
    m = re.match(r"([\d.]+)\s*(m|')", raw)
    if not m:
        return ""
    value = float(m.group(1))
    return f"{value * FEET_TO_M:.2f}" if m.group(2) == "'" else f"{value:.2f}"


def parse_price(raw):
    m = re.match(r"(£|€|US\$)\s*([\d,]+)", raw)
    return (int(m.group(2).replace(",", "")), CURRENCIES[m.group(1)]) if m else ("", "")


def parse_page(page):
    for panel in re.split(r'<div class="_(?:Standard|Feature|Free)AdPanel">', page)[1:]:
        link = re.search(r'href="/boat/([^"]+)-for-sale/(\d+)"', panel)
        if not link:
            continue
        status = spec("Status", panel)
        if re.search(r"sold|under offer", status, re.I):
            continue
        price, currency = parse_price(spec("Price", panel))
        yield {
            "id": link.group(2),
            # the URL slug is make + model; the displayed title is free text
            "title": link.group(1).replace("-", " ").title(),
            "category": "",
            "loa": parse_length(spec("Length", panel)),
            "year": spec("Year", panel),
            "price": price,
            "currency": currency,
            "location": spec("Location", panel),
            "url": f"{BASE}/boat/{link.group(1)}-for-sale/{link.group(2)}",
        }


def main():
    listings = {}
    offset = 0
    while True:
        new = [l for l in parse_page(fetch(SEARCH.format(offset=offset, limit=PAGE_SIZE))) if l["id"] not in listings]
        print(f"offset {offset}: {len(new)} new")
        if not new:
            break
        listings.update((l["id"], l) for l in new)
        offset += PAGE_SIZE
        time.sleep(DELAY_S)
    save("apolloduck", list(listings.values()))


if __name__ == "__main__":
    main()
