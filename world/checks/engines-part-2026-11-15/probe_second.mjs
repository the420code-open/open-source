// Dry only, never a result. Runs the second engine's own runner, run_cell.mjs, unchanged, and reads each World
// right after its run() returns, through a wrapper on World.prototype.run that calls the engine's own run and then
// only reads: every configuration, every link with how it ended and who cut it, every cut and ruin. One line per
// seed to PROBE. The engine's numbers, the packet and the summary are run_cell.mjs's own.
//
//   node probe_second.mjs BROWSER_DIR CELL.json SEEDS OUT_DIR PROBE.jsonl.gz
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { createWriteStream } from 'node:fs';
import { createGzip } from 'node:zlib';

const [dir, cell, seeds, out, probe] = process.argv.slice(2);
const eng = await import(pathToFileURL(resolve(dir, 'engine.mjs')).href);
const lines = [];
const run = eng.World.prototype.run;
eng.World.prototype.run = function (...a) {
  const r = run.apply(this, a);
  const nm = i => this.ops[i].name;
  lines.push(JSON.stringify({
    seed: this.seed,
    ops: this.ops.map(o => ({ name: o.name, type: o.type, alive: o.alive, ruin_t: o.ruinTime })),
    left_out: (this.linksLeftOut || []).map(x => x.map(String)),
    ruins: this.ruins.map(x => ({ op: x.operator, t: x.time })),
    cuts: this.cuts.map(c => ({ round: c.round, by: c.by, link: c.link })),
    links: this.links.map(l => ({ ends: l.ends.map(nm), born: l.born, end: l.end, cause: l.endCause, cut_by: l.cutBy })),
    cfgs: this.configs.map(c => ({ owner: nm(c.owner), members: c.members.map(nm), start: c.start, end: c.end,
                                   reason: c.endCause, clock: c.clockStart })),
  }));
  return r;
};
const rc = resolve(dir, 'run_cell.mjs');
process.argv = [process.argv[0], rc, cell, '--seeds', seeds, '--out', out];
await import(pathToFileURL(rc).href);
const gz = createGzip(); const f = createWriteStream(probe); gz.pipe(f);
for (const l of lines) gz.write(l + '\n');
gz.end();
await new Promise(res => f.on('finish', res));
console.log('probe written:', probe, lines.length, 'seeds');
