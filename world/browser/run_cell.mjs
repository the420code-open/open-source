// run_cell.mjs · runs one cell of the world in the second engine, under Node.
//
//   node world/browser/run_cell.mjs CELL.json --seeds 100001-100100 --out DIR
//
// The cell file is the reference's own (world/reference/cells): the setting,
// its overrides, the network, the types, entry and the label. Every cell runs
// 4,000 rounds (Part Nine, point 4) unless it is a cell outside every
// hypothesis that names its own "rounds". The defectors' places are drawn with
// the seed, from this engine's own generator: the two engines never share
// random numbers (Part Seven).
//
// It writes packet.jsonl (a head, then one line per seed) and summary.json,
// with B1's measure as the reference gives it: for each seed, the largest
// survival in spans, less the record window where at least one counterparty
// is type C, among the configurations a defector is in, from their clock's
// start; then the mean across the seeds, its standard error, the largest seed
// and the zone. A defector that starts with no live link is reported, and not
// watched. A seed with any watched configuration too long to judge in this run
// is left out whole, counted and reported; so is a seed left with nothing to
// watch (B1, section 7, draft 3); if more than one seed in ten is left out,
// the two counted together, the cell settles nothing. Each seed's value is kept, so a second
// hundred can be pooled with the first (B1's section 9).
//
// Terms: CC0 1.0 Universal.

import { World, resolveParams, makeRng, SPEC_VERSION, CODE_VERSION } from './engine.mjs';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const sha = p => createHash('sha256').update(readFileSync(p)).digest('hex');

function parseSeeds(text) {
  const out = [];
  for (const part of text.split(',')) {
    if (part.includes('-')) {
      const [a, b] = part.split('-').map(Number);
      for (let s = a; s <= b; s++) out.push(s);
    } else out.push(Number(part));
  }
  return out;
}

// B1, section 10: a control cell is never printed as "fires" or "holds". It
// is printed as "a defector lasts" or "no defector lasts", with "control:
// fires nothing" beside it. A control is a cell that says so, or one whose
// every host is of type U.
const CONTROL_WORDS = { fires: 'a defector lasts', holds: 'no defector lasts' };
const FIRES_NOTHING = 'control: fires nothing';
export const isControl = cell => !!cell.control || (cell.types && cell.types.hosts === 'U');
export function controlWords(m) {
  if (m && 'zone' in m) { m.zone = CONTROL_WORDS[m.zone] ?? m.zone; m.control = FIRES_NOTHING; }
  return m;
}

function zone(mean, se, line = 3) {
  if (mean + 2 * se <= line) return 'holds';
  if (mean - 2 * se > line) return 'fires';
  return 'settles nothing';
}

// The cell's types, by name. "hosts" and "defectors": the defectors' places
// are drawn with the seed; otherwise the cell names each operator's type.
function typesFor(cell, names, seed) {
  const T = cell.types || {};
  if (!('hosts' in T)) return { ...T };
  const types = Object.fromEntries(names.map(n => [n, T.hosts]));
  let d = T.defectors || 0;
  if ('defector_share' in T) d = Math.round(T.defector_share * names.length);
  const rng = makeRng(seed, 5);
  const idx = names.map((_, i) => i);
  for (let k = 0; k < d; k++) {                       // a partial shuffle: d places, none twice
    const j = k + Math.floor(rng.uniform() * (idx.length - k));
    [idx[k], idx[j]] = [idx[j], idx[k]];
    types[names[idx[k]]] = 'D';
  }
  return types;
}

function paramsFor(cell, tv) {
  const ov = { ...(cell.overrides || {}) };
  if (cell.topology) ov.topology = cell.topology;
  if (cell.p !== undefined) ov.p_link = cell.p;
  if (cell.N !== undefined) ov.N = cell.N;
  if (cell.operators) ov.operators = cell.operators;
  if (cell.rounds !== undefined) ov.horizon = cell.rounds;
  if (cell.entry) ov.open = { ...cell.entry };
  if (cell.drift && cell.drift.uneven) throw new Error('uneven drift is not yet in this runner');
  return resolveParams(tv.settings[cell.setting], ov);
}

