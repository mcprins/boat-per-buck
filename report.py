"""Match boat listings to ORC polars and show the fastest boat models per price bracket.

Run fetch_polars.py and the fetch_<site>.py scrapers first.
Writes data/matched.csv and report.html.
"""

import csv
import math
import re
import statistics
import urllib.request
from collections import defaultdict
from pathlib import Path

import html_report
from fetch_polars import norm
from listings import DATA, load_all

BRACKETS_EUR = [0, 10_000, 25_000, 50_000, 100_000, 200_000, 350_000, 500_000, 1_000_000, float("inf")]
ECB_RATES = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
FALLBACK_RATES = {"EUR": 1.0, "CHF": 0.93, "GBP": 0.86, "DKK": 7.46, "SEK": 11.0, "NOK": 11.6, "USD": 1.10}
HTML_OUT = Path(__file__).parent / "report.html"
TOP_N = 10
MIN_PRICE_EUR = 500  # below this it's a placeholder ("bid from €100"), not a price
OUTLIER_FRACTION = 0.25  # drop listings priced below 25% of their model's median (deposits, typos)
OUTLIER_MIN_LISTINGS = 3  # ...when the model has at least this many listings to compare against
LOA_TOLERANCE = 0.15  # reject matches whose length differs by more than 15%
YEAR_TOLERANCE = 15  # reject boats built this long before the model's ORC series year
# ORC "types" that are rig/class descriptions rather than models
GENERIC_KEYS = {
    "ketch", "yawl", "sloop", "cutter", "schooner", "cruisingsloop", "bermudiansloop", "oneoff", "custom",
    "unknown", "cruiserracer", "maxi", "halftonner", "onetonner", "quartertonner", "threequartertonner",
}
# ORC doesn't rate multihulls; the rest aren't sailboats
SKIP_CATEGORIES = re.compile(r"multi ?hull|catamaran|trailer|live a board", re.I)
# sold boats, and auctions (whose price is a starting bid)
SOLD = re.compile(r"\b(sold|solgt|såld|verkauft|verkocht|reserved|reserviert)\b|veiling|geveild|auction|auktion|versteiger", re.I)
# words sellers put around the model name ("Te koop: zeiljacht Etap 22i")
FILLER = {
    "te", "koop", "zeiljacht", "zeilboot", "kajuitzeilboot", "zeilschip", "segelboot", "segelyacht",
    "sailboat", "sailing", "yacht", "for", "sale", "/", "-", "–", "|", "+", "&",
}
# separators between the model and the rest of a free-text title
SEGMENTS = re.compile(r"\s[-–|]\s|[,(|:;!]|\s(?:met|mit|with|incl|inkl)\b", re.I)
# variant letters glued to a model number: "Etap 22i", "Dehler 25CR"
VARIANT_SUFFIX = re.compile(r"\b(\d+)[a-z]{1,3}\b", re.I)
MIN_BRAND_BOATS = 5  # brands with fewer boats for sale are left out of the brand chart
# ORC builder names -> brand, keyed on the builder's first word (or first two, checked first);
# unlisted builders become their title-cased first word
BRAND_ALIASES = {
    "j rogers": "Contessa (J. Rogers)", "cantiere del": "Grand Soleil", "cantiere zuanelli": "Zuanelli",
    "j": "J/Boats", "tpi": "J/Boats", "tillotson": "J/Boats", "x": "X-Yachts", "hallberg": "Hallberg-Rassy",
    "nautor": "Nautor's Swan", "benneteau": "Beneteau", "hanseyachtsag": "Hanse", "kirie": "Feeling",
    "del": "Grand Soleil", "gibert": "Gib'Sea", "gibsea": "Gib'Sea", "marine": "Marine Projects (Moody, Sigma)",
    "comfort": "Comfortbåtar", "notesund": "Vindö", "yz": "YZ Greifswald", "camper": "Camper & Nicholson",
    "sd": "SD Marine", "ad": "AD Boats", "t": "Waarschip", "jachtbouw": "Jachtbouw Meijer",
    "sweden": "Sweden Yachts", "thames": "Thames Marine", "boo": "Boo Marin", "rus": "Rus Jachten",
    "frank": "Frank Butler", "proteus": "Esse",
}


