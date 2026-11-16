// check.mjs · runs every case and every check in ../test-values.json
// against engine.mjs, then the engine's own checks of Part Nine (draft 4).
// One line per check; exit code 1 if any fails.
//
//   node check.mjs
//
// Terms: Zero-Clause BSD (LICENSE-0BSD).

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { World, resolveParams, formulas, SPEC_VERSION, CODE_VERSION, NOT_SHORTER } from './engine.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const tv = JSON.parse(readFileSync(join(here, '..', 'test-values.json'), 'utf8'));

const rows = [];
let failed = 0;

const fmt = v => {
  if (v === null || v === undefined) return 'none';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(+v.toFixed(7));
  if (Array.isArray(v)) return '[' + v.map(fmt).join(',') + ']';
  if (typeof v === 'object') return '{' + Object.entries(v).map(([k, x]) => `${k}:${fmt(x)}`).join(' ') + '}';
  return String(v);
};
const near = (got, want, tol) => typeof got === 'number' && Number.isFinite(got) && Math.abs(got - want) <= tol;
const sameSet = (a, b) => a.length === b.length && [...a].sort().join('|') === [...b].sort().join('|');

function line(id, what, expected, got, pass) {
  if (!pass) failed += 1;
  rows.push([id, what, fmt(expected), fmt(got), pass ? 'pass' : 'FAIL']);
}

function buildWorld(cs) {
  const ov = { ...(cs.overrides || {}) };
  if (cs.topology) ov.topology = cs.topology;
  if (cs.operators) ov.operators = cs.operators;
  const params = resolveParams(tv.settings[cs.setting], ov);
  const world = new World(params, { types: cs.types || {}, seed: 1, log: true });
  world.runTo(cs.run_to);
  return world;
}

