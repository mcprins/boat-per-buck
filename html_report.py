"""Render the bracket results as a standalone HTML page (no external assets)."""

import datetime
import html
import json
from collections import Counter

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Boat per buck: fastest sailboats per price bracket</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e;
  --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --other: #c3c2b7; --row-hover: #f0efec;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0d0d0d; --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --other: #52514e; --row-hover: #262624;
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
.legend { display: flex; gap: 20px; color: var(--text-secondary); font-size: 13px; margin: 4px 0 8px; }
.legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  margin-right: 6px; vertical-align: -1px; background: var(--key); }
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
.picker { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 12px; }
.chip, .picker select { font: inherit; font-size: 13px; color: var(--text-secondary); background: transparent;
  border: 1px solid var(--border); border-radius: 999px; padding: 3px 10px; cursor: pointer; }
.chip:hover { background: var(--row-hover); }
.chip[aria-pressed="true"] { color: var(--text-primary); border-color: var(--axis); background: var(--row-hover); }
.chip[aria-pressed="true"]::before { content: ""; display: inline-block; width: 10px; height: 3px; border-radius: 2px;
  margin-right: 6px; vertical-align: 3px; background: var(--key); }
.chart .line-label { fill: var(--text-primary); font-weight: 600; paint-order: stroke;
  stroke: var(--surface-1); stroke-width: 4px; stroke-linejoin: round; }
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
@media (max-width: 640px) { .hide-sm { display: none; } }
</style>
</head>
<body>
<main>
  <h1>Fastest sailboat models per price bracket</h1>
  <p class="sub">Predicted top speed at 15 kts true wind (ORC VPP, best angle) for boats currently for sale. Generated __DATE__.</p>

  <div class="tiles">__TILES__</div>

  <section class="card">
    <h2>Speed vs. asking price</h2>
    <div class="legend"><span style="--key: var(--series-1)">Top __TOP_N__ models in bracket</span><span style="--key: var(--other)">Other matched boats</span></div>
    <div id="chart" class="chart"><div id="tip" class="tip"></div></div>
  </section>

  <section class="card">
    <h2>Speed vs. length</h2>
    <p class="note">One dot per boat model for sale (length overall from its ORC certificates); click a dot to open its cheapest listing.
      The dashed curve is the classic displacement hull speed, 1.34·√LOA (ft), treating length overall as waterline length.</p>
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

  <section class="card">
    <h2>Brands: price range and speed range</h2>
    <p class="note">One line per brand, from its cheapest to its dearest boats (5th–95th percentile of asking price), following
      the least-squares trend of speed against price. A steep line means paying more buys a lot more speed within that brand.
      Pick up to three brands to colour them and show their boats as dots; click a grey line to pick that brand.</p>
    <div id="range-picker" class="picker" role="group" aria-label="Brands to highlight"></div>
    <div id="range-chart" class="chart"><div id="range-tip" class="tip"></div></div>
    <details>
      <summary>Show as table</summary>
      <table>
        <thead><tr><th>Brand</th><th class="num">Boats</th><th class="num">Price range</th><th class="num">Knots range</th><th class="num hide-sm">Trend line</th></tr></thead>
        <tbody>__RANGE_ROWS__</tbody>
      </table>
    </details>
  </section>

  __BRACKETS__

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

const fmt = v => v >= 1e6 ? "€" + (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + "M" : v >= 1e3 ? "€" + Math.round(v / 1e3) + "K" : "€" + v;
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent.appendChild(e);
  return e;
};