def load_polars():
    """key -> list of eras (a reused model name has one row per era)."""
    polars = defaultdict(list)
    for r in csv.DictReader((DATA / "polars.csv").open()):
        r["model_id"] = f"{r['key']}#{r['era']}"
        polars[r["key"]].append(r)
    return polars


def pick_era(eras, year):
    """The era whose ORC series years are closest to the listing's build year; else the best-documented one."""
    if len(eras) == 1 or not year:
        return max(eras, key=lambda e: int(e["n_certs"]))

    def distance(e):
        if not e["first_year"]:
            return float("inf")
        lo, hi, y = int(e["first_year"]), int(e["last_year"]), int(year)
        return 0 if lo <= y <= hi else min(abs(y - lo), abs(y - hi))

    return min(eras, key=lambda e: (distance(e), -int(e["n_certs"])))


def brand(builder):
    words = re.sub(r"[-./'&,]", " ", builder.lower()).split()
    if not words:
        return None
    alias = BRAND_ALIASES.get(" ".join(words[:2])) or BRAND_ALIASES.get(words[0])
    # an initial ("P PETTERSSON") isn't a brand on its own
    return alias or " ".join(words[:2] if len(words[0]) == 1 else words[:1]).title()


def match(title, loa, year, polars):
    """Try the whole title, then each segment, then the same without variant suffixes."""
    texts = [title, *SEGMENTS.split(title)]
    for text in texts + [VARIANT_SUFFIX.sub(r"\1", t) for t in texts]:
        if p := match_text(text, loa, year, polars):
            return p
    return None


def match_text(text, loa, year, polars):
    """Find the longest run of words (optionally skipping a 1-2 word builder) that is an ORC model."""
    words = [w for w in text.split() if w.lower().strip(":.,!") not in FILLER]
    candidates = [
        (norm(" ".join(words[start:end])), end == len(words))
        for start in range(min(3, len(words)))
        for end in range(len(words), start, -1)
    ]
    # longest first; ties keep title order (dict.fromkeys dedupes without set's random order)
    for key, to_end in sorted(dict.fromkeys(candidates), key=lambda c: -len(c[0])):
        eras = polars.get(key)
        # short keys only when they carry a number ("j24", "x35"); a bare number ("930") isn't a model
        if not eras or len(key) < 3 or key.isdigit() or (len(key) == 3 and not any(ch.isdigit() for ch in key)) or key in GENERIC_KEYS:
            continue
        # digit-less keys ("surprise") are only trusted at the end of the title, not in a builder name
        if not to_end and not any(ch.isdigit() for ch in key):
            continue
        p = pick_era(eras, year)
        if loa and p["loa"] and abs(float(loa) - float(p["loa"])) / float(p["loa"]) > LOA_TOLERANCE:
            continue
        if year and p["first_year"] and int(year) < int(p["first_year"]) - YEAR_TOLERANCE:
            continue
        return p
    return None


def eur_rates():
    """Units of each currency per EUR: today's ECB reference rates, or fixed fallbacks when offline."""
    try:
        with urllib.request.urlopen(ECB_RATES, timeout=10) as resp:
            xml = resp.read().decode()
        return {"EUR": 1.0} | {c: float(r) for c, r in re.findall(r"currency='(\w+)' rate='([\d.]+)'", xml)}
    except OSError:
        return FALLBACK_RATES


def drop_price_outliers(matched):
    by_model = defaultdict(list)
    for m in matched:
        by_model[m["model_id"]].append(m)
    kept = []
    for boats in by_model.values():
        if len(boats) >= OUTLIER_MIN_LISTINGS:
            floor = OUTLIER_FRACTION * statistics.median(b["price_eur"] for b in boats)
            boats = [b for b in boats if b["price_eur"] >= floor]
        kept += boats
    return kept


def top_models(boats, n):
    """Group boats by model; rank models by speed (top n, or all for n=None), each represented by its cheapest listing."""
    by_model = defaultdict(list)
    for b in boats:
        by_model[b["model_id"]].append(b)
    models = [
        {**min(group, key=lambda b: b["price_eur"]), "listings": sorted(group, key=lambda b: b["price_eur"])}
        for group in by_model.values()
    ]
    return sorted(models, key=lambda m: (-m["speed"], m["price_eur"]))[:n], len(models)