for (const cs of tv.cases) {
  let world = null;
  if (cs.setting) {
    try { world = buildWorld(cs); }
    catch (err) { line(cs.id, 'run', 'runs', String(err.message), false); continue; }
  }
  for (const ck of cs.checks) {
    const tol = ck.tol ?? 0;
    try {
      switch (ck.what) {
        case 'ruin_time': {
          const got = world.op(ck.operator).ruinTime;
          line(cs.id, `ruin_time ${ck.operator}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'never_ruined': {
          const o = world.op(ck.operator);
          line(cs.id, `never_ruined ${ck.operator}`, 'alive', o.alive ? 'alive' : `ruined at ${fmt(o.ruinTime)}`, o.alive);
          break;
        }
        case 'stock_at': {
          const got = world.stockAt(ck.operator, ck.t);
          line(cs.id, `stock_at ${ck.operator} t=${ck.t}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'stock_min': {
          const got = world.op(ck.operator).Emin;
          line(cs.id, `stock_min ${ck.operator}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'stock_max': {
          const got = world.op(ck.operator).Emax;
          line(cs.id, `stock_max ${ck.operator}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'configuration': {
          const owner = world.op(ck.operator);
          const c = world.configs.find(x => x.owner === owner.i && sameSet(world._names(x.members), ck.members));
          // the test value is the measure's own span: under version 1.1,
          // draft 3, points 19 and 22 only shorten a span, never lengthen
          // one, so every test value stands as it was
          const s = c ? world.configSummary(c) : null;
          const expected = {
            members: ck.members, clock: ck.clock_start, stock: ck.stock_above_ruin,
            loss: ck.net_loss_per_round, span: ck.span, end: ck.end,
          };
          const got = s ? {
            members: s.members, clock: s.clock_start, stock: s.stock_above_ruin,
            loss: s.net_loss_per_round, span: s.span, end: s.end,
          } : 'no such configuration';
          const pass = !!s && near(s.clock_start, ck.clock_start, tol) && near(s.stock_above_ruin, ck.stock_above_ruin, tol)
            && near(s.net_loss_per_round, ck.net_loss_per_round, tol) && near(s.span, ck.span, tol)
            && near(s.end, ck.end, tol);
          line(cs.id, `configuration of ${ck.operator}`, expected, got, pass);
          break;
        }
        case 'formula': {
          const out = formulas[ck.name](ck.inputs);
          const got = out[ck.output];
          line(cs.id, `formula ${ck.name} ${ck.output}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'engine_lone': {
          const params = resolveParams(tv.settings[ck.setting], { ...ck.overrides, operators: ['A'], topology: 'none' });
          const lone = new World(params, { seed: 1 });
          lone.runTo(ck.t);
          const got = lone.op('A').E;
          line(cs.id, `engine_lone ${ck.setting} t=${ck.t}`, ck.value, got, near(got, ck.value, tol));
          break;
        }
        case 'no_cut': {
          line(cs.id, 'no_cut', 0, world.cuts.length, world.cuts.length === 0);
          break;
        }
        case 'cut': {
          const hit = world.cuts.find(x => x.round === ck.round && x.by === ck.by
            && sameSet(x.link, ck.link) && x.record_rounds === ck.record_rounds);
          const first = world.cuts[0];
          const got = hit || first
            ? { round: (hit || first).round, by: (hit || first).by, link: (hit || first).link, record_rounds: (hit || first).record_rounds }
            : 'no cut';
          line(cs.id, 'cut', { round: ck.round, by: ck.by, link: ck.link, record_rounds: ck.record_rounds }, got, !!hit);
          break;
        }
        default:
          line(cs.id, ck.what, 'a known check', 'unknown check kind', false);
      }
    } catch (err) {
      line(cs.id, ck.what, 'runs', `error: ${err.message}`, false);
    }
  }
}

// The page carries its own copy of two settings; it must be the same data.
try {
  const src = readFileSync(join(here, 'world.js'), 'utf8');
  const m = src.match(/\/\* SETTINGS-BEGIN \*\/([\s\S]*?)\/\* SETTINGS-END \*\//);
  const page = m ? JSON.parse(m[1].trim().replace(/;$/, '').replace(/^[^{]*/, '')) : null;
  for (const key of ['page_charger', 'network']) {
    const same = !!page && JSON.stringify(page[key]) === JSON.stringify(tv.settings[key]);
    line('PAGE', `settings ${key} as in test-values.json`, 'same', same ? 'same' : 'different', same);
  }
} catch (err) {
  line('PAGE', 'settings as in test-values.json', 'same', `error: ${err.message}`, false);
}

// ---------------------------------------------------------------------------
// The engine's own checks of Part Nine, "How a run is measured". These are
// not test values: each case is worked by hand from the text, and none
// depends on the random draw, since two engines never share one (Part Seven).

const nine = (setting, ov, types = {}, seed = 1) => new World(resolveParams(tv.settings[setting], ov), { types, seed });
const summaryOf = (w, owner, members) => {
  const o = w.op(owner);
  const c = w.configs.find(x => x.owner === o.i && sameSet(w._names(x.members), members));
  return c ? w.configSummary(c) : null;
};
function own(id, what, work) {
  try { const [expected, got, pass] = work(); line(id, what, expected, got, pass); }
  catch (err) { line(id, what, 'runs', `error: ${err.message}`, false); }
}
const SEEDS = [0, 1, 2, 3];

// Point 1. Alone, at the network's drift 0.1 from 50: own input 0.5 is a
// loss (0.5 - 5), so the clock starts at once; own input 6 is a gain (6 - 5),
// so no clock starts. Of any type: the first is a defector.
own('P9.1', 'lone D, s = 0.5: a loss, clock from 0', () => {
  const w = nine('network', { operators: ['D'], topology: 'none', s: 0.5 }, { D: 'D' });
  w.runTo(5);
  const s = summaryOf(w, 'D', ['D']);
  return [{ clock: 0, used: 'whole', stock: 40 }, { clock: s.clock_start, used: s.span_used, stock: s.stock_above_ruin },
    s.clock_start === 0 && s.span_used === 'whole' && near(s.stock_above_ruin, 40, 1e-9)];
});
own('P9.1', 'lone U, s = 6: a gain, no clock', () => {
  const w = nine('network', { operators: ['U'], topology: 'none', s: 6 }, { U: 'U' });
  w.runTo(5);
  const s = summaryOf(w, 'U', ['U']);
  return [{ clock: null, judged: null }, { clock: s.clock_start, judged: s.judged }, s.clock_start === null && s.judged === null];
});

// Point 2, the gaining whole. Ring of D, H1, H2 (H type C), m = 5, g = 2.5.
// D gains 2(12.5) - 0.02 - 5 = 19.98, each host 12.5 - 12.52 - 5 = -5.02:
// the whole gains, so the span is the hosts': 2 x 40 over 2(2.5^2 + 0.01).
const ringH = nine('network', { operators: ['D', 'H1', 'H2'], topology: 'ring', m: 5 }, { D: 'D', H1: 'C', H2: 'C' });
ringH.runTo(10);
own('P9.2', 'ring D H1 H2, m = 5: D gains as a whole', () => {
  const s = summaryOf(ringH, 'D', ['D', 'H1', 'H2']);
  const want = 80 / 12.52;
  return [{ used: 'counterparties', stock: 80, loss: 12.52, span: want },
    { used: s.span_used_by_point_14 ?? s.span_used, stock: s.stock_above_ruin, loss: s.net_loss_per_round, span: s.span },
    (s.span_used_by_point_14 ?? s.span_used) === 'counterparties' && s.span_whole === null && near(s.stock_above_ruin, 80, 1e-9)
      && near(s.net_loss_per_round, 12.52, 1e-9) && near(s.span, want, 1e-9)];
});
// Point 5: the hosts are type C, so the window of 5 rounds comes off. They
// cut D at t = 1, inside it: survival less the window is 0.
own('P9.5', 'ring D H1 H2: survival less the window', () => {
  const s = summaryOf(ringH, 'D', ['D', 'H1', 'H2']);
  return [{ end: 1, window: 5, raw: 12.52 / 80, less: 0 },
    { end: s.end, window: s.window, raw: s.survival_spans, less: s.survival_less_window },
    near(s.end, 1, 1e-9) && s.window === 5 && near(s.survival_spans, 12.52 / 80, 1e-9) && s.survival_less_window === 0];
});

// Point 2, the losing whole: the page's charger, B defects. A: -4 - 12,
// B: +10 - 12, so the whole loses 18 an hour: the span is 200/18.
const charger = nine('page_charger', {}, { A: 'U', B: 'D' });
charger.runTo(30);
own('P9.2', "page's charger, B defects: B loses as a whole", () => {
  const s = summaryOf(charger, 'B', ['A', 'B']);
  return [{ used: 'whole', span: 200 / 18 }, { used: s.span_used, span: s.span },
    s.span_used === 'whole' && near(s.span, 200 / 18, 1e-9)];
});
// Point 5: A is type U, so nothing is subtracted.
own('P9.5', "page's charger, B defects: type U, no window", () => {
  const s = summaryOf(charger, 'B', ['A', 'B']);
  return [{ window: 0, less: 'as survival' }, { window: s.window, less: s.survival_less_window === s.survival_spans ? 'as survival' : s.survival_less_window },
    s.window === 0 && s.survival_spans !== null && s.survival_less_window === s.survival_spans];
});

// Point 4. Ring of D, U1, U2, m = 3, to t = 5: D's configuration still
// stands. Its whole loses 6.06 at the start, falling as the stocks fall, so
// its span is above 120/6.06, about 20, and its bound, 3 spans, is far off.
own('P9.4', 'ring D U1 U2, m = 3, to t = 5: too long to judge', () => {
  const w = nine('network', { operators: ['D', 'U1', 'U2'], topology: 'ring', m: 3 }, { D: 'D', U1: 'U', U2: 'U' });
  w.runTo(5);
  const s = summaryOf(w, 'D', ['D', 'U1', 'U2']);
  return [{ open: true, judged: false, too_long: 1 }, { open: s.open, judged: s.judged, too_long: w.report().too_long_to_judge },
    s.open && s.clock_start === 0 && s.bound > 5 && s.judged === false && w.report().too_long_to_judge === 1];
});
// Point 4, the run's length: a ring of 20, one D, m = 3, run to the horizon.
// D is cut at t = 1 and ruined alone; the hosts settle. Every clock judged.
own('P9.4', 'ring of 20, one D: run to 4,000, all judged', () => {
  const w = nine('network', {}, { 1: 'D' }).run();
  const r = w.report();
  const clocks = r.configurations.filter(s => s.clock_start !== null);
  return [{ time: 4000, too_long: 0, D_configurations: 2 }, { time: w.time(), too_long: r.too_long_to_judge, D_configurations: r.defectors['1'] },
    near(w.time(), 4000, 1e-9) && r.too_long_to_judge === 0 && clocks.length > 0 && clocks.every(s => s.judged === true) && r.defectors['1'] === 2];
});

// Point 9. Ring of D and three C hosts, newcomers type C every 10 rounds,
// the hopper on. The hosts cut D at t = 1; D, alone, is ruined near t = 17.8,
// so it hops at round 10, to a type C, who reads its record: below zero.
own('P9.9', 'ring D H1 H2 H3, entry q = 10, hopper: refused by the record', () => {
  const hops = SEEDS.map(seed => {
    const w = nine('network', { operators: ['D', 'H1', 'H2', 'H3'], topology: 'ring', open: { q: 10, n: 2, hopper: true } },
      { D: 'D', H1: 'C', H2: 'C', H3: 'C' }, seed);
    w.runTo(60);
    return w.hops;
  });
  const got = hops.map(h => `${h.filter(x => !x.accepted && x.reason === 'record').length}/${h.length}`);
  return [{ seeds: SEEDS, refused_by_record: 'all, at least one' }, { seeds: SEEDS, refused_by_record: got },
    hops.every(h => h.length >= 1 && h.every(x => !x.accepted && x.reason === 'record'))];
});
// Point 9. No links; a D and a U; a newcomer of type U every 10 rounds,
// offering none. At round 10 the D hops, to a U either way: accepted.
own('P9.9', 'D and U alone, newcomer U, hopper: first hop accepted', () => {
  const firsts = SEEDS.map(seed => {
    const w = nine('network', { operators: ['D', 'U'], topology: 'none', open: { q: 10, n: 0, hopper: true, type: 'U' } }, { D: 'D', U: 'U' }, seed);
    w.runTo(11);
    return w.hops[0] || null;
  });
  return [{ seeds: SEEDS, first_hop: 'accepted' }, { seeds: SEEDS, first_hop: firsts.map(h => (h ? (h.accepted ? 'accepted' : h.reason) : 'none')) },
    firsts.every(h => h && h.round === 10 && h.accepted)];
});

// Point 10. At m = 3 the give is 1.5 and u_max is 6: four links. A ring of
// six C, a newcomer every 2 rounds offering two links: none ever holds five.
own('P9.10', 'ring of 6 C, entry q = 2, n = 2: at most 4 links', () => {
  const most = SEEDS.map(seed => {
    const w = nine('network', { N: 6, topology: 'ring', open: { q: 2, n: 2 } }, {}, seed);
    let k = 0;
    while (w.time() < 60 - 1e-9) {
      w.runRound();
      for (const o of w.ops) k = Math.max(k, w.linksOf(o.i).length);
    }
    return k;
  });
  return [{ seeds: SEEDS, most_links: '4 at most' }, { seeds: SEEDS, most_links: most }, most.every(k => k <= 4)];
});
// Point 10. Links drawn at the start stand as drawn: all six linked, five
// links each, scaled to 6/5 each. The first newcomer's two offers fall on
// the six, and each refuses: five links already, past four.
own('P9.10', 'six linked to all: offers refused for capacity', () => {
  const w = nine('network', { N: 6, topology: 'random', p_link: 1, open: { q: 2, n: 2 } });
  w.runTo(3);
  const e = w.entries[0];
  const links = w.ops.slice(0, 6).map(o => w.linksOf(o.i).length);
  return [{ refused: 'capacity, capacity', links: [5, 5, 5, 5, 5, 5] },
    { refused: e ? e.refused.map(x => x.reason).join(', ') : 'no entry', links },
    !!e && e.accepted.length === 0 && e.refused.length === 2 && e.refused.every(x => x.reason === 'capacity') && links.every(k => k === 5)];
});

// B1's premise check, seed by seed. Two defectors and a type C host, none
// linked: both defectors are reported, and neither is watched, though
// alone, at a loss, their clocks start. On a ring of D, H1, H2 the
// defector starts with two live links, and is watched.
own('B1.7', 'defectors with no live link at the start: reported, not watched', () => {
  const w = nine('network', { operators: ['D1', 'D2', 'H'], topology: 'none' }, { D1: 'D', D2: 'D', H: 'C' });
  w.runTo(3);
  const r = w.report();
  const clocked = r.configurations.filter(s => s.clock_start !== null && s.has_defector);
  const watched = clocked.filter(s => s.watched_b1);
  return [{ reported: ['D1', 'D2'], clocked: 2, watched: 0 },
    { reported: r.defectors_with_no_live_link_at_start, clocked: clocked.length, watched: watched.length },
    sameSet(r.defectors_with_no_live_link_at_start, ['D1', 'D2']) && clocked.length === 2 && watched.length === 0];
});
own('B1.7', 'a defector with live links at the start is watched', () => {
  const r = ringH.report();
  const watched = r.configurations.filter(s => s.clock_start !== null && s.watched_b1);
  return [{ reported: [], watched: '>0' }, { reported: r.defectors_with_no_live_link_at_start, watched: watched.length },
    r.defectors_with_no_live_link_at_start.length === 0 && watched.length > 0];
});

// B1's section 7: a seed left with nothing to watch is left out of the
// mean, counted, and counts towards the one in ten.
const { measure } = await import('./run_cell.mjs');
own('B1.7', 'nothing to watch: out of the mean, and towards the one in ten', () => {
  const cfg = (seed, v, judged = true) => ({ seed, span: 1, judged, id: seed, operator: 'D', bound: 3, survival_less_window: v });
  const seeds = Array.from({ length: 20 }, (_, i) => i);
  const chosen = [...seeds.slice(2).map(s => cfg(s, 0.5)), cfg(1, 0.2, false)];
  const a = measure(seeds, chosen, 'survival_less_window');
  const b = measure(seeds, chosen.slice(1), 'survival_less_window');
  return [{ first: '18 in, 2 out, not settled', second: 'settles nothing' },
    { first: `${a.seeds_measured} in, ${a.seeds_not_in_the_mean} out, ${a.zone === 'settles nothing' ? 'settles nothing' : 'not settled'}`, second: b.zone },
    a.seeds_measured === 18 && a.seeds_not_in_the_mean === 2 && a.zone !== 'settles nothing' && b.zone === 'settles nothing' && b.seeds_not_in_the_mean === 3];
});

// No link joins two defectors. A ring of D1, D2, H: the ring would join D1
// and D2; that link is left out, and each keeps its link to H. A ring of D1,
// D2, D3, H: D1 - D2 and D2 - D3 are left out, so D2 starts with no live
// link. Two lone defectors with type D newcomers: every hop makes no link.
own('LINKS', 'ring D1 D2 H: D1 - D2 left out', () => {
  const w = nine('network', { operators: ['D1', 'D2', 'H'], topology: 'ring' }, { D1: 'D', D2: 'D', H: 'C' });
  const nb = x => w.counterparties(w.op(x).i).map(q => w.ops[q].name).join(',');
  return [{ left_out: 'D1-D2', D1: 'H', D2: 'H' }, { left_out: w.linksLeftOut.map(l => l.join('-')).join(' '), D1: nb('D1'), D2: nb('D2') },
    w.linksLeftOut.length === 1 && sameSet(w.linksLeftOut[0], ['D1', 'D2']) && nb('D1') === 'H' && nb('D2') === 'H'];
});
own('LINKS', 'ring D1 D2 D3 H: two left out, D2 with no live link', () => {
  const w = nine('network', { operators: ['D1', 'D2', 'D3', 'H'], topology: 'ring' }, { D1: 'D', D2: 'D', D3: 'D', H: 'C' });
  const r = w.report();
  return [{ left_out: 2, no_live_link: ['D2'] }, { left_out: w.linksLeftOut.length, no_live_link: r.defectors_with_no_live_link_at_start },
    w.linksLeftOut.length === 2 && sameSet(r.defectors_with_no_live_link_at_start, ['D2'])];
});
own('LINKS', 'hops between defectors: no link', () => {
  const w = nine('network', { operators: ['D1', 'D2'], topology: 'none', open: { q: 10, n: 0, type: 'D' } }, { D1: 'D', D2: 'D' });
  w.runTo(31);
  const ok = w.hops.length > 0 && w.hops.every(h => !h.accepted && h.reason === 'no link joins two defectors') && w.liveLinks.length === 0;
  return [{ hops: '>0', none_linked: true }, { hops: w.hops.length, none_linked: ok }, ok];
});

// Point 19, worked by hand. D and four type U hosts, all linked, m = 5: each
// host's give of 2.5 a link is scaled by capacity to 6/4 = 1.5, so on its
// link to D it spends 1.5^2 + 0.01 = 2.26 a round and gets nothing back. The
// counterparties' net loss through their links to D is 4 x 2.26 = 9.04 at
// every sample, and their records over the last 5 rounds add to -45.2.
// With noise, from 50: the span is 160/9.04 = 17.699, and at t = 400, 22.6
// spans, judged; by point 14 alone the whole's span ran past the run.
// Quiet, from 200: the whole loses throughout, so point 14's counterparties'
// span never applied; point 19 gives 760/9.04 = 84.071, and 4.758 spans.
// An operator alone has no counterparty, and point 19 does not apply.
const P19 = { D: 'D', H1: 'U', H2: 'U', H3: 'U', H4: 'U' };
own('P19', 'D and four U hosts, noise: 160/9.04, records -45.2, 22.6 spans, judged', () => {
  const got = SEEDS.map(seed => {
    const w = nine('network', { operators: Object.keys(P19), topology: 'random', p_link: 1, m: 5, sigma_s: 2, sigma_r: 1 }, P19, seed);
    w.runTo(400);
    return summaryOf(w, 'D', Object.keys(P19));
  });
  const ok = got.every(s => s && near(s.span, 160 / 9.04, 1e-9) && near(s.counterparties_records_last_w_rounds, -45.2, 1e-9)
    && near(s.survival_less_window, 22.6, 1e-9) && s.judged === true && s.point_19 !== null && s.span_by_point_14 > 400);
  return [{ span: 160 / 9.04, records: -45.2, spans: 22.6, judged: true },
    { span: got[0]?.span, records: got[0]?.counterparties_records_last_w_rounds, spans: got[0]?.survival_less_window, judged: got.every(s => s?.judged) }, ok];
});
own('P19', 'quiet, from 200: the whole loses throughout; 760/9.04, 4.758 spans, judged', () => {
  const w = nine('network', { operators: Object.keys(P19), topology: 'random', p_link: 1, m: 5, E0: 200 }, P19);
  w.runTo(400);
  const s = summaryOf(w, 'D', Object.keys(P19));
  return [{ span: 760 / 9.04, spans: 400 * 9.04 / 760, point_14: 'whole' }, { span: s.span, spans: s.survival_less_window, point_14: s.span_used_by_point_14 },
    near(s.span, 760 / 9.04, 1e-9) && near(s.survival_less_window, 400 * 9.04 / 760, 1e-9) && s.judged === true
    && s.span_counterparties === null && s.span_used_by_point_14 === 'whole' && s.span_by_point_14 > 400];
});
own('P19', 'an operator alone: point 19 does not apply', () => {
  const w = nine('network', { operators: ['D'], topology: 'none', s: 1.5 }, { D: 'D' });
  w.runTo(400);
  const s = summaryOf(w, 'D', ['D']);
  return [{ point_19: null, judged: false }, { point_19: s.point_19, judged: s.judged }, s.point_19 === null && s.judged === false];
});

// B1, section 10: a control cell prints "a defector lasts" or "no defector
// lasts", never "fires" or "holds", with "control: fires nothing" beside it.
const { controlWords, isControl } = await import('./run_cell.mjs');
own('B1.10', 'a control: a defector lasts, no defector lasts, fires nothing', () => {
  const seeds = Array.from({ length: 20 }, (_, i) => i);
  const mk = v => seeds.map(s => ({ seed: s, span: 1, judged: true, id: s, operator: 'D', bound: 3, survival_less_window: v + 0.01 * (s % 2) }));
  const hi = measure(seeds, mk(9), 'survival_less_window'), lo = measure(seeds, mk(0.3), 'survival_less_window');
  const before = [hi.zone, lo.zone];
  const after = [controlWords({ ...hi }), controlWords({ ...lo })];
  const ok = before[0] === 'fires' && before[1] === 'holds' && after[0].zone === 'a defector lasts' && after[1].zone === 'no defector lasts'
    && after.every(m => m.control === 'control: fires nothing') && isControl({ types: { hosts: 'U' } }) && !isControl({ types: { hosts: 'C' } });
  return [{ cell: 'fires, holds', control: 'a defector lasts, no defector lasts' }, { cell: before.join(', '), control: after.map(m => m.zone).join(', ') }, ok];
});

// Point 12, the uneven drift: first the random links, the defectors' places
// and the uneven drift. Each operator the world starts with draws its own a,
// uniform on [lo, hi], from the drift's own stream, so that it moves no other
// draw. Worked from the text; none depends on what the draw is, since two
// engines never share one (Part Seven).
const UNEVEN = [0.06, 0.2];
own('P9.12', 'uneven drift: each a in [lo, hi], uneven, drawn with the seed', () => {
  const drifts = seed => nine('network', { drift_uneven: UNEVEN }, {}, seed).ops.map(o => o.a);
  const got = SEEDS.map(drifts), again = SEEDS.map(drifts);
  const inRange = got.every(as => as.length === 20 && as.every(a => a >= UNEVEN[0] && a <= UNEVEN[1]));
  const uneven = got.every(as => new Set(as).size === as.length);
  const sameSeed = JSON.stringify(got) === JSON.stringify(again);
  const seedsDiffer = new Set(got.map(as => as.join(','))).size === SEEDS.length;
  return [{ in_range: true, all_different: true, same_seed_same: true, seeds_differ: true },
    { in_range: inRange, all_different: uneven, same_seed_same: sameSeed, seeds_differ: seedsDiffer }, inRange && uneven && sameSeed && seedsDiffer];
});
// It moves no other draw: random links, p = 0.2 among 20, the same with it as
// without it; and with lo = hi = 0.1, a world with one defector and both
// noises on is the even world, stock for stock, at t = 50.
own('P9.12', 'uneven drift moves no other draw: links, noise, stocks as without it', () => {
  const ends = w => w.links.map(l => l.ends.join('-')).join(' ');
  const linksSame = SEEDS.every(seed => ends(nine('network', { topology: 'random', p_link: 0.2, drift_uneven: UNEVEN }, {}, seed))
    === ends(nine('network', { topology: 'random', p_link: 0.2 }, {}, seed)));
  const noisy = { topology: 'random', p_link: 0.2, sigma_s: 1, sigma_r: 1 };
  const stocksSame = SEEDS.every(seed => {
    const u = nine('network', { ...noisy, drift_uneven: [0.1, 0.1] }, { 1: 'D' }, seed), e = nine('network', noisy, { 1: 'D' }, seed);
    u.runTo(50); e.runTo(50);
    return u.ops.every(o => o.a === 0.1) && u.ops.every((o, i) => o.E === e.ops[i].E) && u.cuts.length === e.cuts.length;
  });
  return [{ links_same: true, stocks_same: true }, { links_same: linksSame, stocks_same: stocksSame }, linksSame && stocksSame];
});
// Part Two's law, -a_i E_i, in the stock equation: twenty operators alone,
// no giving, s = 0. Each follows its own drift, E = 50 (1 - a_i dt)^(t/dt),
// and its lone configuration's smallest net loss at t = 5 is a_i E_i.
own('P9.12', 'each operator alone falls by its own drift: E = 50(1 - a dt)^500 at t = 5', () => {
  const ok = SEEDS.map(seed => {
    const w = nine('network', { topology: 'none', drift_uneven: UNEVEN }, {}, seed);
    w.runTo(5);
    return w.ops.every(o => o.alive && near(o.E, 50 * Math.pow(1 - o.a * 0.01, 500), 1e-9)
      && near(summaryOf(w, o.name, [o.name]).net_loss_per_round, o.a * o.E, 1e-9));
  });
  return [{ seeds: SEEDS, every_operator: 'its own drift' }, { seeds: SEEDS, every_operator: ok.map(x => (x ? 'its own drift' : 'not')) }, ok.every(Boolean)];
});
// The text draws the uneven drift first, and no drift in a round, so a
// newcomer keeps the setting's a (0.1); the twenty drawn at the start are as
// in the closed world. Ring of 20, a newcomer every 2 rounds, to t = 10:
// four newcomers, at rounds 2, 4, 6 and 8.
own('P9.12', "a newcomer keeps the setting's drift; the drawn twenty as without entry", () => {
  const ok = SEEDS.map(seed => {
    const w = nine('network', { drift_uneven: UNEVEN, open: { q: 2, n: 2 } }, {}, seed), closed = nine('network', { drift_uneven: UNEVEN }, {}, seed);
    w.runTo(10);
    const fresh = w.ops.slice(20);
    return fresh.length === 4 && fresh.every(o => o.a === 0.1) && w.ops.slice(0, 20).every((o, i) => o.a === closed.ops[i].a);
  });
  return [{ seeds: SEEDS, newcomers: "4, each at the setting's a" }, { seeds: SEEDS, newcomers: ok.map(x => (x ? "4, each at the setting's a" : 'not')) }, ok.every(Boolean)];
});

// ---- Part Nine, points 20 to 22 (version 1.1), and B2's section 10 ----
// From a configuration's reported spans alone: the span of points 2, 3 and
// 14, the longer of those that applied.
const span2314 = d => {
  const xs = [d.span_whole, d.span_counterparties].filter(x => x !== null && x !== undefined);
  return xs.length ? Math.max(...xs) : null;
};
// B2's dry cell D1 on six seeds and 400 rounds: passive flow, uneven drift,
// five defectors at fixed places, noise "more". From each link's kept rounds
// alone, not from the engine's clock, is worked out what each clock should
// do: start at the first close whose window record is below zero (point 20),
// turn where the window stands at zero or above to the end (point 21), and
// take the counterparties' span at any end below zero (point 22).
const D1OV = { topology: 'random', p_link: 0.2, m: 5, s: 0.5, sigma_s: 1, sigma_r: 1, k: 0.05, drift_uneven: [0.06, 0.2] };
const DEF = { 3: 'D', 8: 'D', 12: 'D', 17: 'D', 20: 'D' };
const allU = Object.fromEntries(Array.from({ length: 20 }, (_, i) => [String(i + 1), DEF[i + 1] ?? 'U']));
const b2worlds = [];
for (const seed of [2000000, 2000001, 2000002, 2000003, 2000004, 2000005]) {
  for (const types of [DEF, allU]) { const w = nine('network', D1OV, types, seed); w.runTo(400); b2worlds.push(w); }
}
// each close a configuration was open at: [time, the window record then]
function closesOf(w, c) {
  const R = w.p.round, W = w.p.w, out = [];
  const tEnd = w.time();
  const last = c.end ?? tEnd;
  // rounds whose close came while it was open: close of round r at (r + 1) R
  const first = Math.floor(c.start / R + 1e-9);
  for (let r = first; (r + 1) * R <= last + 1e-9; r++) {
    const T = (r + 1) * R;
    if (!(c.start < T - 1e-9 || (c.start === 0 && T > 0))) continue;
    let tot = 0;
    for (const l of c.linkObjs) {
      const e = l.ends[0] === c.owner ? 1 : 0, hist = [...l.rec[e]];
      if (l.active && w.j === 0) hist.push(l.cur[e]);            // the last round, still in cur at the run's end
      const k = r - l.born;                                       // the index of round r in this link's record
      if (k < 0) continue;
      for (const x of hist.slice(Math.max(0, k - W + 1), k + 1)) tot += x;
    }
    out.push([T, tot]);
  }
  return out;
}
function expected20to22(w, c) {
  const R = w.p.round, cl = closesOf(w, c);
  const tested = cl.filter(([T]) => c.start < T - 1e-9 && T <= (c.end ?? w.time()) + 1e-9);
  const hit = tested.find(([, v]) => v < 0);
  const clock = hit ? Math.max(c.start, hit[0] - R) : null;
  let turn = null, started = false;
  if (clock !== null) for (const [T, v] of tested) {
    if (!started) { started = v < 0; continue; }
    if (v >= 0 && turn === null) turn = T - R; else if (v < 0) turn = null;
  }
  const before = cl.filter(([T]) => T <= (c.end ?? w.time()) + 1e-9);
  return { clock, turn, recEnd: before.length ? before[before.length - 1][1] : 0 };
}
const st = { n: 0, clock: 0, differs: 0, turnN: 0, turn: 0, turned: 0, p22N: 0, p22: 0, applied: 0 };
for (const w of b2worlds) for (const c of w.configs) {
  if (!c.counterparties.length) continue;
  const x = expected20to22(w, c);
  st.n++;
  if ((x.clock === null && c.clockStart === null) || (x.clock !== null && c.clockStart !== null && near(x.clock, c.clockStart, 1e-9))) st.clock++;
  if ((c.would1 ? 1 : 0) !== (x.clock !== null ? 1 : 0) || (c.would1 && x.clock === null)) st.differs++;
  if (c.clockStart === null) continue;
  const s = w.configSummary(c);
  st.turnN++;
  const turnOk = (x.turn === null && c.turn === null) || (x.turn !== null && c.turn !== null && near(x.turn, c.turn.t, 1e-9));
  if (turnOk && (!c.turn || (s.judged === true && near(s.survival_spans * s.span, c.turn.t - c.clockStart, 1e-6)))) st.turn++;
  if (c.turn) st.turned++;
  if (c.end !== null && s.span !== null) {
    st.p22N++;
    // version 1.1, draft 3: only where the counterparties' span, at every
    // sample, is the shorter
    const cpall = s.span_counterparties_every_sample ?? null;
    const want = x.turn === null && x.recEnd < 0 && !(cpall !== null && cpall >= span2314(s));
    const has = s.span_used === 'counterparties (point 22)';
    if (want === has && near(x.recEnd, c.recWEnd, 1e-6)) st.p22++;
    if (has) st.applied++;
  }
}
own('B2.P20', 'each clock starts at the first close whose window record is below zero',
  () => [`${st.n} of ${st.n}`, `${st.clock} of ${st.n} (one round alone would differ on ${st.differs})`, st.clock === st.n && st.differs > 0]);
own('B2.P21', 'a clocked configuration turns where the window stands at zero or above to its end',
  () => [`${st.turnN} of ${st.turnN}, some turned`, `${st.turn} of ${st.turnN}, ${st.turned} turned`, st.turn === st.turnN && st.turned > 0]);
own('B2.P22', "an end below zero by the window takes the counterparties' span, where shorter",
  () => [`${st.p22N} of ${st.p22N}, some applied`, `${st.p22} of ${st.p22N}, ${st.applied} applied`, st.p22 === st.p22N && st.applied > 0]);
// point 21 by hand: two type U operators, 200 and 50, passive flow 0.05,
// m = 5, no noise: the richer's record starts below zero, so the poorer's
// configuration is watched from 0, and turns as the two draw together
own('B2.P21', "a pair drawing together: the poorer's watched from 0, turns, judged to its turn", () => {
  const w = nine('network', { operators: ['R', 'P'], topology: 'ring', m: 5, k: 0.05 }, { R: 'U', P: 'U' });
  w.op('R').E = 200; w.op('P').E = 50;
  for (const c of w.configs) c.mark = w._mark(c.members, c.counterparties, 0, q => q.E);
  w.runTo(200);
  const c = w.configs.find(x => x.owner === w.op('P').i && x.clockStart !== null);
  const x = expected20to22(w, c), s = w.configSummary(c);
  return [{ clock: 0, turned: x.turn }, { clock: c.clockStart, turned: c.turn && c.turn.t, judged: s.judged },
    c.clockStart === 0 && x.turn !== null && c.turn !== null && near(c.turn.t, x.turn, 1e-9) && s.judged === true && s.point_21 !== null];
});
// B2 draft 4, section 4: a made case, a sink whose taxed operators cannot
// cut, to show that the measure can show a sink lasting at all. A ring of
// three type U operators, m = 3, passive flow 0.5, no noise: A and B with
// drift 0.02, C with drift 0.5, each started at its steady stock, 32, 32 and
// 24.32. Each link brings each end 2.24 a round; the flow from A and from B
// to C, 0.5 x 7.68 = 3.84 a round, outweighs it, so their records on their
// links to C, added together, are -3.2 a round, -16 over the window. C's
// configuration is a sink's, watched from round 0, and stands to the end;
// its span is the counterparties', 44 / 3.2 = 13.75; at t = 4,000, 290.9
// spans, judged.
own('B2.SINK', "a made sink, its taxed operators of type U: watched from 0, lasts 290.9 spans", () => {
  const w = nine('network', { operators: ['A', 'B', 'C'], topology: 'ring', k: 0.5 }, { A: 'U', B: 'U', C: 'U' });
  w.op('A').a = 0.02; w.op('B').a = 0.02; w.op('C').a = 0.5;
  w.op('A').E = 32; w.op('B').E = 32; w.op('C').E = 24.32;
  for (const c of w.configs) c.mark = w._mark(c.members, c.counterparties, 0, q => q.E);
  w.runTo(4000);
  const cs = w.configs.filter(c => c.owner === w.op('C').i && c.clockStart !== null);
  const s = cs.length ? w.configSummary(cs[0]) : {};
  return [{ kind: "a sink's", clock: 0, span: 13.75, spans: 290.9, judged: true },
    { kind: s.kind, clock: s.clock_start, span: s.span, spans: s.survival_less_window, judged: s.judged, cuts: w.cuts.length },
    cs.length === 1 && s.kind === "a sink's" && s.clock_start === 0 && s.end === null && near(s.span, 44 / 3.2, 1e-9)
      && near(s.survival_less_window, 4000 * 3.2 / 44, 1e-6) && s.judged === true
      && near(s.counterparties_records_last_w_rounds, -16, 1e-6) && w.cuts.length === 0];
});
// Version 1.1, draft 3: points 19 and 22 only shorten a span, never lengthen
// one. Every configuration with a span, in D1 and its control on six seeds
// and 400 rounds, the hand cases of point 19, and the page's pair still
// standing at t = 5 (point 19) and ended at A's ruin (point 22), where the
// counterparties' span, 25 hours, is the longer.
own('B2.P19-22', 'points 19 and 22 never lengthen a span: shorter taken, longer left', () => {
  const sums = [];
  for (const w of b2worlds) for (const c of w.configs) if (c.clockStart !== null) sums.push(w.configSummary(c));
  for (const seed of SEEDS) {
    const w = nine('network', { operators: Object.keys(P19), topology: 'random', p_link: 1, m: 5, sigma_s: 2, sigma_r: 1 }, P19, seed);
    w.runTo(400);
    for (const c of w.configs) if (c.clockStart !== null) sums.push(w.configSummary(c));
  }
  const quiet = nine('network', { operators: Object.keys(P19), topology: 'random', p_link: 1, m: 5, E0: 200 }, P19);
  quiet.runTo(400);
  for (const c of quiet.configs) if (c.clockStart !== null) sums.push(quiet.configSummary(c));
  const page = {};
  for (const t of [5, 30]) {
    const w = nine('page_charger', {}, { A: 'U', B: 'D' });
    w.runTo(t);
    page[t] = summaryOf(w, 'B', ['A', 'B']);
    sums.push(page[t]);
  }
  let n = 0, longer = 0, shortened = 0, left = 0, bad = 0;
  for (const d of sums) {
    if (!d || !d.span) continue;
    n++;
    const s14 = span2314(d), cpall = d.span_counterparties_every_sample ?? null;
    if (d.span > s14 * (1 + 1e-12)) longer++;
    if (d.span_used === 'counterparties (point 19)' || d.span_used === 'counterparties (point 22)') {
      shortened++;
      if (!(cpall !== null && cpall < s14 && near(d.span, cpall, 1e-12 * cpall))) bad++;
    } else if (d.point_19_not_applied || d.point_22_not_applied) {
      left++;
      if (!(cpall !== null && cpall >= s14 && near(d.span, s14, 1e-12 * s14))) bad++;
    } else if (!near(d.span, s14, 1e-12 * s14)) bad++;
  }
  const p5 = page[5], p30 = page[30];
  const pageOk = [p5, p30].every(x => near(x.span, 200 / 18, 1e-6) && x.span_used === 'whole' && near(x.span_counterparties_every_sample, 25, 1e-6))
    && p5.point_19_not_applied === NOT_SHORTER && p30.point_22_not_applied === NOT_SHORTER;
  return [`0 longer of ${n}; some shortened, some left`,
    `${longer} longer of ${n}; ${shortened} shortened, ${left} left; the page's pair ${p30.span.toFixed(4)}, its counterparties' ${(p30.span_counterparties_every_sample ?? NaN).toFixed(4)} left`,
    longer === 0 && bad === 0 && shortened > 0 && left > 0 && pageOk];
});
own('B2.10', 'kinds named: a defector\'s, a sink\'s, an operator alone', () => {
  const kinds = new Set();
  for (const w of b2worlds) for (const c of w.configs) if (c.clockStart !== null) kinds.add(w.configSummary(c).kind);
  const ok = [...kinds].every(k => ["a defector's", "a sink's", 'an operator alone'].includes(k)) && kinds.has('an operator alone') && kinds.has("a defector's");
  return ['named', [...kinds].sort().join(', '), ok];
});

const widths = rows[0].map((_, k) => Math.max(...rows.map(r => r[k].length)));
console.log(`${SPEC_VERSION}\n${CODE_VERSION}\n`);
console.log(['id', 'what', 'expected', 'got', 'result'].map((h, k) => h.padEnd(widths[k])).join('  '));
for (const r of rows) console.log(r.map((x, k) => (k === 4 ? x : x.padEnd(widths[k]))).join('  '));
console.log(`\n${rows.length - failed} of ${rows.length} checks pass.${failed ? ` ${failed} fail.` : ''}`);
process.exit(failed ? 1 : 0);