(function () {
  const root = document.getElementById("chart");
  const tip = document.getElementById("tip");
  const W = 1000, H = 440, m = { t: 28, r: 16, b: 40, l: 44 };
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

  // other boats first, highlighted on top
  const sorted = [...BOATS].sort((a, b) => a.top - b.top);
  sorted.forEach(b => {
    b.cx = x(b.p); b.cy = y(b.s);
    el("circle", b.top
      ? { cx: b.cx, cy: b.cy, r: 4.5, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 2 }
      : { cx: b.cx, cy: b.cy, r: 2.5, fill: "var(--other)" }, svg);
  });
  const ring = el("circle", { r: 7, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  // hover: nearest boat within 14 viewBox px, highlighted boats preferred
  let current = null;
  const nearest = (px, py) => {
    let best = null, bd = 14 * 14;
    for (const b of sorted) {
      const d = (b.cx - px) ** 2 + (b.cy - py) ** 2 - (b.top ? 40 : 0);
      if (d < bd) { bd = d; best = b; }
    }
    return best;
  };
  svg.addEventListener("mousemove", ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width;
    const b = nearest((ev.clientX - r.left) * k, (ev.clientY - r.top) * k);
    current = b;
    if (!b) { tip.style.opacity = 0; ring.setAttribute("opacity", 0); svg.style.cursor = ""; return; }
    ring.setAttribute("cx", b.cx); ring.setAttribute("cy", b.cy); ring.setAttribute("opacity", 1);
    svg.style.cursor = "pointer";
    tip.innerHTML = `<b></b><div class="meta"></div>`;
    tip.querySelector("b").textContent = b.t;
    tip.querySelector(".meta").textContent =
      `${b.s.toFixed(2)} kn · €${b.p.toLocaleString("en")}${b.y ? " · " + b.y : ""} · ${b.src}`;
    const tx = b.cx / k, ty = b.cy / k;
    tip.style.left = Math.min(tx + 14, r.width - tip.offsetWidth - 4) + "px";
    tip.style.top = (ty - tip.offsetHeight - 10 < 0 ? ty + 14 : ty - tip.offsetHeight - 10) + "px";
    tip.style.opacity = 1;
  });
  svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); current = null; });
  svg.addEventListener("click", () => { if (current) window.open(current.u, "_blank", "noopener"); });
})();

