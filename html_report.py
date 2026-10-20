"""Render the bracket results as a standalone HTML page (no external assets)."""

import datetime
import html
import json
import math
import statistics
from collections import Counter

# Shared by the report and the VPP page
STYLE = """:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-rest: #52514e; --other: #c3c2b7; --row-hover: #f0efec;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-rest: #c3c2b7; --other: #52514e; --row-hover: #262624;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--text-primary);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 40px 24px 64px; }
h1 { font-size: 28px; font-weight: 600; margin: 0 0 4px; }
h2 { font-size: 18px; font-weight: 600; margin: 0; }
.sub { color: var(--text-secondary); margin: 0 0 24px; }
.card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 14px 18px; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 24px; font-weight: 600; }
.chart { position: relative; }
.chart svg { display: block; width: 100%; height: auto; overflow: visible; }
.chart text { fill: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }
.chart .bracket-label, .chart .brand-label { fill: var(--text-secondary); }
.tip { position: absolute; pointer-events: none; background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; font-size: 13px; box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  opacity: 0; transition: opacity .1s; white-space: nowrap; z-index: 2; }
.tip b { font-weight: 600; }
.tip .meta { color: var(--text-secondary); }
.note { color: var(--text-secondary); font-size: 13px; margin: 4px 0 8px; }
.picker { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; --key: var(--series-1); }
.chip, .picker select { font: inherit; font-size: 13px; color: var(--text-secondary); background: transparent;
  border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px; cursor: pointer; }
.chip:hover { background: var(--row-hover); }
.chip[aria-pressed="true"] { color: var(--text-primary); border-color: var(--axis); background: var(--row-hover); }
.chip[aria-pressed="true"]::before { content: ""; display: inline-block; width: 10px; height: 3px; border-radius: 2px;
  margin-right: 6px; vertical-align: 3px; background: var(--key); }
details { margin-top: 12px; }
summary { cursor: pointer; color: var(--text-secondary); font-size: 13px; }
details table { margin-top: 8px; }
.bracket-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.bracket-head .count { color: var(--text-secondary); font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-weight: 500; color: var(--text-secondary); font-size: 12px; padding: 6px 8px;
  border-bottom: 1px solid var(--axis); }
td { padding: 7px 8px; border-bottom: 1px solid var(--grid); }
tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--row-hover); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.rank { color: var(--muted); width: 28px; }
td .orc { color: var(--text-secondary); font-size: 12px; }
a { color: inherit; text-decoration-color: var(--axis); text-underline-offset: 3px; }
a:hover { text-decoration-color: currentColor; }
.src { color: var(--text-secondary); font-size: 13px; }
footer { color: var(--muted); font-size: 13px; margin-top: 32px; }
.tip .links { pointer-events: auto; display: flex; gap: 18px; margin-top: 6px; }
.tip .links a { padding: 4px 0; font-weight: 600; color: var(--series-1); text-decoration: none; }
.tip .links a:hover { text-decoration: underline; }
@media (max-width: 640px) {
  .hide-sm { display: none; }
  main { padding: 24px 16px 48px; }
  h1 { font-size: 22px; }
  /* no card chrome on a phone: charts run edge to edge */
  .card { padding: 16px 0; margin: 0; border: 0; border-radius: 0; background: none; }
  .card + .card { border-top: 1px solid var(--grid); }
  .chart { margin: 0 -16px; }
  .note { display: none; }
  .picker { flex-wrap: nowrap; overflow-x: auto; margin: 8px -16px 4px; padding: 0 16px; scrollbar-width: none; }
  .chip, .picker select { flex: none; }
  .tiles { grid-template-columns: 1fr 1fr; }
  .tile .value { font-size: 20px; }
  .tip { white-space: normal; max-width: calc(100% - 8px); }
  table { font-size: 13px; }
  th, td { padding: 6px 4px; }
}
"""

