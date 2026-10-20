"""Download ORC certificate polars and compute each boat model's top speed at 15 kts TWS.

Source: https://github.com/jieter/orc-data (ORC VPP data, wind speeds 6-24 kts).
Output: data/polars.csv (one row per normalized model name and era) and data/vpp.json (each one's median VPP table).
"""

import ast
import csv
import json
import re
import statistics
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

YEARS = range(2019, 2026)
URL = "https://raw.githubusercontent.com/jieter/orc-data/master/ALL{year}.json"
TWS = 15
ERA_GAP_YEARS = 10
OUT = Path(__file__).parent / "data" / "polars.csv"
VPP_OUT = OUT.parent / "vpp.json"
# VPP table rows besides the true wind angles: optimal upwind/downwind angle and VMG, per wind speed
VMG_ROWS = ("beat_angle", "beat_vmg", "run_angle", "run_vmg")

# Certificate variants that don't change which model it is.
VARIANT_WORDS = (
    r"mod|modified|od|one design|cr|sd|dk|deep keel|shoal keel|sk|gte|le|"
    r"racing|race|irc|tall rig|tr|std|standard|cruising|ss"
)


def norm(name):
    """Normalize a model name to a compact key: 'J/109 (DK) mod.' -> 'j109'."""
    s = name.lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(rf"\b({VARIANT_WORDS})\b\.?", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def top_speed(vpp, tws=TWS):
    """Max boat speed over all true wind angles, linearly interpolated to `tws`."""
    speeds = vpp["speeds"]
    hi = next(i for i, s in enumerate(speeds) if s >= tws)
    lo = hi - 1
    frac = (tws - speeds[lo]) / (speeds[hi] - speeds[lo])
    rows = [vpp[a] for a in vpp["angles"]]
    return max(r[lo] + frac * (r[hi] - r[lo]) for r in rows)


def main():
    by_model = defaultdict(list)
    for year in YEARS:
        print(f"downloading {year}...")
        with urllib.request.urlopen(URL.format(year=year)) as resp:
            # files are Python-literal reprs, not strict JSON
            certs = ast.literal_eval(resp.read().decode())
        for c in certs:
            boat = c["boat"]
            if not boat.get("type"):
                continue
            try:
                speed = top_speed(c["vpp"])
            except (KeyError, StopIteration, ZeroDivisionError):
                continue
            key = norm(boat["type"])
            if key:
                by_model[key].append(
                    (speed, boat["sizes"].get("loa"), boat["type"].strip(), boat.get("builder") or "", c["vpp"], boat.get("year"))
                )

    OUT.parent.mkdir(exist_ok=True)
    n_rows = 0
    vpps = {}
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "era", "type", "builder", "loa", "top_speed_15kt", "n_certs", "first_year", "last_year"])
        for key, vals in sorted(by_model.items()):
            for era, certs in enumerate(split_eras(vals)):
                loas = [l for _, l, *_ in certs if l]
                years = [y for *_, y in certs if valid_year(y)]
                w.writerow([
                    key,
                    era,
                    Counter(t for _, _, t, *_ in certs).most_common(1)[0][0],
                    Counter(b.strip() for _, _, _, b, *_ in certs).most_common(1)[0][0],
                    round(statistics.median(loas), 2) if loas else "",
                    round(statistics.median(s for s, *_ in certs), 2),
                    len(certs),
                    min(years) if years else "",
                    max(years) if years else "",
                ])
                vpps[f"{key}#{era}"] = median_vpp([v for *_, v, _ in certs])
                n_rows += 1
    VPP_OUT.write_text(json.dumps(vpps, separators=(",", ":")))
    print(f"wrote {len(by_model)} boat models ({n_rows} incl. eras) to {OUT}")


def median_vpp(vpps):
    """Cell-wise median of the certificates' VPP tables.

    ORC's grid of wind angles and speeds is fixed per year (2024 added 24 kts), so use the most common grid.
    """
    grid = Counter((tuple(v["angles"]), tuple(v["speeds"])) for v in vpps).most_common(1)[0][0]
    vpps = [v for v in vpps if (tuple(v["angles"]), tuple(v["speeds"])) == grid]
    angles, speeds = grid
    return {
        "angles": list(angles), "speeds": list(speeds),
        **{str(r): [round(statistics.median(v[r][i] for v in vpps), 2) for i in range(len(speeds))]
           for r in [*angles, *VMG_ROWS]},
    }


def valid_year(y):
    return isinstance(y, int) and 1900 < y < 2100


def split_eras(certs):
    """Split one model name into eras when build years jump by more than ERA_GAP_YEARS.

    Builders reuse names (Beneteau First 30: 1977 and 2010), and the two boats have different polars.
    Certificates without a build year go to the largest era.
    """
    dated = sorted((c for c in certs if valid_year(c[-1])), key=lambda c: c[-1])
    undated = [c for c in certs if not valid_year(c[-1])]
    eras = []
    for c in dated:
        if eras and c[-1] - eras[-1][-1][-1] <= ERA_GAP_YEARS:
            eras[-1].append(c)
        else:
            eras.append([c])
    if not eras:
        return [undated]
    max(eras, key=len).extend(undated)
    return eras


if __name__ == "__main__":
    main()