(function () {
  const root = document.getElementById("length-chart");
  const tip = document.getElementById("length-tip");
  const W = 1000, H = 480, m = { t: 28, r: 16, b: 40, l: 44 };
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
  for (let l = Math.ceil(xmin / 5) * 5; l <= xmax; l += 5) {
    el("line", { x1: x(l), x2: x(l), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    el("text", { x: x(l), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = l + (l === xmax - xmax % 5 ? " ft" : "");
  }

  const hull = ft => 1.34 * Math.sqrt(ft);
  let d = "";
  for (let l = xmin; l <= xmax; l += 1) {
    if (hull(l) > ymax) break;
    d += (d ? "L" : "M") + x(l).toFixed(1) + "," + y(hull(l)).toFixed(1);
  }
  el("path", { d, fill: "none", stroke: "var(--text-secondary)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }, svg);
  // label below the curve, which rises away from it to the right
  el("text", { x: x(xmax - 20), y: y(hull(xmax - 20)) + 20, "text-anchor": "start", class: "brand-label" }, svg).textContent = "hull speed";

  MODELS.forEach(b => {
    b.cx = x(b.ft); b.cy = y(b.s);
    el("circle", { cx: b.cx, cy: b.cy, r: 3.5, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 1 }, svg);
  });
  const ring = el("circle", { r: 7, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  let current = null;
  svg.addEventListener("mousemove", ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width;
    const px = (ev.clientX - r.left) * k, py = (ev.clientY - r.top) * k;
    let best = null, bd = 12 * 12;
    for (const b of MODELS) {
      const dd = (b.cx - px) ** 2 + (b.cy - py) ** 2;
      if (dd < bd) { bd = dd; best = b; }
    }
    current = best;
    if (!best) { tip.style.opacity = 0; ring.setAttribute("opacity", 0); svg.style.cursor = ""; return; }
    ring.setAttribute("cx", best.cx); ring.setAttribute("cy", best.cy); ring.setAttribute("opacity", 1);
    svg.style.cursor = "pointer";
    tip.innerHTML = `<b></b><div class="meta"></div><div class="meta"></div>`;
    tip.querySelector("b").textContent = best.t;
    const metas = tip.querySelectorAll(".meta");
    metas[0].textContent = `${best.s.toFixed(2)} kn · ${best.ft.toFixed(1)} ft (${best.l.toFixed(2)} m) · ORC: ${best.orc}`;
    metas[1].textContent = `${best.n} for sale, from €${best.p.toLocaleString("en")}`;
    const tx = best.cx / k, ty = best.cy / k;
    tip.style.left = Math.min(tx + 14, r.width - tip.offsetWidth - 4) + "px";
    tip.style.top = (ty - tip.offsetHeight - 10 < 0 ? ty + 14 : ty - tip.offsetHeight - 10) + "px";
    tip.style.opacity = 1;
  });
  svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); current = null; });
  svg.addEventListener("click", () => { if (current) window.open(current.u, "_blank", "noopener"); });
})();

(function () {
  const root = document.getElementById("brand-chart");
  const tip = document.getElementById("brand-tip");
  const W = 1000, H = 520, m = { t: 28, r: 24, b: 40, l: 44 };
  const xmin = Math.log10(Math.min(...BRANDS.map(b => b.p)) / 1.4);
  const xmax = Math.log10(Math.max(...BRANDS.map(b => b.p)) * 1.4);
  const ymin = Math.floor(Math.min(...BRANDS.map(b => b.s)) - 0.25);
  const ymax = Math.ceil(Math.max(...BRANDS.map(b => b.s)) + 0.25);
  const x = p => m.l + (Math.log10(p) - xmin) / (xmax - xmin) * (W - m.l - m.r);
  const y = s => H - m.b - (s - ymin) / (ymax - ymin) * (H - m.t - m.b);
  const maxN = Math.max(...BRANDS.map(b => b.n));
  const rad = n => 4 + 12 * Math.sqrt(n / maxN);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Scatter plot of each brand's median speed against median asking price; the table below lists the same brands." }, root);

  for (let s = ymin; s <= ymax; s += 0.5) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s), stroke: "var(--grid)" }, svg);
    if (s % 1 === 0) el("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" }, svg).textContent = s;
  }
  el("text", { x: m.l - 8, y: m.t - 12, "text-anchor": "end" }, svg).textContent = "knots";
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)" }, svg);
  [2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6].forEach(v => {
    const lv = Math.log10(v);
    if (lv < xmin || lv > xmax) return;
    el("line", { x1: x(v), x2: x(v), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    el("text", { x: x(v), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = fmt(v);
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

  // hover: the smallest dot under the pointer (or within 6 px of its edge)
  svg.addEventListener("mousemove", ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width;
    const px = (ev.clientX - r.left) * k, py = (ev.clientY - r.top) * k;
    let best = null;
    for (const b of dots) {
      if (Math.hypot(b.cx - px, b.cy - py) <= b.r + 6 && (!best || b.r < best.r)) best = b;
    }
    if (!best) { tip.style.opacity = 0; ring.setAttribute("opacity", 0); return; }
    ring.setAttribute("cx", best.cx); ring.setAttribute("cy", best.cy); ring.setAttribute("r", best.r + 3);
    ring.setAttribute("opacity", 1);
    tip.innerHTML = `<b></b><div class="meta"></div><div class="meta"></div>`;
    tip.querySelector("b").textContent = best.brand;
    const metas = tip.querySelectorAll(".meta");
    metas[0].textContent = `${best.s.toFixed(2)} kn · €${best.p.toLocaleString("en")} (medians)`;
    metas[1].textContent = `${best.n} boats · ${best.models} models`;
    const tx = best.cx / k, ty = (best.cy - best.r) / k;
    tip.style.left = Math.min(tx + 14, r.width - tip.offsetWidth - 4) + "px";
    tip.style.top = (ty - tip.offsetHeight - 8 < 0 ? (best.cy + best.r) / k + 8 : ty - tip.offsetHeight - 8) + "px";
    tip.style.opacity = 1;
  });
  svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); });
})();