HELPERS = """const fmt = v => v >= 1e6 ? "€" + (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + "M" : v >= 1e3 ? "€" + Math.round(v / 1e3) + "K" : "€" + v;
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent.appendChild(e);
  return e;
};
// draw at the container's real width so text stays 12px on a phone; on a narrow screen, fill most of its height
const size = (root, h) => {
  const W = Math.round(root.clientWidth) || 1000;
  return [W, W < 640 ? Math.max(320, Math.round(window.innerHeight * 0.7)) : h];
};
// tooltip above the item (r: its radius), or below it near the top edge; when pinned, with the item's links
const place = (svg, tip, cx, cy, r = 0) => {
  if (tip.links?.length) {
    const div = document.createElement("div");
    div.className = "links";
    tip.links.forEach(([label, href]) => {
      const a = document.createElement("a");
      a.href = href; a.target = "_blank"; a.rel = "noopener";
      a.textContent = label + " ↗";
      div.appendChild(a);
    });
    tip.appendChild(div);
  }
  const rect = svg.getBoundingClientRect(), k = svg.viewBox.baseVal.width / rect.width;
  const tx = cx / k, top = (cy - r) / k - tip.offsetHeight - 10;
  tip.style.left = Math.max(4, Math.min(tx + 14, rect.width - tip.offsetWidth - 4)) + "px";
  tip.style.top = (top < 0 ? (cy + r) / k + 14 : top) + "px";
  tip.style.opacity = 1;
};
// With a mouse, hover shows the tooltip. A click (or tap: touch has no hover) pins it as a small popup with the
// item's links; clicking the item again, clicking elsewhere or Escape closes it.
let pointerType = "mouse";
function interact(svg, tip, { hit, show, hide, links }) {
  let pinned = null;
  const point = ev => {
    const r = svg.getBoundingClientRect(), k = svg.viewBox.baseVal.width / r.width;
    return [(ev.clientX - r.left) * k, (ev.clientY - r.top) * k];
  };
  const open = (item, pin) => { tip.links = pin && links ? links(item) : null; show(item); };
  // hide() only fades the tooltip, so drop the links too or they stay clickable while invisible
  const clear = () => { hide(); tip.querySelector(".links")?.remove(); pinned = null; svg.style.cursor = ""; };
  svg.addEventListener("pointerdown", ev => { pointerType = ev.pointerType; });
  svg.addEventListener("pointermove", ev => {
    if (ev.pointerType !== "mouse" || pinned) return;  // a pinned popup stays put while the mouse heads for its links
    const item = hit(...point(ev), 1);
    if (!item) return clear();
    open(item, false);
    svg.style.cursor = "pointer";
  });
  svg.addEventListener("pointerleave", ev => { if (ev.pointerType === "mouse" && !pinned) clear(); });
  svg.addEventListener("click", ev => {
    const item = hit(...point(ev), pointerType === "mouse" ? 1 : 2);  // fingers are less precise: twice the reach
    if (!item || item === pinned) return clear();
    pinned = item;
    open(item, true);
  });
  document.addEventListener("click", ev => {
    if (pinned && !svg.contains(ev.target) && !tip.contains(ev.target)) clear();
  });
  document.addEventListener("keydown", ev => { if (pinned && ev.key === "Escape") clear(); });
}
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Boat per buck: fastest sailboats per price bracket</title>
<style>
__STYLE__
</style>
</head>
<body>
<main>
  <h1>Fastest sailboat models per price bracket</h1>
  <p class="sub">Predicted top speed at 15 kts true wind (ORC VPP, best angle) for boats currently for sale. Generated __DATE__.</p>

  <section class="card">
    <h2>Speed vs. asking price</h2>
    <p class="note">One dot per boat for sale; click or tap a dot for links to its listing and its model's VPP (speed polar).
      Pick brands to grey out the rest, so only the picked brands' boats can be clicked; the first three picks get their own colour, later picks share dark grey.</p>
    <div id="price-picker" class="picker" role="group" aria-label="Brands to show"></div>
    <div id="chart" class="chart"><div id="tip" class="tip"></div></div>
  </section>

  <section class="card">
    <h2>Speed vs. length</h2>
    <p class="note">One dot per boat model for sale (length overall from its ORC certificates); click or tap a dot for links to its cheapest listing and its VPP.
      The dashed curve is the classic displacement hull speed, 1.34·√LOA (ft), treating length overall as waterline length.
      The solid curve is the trend through the dots: __FIT__.</p>
    <div id="length-picker" class="picker" role="group" aria-label="Brands to show"></div>
    <div id="length-chart" class="chart"><div id="length-tip" class="tip"></div></div>
  </section>

  <section class="card">
    <h2>Brands: median speed vs. median asking price</h2>
    <p class="note">One dot per brand (ORC builder) with at least __MIN_BRAND__ boats for sale; dot size is the number of boats.</p>
    <div id="brand-chart" class="chart"><div id="brand-tip" class="tip"></div></div>
    <details>
      <summary>Show as table</summary>
      <table>
        <thead><tr><th>Brand</th><th class="num">Boats</th><th class="num">Models</th><th class="num">Median price</th><th class="num">Median knots</th></tr></thead>
        <tbody>__BRAND_ROWS__</tbody>
      </table>
    </details>
  </section>

  __BRACKETS__

  <div class="tiles">__TILES__</div>

  <footer>
    Sources: __SOURCES__. Polars: ORC certificates via github.com/jieter/orc-data.
    Speeds are per model (median over certificates), not per individual boat. Prices converted to EUR at ECB reference rates.
  </footer>
</main>
<script>
const BOATS = __DATA__;
const BRACKET_EDGES = __EDGES__;
const BRANDS = __BRANDS__;
const MODELS = __MODELS__;
const FIT = __FIT_JSON__;

__HELPERS__

// Brand filter: chips for the most-listed brands, a dropdown for the rest. An empty selection shows every brand.
// Only the first three picks get their own hue (more stop being distinguishable in a scatter, colour-blind or not);
// later picks share a neutral. A brand keeps its colour while it stays picked.
const slotColor = k => k ? `var(--series-${k})` : "var(--series-rest)";
function brandPicker(root, items, onChange) {
  const CHIPS = 12, EXTRA_CHIPS = 6;  // dropdown picks get a chip too, while there are only a few of them
  const counts = new Map();
  items.forEach(d => { if (d.b) counts.set(d.b, (counts.get(d.b) || 0) + 1); });
  const brands = [...counts.keys()].sort((a, b) => counts.get(b) - counts.get(a) || a.localeCompare(b));
  const sel = new Map();  // brand -> colour slot (1-3, or 0 for the shared neutral)
  const add = b => sel.set(b, [1, 2, 3].find(k => ![...sel.values()].includes(k)) || 0);
  const toggle = b => { sel.has(b) ? sel.delete(b) : add(b); update(); };
  const update = () => { draw(); onChange(sel); };
  const chip = (label, pressed, onClick, key) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = label;
    if (pressed !== undefined) btn.setAttribute("aria-pressed", pressed ? "true" : "false");
    if (key) btn.style.setProperty("--key", key);
    btn.addEventListener("click", onClick);
    root.appendChild(btn);
  };
  function draw() {
    root.replaceChildren();
    if (sel.size < brands.length) chip("Select all", undefined, () => { brands.forEach(b => { if (!sel.has(b)) add(b); }); update(); });
    if (sel.size) chip("Clear", undefined, () => { sel.clear(); update(); });
    const picked = brands.slice(CHIPS).filter(b => sel.has(b));
    const shown = [...brands.slice(0, CHIPS), ...(picked.length <= EXTRA_CHIPS ? picked : [])];
    shown.forEach(b => chip(b, sel.has(b), () => toggle(b), sel.has(b) && slotColor(sel.get(b))));
    const more = brands.filter(b => !shown.includes(b));
    if (!more.length) return;
    const select = document.createElement("select");
    select.setAttribute("aria-label", "More brands");
    const n = more.filter(b => sel.has(b)).length;
    [["", `More brands (${n ? n + " of " : ""}${more.length})…`],
     ...more.map(b => [b, `${sel.has(b) ? "✓ " : ""}${b} (${counts.get(b)})`])].forEach(([value, text]) => {
      const o = document.createElement("option");
      o.value = value;
      o.textContent = text;
      select.appendChild(o);
    });
    select.addEventListener("change", () => { if (select.value) toggle(select.value); });
    root.appendChild(select);
  }
  draw();
}

// Dots for items (each with cx, cy and brand b), filtered by a brand picker: the picked brands' dots in their colours
// on top (first pick topmost), the rest grey underneath. Returns a function giving the dots that can currently be hit.
function filteredDots(svg, items, pickerRoot, r) {
  const layer = el("g", {}, svg);
  let active = items;
  const draw = sel => {
    layer.replaceChildren();
    active = sel.size ? items.filter(d => sel.has(d.b)) : items;
    if (sel.size) items.forEach(d => { if (!sel.has(d.b)) el("circle", { cx: d.cx, cy: d.cy, r: r - 1, fill: "var(--other)" }, layer); });
    const z = d => sel.size && sel.get(d.b) ? 4 - sel.get(d.b) : 0;
    [...active].sort((a, b) => z(a) - z(b)).forEach(d =>
      el("circle", { cx: d.cx, cy: d.cy, r, fill: sel.size ? slotColor(sel.get(d.b)) : "var(--series-1)",
        stroke: "var(--surface-1)", "stroke-width": 1 }, layer));
  };
  draw(new Set());
  brandPicker(pickerRoot, items, draw);
  return () => active;
}

(function () {
  const root = document.getElementById("chart");
  const tip = document.getElementById("tip");
  const [W, H] = size(root, 440), m = { t: 28, r: 16, b: 40, l: 44 };
  const xmin = Math.log10(Math.max(500, Math.min(...BOATS.map(b => b.p)) * 0.9));
  const xmax = Math.log10(Math.max(...BOATS.map(b => b.p)) * 1.1);
  const ymin = Math.floor(Math.min(...BOATS.map(b => b.s))) - 0.5;
  const ymax = Math.ceil(Math.max(...BOATS.map(b => b.s))) + 0.5;
  const x = p => m.l + (Math.log10(p) - xmin) / (xmax - xmin) * (W - m.l - m.r);
  const y = s => H - m.b - (s - ymin) / (ymax - ymin) * (H - m.t - m.b);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Scatter plot of predicted speed against asking price; tables below list the same boats." }, root);

  // gridlines + y ticks
  for (let s = Math.ceil(ymin); s <= ymax; s++) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s), stroke: "var(--grid)" }, svg);
    el("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" }, svg).textContent = s;
  }
  el("text", { x: m.l - 8, y: m.t - 12, "text-anchor": "end" }, svg).textContent = "knots";
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)" }, svg);
  // x ticks: bracket edges (with a gridline each), plus round values outside the bracket range
  const lo = BRACKET_EDGES.find(e => e > 0), hi = BRACKET_EDGES[BRACKET_EDGES.length - 1];
  const extra = [1e3, 2e3, 5e3, 2e6, 5e6].filter(v => v < lo || v > hi);
  let lastLabelX = -Infinity;
  [...BRACKET_EDGES.filter(e => e > 0), ...extra].sort((a, b) => a - b).forEach(v => {
    const lv = Math.log10(v);
    if (lv < xmin || lv > xmax) return;
    if (BRACKET_EDGES.includes(v)) el("line", { x1: x(v), x2: x(v), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    if (x(v) - lastLabelX < 56) return;  // labels would collide; the gridline stays
    el("text", { x: x(v), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = fmt(v);
    lastLabelX = x(v);
  });

  BOATS.forEach(b => { b.cx = x(b.p); b.cy = y(b.s); });
  const dots = filteredDots(svg, BOATS, document.getElementById("price-picker"), 3.5);
  const ring = el("circle", { r: 7, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  interact(svg, tip, {
    // nearest shown boat within 12 px
    hit: (px, py, reach) => {
      let best = null, bd = (12 * reach) ** 2;
      for (const b of dots()) {
        const d = (b.cx - px) ** 2 + (b.cy - py) ** 2;
        if (d < bd) { bd = d; best = b; }
      }
      return best;
    },
    show: b => {
      ring.setAttribute("cx", b.cx); ring.setAttribute("cy", b.cy); ring.setAttribute("opacity", 1);
      tip.innerHTML = `<b></b><div class="meta"></div>`;
      tip.querySelector("b").textContent = b.t;
      tip.querySelector(".meta").textContent =
        `${b.s.toFixed(2)} kn · €${b.p.toLocaleString("en")}${b.y ? " · " + b.y : ""} · ${b.src}`;
      place(svg, tip, b.cx, b.cy);
    },
    hide: () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); },
    links: b => [["Listing", b.u], ["VPP", "vpp.html#" + b.v]],
  });
})();

(function () {
  const root = document.getElementById("length-chart");
  const tip = document.getElementById("length-tip");
  const [W, H] = size(root, 480), m = { t: 28, r: 16, b: 40, l: 44 };
  MODELS.forEach(b => { b.ft = b.l * 3.28084; });
  const xmin = Math.floor(Math.min(...MODELS.map(b => b.ft))), xmax = Math.ceil(Math.max(...MODELS.map(b => b.ft)));
  const ymin = Math.floor(Math.min(...MODELS.map(b => b.s))) - 0.5;
  const ymax = Math.ceil(Math.max(...MODELS.map(b => b.s))) + 0.5;
  const x = l => m.l + (l - xmin) / (xmax - xmin) * (W - m.l - m.r);
  const y = s => H - m.b - (s - ymin) / (ymax - ymin) * (H - m.t - m.b);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Scatter plot of predicted speed against length overall, one dot per boat model for sale." }, root);

  for (let s = Math.ceil(ymin); s <= ymax; s++) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s), stroke: "var(--grid)" }, svg);
    el("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" }, svg).textContent = s;
  }
  el("text", { x: m.l - 8, y: m.t - 12, "text-anchor": "end" }, svg).textContent = "knots";
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)" }, svg);
  // every 5 ft, or 10/15/... when the labels would sit closer than 40 px
  const step = 5 * Math.ceil(40 / (5 * (x(1) - x(0)))), lastTick = xmax - xmax % step;
  for (let l = Math.ceil(xmin / step) * step; l <= xmax; l += step) {
    el("line", { x1: x(l), x2: x(l), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    el("text", { x: x(l), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = l + (l === lastTick ? " ft" : "");
  }

  const hull = ft => 1.34 * Math.sqrt(ft);
  let d = "";
  for (let l = xmin; l <= xmax; l += 1) {
    if (hull(l) > ymax) break;
    d += (d ? "L" : "M") + x(l).toFixed(1) + "," + y(hull(l)).toFixed(1);
  }
  el("path", { d, fill: "none", stroke: "var(--text-secondary)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }, svg);
  // label below the curve near its left end, where it runs under the trend and the dots
  el("text", { x: x(xmin + 1), y: y(hull(xmin + 1)) + 22, "text-anchor": "start", class: "brand-label" }, svg).textContent = "hull speed 1.34·√L";

  // trend through the dots (fitted in report.py), labelled below its right end (where it runs under the hull-speed
  // curve), with the constant the data gives when forced into the hull-speed form
  const trend = ft => FIT.a * ft ** FIT.b;
  d = "";
  for (let l = xmin; l <= xmax; l += 1) d += (d ? "L" : "M") + x(l).toFixed(1) + "," + y(trend(l)).toFixed(1);
  el("path", { d, fill: "none", stroke: "var(--text-primary)", "stroke-width": 2 }, svg);
  const trendLabel = el("text", { x: x(xmax), y: y(trend(xmax)) + 22, "text-anchor": "end", class: "brand-label" }, svg);
  trendLabel.textContent = `trend ${FIT.a.toFixed(2)}·L`;
  el("tspan", { dy: -5, "font-size": 10 }, trendLabel).textContent = FIT.b.toFixed(2);
  el("tspan", { x: x(xmax), dy: 20 }, trendLabel).textContent = `as k·√L: k = ${FIT.k.toFixed(2)}`;

  MODELS.forEach(b => { b.cx = x(b.ft); b.cy = y(b.s); });
  const dots = filteredDots(svg, MODELS, document.getElementById("length-picker"), 3.5);
  const ring = el("circle", { r: 7, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  interact(svg, tip, {
    hit: (px, py, reach) => {
      let best = null, bd = (12 * reach) ** 2;
      for (const b of dots()) {
        const dd = (b.cx - px) ** 2 + (b.cy - py) ** 2;
        if (dd < bd) { bd = dd; best = b; }
      }
      return best;
    },
    show: b => {
      ring.setAttribute("cx", b.cx); ring.setAttribute("cy", b.cy); ring.setAttribute("opacity", 1);
      tip.innerHTML = `<b></b><div class="meta"></div><div class="meta"></div>`;
      tip.querySelector("b").textContent = b.t;
      const metas = tip.querySelectorAll(".meta");
      metas[0].textContent = `${b.s.toFixed(2)} kn · ${b.ft.toFixed(1)} ft (${b.l.toFixed(2)} m) · ORC: ${b.orc}`;
      metas[1].textContent = `${b.n} for sale, from €${b.p.toLocaleString("en")}`;
      place(svg, tip, b.cx, b.cy);
    },
    hide: () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); },
    links: b => [["Listing", b.u], ["VPP", "vpp.html#" + b.v]],
  });
})();

(function () {
  const root = document.getElementById("brand-chart");
  const tip = document.getElementById("brand-tip");
  const [W, H] = size(root, 520), m = { t: 28, r: 24, b: 40, l: 44 };
  const xmin = Math.log10(Math.min(...BRANDS.map(b => b.p)) / 1.4);
  const xmax = Math.log10(Math.max(...BRANDS.map(b => b.p)) * 1.4);
  const ymin = Math.floor(Math.min(...BRANDS.map(b => b.s)) - 0.25);
  const ymax = Math.ceil(Math.max(...BRANDS.map(b => b.s)) + 0.25);
  const x = p => m.l + (Math.log10(p) - xmin) / (xmax - xmin) * (W - m.l - m.r);
  const y = s => H - m.b - (s - ymin) / (ymax - ymin) * (H - m.t - m.b);
  const maxN = Math.max(...BRANDS.map(b => b.n));
  const rad = n => (4 + 12 * Math.sqrt(n / maxN)) * Math.max(0.6, Math.min(1, W / 800));
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Scatter plot of each brand's median speed against median asking price; the table below lists the same brands." }, root);

  for (let s = ymin; s <= ymax; s += 0.5) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s), stroke: "var(--grid)" }, svg);
    if (s % 1 === 0) el("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" }, svg).textContent = s;
  }
  el("text", { x: m.l - 8, y: m.t - 12, "text-anchor": "end" }, svg).textContent = "knots";
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)" }, svg);
  let lastLabelX = -Infinity;
  [2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6].forEach(v => {
    const lv = Math.log10(v);
    if (lv < xmin || lv > xmax) return;
    el("line", { x1: x(v), x2: x(v), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    if (x(v) - lastLabelX < 48) return;  // labels would collide; the gridline stays
    el("text", { x: x(v), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = fmt(v);
    lastLabelX = x(v);
  });

  // biggest dots first so small brands stay visible on top
  const dots = [...BRANDS].sort((a, b) => b.n - a.n);
  dots.forEach(b => { b.cx = x(b.p); b.cy = y(b.s); b.r = rad(b.n); });
  dots.forEach(b =>
    el("circle", { cx: b.cx, cy: b.cy, r: b.r, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 2 }, svg));

  // direct labels, most-listed brands first; skip any that would cover a dot or a placed label
  const boxes = dots.map(b => [b.cx - b.r, b.cy - b.r, b.cx + b.r, b.cy + b.r]);
  const labelLayer = el("g", {}, svg);
  dots.forEach(b => {
    const w = b.brand.length * 6.8, h = 13, d = b.r * 0.7 + 3;
    // next to the dot first; failing that, further out with a leader line (only in crowded clusters)
    const spots = [0, 22].flatMap(o => [
      [b.cx + b.r + 4 + o, b.cy + 4, "start"], [b.cx - b.r - 4 - o, b.cy + 4, "end"],
      [b.cx, b.cy - b.r - 5 - o, "middle"], [b.cx, b.cy + b.r + 14 + o, "middle"],
      [b.cx + d + o, b.cy - d - 2 - o, "start"], [b.cx - d - o, b.cy - d - 2 - o, "end"],
      [b.cx + d + o, b.cy + d + 11 + o, "start"], [b.cx - d - o, b.cy + d + 11 + o, "end"],
    ].map(s => [...s, o]));
    for (const [lx, ly, anchor, o] of spots) {
      const x0 = anchor === "start" ? lx : anchor === "end" ? lx - w : lx - w / 2;
      const box = [x0, ly - 10, x0 + w, ly - 10 + h];
      if (box[0] < m.l || box[2] > W - m.r || box[1] < m.t - 8 || box[3] > H - m.b) continue;
      if (boxes.some(o => box[0] < o[2] && box[2] > o[0] && box[1] < o[3] && box[3] > o[1])) continue;
      if (o && b.n < maxN / 4) break;
      boxes.push(box);
      if (o) {
        // leader from the dot's edge to the label's nearest edge point
        const tx = Math.max(box[0], Math.min(b.cx, box[2])), ty = Math.max(box[1], Math.min(b.cy, box[3]));
        const len = Math.hypot(tx - b.cx, ty - b.cy);
        el("line", { x1: b.cx + (tx - b.cx) * b.r / len, y1: b.cy + (ty - b.cy) * b.r / len, x2: tx, y2: ty,
          stroke: "var(--muted)", "stroke-width": 1 }, labelLayer);
      }
      el("text", { x: lx, y: ly, "text-anchor": anchor, class: "brand-label" }, labelLayer).textContent = b.brand;
      break;
    }
  });
  const ring = el("circle", { fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  interact(svg, tip, {
    // the smallest dot under the pointer (or within 6 px of its edge)
    hit: (px, py, reach) => {
      let best = null;
      for (const b of dots) {
        if (Math.hypot(b.cx - px, b.cy - py) <= b.r + 6 * reach && (!best || b.r < best.r)) best = b;
      }
      return best;
    },
    show: b => {
      ring.setAttribute("cx", b.cx); ring.setAttribute("cy", b.cy); ring.setAttribute("r", b.r + 3);
      ring.setAttribute("opacity", 1);
      tip.innerHTML = `<b></b><div class="meta"></div><div class="meta"></div>`;
      tip.querySelector("b").textContent = b.brand;
      const metas = tip.querySelectorAll(".meta");
      metas[0].textContent = `${b.s.toFixed(2)} kn · €${b.p.toLocaleString("en")} (medians)`;
      metas[1].textContent = `${b.n} boats · ${b.models} models`;
      place(svg, tip, b.cx, b.cy, b.r);
    },
    hide: () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); },
  });
})();
</script>
</body>
</html>
"""