export function measure(seeds, chosen, key) {
  const by = new Map(seeds.map(s => [s, []]));
  for (const c of chosen) if (c.span) by.get(c.seed).push(c);
  const vals = [], leftOut = [], perSeed = {};
  let without = 0;
  for (const s of seeds) {
    const cs = by.get(s);
    if (!cs.length) { without++; continue; }
    const tooLong = cs.filter(c => c.judged === false);
    if (tooLong.length) {
      leftOut.push({ seed: s, too_long_to_judge: tooLong.map(c => ({ cfg: c.id, owner: c.operator, span: c.span, bound: c.bound, survival_spans_so_far: c[key] })) });
      continue;
    }
    const v = Math.max(...cs.map(c => c[key]));
    vals.push(v);
    perSeed[s] = v;
  }
  const n = vals.length;
  const out = { seeds: seeds.length, seeds_measured: n, seeds_without_a_watched_configuration: without, seeds_left_out: leftOut.length, left_out: leftOut, seeds_not_in_the_mean: leftOut.length + without, per_seed: perSeed };
  if (n) {
    const mean = vals.reduce((a, b) => a + b, 0) / n;
    const se = n > 1 ? Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1)) / Math.sqrt(n) : NaN;
    Object.assign(out, { mean, se, largest_seed: Math.max(...vals), zone: zone(mean, Number.isFinite(se) ? se : Infinity) });
  }
  // B1, section 7: a seed left with nothing to watch counts towards the one in ten
  if ((leftOut.length + without) * 10 > seeds.length) {
    out.zone = 'settles nothing';
    out.why = `${leftOut.length + without} of ${seeds.length} seeds left out, more than one in ten: ${leftOut.length} too long to judge, ${without} with nothing to watch`;
  } else if (!n) {
    out.zone = 'settles nothing';
    out.why = 'no seed has a watched configuration with a span';
  }
  return out;
}