(function () {
  const root = document.getElementById("range-chart");
  const tip = document.getElementById("range-tip");
  const picker = document.getElementById("range-picker");
  const W = 1000, H = 520, m = { t: 28, r: 16, b: 40, l: 44 };
  const SLOTS = [1, 2, 3];  // the palette's first three hues stay distinguishable when lines and dots overlap
  const CHIPS = 16;  // most-listed brands get a chip; the rest are in the dropdown
  const byBrand = new Map(BRANDS.map(b => [b.brand, { ...b, boats: [] }]));
  BOATS.forEach(d => byBrand.get(d.b)?.boats.push(d));
  const brands = [...byBrand.values()];
  const all = brands.flatMap(b => b.boats);
  const xmin = Math.log10(Math.min(...all.map(d => d.p)) * 0.9), xmax = Math.log10(Math.max(...all.map(d => d.p)) * 1.1);
  const ymin = Math.floor(Math.min(...all.map(d => d.s))) - 0.5, ymax = Math.ceil(Math.max(...all.map(d => d.s))) + 0.5;
  const x = p => m.l + (Math.log10(p) - xmin) / (xmax - xmin) * (W - m.l - m.r);
  const y = s => H - m.b - (s - ymin) / (ymax - ymin) * (H - m.t - m.b);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "One trend line per brand of predicted speed against asking price; the table below lists each brand's ranges." }, root);

  for (let s = Math.ceil(ymin); s <= ymax; s++) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(s), y2: y(s), stroke: "var(--grid)" }, svg);
    el("text", { x: m.l - 8, y: y(s) + 4, "text-anchor": "end" }, svg).textContent = s;
  }
  el("text", { x: m.l - 8, y: m.t - 12, "text-anchor": "end" }, svg).textContent = "knots";
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)" }, svg);
  [1e3, 2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6].forEach(v => {
    const lv = Math.log10(v);
    if (lv < xmin || lv > xmax) return;
    el("line", { x1: x(v), x2: x(v), y1: m.t - 8, y2: H - m.b, stroke: "var(--grid)" }, svg);
    el("text", { x: x(v), y: H - m.b + 20, "text-anchor": "middle" }, svg).textContent = fmt(v);
  });

  brands.forEach(b => { b.x1 = x(b.line[0]); b.y1 = y(b.line[1]); b.x2 = x(b.line[2]); b.y2 = y(b.line[3]); });
  const base = el("g", {}, svg);
  brands.forEach(b => el("line", { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2,
    stroke: "var(--other)", "stroke-width": 2, "stroke-linecap": "round" }, base));
  const selLayer = el("g", {}, svg);
  const hoverLine = el("line", { stroke: "var(--text-primary)", "stroke-width": 2.5, "stroke-linecap": "round", opacity: 0 }, svg);
  const labelLayer = el("g", {}, svg);
  const ring = el("circle", { r: 7, fill: "none", stroke: "var(--text-primary)", "stroke-width": 1.5, opacity: 0 }, svg);

  // a brand keeps its colour while it stays selected; a fourth pick replaces the oldest
  let sel = ["Beneteau", "Hallberg-Rassy", "Nautor's Swan"].filter(n => byBrand.has(n));
  if (!sel.length) sel = brands.slice(0, 3).map(b => b.brand);
  sel = sel.map((name, i) => ({ name, slot: SLOTS[i] }));
  const toggle = name => {
    const i = sel.findIndex(s => s.name === name);
    if (i >= 0) sel.splice(i, 1);
    else {
      if (sel.length === SLOTS.length) sel.shift();
      sel.push({ name, slot: SLOTS.find(k => !sel.some(s => s.slot === k)) });
    }
    draw();
  };

  let dots = [];
  function draw() {
    selLayer.replaceChildren();
    labelLayer.replaceChildren();
    dots = [];
    sel.forEach(({ name, slot }) => byBrand.get(name).boats.forEach(d => {
      const dot = { d, brand: name, cx: x(d.p), cy: y(d.s) };
      dots.push(dot);
      el("circle", { cx: dot.cx, cy: dot.cy, r: 3.5, fill: `var(--series-${slot})`, stroke: "var(--surface-1)", "stroke-width": 1 }, selLayer);
    }));
    // lines over every selected brand's dots, each on a surface halo
    sel.forEach(({ name, slot }) => {
      const b = byBrand.get(name), a = { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2, "stroke-linecap": "round" };
      el("line", { ...a, stroke: "var(--surface-1)", "stroke-width": 7 }, selLayer);
      el("line", { ...a, stroke: `var(--series-${slot})`, "stroke-width": 3 }, selLayer);
    });
    // direct label past the line's dearer end; above it when that would run off the plot; nudged down off other labels
    const boxes = [];
    sel.forEach(({ name }) => {
      const b = byBrand.get(name), w = name.length * 7.4;
      let [lx, ly, anchor] = b.x2 + 8 + w <= W - m.r ? [b.x2 + 8, b.y2 + 4, "start"] : [b.x2, b.y2 - 10, "end"];
      const x0 = anchor === "start" ? lx : lx - w;
      for (let i = 0; i < 6 && boxes.some(o => x0 < o[2] && x0 + w > o[0] && ly - 11 < o[3] && ly + 3 > o[1]); i++) ly += 14;
      boxes.push([x0, ly - 11, x0 + w, ly + 3]);
      el("text", { x: lx, y: ly, "text-anchor": anchor, class: "line-label" }, labelLayer).textContent = name;
    });

    picker.replaceChildren();
    const shown = brands.slice(0, CHIPS).map(b => b.brand);
    sel.forEach(s => { if (!shown.includes(s.name)) shown.push(s.name); });
    shown.forEach(name => {
      const s = sel.find(s => s.name === name), btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.textContent = name;
      btn.setAttribute("aria-pressed", s ? "true" : "false");
      if (s) btn.style.setProperty("--key", `var(--series-${s.slot})`);
      btn.addEventListener("click", () => toggle(name));
      picker.appendChild(btn);
    });
    const more = brands.filter(b => !shown.includes(b.brand));
    if (more.length) {
      const select = document.createElement("select");
      select.setAttribute("aria-label", "More brands");
      [{ brand: `More brands (${more.length})…`, n: 0 }, ...more].forEach((b, i) => {
        const o = document.createElement("option");
        o.value = i ? b.brand : "";
        o.textContent = i ? `${b.brand} (${b.n})` : b.brand;
        select.appendChild(o);
      });
      select.addEventListener("change", () => { if (select.value) toggle(select.value); });
      picker.appendChild(select);
    }
  }
  draw();

  const segDist = (b, px, py) => {
    const dx = b.x2 - b.x1, dy = b.y2 - b.y1, len2 = dx * dx + dy * dy;
    const t = len2 ? Math.max(0, Math.min(1, ((px - b.x1) * dx + (py - b.y1) * dy) / len2)) : 0;
    return Math.hypot(b.x1 + t * dx - px, b.y1 + t * dy - py);
  };
  const hide = () => { tip.style.opacity = 0; ring.setAttribute("opacity", 0); hoverLine.setAttribute("opacity", 0); svg.style.cursor = ""; };
  const place = (r, k, tx, ty) => {
    tip.style.left = Math.min(tx / k + 14, r.width - tip.offsetWidth - 4) + "px";
    tip.style.top = (ty / k - tip.offsetHeight - 10 < 0 ? ty / k + 14 : ty / k - tip.offsetHeight - 10) + "px";
    tip.style.opacity = 1;
  };

  // hover: a selected brand's boat within 10 px wins, else the nearest line within 8 px (selected lines favoured)
  let current = null;
  svg.addEventListener("mousemove", ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width;
    const px = (ev.clientX - r.left) * k, py = (ev.clientY - r.top) * k;
    let dot = null, dd = 10, line = null, ld = 8;
    for (const o of dots) { const q = Math.hypot(o.cx - px, o.cy - py); if (q < dd) { dd = q; dot = o; } }
    if (!dot) for (const b of brands) {
      const q = segDist(b, px, py) - (sel.some(s => s.name === b.brand) ? 3 : 0);
      if (q < ld) { ld = q; line = b; }
    }
    current = dot || line;
    if (!current) return hide();
    svg.style.cursor = "pointer";
    tip.innerHTML = `<b></b><div class="meta"></div><div class="meta"></div>`;
    const metas = tip.querySelectorAll(".meta");
    if (dot) {
      hoverLine.setAttribute("opacity", 0);
      ring.setAttribute("cx", dot.cx); ring.setAttribute("cy", dot.cy); ring.setAttribute("opacity", 1);
      tip.querySelector("b").textContent = dot.d.t;
      metas[0].textContent = `${dot.d.s.toFixed(2)} kn · €${dot.d.p.toLocaleString("en")}${dot.d.y ? " · " + dot.d.y : ""} · ${dot.d.src}`;
      metas[1].textContent = dot.brand;
      place(r, k, dot.cx, dot.cy);
    } else {
      ring.setAttribute("opacity", 0);
      for (const a of ["x1", "y1", "x2", "y2"]) hoverLine.setAttribute(a, line[a]);
      hoverLine.setAttribute("opacity", 1);
      const picked = sel.some(s => s.name === line.brand);
      tip.querySelector("b").textContent = line.brand;
      metas[0].textContent = `€${line.pr[0].toLocaleString("en")} – €${line.pr[1].toLocaleString("en")} · ${line.sr[0].toFixed(1)}–${line.sr[1].toFixed(1)} kn`;
      metas[1].textContent = `${line.n} boats · ${line.models} models · click to ${picked ? "hide" : "show"} its boats`;
      place(r, k, px, py);
    }
  });
  svg.addEventListener("mouseleave", () => { hide(); current = null; });
  svg.addEventListener("click", () => {
    if (!current) return;
    if (current.d) window.open(current.d.u, "_blank", "noopener");
    else { toggle(current.brand); hide(); current = null; }
  });
})();
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
<td><a href="{html.escape(b['url'])}" target="_blank" rel="noopener">{html.escape(b['title'])}</a><br><span class="orc">ORC: {html.escape(b['orc_type'])}{_more(b)}</span></td>
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