VPP_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Boat per buck: VPP</title>
<style>
__STYLE__
/* wind speeds, light to dark (dark mode: dark to light), so stronger wind always has more contrast */
:root { --tws-0: #86b6ef; --tws-1: #6da7ec; --tws-2: #5598e7; --tws-3: #3987e5; --tws-4: #2a78d6; --tws-5: #1c5cab; --tws-6: #184f95; --tws-7: #0d366b; }
@media (prefers-color-scheme: dark) {
  :root { --tws-0: #184f95; --tws-1: #1c5cab; --tws-2: #256abf; --tws-3: #3987e5; --tws-4: #5598e7; --tws-5: #6da7ec; --tws-6: #9ec5f4; --tws-7: #cde2fb; }
}
.home { color: var(--text-secondary); font-size: 13px; }
.model-pick { margin: 4px 0 20px; }
.model-pick select { font: inherit; font-size: 14px; color: var(--text-primary); background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px; padding: 4px 8px; max-width: 100%; }
.vpp-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr); gap: 20px; align-items: start; }
.vpp-grid .card { margin-bottom: 0; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 13px; color: var(--text-secondary); margin: 4px 0 8px; }
.legend span::before { content: ""; display: inline-block; width: 14px; height: 3px; border-radius: 2px;
  margin-right: 6px; vertical-align: 3px; background: var(--key); }
