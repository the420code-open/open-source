// Dry only, never a result. The second engine's drawn networks alone, at round 0, with no run: for each seed, a World
// built as run_cell.mjs builds it (typesFor and paramsFor copied word for word from run_cell.mjs at the tag), then
// read. Counts per seed: operators with no live link, careful givers whose every link is to a defector, defectors
// with a link, links between two careful givers, links between a careful giver and a defector, links left out.
//
//   node drawing_second.mjs BROWSER_DIR CELL.json FIRST LAST OUT.json
import { pathToFileURL } from 'node:url';
import { resolve, join } from 'node:path';
import { readFileSync, writeFileSync } from 'node:fs';

const [dir, cellPath, first, last, out] = process.argv.slice(2);
const { World, resolveParams, makeRng } = await import(pathToFileURL(resolve(dir, 'engine.mjs')).href);
const cell = JSON.parse(readFileSync(cellPath, 'utf-8'));
const tv = JSON.parse(readFileSync(join(dir, '..', 'test-values.json'), 'utf-8'));

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

const params = paramsFor(cell, tv);
const rows = [];
for (let seed = Number(first); seed <= Number(last); seed++) {
  const names = params.operators ? params.operators.slice() : Array.from({ length: params.N }, (_, i) => String(i + 1));
  const types = typesFor(cell, names, seed);
  const w = new World(params, { types, seed });
  const deg = new Map(w.ops.map(o => [o.i, []]));
  let cc = 0, cd = 0;
  for (const l of w.liveLinks) {
    const [i, j] = l.ends; deg.get(i).push(j); deg.get(j).push(i);
    const k = [w.ops[i].type, w.ops[j].type].sort().join('');
    if (k === 'CC') cc++; else cd++;
  }
  let alone = 0, cAllD = 0, dLinked = 0;
  for (const o of w.ops) {
    const nb = deg.get(o.i);
    if (!nb.length) alone++;
    else if (o.type === 'C' && nb.every(q => w.ops[q].type === 'D')) cAllD++;
    if (o.type === 'D' && nb.length) dLinked++;
  }
  rows.push([alone, cAllD, dLinked, cc, cd, (w.linksLeftOut || []).length]);
}
writeFileSync(out, JSON.stringify({ engine: 'second', cell: cell.id, first: Number(first), last: Number(last),
  columns: ['alone', 'careful_givers_every_link_to_a_defector', 'defectors_linked', 'links_CC', 'links_CD', 'links_left_out'], rows }));
console.log('drawn:', rows.length, 'seeds');