function main() {
  const argv = process.argv.slice(2);
  const cellPath = argv[0];
  const opt = k => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
  if (!cellPath || !opt('--seeds') || !opt('--out')) {
    console.error('usage: node run_cell.mjs CELL.json --seeds A-B --out DIR');
    process.exit(2);
  }
  const cell = JSON.parse(readFileSync(cellPath, 'utf-8'));
  const tvPath = join(HERE, '..', 'test-values.json');
  const tv = JSON.parse(readFileSync(tvPath, 'utf-8'));
  const seeds = parseSeeds(opt('--seeds'));
  const out = opt('--out');
  mkdirSync(out, { recursive: true });
  const params = paramsFor(cell, tv);
  const head = {
    kind: 'world run', engine: 'the second engine (browser engine, under Node)', label: cell.label || '', cell: cell.id,
    specification: SPEC_VERSION, specification_sha256: sha(join(HERE, '..', 'spec', 'world_spec_v1.0.md')),
    code: CODE_VERSION, code_sha256: createHash('sha256').update(readFileSync(join(HERE, 'engine.mjs'))).update(readFileSync(join(HERE, 'run_cell.mjs'))).digest('hex'),
    parameters: params, cell_definition: cell, seeds,
    generator: "the engine's own (xoshiro128**, seeded by splitmix32), streams per seed: 1 stock noise, 2 reading noise, 3 random links, 4 entry, 5 the defectors' places",
    node: process.version, date: new Date().toISOString().slice(0, 10),
    ...(isControl(cell) ? { control: FIRES_NOTHING } : {}),
  };
  const t0 = Date.now();
  const lines = [JSON.stringify(head)];
  const chosen = [], unc = [], leftOut = [];
  let nDef = 0, ruined = 0, passed = [], clockedAll = 0;
  for (const seed of seeds) {
    const names = params.operators ? params.operators.slice() : Array.from({ length: params.N }, (_, i) => String(i + 1));
    const types = typesFor(cell, names, seed);
    const w = new World(params, { types, seed }).run();
    const r = w.report();
    const defs = w.ops.filter(o => o.type === 'D');
    nDef += defs.length;
    ruined += defs.filter(o => !o.alive).length;
    for (const o of defs) passed.push(r.defectors[o.name]);
    if (r.defectors_with_no_live_link_at_start.length) unc.push({ seed, defectors: r.defectors_with_no_live_link_at_start });
    if (r.links_between_two_defectors_left_out.length) leftOut.push({ seed, links: r.links_between_two_defectors_left_out });
    const clocked = r.configurations.filter(s => s.clock_start !== null);
    clockedAll += clocked.length;
    for (const s of clocked) if (s.watched_b1) chosen.push({ ...s, seed });
    lines.push(JSON.stringify({
      seed, defectors: defs.map(o => o.name), defectors_with_no_live_link_at_start: r.defectors_with_no_live_link_at_start,
      links_between_two_defectors_left_out: r.links_between_two_defectors_left_out,
      ruins: r.ruins, cuts: r.cuts.length, configurations: clocked,
      standing: Object.fromEntries(w.ops.filter(o => o.alive).map(o => [o.name, o.E])),
    }));
  }
  const seconds = (Date.now() - t0) / 1000;
  writeFileSync(join(out, 'packet.jsonl'), lines.join('\n') + '\n');
  const timed = chosen.filter(c => c.span);
  const summary = {
    label: cell.label || '', cell: cell.id, engine: head.engine, code: CODE_VERSION, specification: SPEC_VERSION, seeds: seeds.length,
    B1: {
      watched: "configurations with a defector in them, from their clock's start; a defector that starts with no live link is reported, and not watched",
      configurations: chosen.length,
      no_span: chosen.length - timed.length,
      too_long_to_judge: timed.filter(c => c.judged === false).length,
      point_19: { applied: chosen.filter(c => c.span_used === 'counterparties (point 19)').length,
        applies_with_no_span: chosen.filter(c => c.point_19 === 'applies, but the counterparties lost at no sample: no span').length },
      measure: measure(seeds, chosen, 'survival_less_window'),
      for_reference_without_the_window: measure(seeds, chosen, 'survival_spans'),
    },
    defectors: { defectors: nDef, ruined, configurations_passed_through: { mean: passed.length ? passed.reduce((a, b) => a + b, 0) / passed.length : null, max: passed.length ? Math.max(...passed) : null } },
    premise_check: {
      defectors: nDef,
      defectors_coupled_at_start: nDef - unc.reduce((a, u) => a + u.defectors.length, 0),
      defectors_with_no_live_link_at_start_reported_not_watched: unc,
      seeds_with_every_defector_coupled: seeds.length - unc.length,
      links_between_two_defectors_left_out: { seeds: leftOut.length, links: leftOut.reduce((a, x) => a + x.links.length, 0), where: leftOut },
    },
    clocked_configurations: clockedAll,
    run: { rounds: params.horizon, seconds },
    files: { 'packet.jsonl': sha(join(out, 'packet.jsonl')) },
  };
  if (isControl(cell)) {
    summary.control = FIRES_NOTHING;
    controlWords(summary.B1.measure);
    controlWords(summary.B1.for_reference_without_the_window);
  }
  writeFileSync(join(out, 'summary.json'), JSON.stringify(summary, null, 1));
  const m = summary.B1.measure;
  console.log(JSON.stringify({ cell: cell.id, seeds: seeds.length, mean: m.mean, se: m.se, largest_seed: m.largest_seed, zone: m.zone, ...(m.control ? { control: m.control } : {}), seconds }, null, 1));
}

// run as a script, not when imported by the checks
if (process.argv[1] && resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) main();