.polar path.curve { transition: opacity .1s; }
td.best { font-weight: 600; }
tr.vmg td { color: var(--text-secondary); }
.scroll { overflow-x: auto; }
.sub a { white-space: nowrap; }
@media (max-width: 900px) { .vpp-grid { grid-template-columns: minmax(0, 1fr); } }
</style>
<script>
const MODELS = __VPP__;
__HELPERS__
</script>
</head>
<body>
<main>
  <a class="home" href="./">← Boat per buck</a>
  <h1 id="title">VPP</h1>
  <p class="sub" id="sub">Pick a model.</p>
  <div class="model-pick"><select id="pick" aria-label="Boat model"></select></div>
  <div class="vpp-grid" id="content" hidden>
    <section class="card">
      <h2>Polar</h2>
      <p class="note">Predicted boat speed by true wind angle, one curve per true wind speed. Hover or tap a curve for its values.</p>
      <div class="legend" id="legend"></div>
      <div id="polar" class="chart"><div id="polar-tip" class="tip"></div></div>
    </section>
    <section class="card">
      <h2>Boat speed (knots)</h2>
      <p class="note">Median over the model's ORC certificates. Bold: the fastest angle at each wind speed.
        Beat and run rows give the optimal angle and the velocity made good up- and downwind.</p>
      <div class="scroll"><table id="table"></table></div>
    </section>
  </div>
  <footer>Polars: ORC certificates via github.com/jieter/orc-data. Generated __DATE__.</footer>
