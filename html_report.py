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
.tip .open { pointer-events: auto; display: inline-block; margin-top: 6px; padding: 4px 0; font-weight: 600;
  color: var(--series-1); text-decoration: none; }
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
</style>
</head>
<body>
<main>
  <h1>Fastest sailboat models per price bracket</h1>
  <p class="sub">Predicted top speed at 15 kts true wind (ORC VPP, best angle) for boats currently for sale. Generated __DATE__.</p>

  <section class="card">
    <h2>Speed vs. asking price</h2>
    <p class="note">One dot per boat for sale; click a dot (tap twice on a phone) to open its listing.
      Pick brands to grey out the rest, so only the picked brands' boats can be clicked; the first three picks get their own colour, later picks share dark grey.</p>
    <div id="price-picker" class="picker" role="group" aria-label="Brands to show"></div>
    <div id="chart" class="chart"><div id="tip" class="tip"></div></div>
  </section>

  <section class="card">
    <h2>Speed vs. length</h2>
    <p class="note">One dot per boat model for sale (length overall from its ORC certificates); click a dot (tap twice on a phone) to open its cheapest listing.
      The dashed curve is the classic displacement hull speed, 1.34·√LOA (ft), treating length overall as waterline length.</p>
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

const fmt = v => v >= 1e6 ? "€" + (v / 1e6).toFixed(v % 1e6 ? 1 : 0) + "M" : v >= 1e3 ? "€" + Math.round(v / 1e3) + "K" : "€" + v;
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
// tooltip above the item (r: its radius), or below it near the top edge; on touch, with a link to the listing
const place = (svg, tip, cx, cy, r = 0) => {
  if (tip.dataset.link) {
    const a = document.createElement("a");
    a.className = "open"; a.href = tip.dataset.link; a.target = "_blank"; a.rel = "noopener";
    a.textContent = "Open listing ↗";
    tip.appendChild(a);
  }
  const rect = svg.getBoundingClientRect(), k = svg.viewBox.baseVal.width / rect.width;
  const tx = cx / k, top = (cy - r) / k - tip.offsetHeight - 10;
  tip.style.left = Math.max(4, Math.min(tx + 14, rect.width - tip.offsetWidth - 4)) + "px";
  tip.style.top = (top < 0 ? (cy + r) / k + 14 : top) + "px";
  tip.style.opacity = 1;
};
// With a mouse: hover shows the tooltip, click opens the listing (url) or runs the action.
// Touch has no hover, so the first tap shows the tooltip (with an "Open listing" link) and a second tap on the same item opens it.
let pointerType = "mouse";
function interact(svg, tip, { hit, show, hide, url, action }) {
  let pinned = null;
  const point = ev => {
    const r = svg.getBoundingClientRect(), k = svg.viewBox.baseVal.width / r.width;
    return [(ev.clientX - r.left) * k, (ev.clientY - r.top) * k];
  };
  const clear = () => { hide(); tip.querySelector(".open")?.remove(); pinned = null; svg.style.cursor = ""; };
  svg.addEventListener("pointerdown", ev => { pointerType = ev.pointerType; });
  svg.addEventListener("pointermove", ev => {
    if (ev.pointerType !== "mouse") return;
    const item = hit(...point(ev), 1);
    if (!item) return clear();
    delete tip.dataset.link;
    show(item, false);
    svg.style.cursor = url?.(item) || action ? "pointer" : "";
  });
  svg.addEventListener("pointerleave", ev => { if (ev.pointerType === "mouse") clear(); });
  svg.addEventListener("click", ev => {
    const touch = pointerType !== "mouse";
    const item = hit(...point(ev), touch ? 2 : 1);  // fingers are less precise: twice the reach
    if (!item) return clear();
    if (touch && item !== pinned) {
      pinned = item;
      if (url?.(item)) tip.dataset.link = url(item); else delete tip.dataset.link;
      show(item, true);
      return;
    }
    if (url?.(item)) window.open(url(item), "_blank", "noopener");
    else if (action) { action(item); clear(); }
  });
  document.addEventListener("click", ev => {
    if (pinned && !svg.contains(ev.target) && !tip.contains(ev.target)) clear();
  });
}

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
    url: b => b.u,
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
  // label below the curve, which rises away from it to the right
  el("text", { x: x(xmax - 20), y: y(hull(xmax - 20)) + 20, "text-anchor": "start", class: "brand-label" }, svg).textContent = "hull speed";

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
    url: b => b.u,
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


def render(path, brackets, brands, min_brand_boats, models, matched, n_listings, edges):
    """brackets: list of (label, top models, boats in bracket, models in bracket); each model carries its listings.
    brands: dicts with brand, boats, models, median price_eur and speed.
    models: every matched model, as its cheapest listing plus all its listings."""
    data = [
        {
            "t": b["title"], "s": round(b["speed"], 2), "p": b["price_eur"], "y": b["year"],
            "src": b["source"], "u": b["url"], "b": b.get("brand"),
        }
        for b in matched
    ]
    brand_data = [
        {"brand": b["brand"], "n": b["boats"], "models": b["models"], "p": b["price_eur"], "s": round(b["speed"], 2)}
        for b in brands
    ]
    model_data = [
        {"t": m["title"], "orc": m["orc_type"], "l": m["orc_loa"], "s": round(m["speed"], 2),
         "p": m["price_eur"], "n": len(m["listings"]), "u": m["url"], "b": m.get("brand")}
        for m in models if m["orc_loa"]
    ]
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
        PAGE.replace("__DATE__", datetime.date.today().isoformat())
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