def trend(boats):
    """Least-squares speed ~ log10(price), as a segment over the brand's 5th-95th percentile price span."""
    xs = [math.log10(m["price_eur"]) for m in boats]
    ys = [m["speed"] for m in boats]
    cuts = statistics.quantiles(xs, n=20, method="inclusive")
    lo, hi = cuts[0], cuts[-1]
    try:
        slope, intercept = statistics.linear_regression(xs, ys)
    except statistics.StatisticsError:  # every boat at the same price
        slope, intercept = 0.0, statistics.mean(ys)
    return [round(10**lo), round(intercept + slope * lo, 2), round(10**hi), round(intercept + slope * hi, 2)]


def main():
    polars = load_polars()
    rates = eur_rates()
    listings = [
        {**l, "price_eur": round(int(l["price"]) / rates[l["currency"]])}
        for l in load_all()
        if l["price"] and l["currency"] in rates
        and not SKIP_CATEGORIES.search(l["category"]) and not SOLD.search(l["title"])
    ]
    listings = [l for l in listings if l["price_eur"] >= MIN_PRICE_EUR]

    matched = {}
    for l in listings:
        p = match(l["title"], l["loa"], l["year"], polars)
        if p:
            # the same boat cross-posted on several sites
            dedupe_key = (p["model_id"], l["year"], round(l["price_eur"], -2))
            matched.setdefault(dedupe_key, {
                **l, "model_id": p["model_id"], "orc_type": p["type"], "builder": p["builder"],
                "orc_loa": float(p["loa"]) if p["loa"] else None, "speed": float(p["top_speed_15kt"]),
            })
    n_matched = len(matched)
    matched = drop_price_outliers(list(matched.values()))

    with (DATA / "matched.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=matched[0].keys())
        w.writeheader()
        w.writerows(sorted(matched, key=lambda m: m["price_eur"]))

    brackets = []
    for lo, hi in zip(BRACKETS_EUR, BRACKETS_EUR[1:]):
        label = f"€{lo:,.0f} – €{hi:,.0f}" if hi != float("inf") else f"€{lo:,.0f}+"
        in_bracket = [m for m in matched if lo <= m["price_eur"] < hi]
        top, n_models = top_models(in_bracket, TOP_N)
        brackets.append((label, top, len(in_bracket), n_models))
    models, _ = top_models(matched, None)

    by_brand = defaultdict(list)
    for m in matched:
        if b := brand(m["builder"]):
            m["brand"] = b
            by_brand[b].append(m)
    brands = sorted(
        (
            {
                "brand": b, "boats": len(boats), "models": len({m["model_id"] for m in boats}),
                "price_eur": round(statistics.median(m["price_eur"] for m in boats)),
                "speed": statistics.median(m["speed"] for m in boats),
                "price_range": (min(m["price_eur"] for m in boats), max(m["price_eur"] for m in boats)),
                "speed_range": (min(m["speed"] for m in boats), max(m["speed"] for m in boats)),
                "trend": trend(boats),
            }
            for b, boats in by_brand.items()
            if len(boats) >= MIN_BRAND_BOATS
        ),
        key=lambda b: -b["boats"],
    )

    print(f"{n_matched} of {len(listings)} priced listings matched an ORC polar; "
          f"{n_matched - len(matched)} dropped as price outliers\n")
    print("Fastest models per bracket: top speed at 15 kts true wind (ORC VPP, best angle)\n")
    for label, top, n_boats, n_models in brackets:
        print(f"{label}  ({n_boats} boats, {n_models} models)")
        for m in top:
            more = f"  (+{len(m['listings']) - 1} more)" if len(m["listings"]) > 1 else ""
            print(f"  {m['speed']:5.2f} kn  €{m['price_eur']:>9,}  {m['year']:4}  {m['title'][:34]:34}  [ORC: {m['orc_type']}]  {m['source']}{more}")
        print()

    html_report.render(HTML_OUT, brackets, brands, MIN_BRAND_BOATS, models, matched, len(listings), BRACKETS_EUR, TOP_N)


if __name__ == "__main__":
    main()