</main>
<script>
const ids = Object.keys(MODELS).sort((a, b) => MODELS[a].t.localeCompare(MODELS[b].t) || a.localeCompare(b));
const pick = document.getElementById("pick");
[["", "Pick a model…"], ...ids.map(id => [id, `${MODELS[id].t} (${MODELS[id].bl})`])].forEach(([value, text]) => {
  const o = document.createElement("option");
  o.value = value; o.textContent = text;
  pick.appendChild(o);
});
pick.addEventListener("change", () => { if (pick.value) location.hash = pick.value; });

// each curve: the table's angles plus the optimal beat and run angles, where boat speed = VMG / |cos(angle)|
function curves(v) {
  const rad = a => a * Math.PI / 180;
  return v.speeds.map((tws, i) => ({
    tws, key: `var(--tws-${i})`,
    pts: [
      [v.beat_angle[i], v.beat_vmg[i] / Math.cos(rad(v.beat_angle[i]))],
      ...v.angles.map(a => [a, v[a][i]]),
      [v.run_angle[i], v.run_vmg[i] / -Math.cos(rad(v.run_angle[i]))],
    ].sort((p, q) => p[0] - q[0]),
  }));
}

function drawPolar(m) {
  const root = document.getElementById("polar"), tip = document.getElementById("polar-tip");
  root.querySelector("svg")?.remove();
  // room for the angle labels just outside the rim (at 1.07 R)
  const W = Math.round(root.clientWidth) || 400, R = Math.min((W - 16 - 36) / 1.07, 300);
  const mg = { t: 0.07 * R + 16, r: 0.07 * R + 36, b: 0.07 * R + 16, l: 16 }, H = Math.round(2 * R + mg.t + mg.b);
  const cx = mg.l, cy = mg.t + R;
  const cs = curves(m.v);
  const vmax = 2 * Math.ceil(Math.max(...cs.flatMap(c => c.pts.map(p => p[1]))) / 2);
  const pos = (a, s) => [cx + R * s / vmax * Math.sin(a * Math.PI / 180), cy - R * s / vmax * Math.cos(a * Math.PI / 180)];
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", class: "polar",
    "aria-label": `Polar diagram of ${m.t}: boat speed by true wind angle for wind speeds ${m.v.speeds.join(", ")} knots; the table lists the same values.` }, root);
  root.insertBefore(svg, tip);

  // speed rings every 2 kn, labelled on the upwind axis; spokes every 30°, labelled outside the rim
  for (let s = 2; s <= vmax; s += 2) {
    const [x1, y1] = pos(0, s), [x2, y2] = pos(180, s);
    el("path", { d: `M${x1},${y1} A${R * s / vmax},${R * s / vmax} 0 0 1 ${x2},${y2}`, fill: "none", stroke: "var(--grid)" }, svg);
    el("text", { x: cx + 4, y: y1 + 12, "text-anchor": "start" }, svg).textContent = s + (s === vmax ? " kn" : "");
  }
  for (let a = 0; a <= 180; a += 30) {
    const [x, y] = pos(a, vmax), [lx, ly] = pos(a, vmax * 1.07);
    el("line", { x1: cx, y1: cy, x2: x, y2: y, stroke: a % 180 ? "var(--grid)" : "var(--axis)" }, svg);
    el("text", { x: lx, y: ly + 4, "text-anchor": a % 180 ? "start" : "middle" }, svg).textContent = a + "°";
  }

  // smooth through the points (Catmull-Rom as cubic Béziers); the points themselves are the VPP's values
  const smooth = ps => ps.slice(1).reduce((d, p2, i) => {
    const p0 = ps[Math.max(i - 1, 0)], p1 = ps[i], p3 = ps[Math.min(i + 2, ps.length - 1)];
    const c = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    return d + `C${c.map(n => n.toFixed(1)).join(",")},${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }, `M${ps[0][0].toFixed(1)},${ps[0][1].toFixed(1)}`);
  const paths = cs.map(c => el("path", {
    class: "curve", fill: "none", stroke: c.key, "stroke-width": 2, d: smooth(c.pts.map(p => pos(...p))),
  }, svg));
  const ring = el("circle", { r: 5, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);
  const items = cs.flatMap((c, ci) => c.pts.map(([a, s]) => { const [x, y] = pos(a, s); return { c, ci, a, s, x, y }; }));

  interact(svg, tip, {
    hit: (px, py, reach) => {
      let best = null, bd = (16 * reach) ** 2;
      for (const it of items) {
        const d = (it.x - px) ** 2 + (it.y - py) ** 2;
        if (d < bd) { bd = d; best = it; }
      }
      return best;
    },
    show: it => {
      paths.forEach((p, i) => p.setAttribute("opacity", i === it.ci ? 1 : 0.25));
      ring.setAttribute("cx", it.x); ring.setAttribute("cy", it.y); ring.setAttribute("opacity", 1);
      tip.innerHTML = `<b></b><div class="meta"></div>`;
      tip.querySelector("b").textContent = `${it.s.toFixed(2)} kn`;
      tip.querySelector(".meta").textContent = `${it.c.tws} kn true wind at ${Math.round(it.a)}°`;
      place(svg, tip, it.x, it.y);
    },
    hide: () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); paths.forEach(p => p.setAttribute("opacity", 1)); },
  });
}

function render() {
  const id = decodeURIComponent(location.hash.slice(1)), m = MODELS[id];
  document.getElementById("content").hidden = !m;
  pick.value = m ? id : "";
  if (!m) return;
  document.title = `${m.t}: VPP · Boat per buck`;
  document.getElementById("title").textContent = m.t;
  const ft = (m.l * 3.28084).toFixed(1);
  const sub = document.getElementById("sub");
  sub.textContent = `${m.bl} · ${m.l.toFixed(2)} m (${ft} ft) · median of ${m.c} ORC certificate${m.c === 1 ? "" : "s"} · `
    + `top speed at 15 kn true wind: ${m.s.toFixed(2)} kn · ${m.n} for sale, from `;
  const a = document.createElement("a");
  a.href = m.u; a.target = "_blank"; a.rel = "noopener";
  a.textContent = `€${m.p.toLocaleString("en")} ↗`;
  sub.appendChild(a);

  const legend = document.getElementById("legend");
  legend.replaceChildren(...m.v.speeds.map((tws, i) => {
    const s = document.createElement("span");
    s.style.setProperty("--key", `var(--tws-${i})`);
    s.textContent = `${tws} kn`;
    return s;
  }));
  drawPolar(m);

  const v = m.v, table = document.getElementById("table");
  const best = v.speeds.map((_, i) => Math.max(...v.angles.map(a => v[a][i])));
  const row = (label, vals, cls, digits = 2, bold = () => false) =>
    `<tr class="${cls}"><td>${label}</td>${vals.map((x, i) =>
      `<td class="num${bold(x, i) ? " best" : ""}">${x.toFixed(digits)}</td>`).join("")}</tr>`;
  table.innerHTML = `<thead><tr><th>True wind</th>${v.speeds.map(s => `<th class="num">${s} kn</th>`).join("")}</tr></thead><tbody>`
    + row("Beat angle", v.beat_angle, "vmg", 1) + row("Beat VMG", v.beat_vmg, "vmg")
    + v.angles.map(a => row(a + "°", v[a], "", 2, (x, i) => x === best[i])).join("")
    + row("Run angle", v.run_angle, "vmg", 1) + row("Run VMG", v.run_vmg, "vmg") + "</tbody>";
}
window.addEventListener("hashchange", render);
let lastW = 0;
window.addEventListener("resize", () => {
  const w = document.getElementById("polar").clientWidth, m = MODELS[decodeURIComponent(location.hash.slice(1))];
  if (m && w !== lastW) { lastW = w; drawPolar(m); }
});
render();
</script>
</body>
</html>
"""


def _bracket_html(label, models, n_boats, n_models):
    rows = "".join(
        f"""<tr>
<td class="rank">{i}</td>
<td class="num">{b['speed']:.2f}</td>
<td class="num">€{b['price_eur']:,}</td>
<td class="num hide-sm">{html.escape(b['year'] or '–')}</td>
<td><a href="{html.escape(b['url'])}" target="_blank" rel="noopener">{html.escape(b['title'])}</a><br><span class="orc">ORC: {html.escape(b['orc_type'])} (<a href="vpp.html#{_vpp_id(b)}" target="_blank" rel="noopener">VPP</a>){_more(b)}</span></td>
<td class="src hide-sm">{html.escape(b['source'])}</td>
</tr>"""
        for i, b in enumerate(models, 1)
    )
    return f"""<section class="card">
  <div class="bracket-head"><h2>{html.escape(label)}</h2><span class="count">{n_boats:,} boats · {n_models:,} models</span></div>
  <table>
    <thead><tr><th></th><th class="num">Knots</th><th class="num">Price</th><th class="num hide-sm">Year</th><th>Boat</th><th class="hide-sm">Site</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>"""


def _more(model):
    others = model["listings"][1:]
    if not others:
        return ""
    links = ", ".join(
        f'<a href="{html.escape(o["url"])}" target="_blank" rel="noopener">€{o["price_eur"]:,}</a>' for o in others[:4]
    )
    extra = f" and {len(others) - 4} more" if len(others) > 4 else ""
    return f" · also {links}{extra}"


def _vpp_id(model):
    """URL fragment for a model on the VPP page ("j109#0" -> "j109-0"; keys are [a-z0-9] only)."""
    return model["model_id"].replace("#", "-")


def _sqrt_fit(points):
    """Least-squares k for y = k·√x: the hull-speed form, with the data's constant instead of 1.34."""
    return sum(y * math.sqrt(x) for x, y in points) / sum(x for x, _ in points)


def _power_fit(points):
    """Least-squares fit of y = a·x^b, as a straight line in log-log space."""
    b, ln_a = statistics.linear_regression([math.log(x) for x, _ in points], [math.log(y) for _, y in points])
    return math.exp(ln_a), b


def render(path, brackets, brands, min_brand_boats, models, matched, n_listings, edges):
    """brackets: list of (label, top models, boats in bracket, models in bracket); each model carries its listings.
    brands: dicts with brand, boats, models, median price_eur and speed.
    models: every matched model, as its cheapest listing plus all its listings."""
    data = [
        {
            "t": b["title"], "s": round(b["speed"], 2), "p": b["price_eur"], "y": b["year"],
            "src": b["source"], "u": b["url"], "b": b.get("brand"), "v": _vpp_id(b),
        }
        for b in matched
    ]
    brand_data = [
        {"brand": b["brand"], "n": b["boats"], "models": b["models"], "p": b["price_eur"], "s": round(b["speed"], 2)}
        for b in brands
    ]
    model_data = [
        {"t": m["title"], "orc": m["orc_type"], "l": m["orc_loa"], "s": round(m["speed"], 2),
         "p": m["price_eur"], "n": len(m["listings"]), "u": m["url"], "b": m.get("brand"), "v": _vpp_id(m)}
        for m in models if m["orc_loa"]
    ]
    points = [(m["l"] * 3.28084, m["s"]) for m in model_data]
    fit_k, (fit_a, fit_b) = _sqrt_fit(points), _power_fit(points)
    fit_text = (
        f"forced into the hull-speed form, the data gives {fit_k:.2f}·√LOA instead of 1.34; "
        f"with a free exponent it is {fit_a:.2f}·LOA^{fit_b:.2f} (least squares over {len(points):,} models), "
        f"so {'small boats beat hull speed and big ones fall short of it' if fit_b < 0.5 else 'big boats beat hull speed more than small ones'}"
    )
    brand_rows = "".join(
        f'<tr><td>{html.escape(b["brand"])}</td><td class="num">{b["boats"]:,}</td><td class="num">{b["models"]:,}</td>'
        f'<td class="num">€{b["price_eur"]:,}</td><td class="num">{b["speed"]:.2f}</td></tr>'
        for b in brands
    )
    fastest = max(matched, key=lambda b: b["speed"])
    tiles = [
        ("Boats for sale (priced)", f"{n_listings:,}"),
        ("Matched to an ORC polar", f"{len(matched):,}"),
        ("Sites", str(len({b['source'] for b in matched}))),
        ("Fastest overall", f"{fastest['speed']:.1f} kn"),
    ]
    sources = ", ".join(f"{s} ({n:,})" for s, n in Counter(b["source"] for b in matched).most_common())
    page = (
        PAGE.replace("__STYLE__", STYLE).replace("__HELPERS__", HELPERS)
        .replace("__DATE__", datetime.date.today().isoformat())
        .replace("__FIT__", html.escape(fit_text))
        .replace("__FIT_JSON__", json.dumps({"k": round(fit_k, 4), "a": round(fit_a, 4), "b": round(fit_b, 4)}))
        .replace("__TILES__", "".join(
            f'<div class="tile"><div class="label">{l}</div><div class="value">{v}</div></div>' for l, v in tiles
        ))
        .replace("__MIN_BRAND__", str(min_brand_boats))
        .replace("__BRAND_ROWS__", brand_rows)
        .replace("__MODELS__", json.dumps(model_data).replace("</", "<\\/"))
        .replace("__BRANDS__", json.dumps(brand_data).replace("</", "<\\/"))
        .replace("__BRACKETS__", "\n".join(_bracket_html(*b) for b in brackets))
        .replace("__SOURCES__", html.escape(sources))
        .replace("__EDGES__", json.dumps([e for e in edges if e != float("inf")]))
        .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    )
    path.write_text(page)
    print(f"wrote {path}")


def render_vpp(path, models, vpps):
    """One page with every matched model's VPP table, shown by the URL fragment (vpp.html#j109-0).
    models: every matched model, as from render(); vpps: model_id -> median VPP table (data/vpp.json)."""
    data = {
        _vpp_id(m): {
            "t": m["orc_type"], "bl": m["builder"], "l": m["orc_loa"], "s": round(m["speed"], 2), "c": m["n_certs"],
            "n": len(m["listings"]), "p": m["price_eur"], "u": m["url"], "v": vpps[m["model_id"]],
        }
        for m in models if m["orc_loa"] and m["model_id"] in vpps
    }
    page = (
        VPP_PAGE.replace("__STYLE__", STYLE).replace("__HELPERS__", HELPERS)
        .replace("__DATE__", datetime.date.today().isoformat())
        .replace("__VPP__", json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))
    )
    path.write_text(page)
    print(f"wrote {path}")
