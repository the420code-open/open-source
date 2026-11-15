// check.mjs · runs every case and every check in ../test-values.json
// against engine.mjs, then the engine's own checks of Part Nine (draft 4).
// One line per check; exit code 1 if any fails.
//
//   node check.mjs
//
// Terms: CC0 1.0 Universal.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { World, resolveParams, formulas, SPEC_VERSION, CODE_VERSION } from './engine.mjs';

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
    { used: s.span_used, stock: s.stock_above_ruin, loss: s.net_loss_per_round, span: s.span },
    s.span_used === 'counterparties' && s.span_whole === null && near(s.stock_above_ruin, 80, 1e-9)
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

const widths = rows[0].map((_, k) => Math.max(...rows.map(r => r[k].length)));
console.log(`${SPEC_VERSION}\n${CODE_VERSION}\n`);
console.log(['id', 'what', 'expected', 'got', 'result'].map((h, k) => h.padEnd(widths[k])).join('  '));
for (const r of rows) console.log(r.map((x, k) => (k === 4 ? x : x.padEnd(widths[k]))).join('  '));
console.log(`\n${rows.length - failed} of ${rows.length} checks pass.${failed ? ` ${failed} fail.` : ''}`);
process.exit(failed ? 1 : 0);