def render(path, brackets, brands, min_brand_boats, models, matched, n_listings, edges, top_n):
    """brackets: list of (label, top models, boats in bracket, models in bracket); each model carries its listings.
    brands: dicts with brand, boats, models, median price_eur and speed.
    models: every matched model, as its cheapest listing plus all its listings."""
    top_ids = {(b["source"], b["id"]) for _, top, _, _ in brackets for m in top for b in m["listings"]}
    data = [
        {
            "t": b["title"], "s": round(b["speed"], 2), "p": b["price_eur"], "y": b["year"],
            "src": b["source"], "u": b["url"], "top": (b["source"], b["id"]) in top_ids, "b": b.get("brand"),
        }
        for b in matched
    ]
    brand_data = [
        {"brand": b["brand"], "n": b["boats"], "models": b["models"], "p": b["price_eur"], "s": round(b["speed"], 2),
         "pr": b["price_range"], "sr": b["speed_range"], "line": b["trend"]}
        for b in brands
    ]
    model_data = [
        {"t": m["title"], "orc": m["orc_type"], "l": m["orc_loa"], "s": round(m["speed"], 2),
         "p": m["price_eur"], "n": len(m["listings"]), "u": m["url"]}
        for m in models if m["orc_loa"]
    ]
    brand_rows = "".join(
        f'<tr><td>{html.escape(b["brand"])}</td><td class="num">{b["boats"]:,}</td><td class="num">{b["models"]:,}</td>'
        f'<td class="num">€{b["price_eur"]:,}</td><td class="num">{b["speed"]:.2f}</td></tr>'
        for b in brands
    )
    range_rows = "".join(
        f'<tr><td>{html.escape(b["brand"])}</td><td class="num">{b["boats"]:,}</td>'
        f'<td class="num">€{b["price_range"][0]:,} – €{b["price_range"][1]:,}</td>'
        f'<td class="num">{b["speed_range"][0]:.1f} – {b["speed_range"][1]:.1f}</td>'
        f'<td class="num hide-sm">{b["trend"][1]:.1f} kn at €{b["trend"][0]:,} → {b["trend"][3]:.1f} kn at €{b["trend"][2]:,}</td></tr>'
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
        PAGE.replace("__DATE__", datetime.date.today().isoformat())
        .replace("__TILES__", "".join(
            f'<div class="tile"><div class="label">{l}</div><div class="value">{v}</div></div>' for l, v in tiles
        ))
        .replace("__TOP_N__", str(top_n))
        .replace("__MIN_BRAND__", str(min_brand_boats))
        .replace("__BRAND_ROWS__", brand_rows)
        .replace("__RANGE_ROWS__", range_rows)
        .replace("__MODELS__", json.dumps(model_data).replace("</", "<\\/"))
        .replace("__BRANDS__", json.dumps(brand_data).replace("</", "<\\/"))
        .replace("__BRACKETS__", "\n".join(_bracket_html(*b) for b in brackets))
        .replace("__SOURCES__", html.escape(sources))
        .replace("__EDGES__", json.dumps([e for e in edges if e != float("inf")]))
        .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    )
    path.write_text(page)
    print(f"wrote {path}")
