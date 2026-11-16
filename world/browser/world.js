// world.js · the page. Runs engine.mjs in the browser. Nothing is fetched
// and nothing is sent anywhere; the settings live in the address, after #.
//
// Terms: Zero-Clause BSD (LICENSE-0BSD).

import { World, resolveParams, SPEC_VERSION, CODE_VERSION } from './engine.mjs';

// The two settings the page uses, copied from ../test-values.json as data.
// check.mjs fails if this copy and that file ever differ.
/* SETTINGS-BEGIN */
const SETTINGS = {
 "page_charger": {
  "name": "The page's charger",
  "operators": ["A", "B"],
  "topology": "pair",
  "E0": 100, "b": 12, "a": 0, "schedule": "both",
  "g": 1, "m": 10, "c": 4, "lam": 0, "eps": 0, "k": 0,
  "E_r": 0, "E_max": null,
  "round": 1, "dt": 0.001,
  "s": 0, "u_max": null, "sigma_s": 0, "sigma_r": 0, "w": 5
 },
 "network": {
  "name": "AP02's network",
  "N": 20,
  "topology": "ring",
  "E0": 50, "b": 0, "a": 0.1, "schedule": "always",
  "g": "m/(2*lam)", "m": 3, "c": 0, "lam": 1, "eps": 0.01, "k": 0,
  "E_r": 10, "E_max": null,
  "round": 1, "dt": 0.01,
  "s": 0, "u_max": 6, "sigma_s": 0, "sigma_r": 0, "w": 5
 }
};
/* SETTINGS-END */

const NET = SETTINGS.network, CH = SETTINGS.page_charger;
const HORIZON = 200;          // rounds the world runs on the page
const HISTORY = 40;           // rounds a corridor shows
const SAMPLES_PER_ROUND = 4;

const $ = (s, el = document) => el.querySelector(s);
const SVGNS = 'http://www.w3.org/2000/svg';
function el(tag, attrs = {}, parent = null, text = null) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== null) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}
function html(tag, cls = '', text = null) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== null) e.textContent = text;
  return e;
}
const f2 = x => (x === null || x === undefined || !Number.isFinite(x) ? 'none' : x.toFixed(2));
// Hours and whole minutes, the minutes cut down, not rounded: the page
// gives 13.541667 hours as "thirteen hours and thirty-two minutes".
function hm(h) {
  if (!Number.isFinite(h)) return '';
  const mins = Math.floor(h * 60 + 1e-6);
  return `${Math.floor(mins / 60)} h ${mins % 60} min`;
}

// ---------------------------------------------------------------------------
// Settings in the address. Only settings go there.

const LIMITS = {
  ops: [3, 12, 1], give: [0, 6, 0.05], cost: [0.2, 3, 0.05], drift: [0, 0.5, 0.01],
  mult: [0, 8, 0.1], noise: [0, 5, 0.1], seed: [1, 999999, 1], cmult: [2, 14, 0.1],
};
const DEFAULTS = {
  ops: 6, types: 'CCCCCC', give: 'auto', cost: NET.lam, drift: NET.a, mult: NET.m,
  noise: NET.sigma_s, seed: 1, cmult: CH.m,
};
const decimals = st => (String(st).split('.')[1] || '').length;
function snap(key, v) {
  const [lo, hi, st] = LIMITS[key];
  const x = Math.min(hi, Math.max(lo, lo + Math.round((v - lo) / st) * st));
  return Number(x.toFixed(decimals(st)));
}
const show = (key, v) => v.toFixed(decimals(LIMITS[key][2]));

function readHash() {
  const h = new URLSearchParams(location.hash.replace(/^#/, ''));
  const s = { ...DEFAULTS };
  for (const k of ['ops', 'cost', 'drift', 'mult', 'noise', 'seed', 'cmult']) {
    if (!h.has(k)) continue;
    const v = Number(h.get(k));
    if (Number.isFinite(v)) s[k] = snap(k, v);
  }
  if (h.has('give') && h.get('give') !== 'auto') {
    const v = Number(h.get('give'));
    if (Number.isFinite(v)) s.give = snap('give', v);
  }
  const t = (h.get('types') || '').toUpperCase().replace(/[^CUD]/g, '');
  s.types = (t + 'C'.repeat(s.ops)).slice(0, s.ops);
  return s;
}
function hashOf(s) {
  return '#' + [
    `ops=${s.ops}`, `types=${s.types}`,
    `give=${s.give === 'auto' ? 'auto' : show('give', s.give)}`,
    `cost=${show('cost', s.cost)}`, `drift=${show('drift', s.drift)}`,
    `mult=${show('mult', s.mult)}`, `noise=${show('noise', s.noise)}`,
    `seed=${s.seed}`, `cmult=${show('cmult', s.cmult)}`,
  ].join('&');
}
function writeHash() {
  const h = hashOf(state);
  if (location.hash !== h) history.replaceState(null, '', h);
}

let state = readHash();

// ---------------------------------------------------------------------------
// The world: operators on a ring.

let world = null, samples = [], Escale = 100;
let playing = false, raf = 0, lastTs = 0, carry = 0, speed = 5, lastPanel = 0;
let geo = null;

function worldParams() {
  return resolveParams(NET, {
    N: state.ops, topology: 'ring',
    g: state.give === 'auto' ? NET.g : state.give,
    lam: state.cost, a: state.drift, m: state.mult,
    sigma_s: state.noise, sigma_r: state.noise,
  });
}

function newWorld() {
  const types = {};
  [...state.types].forEach((t, i) => { types[String(i + 1)] = t; });
  world = new World(worldParams(), { types, seed: state.seed });
  samples = [];
  pushSample();
  Escale = Math.max(100, world.p.E0 * 2);
  carry = 0;
  buildRing();
  buildOpsTable();
  draw(true);
}

function pushSample() {
  samples.push({
    t: world.time(),
    E: Float64Array.from(world.ops, o => o.E),
    alive: world.ops.map(o => o.alive),
  });
  while (samples.length > 2 && world.time() - samples[0].t > HISTORY + 1) samples.shift();
}

const finished = () => world.time() >= HORIZON - 1e-9 || world.allRuined();

function tick(ts) {
  raf = 0;
  if (!playing) return;
  const elapsed = lastTs ? Math.min(0.1, (ts - lastTs) / 1000) : 0;
  lastTs = ts;
  carry += elapsed * speed * world.nsub;
  let n = Math.floor(carry);
  carry -= n;
  const every = Math.max(1, Math.round(world.nsub / SAMPLES_PER_ROUND));
  while (n-- > 0 && !finished()) {
    world.step();
    if (world.j % every === 0) pushSample();
  }
  draw();
  if (finished()) { setPlaying(false); return; }
  raf = requestAnimationFrame(tick);
}

function setPlaying(on) {
  playing = on && !finished();
  const b = $('#play');
  b.textContent = playing ? 'Pause' : finished() ? 'Run again' : 'Play';   // the label names what it does now
  if (playing && !raf) { lastTs = 0; raf = requestAnimationFrame(tick); }
}

// ---- drawing the ring -------------------------------------------------------

// A drawing with a fixed viewBox scales with the page. --u is its units per CSS
// pixel, so that its labels can be set at 16 pixels on any screen.
const unitWatch = typeof ResizeObserver === 'function'
  ? new ResizeObserver(es => { for (const e of es) setUnits(e.target); }) : null;
function setUnits(svgEl) {
  const vb = svgEl.viewBox.baseVal, w = svgEl.clientWidth || svgEl.getBoundingClientRect().width;
  if (vb && vb.width && w) svgEl.style.setProperty('--u', (vb.width / w).toFixed(4));
}

function buildRing() {
  const ring = $('#ring');
  ring.replaceChildren();
  setUnits(ring);
  if (unitWatch) unitWatch.observe(ring);
  const N = world.ops.length, C = 220, R = 72, R0 = 98, LEN = 110;
  const Wmax = Math.min(44, 0.75 * 2 * Math.PI * R0 / N);
  geo = { C, R, R0, LEN, Wmax, nodes: [], links: new Map() };
  const gRuin = el('g', { class: 'ruinlines' }, ring);
  const gCorr = el('g', { class: 'corridors' }, ring);
  const gLinks = el('g', { class: 'links' }, ring);
  const gNodes = el('g', { class: 'nodes' }, ring);
  // each operator's number, drawn beside its button and not inside it: the button's name already says "Operator 1",
  // and a button's visible text must be part of its name (axe, label-content-name-mismatch; WCAG 2.5.3)
  const gNames = el('g', { class: 'names', 'aria-hidden': 'true' }, ring);
  world.ops.forEach((o, i) => {
    const th = -Math.PI / 2 + 2 * Math.PI * i / N;
    const u = [Math.cos(th), Math.sin(th)], v = [-Math.sin(th), Math.cos(th)];
    const x = C + R * u[0], y = C + R * u[1];
    const corr = el('path', { class: 'corridor' }, gCorr);
    const ruinA = el('line', { class: 'ruinline' }, gRuin), ruinB = el('line', { class: 'ruinline' }, gRuin);
    // the ring is aria-hidden: its dots are for the eye and the pointer only, and take no focus. Each operator's
    // button is in the operators table (buildOpsTable), with the same name, and does the same.
    const g = el('g', { class: 'node' }, gNodes);
    const title = el('title', {}, g);
    el('circle', { cx: x, cy: y, r: 22, class: 'hit' }, g);
    el('circle', { cx: x, cy: y, r: 17, class: 'dot' }, g);
    const letter = el('text', { x, y, class: 'letter', 'text-anchor': 'middle', 'dominant-baseline': 'central' }, g);
    el('text', {
      x: C + (R - 32) * u[0], y: C + (R - 32) * u[1], class: 'name',
      'text-anchor': 'middle', 'dominant-baseline': 'central',
    }, gNames, o.name);
    g.addEventListener('click', () => cycleType(i));
    geo.nodes.push({ x, y, u, v, corr, ruinA, ruinB, g, title, letter });
  });
  for (const l of world.links) {
    const a = geo.nodes[l.ends[0]], b = geo.nodes[l.ends[1]];
    geo.links.set(l.id, el('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: 'link' }, gLinks));
  }
  placeRuinLines();
}

function hw(E) { return geo.Wmax / 2 * Math.max(0, Math.min(1, E / Escale)); }

function placeRuinLines() {
  const { C, R0, LEN } = geo, h = hw(world.p.E_r);
  for (const nd of geo.nodes) {
    for (const [ln, sgn] of [[nd.ruinA, 1], [nd.ruinB, -1]]) {
      ln.setAttribute('x1', C + R0 * nd.u[0] + sgn * h * nd.v[0]);
      ln.setAttribute('y1', C + R0 * nd.u[1] + sgn * h * nd.v[1]);
      ln.setAttribute('x2', C + (R0 + LEN) * nd.u[0] + sgn * h * nd.v[0]);
      ln.setAttribute('y2', C + (R0 + LEN) * nd.u[1] + sgn * h * nd.v[1]);
    }
  }
}

function corridorPath(i, now) {
  const { C, R0, LEN } = geo, nd = geo.nodes[i], o = world.ops[i];
  const L = [], Rr = [];
  const put = (age, E, alive) => {
    const d = R0 + age / HISTORY * LEN, h = alive ? hw(E) : 0;
    const cx = C + d * nd.u[0], cy = C + d * nd.u[1];
    L.push(`${(cx + h * nd.v[0]).toFixed(1)},${(cy + h * nd.v[1]).toFixed(1)}`);
    Rr.push(`${(cx - h * nd.v[0]).toFixed(1)},${(cy - h * nd.v[1]).toFixed(1)}`);
  };
  put(0, o.E, o.alive);
  for (let k = samples.length - 1; k >= 0; k--) {
    const s = samples[k], age = now - s.t;
    if (age <= 0) continue;
    if (age > HISTORY) { put(HISTORY, s.E[i], s.alive[i]); break; }
    put(age, s.E[i], s.alive[i]);
  }
  if (L.length < 2) return '';
  return 'M' + L.join('L') + 'L' + Rr.reverse().join('L') + 'Z';
}

function draw(force = false) {
  const now = world.time();
  let maxE = 0;
  for (const o of world.ops) if (o.alive) maxE = Math.max(maxE, o.E);
  if (maxE > Escale) {
    Escale = Math.ceil(maxE * 1.25 / 50) * 50;
    placeRuinLines();
  }
  world.ops.forEach((o, i) => {
    const nd = geo.nodes[i];
    nd.corr.setAttribute('d', corridorPath(i, now));
    const cls = `type-${o.type.toLowerCase()}${o.alive ? '' : ' ruined'}`;
    nd.corr.setAttribute('class', `corridor ${cls}`);
    nd.g.setAttribute('class', `node ${cls}`);
    nd.letter.textContent = o.type;
    nd.title.textContent = opLabel(o);
  });
  for (const l of world.links) geo.links.get(l.id).style.display = l.live ? '' : 'none';
  $('#time').textContent = `t = ${now.toFixed(1)} of ${HORIZON}`;
  const t = performance.now();
  if (force || !playing || t - lastPanel > 250) {
    lastPanel = t;
    fillOpsTable();
    fillWorldClocks();
  }
}

// an operator's name, the same in the drawing's tooltip and on its button in the table
function opLabel(o) {
  return `Operator ${o.name}, type ${o.type}, stock ${f2(o.E)}` +
    (o.alive ? '' : `, ruined at t = ${f2(o.ruinTime)}`) + '. Change its type.';
}

// Each row's type is a real button, doing what tapping the operator's dot does. The rows are kept while the number of
// operators is the same, so a button keeps its focus when it changes its operator's type.
function buildOpsTable() {
  const body = $('#ops-body');
  if (body.children.length === world.ops.length) return;
  body.replaceChildren();
  world.ops.forEach((o, i) => {
    const tr = html('tr');
    for (let k = 0; k < 5; k++) tr.appendChild(html('td'));
    tr.children[0].textContent = o.name;
    const b = html('button');
    b.type = 'button';
    b.className = 'chip op-type';
    b.addEventListener('click', () => cycleType(i));
    tr.children[1].appendChild(b);
    body.appendChild(tr);
  });
}

function fillOpsTable() {
  const rows = $('#ops-body').children;
  world.ops.forEach((o, i) => {
    const c = rows[i].children;
    const b = c[1].firstElementChild;
    b.className = `chip op-type type-${o.type.toLowerCase()}`;
    b.textContent = o.type;
    b.setAttribute('aria-label', opLabel(o));
    c[2].textContent = o.alive ? f2(o.E) : `≤ ${world.p.E_r}`;
    c[3].textContent = world.counterparties(o.i).map(q => world.ops[q].name).join(', ') || 'none';
    c[4].textContent = o.alive ? 'live' : `ruined at ${f2(o.ruinTime)}`;
    rows[i].className = o.alive ? '' : 'ruined';
  });
  const cuts = world.cuts.length, ruins = world.ruins.length;
  $('#tally').textContent = `Cuts: ${cuts} · Ruined: ${ruins}`;
}

// ---- clocks -----------------------------------------------------------------

function memberLabel(w, s) {
  const others = s.members.filter(n => n !== s.operator);
  return `${s.operator} (${s.type}) ${others.length ? 'with ' + others.join(', ') : 'alone'}`;
}

// One configuration's clock, in spans: 1, 2 and 3 marked; the bound at 3.
// Survival is counted less the others' record window where they are type C,
// and in full elsewhere (Part Nine, point 5), so the bound is 3 spans for all.
function clockRow(w, s, unit) {
  const row = html('div', 'clock');
  const head = html('div', 'clock-head');
  head.appendChild(html('span', 'clock-name', memberLabel(w, s)));
  const val = s.span === null ? 'no loss yet'
    : `${s.survival_less_window.toFixed(2)} spans${s.open ? ' so far' : ''}`;
  head.appendChild(html('span', 'clock-val', val));
  row.appendChild(head);
  // which span was used: said only where the whole gains, and the span is
  // taken over the others alone (Part Nine, point 2)
  const over = s.span_used === 'counterparties' ? ', over the others alone: the whole gains'
    : (s.span_used || '').endsWith("counterparties'") ? ', over the others alone, the longer span' : '';
  const allC = s.members.every(n => n === s.operator || w.op(n).type === 'C');
  const less = s.span !== null && s.window > 0
    ? ` · less ${w.p.w} rounds of record: ${allC ? 'the others are' : 'one of the others is'} type C` : '';
  const sub = html('div', 'clock-sub',
    `clock from ${f2(s.clock_start)}${unit}` +
    (s.span !== null ? ` · span ${f2(s.span)}${unit}${over} · bound ${f2(s.bound)}${unit}` : '') + less +
    (s.open ? '' : ` · ended ${f2(s.end)}${unit}`));
  row.appendChild(sub);

  // drawn at the width it is shown at, so that its labels stay at 16 pixels
  const W = clockW, X = sp => 10 + Math.min(4, Math.max(0, sp)) * (W - 34) / 4;
  const svgEl = el('svg', { viewBox: `0 0 ${W} 44`, class: 'clock-bar', role: 'img' });
  el('line', { x1: X(0), y1: 12, x2: X(4), y2: 12, class: 'track' }, svgEl);
  for (const k of [1, 2, 3]) {
    el('line', { x1: X(k), y1: 4, x2: X(k), y2: 20, class: k === 3 ? 'tick bound' : 'tick' }, svgEl);
    el('text', { x: X(k), y: 38, 'text-anchor': 'middle', class: 'tick-label' }, svgEl,
      k === 3 ? '3 · bound' : String(k));
  }
  if (s.span !== null) {
    const surv = s.survival_less_window;
    const x1 = X(surv);
    el('rect', { x: X(0), y: 8, width: Math.max(2, x1 - X(0)), height: 8, rx: 4, class: `bar type-${s.type.toLowerCase()}` }, svgEl);
    if (surv > 4) el('text', { x: X(4) + 4, y: 18, class: 'tick-label' }, svgEl, '›');
    if (!s.open) {
      if (s.end_cause === 'ruin') {
        el('path', { d: `M${x1 - 4},8L${x1 + 4},16M${x1 - 4},16L${x1 + 4},8`, class: 'end-mark' }, svgEl);
      } else {
        el('line', { x1, y1: 5, x2: x1, y2: 19, class: 'end-mark' }, svgEl);
      }
    }
  }
  svgEl.setAttribute('aria-label', `${memberLabel(w, s)}: ${val}. Marks at 1, 2 and 3 spans.`);
  row.appendChild(svgEl);
  return row;
}

let clockW = 320;
const fitClocks = box => { clockW = Math.max(240, Math.min(480, Math.round(box.clientWidth || 320))); };

function fillWorldClocks() {
  const box = $('#world-clocks');
  fitClocks(box);
  const all = world.configs.map(c => world.configSummary(c)).filter(s => s.clock_start !== null);
  all.sort((a, b) => (b.open - a.open) || (b.start - a.start));
  box.replaceChildren();
  if (!all.length) { box.appendChild(html('p', 'muted', 'No clock has started.')); return; }
  for (const s of all.slice(0, 8)) box.appendChild(clockRow(world, s, ''));
  if (all.length > 8) box.appendChild(html('p', 'muted', `And ${all.length - 8} more.`));
}

// ---- controls ---------------------------------------------------------------

function cycleType(i) {
  const next = { C: 'U', U: 'D', D: 'C' };
  const t = [...state.types];
  t[i] = next[t[i]];
  state.types = t.join('');
  settingsChanged();
}

function syncControls() {
  for (const k of ['cost', 'drift', 'mult', 'noise', 'ops']) {
    $(`#s-${k}`).value = state[k];
    $(`#o-${k}`).textContent = show(k, state[k]);
    $(`#s-${k}`).setAttribute('aria-valuetext', show(k, state[k]));
  }
  const auto = state.give === 'auto';
  const g = auto ? state.mult / (2 * state.cost) : state.give;
  $('#s-give').value = Math.min(LIMITS.give[1], g);
  $('#o-give').textContent = auto ? `${g.toFixed(2)} · m ÷ 2λ` : show('give', g);
  $('#s-give').setAttribute('aria-valuetext', $('#o-give').textContent);
  $('#give-auto').setAttribute('aria-pressed', String(auto));
  $('#seed').value = state.seed;
  $('#s-cmult').value = state.cmult;
  $('#o-cmult').textContent = show('cmult', state.cmult);
  $('#s-cmult').setAttribute('aria-valuetext', show('cmult', state.cmult));
}

function settingsChanged() {
  writeHash();
  syncControls();
  const was = playing;
  newWorld();
  setPlaying(was);
}

function wireControls() {
  for (const k of ['cost', 'drift', 'mult', 'noise']) {
    $(`#s-${k}`).addEventListener('input', e => { state[k] = snap(k, Number(e.target.value)); settingsChanged(); });
  }
  $('#s-ops').addEventListener('input', e => {
    state.ops = snap('ops', Number(e.target.value));
    state.types = (state.types + 'C'.repeat(state.ops)).slice(0, state.ops);
    settingsChanged();
  });
  $('#s-give').addEventListener('input', e => { state.give = snap('give', Number(e.target.value)); settingsChanged(); });
  $('#give-auto').addEventListener('click', () => { state.give = 'auto'; settingsChanged(); });
  $('#seed').addEventListener('change', e => {
    const v = Number(e.target.value);
    if (Number.isFinite(v)) state.seed = snap('seed', v);
    settingsChanged();
  });
  $('#new-seed').addEventListener('click', () => {
    state.seed = 1 + Math.floor(Math.random() * LIMITS.seed[1]);
    settingsChanged();
  });
  $('#play').addEventListener('click', () => {
    if (finished()) { newWorld(); setPlaying(true); return; }
    setPlaying(!playing);
  });
  $('#restart').addEventListener('click', () => { newWorld(); setPlaying(true); });
  $('#speed').addEventListener('change', e => { speed = Number(e.target.value); });
  $('#copy-link').addEventListener('click', async () => {
    const b = $('#copy-link');
    try { await navigator.clipboard.writeText(location.href); b.textContent = 'Copied'; }
    catch { b.textContent = 'Copy failed'; }
    setTimeout(() => { b.textContent = 'Copy link'; }, 1500);
  });
  $('#s-cmult').addEventListener('input', e => {
    state.cmult = snap('cmult', Number(e.target.value));
    writeHash();
    syncControls();
    scheduleCharger();
  });
  window.addEventListener('hashchange', () => {
    if (!location.hash.includes('=')) return;   // an anchor on the page (such as #main), not the world's settings
    const s = readHash();
    if (hashOf(s) === hashOf(state)) return;
    const chargerOnly = hashOf({ ...s, cmult: state.cmult }) === hashOf(state);
    state = s;
    writeHash();
    syncControls();
    if (!chargerOnly) { const was = playing; newWorld(); setPlaying(was); }
    if (chargerShown) scheduleCharger();
  });
  for (const b of document.querySelectorAll('[role="tab"]')) {
    b.addEventListener('click', () => showView(b.id === 'tab-charger' ? 'charger' : 'world'));
  }
}

let chargerShown = false;
function showView(which) {
  const ch = which === 'charger';
  $('#tab-world').setAttribute('aria-selected', String(!ch));
  $('#tab-charger').setAttribute('aria-selected', String(ch));
  $('#view-world').hidden = ch;
  $('#view-charger').hidden = !ch;
  chargerShown = ch;
  if (ch) {
    if (playing) setPlaying(false);
    if (!sweep) computeSweep();
    scheduleCharger();
  }
}

// ---------------------------------------------------------------------------
// The page's charger, at its own numbers.

function runCharger(m, types, keepTrace) {
  const w = new World(resolveParams(CH, { m }), { types });
  const tr = { A: [[0, w.ops[0].E]], B: [[0, w.ops[1].E]] };
  const every = Math.max(1, Math.round(w.nsub / 20));
  const done = new Set();
  while (!w.allRuined() && w.time() < 200 - 1e-9) {
    w.step();
    if (!keepTrace) continue;
    for (const o of w.ops) {
      if (done.has(o.name)) continue;
      if (!o.alive) { tr[o.name].push([o.ruinTime, w.p.E_r]); done.add(o.name); }
      else if (w.j % every === 0) tr[o.name].push([w.time(), o.E]);
    }
  }
  return { w, tr };
}
const PAIR = { A: 'U', B: 'U' }, DEFECT = { A: 'U', B: 'D' };
const lifeOfPair = w => w.op('A').ruinTime ?? Infinity;
const lifeOfDefector = w => w.op('B').ruinTime ?? Infinity;

let sweep = null;
function computeSweep() {
  const ms = [];
  for (let m = 2; m <= 14 + 1e-9; m += 0.25) ms.push(Number(m.toFixed(2)));
  sweep = { ms, pair: [], defector: [], done: 0 };
  const step = () => {
    const t0 = performance.now();
    while (sweep.done < ms.length && performance.now() - t0 < 25) {
      const m = ms[sweep.done];
      sweep.pair.push(lifeOfPair(runCharger(m, PAIR, false).w));
      sweep.defector.push(lifeOfDefector(runCharger(m, DEFECT, false).w));
      sweep.done += 1;
    }
    drawLifetimes();
    if (sweep.done < ms.length) setTimeout(step, 0);
    else fillLifetimeTable();
  };
  step();
}

let chargerPending = false, scenes = null;
function scheduleCharger() {
  if (chargerPending) return;
  chargerPending = true;
  setTimeout(() => { chargerPending = false; drawCharger(); }, 0);
}

function drawCharger() {
  const m = state.cmult;
  scenes = { pair: runCharger(m, PAIR, true), defector: runCharger(m, DEFECT, true) };
  const lp = lifeOfPair(scenes.pair.w), ld = lifeOfDefector(scenes.defector.w);
  let verdict;
  if (Math.abs(lp - ld) < 1e-6) verdict = 'They last the same: this is the boundary.';
  else verdict = lp > ld ? 'The pair lasts longer.' : 'The defector lasts longer.';
  $('#charger-readout').innerHTML =
    `At m = <b>${show('cmult', m)}</b>: the pair lasts <b>${f2(lp)} h</b> <span class="muted">(${hm(lp)})</span>; ` +
    `the defector lasts <b>${f2(ld)} h</b> <span class="muted">(${hm(ld)})</span>. ${verdict}`;
  $('#charger-readout').dataset.side = Math.abs(lp - ld) < 1e-6 ? 'equal' : lp > ld ? 'pair' : 'defector';
  drawLifetimes();
  const all = [scenes.pair, scenes.defector];
  let tEnd = 0, yTop = 100;
  for (const s of all) for (const o of s.w.ops) {
    tEnd = Math.max(tEnd, o.ruinTime ?? s.w.time());
    yTop = Math.max(yTop, o.Emax);
  }
  const Tmax = Math.max(20, Math.ceil(tEnd / 5) * 5), Ymax = Math.ceil(yTop / 20) * 20;
  drawStocks($('#chart-pair'), scenes.pair, Tmax, Ymax, 'Both crank');
  drawStocks($('#chart-defector'), scenes.defector, Tmax, Ymax, 'B defects');
  fillChargerClocks($('#clocks-pair'), scenes.pair.w);
  fillChargerClocks($('#clocks-defector'), scenes.defector.w);
}

function fillChargerClocks(box, w) {
  box.replaceChildren();
  fitClocks(box);
  const all = w.configs.map(c => w.configSummary(c)).filter(s => s.clock_start !== null);
  if (!all.length) { box.appendChild(html('p', 'muted', 'No clock started.')); return; }
  for (const s of all) box.appendChild(clockRow(w, s, ' h'));
}

// ---- the lifetimes chart ------------------------------------------------------

const LT = { W: 640, H: 330, l: 48, r: 18, t: 30, b: 44, mLo: 2, mHi: 14, hHi: 50 };
const ltX = m => LT.l + (m - LT.mLo) / (LT.mHi - LT.mLo) * (LT.W - LT.l - LT.r);
const ltY = h => LT.t + (LT.H - LT.t - LT.b) * (1 - Math.min(h, LT.hHi) / LT.hHi);

// Charts take their coordinates from the width they are drawn at, so that
// their text stays at its own size on a phone.
const fitWidth = (svgEl, lo, hi, fallback) =>
  Math.max(lo, Math.min(hi, svgEl.clientWidth || svgEl.parentElement.clientWidth || fallback));

// A label near an edge is moved in, never cut off.
function keepInside(svgEl, W) {
  for (const t of svgEl.querySelectorAll('text.value, text.direct, text.region')) {
    const b = t.getBBox();
    if (!b.width) continue;
    const dx = b.x < 2 ? 2 - b.x : b.x + b.width > W - 2 ? W - 2 - b.x - b.width : 0;
    if (dx) for (const n of [t, ...t.querySelectorAll('tspan[x]')]) n.setAttribute('x', +n.getAttribute('x') + dx);
  }
  // a value read off the chart wins over a series name or a region's name in its way
  const hit = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
  const values = [...svgEl.querySelectorAll('text.value')].map(t => t.getBBox());
  for (const t of svgEl.querySelectorAll('text.direct, text.region')) {
    const b = t.getBBox();
    if (values.some(v => hit(b, v))) t.setAttribute('visibility', 'hidden');
  }
}

function drawLifetimes() {
  const svgEl = $('#chart-lifetimes');
  if (!sweep) return;
  LT.W = fitWidth(svgEl, 300, 760, 640);
  LT.H = LT.W < 520 ? 290 : 330;
  svgEl.setAttribute('viewBox', `0 0 ${LT.W} ${LT.H}`);
  const parts = [];
  const x0 = LT.l, x1 = LT.W - LT.r, yb = ltY(0), yt = ltY(LT.hHi);
  for (let h = 0; h <= LT.hHi; h += 10) {
    parts.push(`<line class="${h ? 'grid' : 'axis'}" x1="${x0}" x2="${x1}" y1="${ltY(h)}" y2="${ltY(h)}"/>`);
    parts.push(`<text class="tick-label" x="${x0 - 8}" y="${ltY(h)}" text-anchor="end" dominant-baseline="central">${h}</text>`);
  }
  for (let m = 2; m <= 14; m += 2) {
    parts.push(`<text class="tick-label" x="${ltX(m)}" y="${yb + 18}" text-anchor="middle">${m}</text>`);
  }
  parts.push(`<text class="axis-title" x="${(x0 + x1) / 2}" y="${LT.H - 6}" text-anchor="middle">Delivery multiple m</text>`);
  parts.push(`<text class="axis-title" x="${x0}" y="${LT.t - 14}" text-anchor="start">Hours to ruin</text>`);
  // the boundary at 8
  parts.push(`<line class="boundary" x1="${ltX(8)}" x2="${ltX(8)}" y1="${yt}" y2="${yb}"/>`);
  parts.push(`<text class="boundary-label" x="${ltX(8)}" y="${LT.t - 14}" text-anchor="middle">8</text>`);
  // the two regions' names, drawn over the lines and the marker, so that they can always be read
  let regionsDrawn = false;
  const regions = () => {
    if (regionsDrawn) return;
    regionsDrawn = true;
    for (const [m, who] of [[5, 'Defector'], [11, 'Pair']]) {
      parts.push(LT.W < 600
        ? `<text class="region" x="${ltX(m)}" y="${yt + 18}" text-anchor="middle">${who}<tspan x="${ltX(m)}" dy="18">lasts longer</tspan></text>`
        : `<text class="region" x="${ltX(m)}" y="${yt + 18}" text-anchor="middle">${who} lasts longer</text>`);
    }
  };
  const n = sweep.done;
  const path = arr => arr.slice(0, n).map((h, k) => `${k ? 'L' : 'M'}${ltX(sweep.ms[k]).toFixed(1)},${ltY(h).toFixed(1)}`).join('');
  if (n > 1) {
    parts.push(`<path class="line s1" d="${path(sweep.pair)}"/>`);
    parts.push(`<path class="line s2" d="${path(sweep.defector)}"/>`);
    const at = mm => sweep.ms.indexOf(mm);
    const k12 = at(12);
    if (k12 >= 0 && k12 < n) {
      parts.push(`<text class="direct" x="${ltX(12) - 8}" y="${ltY(sweep.pair[k12]) - 10}" text-anchor="end">Pair</text>`);
      parts.push(`<text class="direct" x="${ltX(12) + 4}" y="${ltY(sweep.defector[k12]) + 20}" text-anchor="start">Defector</text>`);
    }
  }
  // the current m
  if (scenes) {
    const m = state.cmult, lp = lifeOfPair(scenes.pair.w), ld = lifeOfDefector(scenes.defector.w);
    const xm = ltX(m), right = m < 11.5;
    parts.push(`<line class="marker" x1="${xm}" x2="${xm}" y1="${yt}" y2="${yb}"/>`);
    regions();
    for (const [h, cls, lbl] of [[lp, 's1', 'pair'], [ld, 's2', 'defector']]) {
      parts.push(`<circle class="pt ${cls}" cx="${xm}" cy="${ltY(h)}" r="5"/>`);
      const dy = (cls === 's1') === (lp >= ld) ? -9 : 15;
      parts.push(`<text class="value" x="${xm + (right ? 9 : -9)}" y="${ltY(h) + dy}" text-anchor="${right ? 'start' : 'end'}">${f2(h)} h</text>`);
    }
  }
  regions();
  parts.push(`<line class="hover-line" x1="0" x2="0" y1="${yt}" y2="${yb}" visibility="hidden"/>`);
  parts.push(`<rect class="hit-area" x="${x0}" y="${yt}" width="${x1 - x0}" height="${yb - yt}"/>`);
  svgEl.innerHTML = parts.join('');
  keepInside(svgEl, LT.W);
  svgEl.setAttribute('aria-label',
    `Hours to ruin against the delivery multiple m, for the pair and for the defector. The lines cross at m = 8.`);
}

function fillLifetimeTable() {
  const body = $('#lifetime-body');
  body.replaceChildren();
  for (let m = 2; m <= 14; m += 1) {
    const k = sweep.ms.indexOf(m);
    const tr = html('tr');
    tr.innerHTML = `<td>${m}</td><td>${f2(sweep.pair[k])}</td><td>${f2(sweep.defector[k])}</td>`;
    body.appendChild(tr);
  }
}

function svgPoint(svgEl, evt) {
  const r = svgEl.getBoundingClientRect(), vb = svgEl.viewBox.baseVal;
  const s = Math.min(r.width / vb.width, r.height / vb.height);
  const ox = (r.width - vb.width * s) / 2, oy = (r.height - vb.height * s) / 2;
  return { x: (evt.clientX - r.left - ox) / s, y: (evt.clientY - r.top - oy) / s, px: evt.clientX - r.left, py: evt.clientY - r.top };
}

function wireLifetimeChart() {
  const svgEl = $('#chart-lifetimes'), tip = $('#tip-lifetimes');
  const mAt = x => LT.mLo + (x - LT.l) / (LT.W - LT.l - LT.r) * (LT.mHi - LT.mLo);
  let dragging = false;
  svgEl.addEventListener('pointermove', e => {
    if (!sweep || !sweep.done) return;
    const p = svgPoint(svgEl, e);
    const m = mAt(p.x);
    if (m < LT.mLo - 0.2 || m > LT.mHi + 0.2) { tip.hidden = true; return; }
    if (dragging) setChargerM(m);
    let k = Math.round((Math.min(LT.mHi, Math.max(LT.mLo, m)) - LT.mLo) / 0.25);
    k = Math.min(sweep.done - 1, k);
    const line = svgEl.querySelector('.hover-line');
    line.setAttribute('x1', ltX(sweep.ms[k])); line.setAttribute('x2', ltX(sweep.ms[k]));
    line.setAttribute('visibility', 'visible');
    tip.innerHTML = `<b>m = ${sweep.ms[k]}</b><br><span class="sw s1"></span>Pair ${f2(sweep.pair[k])} h<br><span class="sw s2"></span>Defector ${f2(sweep.defector[k])} h`;
    placeTip(tip, svgEl, p);
  });
  svgEl.addEventListener('pointerleave', () => {
    tip.hidden = true;
    const line = svgEl.querySelector('.hover-line');
    if (line) line.setAttribute('visibility', 'hidden');
    dragging = false;
  });
  svgEl.addEventListener('pointerdown', e => {
    const p = svgPoint(svgEl, e), m = mAt(p.x);
    if (m < LT.mLo - 0.2 || m > LT.mHi + 0.2) return;
    dragging = true;
    setChargerM(m);
  });
  window.addEventListener('pointerup', () => { dragging = false; });
}

function setChargerM(m) {
  const v = snap('cmult', m);
  if (v === state.cmult) return;
  state.cmult = v;
  writeHash();
  syncControls();
  scheduleCharger();
}

function placeTip(tip, svgEl, p) {
  tip.hidden = false;
  const box = svgEl.parentElement.getBoundingClientRect();
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let x = p.px + 14, y = p.py - h - 10;
  if (x + w > box.width) x = p.px - w - 14;
  if (x < 0) x = 0;
  if (y < 0) y = p.py + 14;
  tip.style.left = `${x}px`;
  tip.style.top = `${y}px`;
}

// ---- the stock charts ----------------------------------------------------------

const SC = { W: 320, H: 224, l: 42, r: 14, t: 16, b: 46 };

function drawStocks(svgEl, scene, Tmax, Ymax, name) {
  SC.W = fitWidth(svgEl, 260, 560, 320);
  svgEl.setAttribute('viewBox', `0 0 ${SC.W} ${SC.H}`);
  const X = t => SC.l + t / Tmax * (SC.W - SC.l - SC.r);
  const Y = E => SC.t + (SC.H - SC.t - SC.b) * (1 - Math.max(0, E) / Ymax);
  const parts = [], x0 = X(0), x1 = X(Tmax), yb = Y(0), yt = Y(Ymax);
  for (let E = 0; E <= Ymax; E += 20) {
    parts.push(`<line class="${E ? 'grid' : 'axis'}" x1="${x0}" x2="${x1}" y1="${Y(E)}" y2="${Y(E)}"/>`);
    parts.push(`<text class="tick-label" x="${x0 - 6}" y="${Y(E)}" text-anchor="end" dominant-baseline="central">${E}</text>`);
  }
  const dt = Tmax <= 30 ? 5 : Tmax <= 60 ? 10 : 20;
  for (let t = 0; t <= Tmax; t += dt) {
    parts.push(`<text class="tick-label" x="${X(t)}" y="${yb + 20}" text-anchor="middle">${t}</text>`);
  }
  parts.push(`<text class="axis-title" x="${(x0 + x1) / 2}" y="${SC.H - 6}" text-anchor="middle">Hours</text>`);
  const w = scene.w;
  for (const [nm, cls] of [['A', 's1'], ['B', 's2']]) {
    const d = scene.tr[nm].map(([t, E], k) => `${k ? 'L' : 'M'}${X(t).toFixed(1)},${Y(E).toFixed(1)}`).join('');
    parts.push(`<path class="line ${cls}${nm === 'B' ? ' dashed' : ''}" d="${d}"/>`);
  }
  const ra = w.op('A').ruinTime, rb = w.op('B').ruinTime;
  const marks = [];
  if (ra !== null && rb !== null && Math.abs(ra - rb) < 1e-6) marks.push([ra, 'A and B', 's1']);
  else {
    if (ra !== null) marks.push([ra, 'A', 's1']);
    if (rb !== null) marks.push([rb, 'B', 's2']);
  }
  marks.forEach(([t, who, cls], k) => {
    const x = X(t), y = Y(w.p.E_r);
    parts.push(`<circle class="pt ${cls}" cx="${x}" cy="${y}" r="5"/>`);
    const anchor = x > SC.W / 2 ? 'end' : 'start';
    parts.push(`<text class="value" x="${x + (anchor === 'end' ? -4 : 4)}" y="${y - 10 - 22 * k}" text-anchor="${anchor}">${who} ruined ${f2(t)} h</text>`);
  });
  parts.push(`<line class="hover-line" x1="0" x2="0" y1="${yt}" y2="${yb}" visibility="hidden"/>`);
  parts.push(`<rect class="hit-area" x="${x0}" y="${yt}" width="${x1 - x0}" height="${yb - yt}"/>`);
  svgEl.innerHTML = parts.join('');
  keepInside(svgEl, SC.W);
  svgEl.setAttribute('aria-label', `${name}, m = ${show('cmult', state.cmult)}: stock of A and B over hours.` +
    (ra !== null ? ` A ruined at ${f2(ra)} h.` : '') + (rb !== null ? ` B ruined at ${f2(rb)} h.` : ''));
  svgEl._chart = { X, Tmax, scene };
}

function wireStockChart(svgEl, tip) {
  svgEl.addEventListener('pointermove', e => {
    const c = svgEl._chart;
    if (!c) return;
    const p = svgPoint(svgEl, e);
    const t = (p.x - SC.l) / (SC.W - SC.l - SC.r) * c.Tmax;
    if (t < 0 || t > c.Tmax) { tip.hidden = true; return; }
    const at = arr => {
      if (t > arr[arr.length - 1][0] + 1e-9) return null;
      let best = arr[0];
      for (const q of arr) if (Math.abs(q[0] - t) < Math.abs(best[0] - t)) best = q;
      return best[1];
    };
    const a = at(c.scene.tr.A), b = at(c.scene.tr.B);
    const line = svgEl.querySelector('.hover-line');
    line.setAttribute('x1', c.X(t)); line.setAttribute('x2', c.X(t)); line.setAttribute('visibility', 'visible');
    tip.innerHTML = `<b>${t.toFixed(2)} h</b><br><span class="sw s1"></span>A ${a === null ? 'ruined' : f2(a)}<br><span class="sw s2"></span>B ${b === null ? 'ruined' : f2(b)}`;
    placeTip(tip, svgEl, p);
  });
  svgEl.addEventListener('pointerleave', () => {
    tip.hidden = true;
    const line = svgEl.querySelector('.hover-line');
    if (line) line.setAttribute('visibility', 'hidden');
  });
}

// ---------------------------------------------------------------------------

// Each slider also has a minus and a plus, for a thumb on a small screen (the room's build brief, draft 2, part 2).
// Their names are "Less" and "More" before the slider's own: "Less: Noise", "More: Noise" (AG Opus, through G,
// 15 November 2026). Each moves its slider one step, within its own bounds, and tells the page as a drag does.
function addSteps() {
  for (const input of document.querySelectorAll('.slider input[type="range"]')) {
    const name = document.querySelector(`label[for="${input.id}"]`).textContent.trim();
    const row = document.createElement('div');
    row.className = 'slider-row';
    input.replaceWith(row);
    const step = (dir, sign, word) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'step';
      b.textContent = sign;
      b.setAttribute('aria-label', `${word}: ${name}`);
      b.addEventListener('click', () => {
        const was = input.value;
        if (dir < 0) input.stepDown(); else input.stepUp();
        if (input.value !== was) input.dispatchEvent(new Event('input', { bubbles: true }));
      });
      return b;
    };
    row.append(step(-1, '−', 'Less'), input, step(1, '+', 'More'));
  }
}

function start() {
  $('#versions').textContent = `${SPEC_VERSION} · ${CODE_VERSION}`;
  $('#charger-numbers').textContent =
    `${CH.operators.join(' and ')}, linked. Each starts at ${CH.E0} and burns ${CH.b} an hour. ` +
    `Cranking costs ${CH.c} an hour and gives the other m. Ruin at ${CH.E_r}.`;
  writeHash();
  syncControls();
  addSteps();
  wireControls();
  wireLifetimeChart();
  wireStockChart($('#chart-pair'), $('#tip-pair'));
  wireStockChart($('#chart-defector'), $('#tip-defector'));
  let resizeTimer = 0;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (chargerShown) scheduleCharger(); else if (world) fillWorldClocks(); }, 150);
  });
  newWorld();
  setPlaying(false);   // it never starts by itself, for anyone: it waits for play (the room's build brief, 2)
}

start();
