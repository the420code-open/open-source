// engine.mjs · the world, the second engine.
//
// Written from "Phase 2 · the world · specification · draft 3"
// (13 November 2026) alone, and brought to draft 4 the same way: Part Nine,
// how a run is measured, read from the text and not from the reference.
// Now at version 1.0: the window where at least one counterparty is type C,
// and B1's premise check, seed by seed.
// An ES module with no dependencies: it runs in a browser and under Node.
// One engine; every setting comes in as data.
//
// Terms: CC0 1.0 Universal.

export const SPEC_VERSION = 'Phase 2 · the world · specification · version 1.0 (13 November 2026)';
export const CODE_VERSION = 'world browser engine 1.5.1';

// Numerical floor for step 8. A new stock within this distance above the
// ruin line counts as at it. Without it, the rounding of many sums of dt
// decides at random whether a ruin that falls exactly on a substep's end
// is seen in that substep or one substep late (and a late ruin means one
// more substep of giving, which moves the partner's ruin by more than the
// tolerance of Part Six).
export const RUIN_TOLERANCE = 1e-9;

// A net loss counts when it is above zero (Part Nine, point 3), with no
// floor: the text gives none. The same holds for whether a lone operator's
// own net change is a loss (point 1).
export const POINT_19 = "still standing at the end, its counterparties' records on their links to it below zero over the last w rounds: the counterparties' span (Part Nine, point 19)";

// The run's length for every cell of a hypothesis (Part One; Part Nine,
// point 4), in rounds.
export const HORIZON = 4000;

// ---------------------------------------------------------------------------
// Random numbers. sfc32, seeded through splitmix32; one stream per use, so
// that turning a noise on does not move the links or the entries. Engines
// are never expected to share random numbers (Part Seven).

function splitmix32(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x9e3779b9) >>> 0;
    let z = s;
    z = Math.imul(z ^ (z >>> 16), 0x85ebca6b) >>> 0;
    z = Math.imul(z ^ (z >>> 13), 0xc2b2ae35) >>> 0;
    return (z ^ (z >>> 16)) >>> 0;
  };
}

export function makeRng(seed = 1, stream = 0) {
  const mix = splitmix32((Math.floor(Math.abs(seed)) >>> 0) ^ Math.imul((stream + 1) >>> 0, 0x9e3779b1));
  let a = mix(), b = mix(), c = mix(), d = mix();
  const next = () => {
    const t = (((a + b) >>> 0) + d) >>> 0;
    d = (d + 1) >>> 0;
    a = b ^ (b >>> 9);
    b = (c + (c << 3)) >>> 0;
    c = ((c << 21) | (c >>> 11)) >>> 0;
    c = (c + t) >>> 0;
    return t;
  };
  for (let i = 0; i < 16; i++) next();
  let spare = null;
  // Uniform on the open interval (0, 1), 53 bits.
  const uniform = () => ((next() >>> 5) * 67108864 + (next() >>> 6) + 0.5) / 9007199254740992;
  // Standard normal, Box-Muller.
  const normal = () => {
    if (spare !== null) { const z = spare; spare = null; return z; }
    const r = Math.sqrt(-2 * Math.log(uniform()));
    const th = 2 * Math.PI * uniform();
    spare = r * Math.sin(th);
    return r * Math.cos(th);
  };
  return { next, uniform, normal };
}

// ---------------------------------------------------------------------------
// Parameters. Part Three's defaults; a setting and its overrides lie on top.

export const DEFAULTS = Object.freeze({
  operators: null,      // list of names; or N operators named "1".."N"
  N: 6,
  topology: 'ring',     // 'ring' | 'pair' | 'random' | 'none'
  p_link: 0.5,          // random links: each pair linked with probability p
  // open network: { q, n, type, E0, hopper }; closed when null. A newcomer
  // enters every q rounds from round q and offers links to n operators;
  // its type defaults to C. hopper (default true): a defector with no live
  // link offers one link, every q rounds (Part Nine, point 9).
  open: null,
  horizon: HORIZON,     // rounds in a run (Part Nine, point 4); run() stops there
  E0: 50,
  b: 0, a: 0,
  schedule: 'always',   // 'always' (= 'both') | 'turns'
  g: 1, m: 1, c: 0, lam: 0, eps: 0, k: 0,
  E_r: 0, E_max: null,
  round: 1, dt: 0.01,
  s: 0, u_max: null,
  sigma_s: 0, sigma_r: 0,
  w: 5,
  type: 'C',            // type of an operator the case does not name
});

const GIVE_RULES = new Set(['m/(2*lam)', 'm/(2lam)', 'm/2lam', 'm/(2*λ)', 'm/(2λ)', 'm/2λ']);

export function resolveParams(setting = {}, overrides = {}) {
  const p = { ...DEFAULTS, ...setting, ...overrides };
  if (typeof p.g === 'string') {
    const rule = p.g.replace(/\s+/g, '');
    if (!GIVE_RULES.has(rule)) throw new Error(`Unknown give rule: ${p.g}`);
    if (!(p.lam > 0)) throw new Error('The give m/(2*lam) needs lam above zero');
    p.g_rule = p.g;
    p.g = p.m / (2 * p.lam);
  }
  if (p.schedule === 'both') p.schedule = 'always';
  if (p.open && !(Number.isInteger(p.open.q) && p.open.q >= 1)) {
    throw new Error('An open network needs q, a whole number of rounds, at least 1');
  }
  return p;
}

// ---------------------------------------------------------------------------
// AP02's closed forms (Part Six, "AP02's results: at their own formulas").

export const formulas = {
  // Theorem I.1: dE/dt = -aE, no giving.
  drift: ({ a, E0, t }) => ({ E: E0 * Math.exp(-a * t) }),
  // Theorem II.1: least-cost point and effort.
  least_cost_point: ({ a, lam }) => ({ x: 1 / (1 + lam * a * a) }),
  least_cost_effort: ({ a, lam }) => {
    const u = a / (1 + lam * a * a);
    return { u, u1: u, u2: u };
  },
  // Theorem III.1: the event horizon.
  event_horizon: ({ a, u_max }) => ({ x_H: u_max / a }),
  // Theorem IV.1: mean cost of effort, lam * u^2, over a schedule.
  mean_effort_cost: ({ lam, schedule }) => ({
    cost: schedule.reduce((s, u) => s + lam * u * u, 0) / schedule.length,
  }),
  // Theorem VI.1: two operators, own effort at its least-cost level, a
  // passive link k. Steady state of
  //   0 = -a1 E1 + u1 + k (E2 - E1),  0 = -a2 E2 + u2 + k (E1 - E2).
  coupled_steady_state: ({ a1, a2, lam, k }) => {
    const u1 = a1 / (1 + lam * a1 * a1), u2 = a2 / (1 + lam * a2 * a2);
    const A = a1 + k, B = a2 + k, det = A * B - k * k;
    const E1 = (u1 * B + k * u2) / det, E2 = (A * u2 + k * u1) / det;
    return { u1, u2, E1, E2, flow: k * (E1 - E2) };
  },
};

// ---------------------------------------------------------------------------
// The world.

export class World {
  constructor(params, opts = {}) {
    const p = this.p = params;
    this.seed = opts.seed ?? p.seed ?? 1;
    this.logOn = !!opts.log;
    this.log = [];
    this.rngStock = makeRng(this.seed, 1);
    this.rngRead = makeRng(this.seed, 2);
    this.rngTopo = makeRng(this.seed, 3);
    this.rngEntry = makeRng(this.seed, 4);

    this.nsub = Math.round(p.round / p.dt);
    if (!(this.nsub >= 1) || Math.abs(this.nsub * p.dt - p.round) > 1e-9 * p.round) {
      throw new Error('A round must be a whole number of substeps');
    }

    this.r = 0;            // the round in progress (or next to start)
    this.j = 0;            // the next substep within it
    this.ops = [];
    this.links = [];
    this.liveLinks = [];
    this.configs = [];
    this.cuts = [];
    this.ruins = [];
    this.entries = [];
    this.hops = [];        // a lone defector's offers (Part Nine, point 9)
    this.trace = [];       // stocks at every round's start

    const types = opts.types || {};
    const names = p.operators ? p.operators.slice()
      : Array.from({ length: p.N }, (_, i) => String(i + 1));
    for (const n of names) this._addOperator(n, types[n] ?? p.type, p.E0);
    this.linksLeftOut = [];  // drawn links that would join two defectors
    this._buildTopology();
    this._refreshLive();
    // B1's premise check, seed by seed: a defector is coupled if it starts
    // with at least one live link. One that starts with none draws on no
    // one: it is reported, and not watched.
    this.uncoupledAtStart = new Set(this.ops.filter(o => o.type === 'D' && !this.linksOf(o.i).length).map(o => o.i));

    this._emit({
      kind: 'head', spec: SPEC_VERSION, code: CODE_VERSION, seed: this.seed,
      params: { ...p }, types: Object.fromEntries(this.ops.map(o => [o.name, o.type])),
    });
    for (const o of this.ops) this._openConfig(o, 0, q => q.E);
  }

  // ---- building ----------------------------------------------------------

  _addOperator(name, type, E0) {
    if (!['C', 'U', 'D'].includes(type)) throw new Error(`Unknown type ${type}`);
    const o = {
      i: this.ops.length, name, type, E: E0, alive: true, ruinTime: null,
      s: this.p.s, readings: [], readingRounds: [], slope: null, declining: false,
      Emin: E0, Emax: E0, config: null,
    };
    this.ops.push(o);
    return o;
  }

  _link(i, j) {
    const l = {
      id: this.links.length, ends: [i, j], born: this.r, live: true, active: true,
      end: null, endCause: null, cutBy: [],
      g: [0, 0], inc: [0, 0],
      rec: [[], []],              // per round: received less spent, each end
      recSum: [0, 0],             // the closed rounds of rec, added up
      cur: [0, 0],
      received: [0, 0], spent: [0, 0],   // totals
    };
    this.links.push(l);
    return l;
  }

  // No link joins two defectors: nothing passes between them, since neither
  // gives. A drawn link that would join two is left out, after its draw, so
  // the seed's random numbers are drawn as before.
  _drawn(i, j) {
    if (this.ops[i].type === 'D' && this.ops[j].type === 'D') this.linksLeftOut.push([this.ops[i].name, this.ops[j].name]);
    else this._link(i, j);
  }

  _buildTopology() {
    const n = this.ops.length, t = this.p.topology;
    if (t === 'none') return;
    if (t === 'pair') {
      if (n !== 2) throw new Error('A pair needs two operators');
      this._drawn(0, 1);
    } else if (t === 'ring') {
      if (n === 2) this._drawn(0, 1);
      else if (n >= 3) for (let i = 0; i < n; i++) this._drawn(i, (i + 1) % n);
    } else if (t === 'random') {
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        if (this.rngTopo.uniform() < this.p.p_link) this._drawn(i, j);
      }
    } else throw new Error(`Unknown topology ${t}`);
  }

  _refreshLive() { this.liveLinks = this.links.filter(l => l.live); }

  _emit(ev) { if (this.logOn) this.log.push(ev); }

  toJSONL() { return this.log.map(e => JSON.stringify(e)).join('\n') + '\n'; }

  // ---- reading the world -------------------------------------------------

  time() { return this.r * this.p.round + this.j * this.p.dt; }

  op(name) { return this.ops.find(o => o.name === name); }

  linksOf(i) { return this.liveLinks.filter(l => l.ends[0] === i || l.ends[1] === i); }

  counterparties(i) {
    return this.linksOf(i).map(l => (l.ends[0] === i ? l.ends[1] : l.ends[0])).sort((x, y) => x - y);
  }

  stockAt(name, t) {
    const o = this.op(name);
    if (Math.abs(t - this.time()) < 1e-9) return o.E;
    const row = this.trace.find(x => Math.abs(x.t - t) < 1e-9);
    if (!row) throw new Error(`No stock kept at t = ${t}`);
    return row.E[o.i];
  }

  // ---- running -------------------------------------------------------------

  step() {
    if (this.j === 0) this._startRound();
    this._substep();
    this.j += 1;
    if (this.j === this.nsub) { this.j = 0; this.r += 1; this._endRound(); }
  }

  runRound() { do this.step(); while (this.j !== 0); }

  runTo(T) {
    while (this.time() < T - 1e-9) this.step();
  }

  // The whole run: to the horizon, 4,000 rounds unless the setting says
  // otherwise. A closed world in which everyone is ruined stops early, since
  // nothing in it can move again; an open one runs on, for its newcomers.
  run(T = this.p.horizon * this.p.round) {
    while (this.time() < T - 1e-9 && (this.p.open || !this.allRuined())) this.step();
    return this;
  }

  allRuined() { return this.ops.every(o => !o.alive); }

  // ---- the start of a round: steps 1 to 4 ----------------------------------

  _startRound() {
    const p = this.p, r = this.r, t = r * p.round;
    this.trace.push({ t, E: Float64Array.from(this.ops, o => o.E) });

    // 1. Records close. (Each configuration's round closed with the round's
    // last substep, in _endRound.)
    if (r > 0) {
      for (const l of this.links) {
        if (!l.active) continue;
        for (let e = 0; e < 2; e++) { l.rec[e].push(l.cur[e]); l.recSum[e] += l.cur[e]; }
        l.cur = [0, 0];
        if (!l.live) l.active = false;
      }
    }

    // 2. Readings.
    for (const o of this.ops) {
      if (!o.alive) continue;
      const z = p.sigma_r > 0 ? p.sigma_r * this.rngRead.normal() : 0;
      o.readings.push(o.E + z);
      o.readingRounds.push(r);
    }

    // 3. Gradients: least-squares line through the last w readings.
    for (const o of this.ops) {
      if (!o.alive) continue;
      const n = Math.min(p.w, o.readings.length);
      if (n < 2) { o.slope = null; o.declining = false; continue; }
      const ys = o.readings.slice(-n), xs = o.readingRounds.slice(-n);
      const mx = xs.reduce((s, x) => s + x, 0) / n, my = ys.reduce((s, y) => s + y, 0) / n;
      let sxy = 0, sxx = 0;
      for (let k = 0; k < n; k++) { sxy += (xs[k] - mx) * (ys[k] - my); sxx += (xs[k] - mx) ** 2; }
      o.slope = sxy / sxx;
      o.declining = o.slope < 0;
    }

    // 4. Reviews and cuts. All cuts take effect together.
    const before = this.liveLinks;     // as the round just ended left them
    const toCut = new Map();
    for (const o of this.ops) {
      if (!o.alive || o.type !== 'C') continue;
      for (const l of this.linksOf(o.i)) {
        const e = l.ends[0] === o.i ? 0 : 1;
        const n = l.rec[e].length;
        let win = 0;
        if (o.declining) { if (n >= 1) win = Math.min(p.w, n); }   // premise (i)
        else if (n >= p.w) win = p.w;                               // premise (ii)
        if (!win) continue;
        const record = l.rec[e].slice(-win);
        const sum = record.reduce((s, x) => s + x, 0);
        if (sum < 0) {                                              // premise (iii)
          const cut = {
            round: r, time: t, by: o.name, link: l.ends.map(q => this.ops[q].name), linkId: l.id,
            record_rounds: win, record, sum, declining: o.declining,
          };
          this.cuts.push(cut);
          this._emit({ kind: 'cut', ...cut });
          if (!toCut.has(l)) toCut.set(l, []);
          toCut.get(l).push(o.name);
        }
      }
    }
    for (const [l, by] of toCut) { l.live = false; l.end = t; l.endCause = 'cut'; l.cutBy = by; }
    if (toCut.size) this._refreshLive();

    // Entry, in an open network: after the cuts, before anything moves; then
    // the lone defectors' offers (Part Nine, point 9).
    if (p.open && r > 0 && r % p.open.q === 0) {
      this._entry(t);
      if (p.open.hopper !== false) this._hops(t);
    }

    // A link keeps a record for this round only if it is live as the round moves.
    for (const l of this.links) l.active = l.live;

    // A configuration that ends here takes its last sample as it was, before
    // the cuts and the new links.
    let Rbefore = null;
    this._refreshConfigs(t, () => (Rbefore ??= this._rates(before, q => q.E)));

    // The round's start (Part Nine, point 3): every configuration's net
    // change, after the round's cuts, at the gives the round begins with.
    this._setGives(this.liveLinks, r);
    const R = this._rates(this.liveLinks, q => q.E);
    for (const o of this.ops) if (o.alive && o.config) this._sample(o.config, t, R);

    if (this.logOn) {
      for (const o of this.ops) {
        this._emit({
          kind: 'round', round: r, operator: o.name, type: o.type, alive: o.alive, E: o.E,
          reading: o.alive ? o.readings[o.readings.length - 1] : null,
          slope: o.alive ? o.slope : null, declining: o.alive ? o.declining : null,
          links: this.counterparties(o.i).map(q => this.ops[q].name),
        });
      }
    }
  }

  // Part Nine, point 9: a newcomer enters after the round's cuts and offers
  // links to n operators chosen with the seed. It took no reading this round,
  // so its first is the round after.
  _entry(t) {
    const p = this.p, op = p.open;
    let k = this.ops.length + 1;
    while (this.op(String(k))) k += 1;
    const o = this._addOperator(String(k), op.type ?? 'C', op.E0 ?? p.E0);
    const pool = this.ops.filter(q => q.alive && q !== o);
    for (let x = pool.length - 1; x > 0; x--) {          // shuffle, with the seed
      const y = Math.floor(this.rngEntry.uniform() * (x + 1));
      [pool[x], pool[y]] = [pool[y], pool[x]];
    }
    const offered = pool.slice(0, op.n ?? 2), accepted = [], refused = [];
    for (const q of offered) {
      const no = this._refusal(o, q);
      if (no) { refused.push({ operator: q.name, by: no.by, reason: no.reason }); continue; }
      this._link(o.i, q.i);
      accepted.push(q.name);
    }
    this._refreshLive();
    const ev = { round: this.r, time: t, operator: o.name, type: o.type, offered: offered.map(q => q.name), accepted, refused };
    this.entries.push(ev);
    this._emit({ kind: 'entry', ...ev });
  }

  // Part Nine, point 9: in the entry setting, a defector left with no live
  // link offers a link to one operator, chosen with the seed, every q rounds.
  _hops(t) {
    for (const d of this.ops.slice()) {
      if (!d.alive || d.type !== 'D' || this._linkCount(d.i)) continue;
      const pool = this.ops.filter(q => q.alive && q !== d);
      if (!pool.length) continue;
      const q = pool[Math.floor(this.rngEntry.uniform() * pool.length)];
      // nothing would pass between two defectors, so no link joins them
      const no = q.type === 'D' ? { by: null, reason: 'no link joins two defectors' } : this._refusal(d, q);
      if (!no) this._link(d.i, q.i);
      const ev = { round: this.r, time: t, operator: d.name, to: q.name, accepted: !no };
      if (no) { ev.refused_by = no.by; ev.reason = no.reason; }
      this.hops.push(ev);
      this._emit({ kind: 'hop', ...ev });
    }
    this._refreshLive();
  }

  // Why a new link between `from` and `to` is refused, or null if both ends
  // accept. Each end, `to` first:
  //   the record (point 9): a type C refuses an operator whose counterparties'
  //   records on their links to it, added together over its whole record,
  //   are below zero;
  //   capacity (point 10): an operator that gives accepts only while its
  //   capacity still covers the default give on every link, the new one
  //   included. A defector gives nothing, so its capacity never binds.
  _refusal(from, to) {
    const p = this.p;
    for (const [x, y] of [[to, from], [from, to]]) {
      if (x.type === 'C' && this._wholeRecord(y) < 0) return { by: x.name, reason: 'record' };
      if (x.type !== 'D' && p.u_max != null && (this._linkCount(x.i) + 1) * p.g > p.u_max + 1e-9) {
        return { by: x.name, reason: 'capacity' };
      }
    }
    return null;
  }

  // An operator's whole record, as its counterparties hold it: what each
  // received through its link to o, less what it spent on it, over every
  // round of every link o has had.
  _wholeRecord(o) {
    let sum = 0;
    for (const l of this.links) {
      const e = l.ends[0] === o.i ? 1 : l.ends[1] === o.i ? 0 : -1;
      if (e >= 0) sum += l.recSum[e] + l.cur[e];
    }
    return sum;
  }

  _linkCount(i) {
    let n = 0;
    for (const l of this.links) if (l.live && (l.ends[0] === i || l.ends[1] === i)) n += 1;
    return n;
  }

  _give(o, r) {
    if (!o.alive || o.type === 'D') return 0;
    if (this.p.schedule === 'turns' && r % this.ops.length !== o.i) return 0;
    return this.p.g;
  }

  // Step 5 for the given links in round r: each end's give, by its type and
  // the schedule; capacity scales an operator's gives down in proportion.
  _setGives(links, r) {
    const n = this.ops.length;
    if (!this._tot || this._tot.length !== n) this._tot = new Float64Array(n);
    const total = this._tot;
    total.fill(0);
    for (const l of links) {
      l.g[0] = this._give(this.ops[l.ends[0]], r);
      l.g[1] = this._give(this.ops[l.ends[1]], r);
      total[l.ends[0]] += l.g[0];
      total[l.ends[1]] += l.g[1];
    }
    if (this.p.u_max != null) {
      for (const l of links) for (let e = 0; e < 2; e++) {
        const i = l.ends[e];
        if (total[i] > this.p.u_max) l.g[e] *= this.p.u_max / total[i];
      }
    }
  }

  // Part Nine, point 3: the rate of change of every operator, from the given
  // stocks and the gives now set on the given links, by the terms of step 6
  // without the stock's noise. A stock held at the cap does not rise. Also
  // each end's net rate through each link, the rate of its record.
  _rates(links, Eof) {
    const p = this.p, ops = this.ops;
    const rate = new Float64Array(ops.length), net = new Map();
    for (const o of ops) rate[o.i] = o.s - p.b - p.a * Eof(o);
    for (const l of links) {
      const [i, j] = l.ends, gi = l.g[0], gj = l.g[1];
      const flow = p.k * (Eof(ops[j]) - Eof(ops[i]));            // into i
      const n0 = (p.m * gj + flow) - (p.c * gi + p.lam * gi * gi + p.eps);
      const n1 = (p.m * gi - flow) - (p.c * gj + p.lam * gj * gj + p.eps);
      rate[i] += n0;
      rate[j] += n1;
      net.set(l, [n0, n1]);
    }
    if (p.E_max != null) for (const o of ops) if (rate[o.i] > 0 && Eof(o) >= p.E_max) rate[o.i] = 0;
    return { rate, net };
  }

  // ---- one substep: steps 5 to 9 ---------------------------------------------

  _substep() {
    const p = this.p, ops = this.ops, n = ops.length, r = this.r, dt = p.dt;
    const t0 = r * p.round + this.j * dt;
    const links = this.liveLinks;

    if (!this._buf || this._buf.n !== n) {
      this._buf = { n, rate: new Float64Array(n), Eold: new Float64Array(n), Enew: new Float64Array(n) };
    }
    const { rate, Eold, Enew } = this._buf;
    rate.fill(0);

    // 5. Giving, by type and schedule; capacity scales it down in proportion.
    this._setGives(links, r);

    // 6. The stock moves, all at once, from the values at the substep's start.
    for (const o of ops) if (o.alive) rate[o.i] = o.s - p.b - p.a * o.E;
    for (const l of links) {
      const [i, j] = l.ends, gi = l.g[0], gj = l.g[1];
      const flow = p.k * (ops[j].E - ops[i].E);              // into i
      const in0 = p.m * gj + flow, out0 = p.c * gi + p.lam * gi * gi + p.eps;
      const in1 = p.m * gi - flow, out1 = p.c * gj + p.lam * gj * gj + p.eps;
      rate[i] += in0 - out0;
      rate[j] += in1 - out1;
      l.inc[0] = dt * (in0 - out0);
      l.inc[1] = dt * (in1 - out1);
      // 9. Records: what each end received and spent in the substep.
      l.cur[0] += l.inc[0]; l.cur[1] += l.inc[1];
      l.received[0] += dt * in0; l.received[1] += dt * in1;
      l.spent[0] += dt * out0; l.spent[1] += dt * out1;
    }
    const sq = Math.sqrt(dt);
    for (const o of ops) {
      Eold[o.i] = o.E;
      if (!o.alive) { Enew[o.i] = o.E; continue; }
      let e = o.E + dt * rate[o.i];
      if (p.sigma_s > 0) e += p.sigma_s * sq * this.rngStock.normal();
      Enew[o.i] = e;
    }

    // 7. The cap.
    if (p.E_max != null) for (const o of ops) if (o.alive && Enew[o.i] > p.E_max) Enew[o.i] = p.E_max;

    // Configuration clocks: the counterparties' records on their links to
    // the configuration's operator, this substep.
    for (const o of ops) {
      const c = o.config;
      if (!o.alive || !c || !c.linkObjs.length) continue;
      for (const l of c.linkObjs) c.accum += l.inc[l.ends[0] === o.i ? 1 : 0];
    }

    // 8. Ruin, with straight-line interpolation of its time within the substep.
    const ruined = [];
    for (const o of ops) {
      if (!o.alive || Enew[o.i] > p.E_r + RUIN_TOLERANCE) continue;
      const drop = Eold[o.i] - Enew[o.i];
      let frac = drop > 0 ? (Eold[o.i] - p.E_r) / drop : 1;
      frac = Math.min(1, Math.max(0, frac));
      ruined.push({ o, tau: t0 + frac * dt });
    }
    for (const o of ops) {
      if (!o.alive) continue;
      o.E = Enew[o.i];
      if (o.E < o.Emin) o.Emin = o.E;
      if (o.E > o.Emax) o.Emax = o.E;
    }
    if (ruined.length) {
      // In time order; ruins at the same instant are taken together, so
      // that no configuration is opened only to end at the moment it opens.
      ruined.sort((x, y) => x.tau - y.tau || x.o.i - y.o.i);
      for (let k = 0; k < ruined.length;) {
        const tau = ruined[k].tau, group = [];
        while (k < ruined.length && ruined[k].tau - tau <= 1e-12) group.push(ruined[k++].o);
        const f = (tau - t0) / dt;
        this._ruin(group, tau, q => Eold[q.i] + f * (Enew[q.i] - Eold[q.i]));
      }
    }
  }

  _ruin(group, tau, Eat) {
    // The world at the instant, before the links end: the last sample of
    // every configuration this ruin ends (Part Nine, point 3).
    const R = this._rates(this.liveLinks, Eat);
    const hit = new Set();
    for (const o of group) {
      o.alive = false;
      o.ruinTime = tau;
      this.ruins.push({ operator: o.name, time: tau });
      this._emit({ kind: 'ruin', operator: o.name, time: tau });
      for (const l of this.liveLinks) {
        if (l.ends[0] !== o.i && l.ends[1] !== o.i) continue;
        l.live = false; l.end = tau; l.endCause = 'ruin';
        hit.add(l.ends[0] === o.i ? l.ends[1] : l.ends[0]);
      }
    }
    this._refreshLive();
    for (const o of group) if (o.config) { this._closeConfig(o.config, tau, 'ruin', R); o.config = null; }
    for (const qi of [...hit].sort((x, y) => x - y)) {
      const q = this.ops[qi];
      if (!q.alive) continue;
      this._closeConfig(q.config, tau, 'counterparty ruined', R);
      this._openConfig(q, tau, Eat);
    }
  }

  // ---- configurations (Part Five, measured by Part Nine) ---------------------
  //
  // A configuration is an operator and its direct counterparties, joined to
  // it by live links; every cut and every new link starts a new one. Its net
  // change is sampled at every round's start and end and at its own end
  // (point 3). Until its clock starts, the samples of the round in progress
  // wait in `pending`, since a clock that starts starts at the round's start.

  _mark(members, cps, t, Eat) {
    let Sw = 0, Sc = 0;
    for (const q of members) Sw += Eat(this.ops[q]);
    for (const q of cps) Sc += Eat(this.ops[q]);
    return { t, Sw, Sc };
  }

  _openConfig(o, t, Eat) {
    const cps = this.counterparties(o.i);
    const members = [o.i, ...cps];
    const c = {
      id: this.configs.length, owner: o.i, members, counterparties: cps,
      sig: cps.join(','), linkObjs: this.linksOf(o.i),
      defended: cps.some(q => this.ops[q].type === 'C'),
      start: t, end: null, endCause: null,
      clockStart: null, stockWhole: null, stockCps: null,
      lossWhole: null, lossCps: null,      // smallest net loss above zero, per unit of time
      lossCpsAll: null,                    // point 19: the counterparties' at every sample, whatever the whole
      pending: [], accum: 0, mark: this._mark(members, cps, t, Eat),
    };
    this.configs.push(c);
    o.config = c;
    // Point 1: an operator alone is a configuration of one, of any type. Its
    // clock starts when it is left alone, if its own net change is a loss.
    if (!cps.length && this._rates([], Eat).rate[o.i] < 0) this._startClock(c, c.mark);
    this._emit({ kind: 'configuration_start', id: c.id, operator: o.name, members: this._names(members), time: t, clock_start: c.clockStart });
    return c;
  }

  _names(idx) { return idx.map(q => this.ops[q].name); }

  _startClock(c, m) {
    const p = this.p;
    c.clockStart = m.t;
    c.stockWhole = m.Sw - c.members.length * p.E_r;
    c.stockCps = c.counterparties.length ? m.Sc - c.counterparties.length * p.E_r : null;
    for (const s of c.pending) this._fold(c, s);
    c.pending = [];
    if (c.counterparties.length) {
      this._emit({ kind: 'clock_start', id: c.id, operator: this.ops[c.owner].name, time: c.clockStart });
    }
  }

  // One sample: the whole's net change, and the counterparties' net change
  // through their links to the operator (point 2). Positive is a gain.
  _sample(c, t, R) {
    let whole = 0, cps = 0;
    for (const q of c.members) whole += R.rate[q];
    for (const l of c.linkObjs) {
      const n = R.net.get(l);
      if (n) cps += n[l.ends[0] === c.owner ? 1 : 0];
    }
    const s = { t, whole, cps };
    if (c.clockStart === null) c.pending.push(s);
    else this._fold(c, s);
  }

  _fold(c, s) {
    if (-s.whole > 0 && (c.lossWhole === null || -s.whole < c.lossWhole)) c.lossWhole = -s.whole;
    // Part Nine, point 14 (draft 5): the counterparties' span applies only where the whole gains
    if (c.counterparties.length && !(-s.whole > 0) && -s.cps > 0 && (c.lossCps === null || -s.cps < c.lossCps)) c.lossCps = -s.cps;
    // Part Nine, point 19: the counterparties' net loss at every sample
    if (c.counterparties.length && -s.cps > 0 && (c.lossCpsAll === null || -s.cps < c.lossCpsAll)) c.lossCpsAll = -s.cps;
  }

  // The clock of a configuration with counterparties starts at the first
  // round in which their records on their links to the operator, added
  // together, are below zero (Part Five); the round's start is its start.
  _clockCheck(c) {
    if (c.clockStart === null && c.counterparties.length && c.accum < 0) this._startClock(c, c.mark);
    c.pending = [];
  }

  // The end of a round: right after its last substep, at the gives it ran
  // with. Every live configuration takes its round's-end sample.
  _endRound() {
    const t = this.r * this.p.round;
    this._setGives(this.liveLinks, this.r - 1);
    const R = this._rates(this.liveLinks, q => q.E);
    for (const o of this.ops) {
      const c = o.config;
      if (!o.alive || !c) continue;
      this._sample(c, t, R);
      this._clockCheck(c);
      c.accum = 0;
      c.mark = this._mark(c.members, c.counterparties, t, q => q.E);
    }
  }

  // R: the world as the configuration last stood, for its end's sample.
  _closeConfig(c, t, cause, R) {
    if (R) this._sample(c, t, R);
    this._clockCheck(c);
    c.end = t;
    c.endCause = cause;
    this._emit({ kind: 'configuration_end', ...this.configSummary(c), cause });
  }

  _refreshConfigs(t, endRates) {
    for (const o of this.ops) {
      if (!o.alive) continue;
      if (!o.config) { this._openConfig(o, t, q => q.E); continue; }
      if (this.counterparties(o.i).join(',') !== o.config.sig) {
        const cause = o.config.linkObjs.some(l => !l.live) ? 'cut' : 'link';
        this._closeConfig(o.config, t, cause, endRates());
        this._openConfig(o, t, q => q.E);
      }
    }
  }

  // A configuration's measures. `now` is the run's end for one still standing.
  //
  // Point 2, the span two ways: where the whole lost at any sample while its
  // clock ran, its span is the whole's stock above the ruin line over the
  // whole's net loss; otherwise, where it gains as a whole, the span is the
  // counterparties' stock above the ruin line over their net loss through
  // their links to the operator. Each loss is taken at its smallest above
  // zero (point 3), each stock when the clock started. Both are reported,
  // and span_used names the one used.
  //
  // Point 5: survival is measured less the record window where the
  // counterparties are defended, that is, where at least one of them is
  // type C; elsewhere nothing is subtracted. Survival less the window is
  // never below zero.
  //
  // Point 4: a configuration that ended is judged. One still standing is
  // judged if its bound has passed, and counts at the run's length; one whose
  // bound has not yet come is "too long to judge in this run": judged false.
  // A configuration with no clock has nothing to judge: judged null.
  configSummary(c, now = this.time()) {
    const p = this.p;
    const spanWhole = c.lossWhole !== null && c.stockWhole !== null ? c.stockWhole / c.lossWhole : null;
    const spanCps = c.lossCps !== null && c.stockCps !== null ? c.stockCps / c.lossCps : null;
    // point 14: the configuration's span is the longest of the spans that applied
    const used14 = spanWhole !== null && spanCps !== null
      ? (spanWhole >= spanCps ? "both applied; the longer, the whole's" : "both applied; the longer, the counterparties'")
      : spanWhole !== null ? 'whole' : spanCps !== null ? 'counterparties' : null;
    const span14 = spanWhole !== null && spanCps !== null ? Math.max(spanWhole, spanCps)
      : spanWhole !== null ? spanWhole : spanCps;
    // Point 19: a configuration still standing at the end, whose
    // counterparties' records on their links to the operator, added together
    // over the last w rounds, are below zero, takes the counterparties' span
    // of point 2: their stock above the ruin line when the clock started, over
    // their smallest net loss through their links to the operator, taken at
    // every sample (point 3). Point 14's span is kept beside it.
    const recW = c.end === null && c.clockStart !== null && c.counterparties.length ? this._cpRecordLastW(c) : null;
    let point19 = null, span19 = null;
    if (span14 !== null && recW !== null && recW < 0) {
      if (c.lossCpsAll !== null && c.stockCps !== null) { span19 = c.stockCps / c.lossCpsAll; point19 = POINT_19; }
      else point19 = 'applies, but the counterparties lost at no sample: no span';
    }
    const used = span19 !== null ? 'counterparties (point 19)' : used14;
    const span = span19 !== null ? span19 : span14;
    const cpsChosen = span19 !== null || (spanCps !== null && (spanWhole === null || spanCps > spanWhole));
    const lossChosen = span19 !== null ? c.lossCpsAll : cpsChosen ? c.lossCps : c.lossWhole;
    const window = c.defended ? p.w * p.round : 0;
    const bound = span !== null ? 3 * span + window : null;
    const elapsed = c.clockStart !== null ? (c.end ?? now) - c.clockStart : null;
    let judged = null;
    if (c.clockStart !== null) {
      judged = c.end !== null ? true : span !== null && now >= c.clockStart + bound - 1e-9;
    }
    const perRound = x => (x === null ? null : x * p.round);
    return {
      id: c.id,
      operator: this.ops[c.owner].name,
      type: this.ops[c.owner].type,
      members: this._names(c.members),
      defended: c.defended,
      has_defector: c.members.some(q => this.ops[q].type === 'D'),
      // B1 watches a configuration a defector is in, unless every defector in
      // it started with no live link
      watched_b1: c.members.some(q => this.ops[q].type === 'D' && !this.uncoupledAtStart.has(q)),
      start: c.start,
      clock_start: c.clockStart,
      span_used: used,
      stock_above_ruin: cpsChosen ? c.stockCps : c.stockWhole,
      net_loss_per_round: perRound(lossChosen),
      span,
      span_whole: spanWhole,
      span_counterparties: spanCps,
      stock_above_ruin_whole: c.stockWhole,
      stock_above_ruin_counterparties: c.stockCps,
      net_loss_whole: perRound(c.lossWhole),
      net_loss_counterparties: perRound(c.lossCps),
      counterparties_records_last_w_rounds: recW,
      point_19: point19,
      ...(span19 !== null ? {
        span_by_point_14: span14, span_used_by_point_14: used14,
        net_loss_counterparties_every_sample: perRound(c.lossCpsAll), span_counterparties_point_19: span19,
      } : {}),
      window,
      bound,
      end: c.end,
      end_cause: c.endCause,
      survival_spans: span !== null ? elapsed / span : null,
      survival_less_window: span !== null ? Math.max(0, elapsed - window) / span : null,
      judged,
      open: c.end === null,
    };
  }

  // Point 19: the counterparties' records on their links to the operator,
  // added together over the last w rounds (all of them, if a link has
  // fewer). At a round's end the round just ended is still in cur.
  _cpRecordLastW(c) {
    const w = this.p.w;
    const atEnd = this.j === 0 && this.r > 0;
    let tot = 0;
    for (const l of c.linkObjs) {
      if (!l.live) continue;
      const e = l.ends[0] === c.owner ? 1 : 0;   // the counterparty's end
      const rounds = atEnd ? [...l.rec[e], l.cur[e]] : l.rec[e];
      for (const x of rounds.slice(-w)) tot += x;
    }
    return tot;
  }

  // Every run reports: each configuration's survival in spans, which span it
  // used, and whether it could be judged; the number of configurations each
  // defector passed through; and how many configurations are too long to
  // judge in this run (point 4: a seed with any such watched configuration
  // is left out of the mean, counted and reported).
  report() {
    const configurations = this.configs.map(c => this.configSummary(c));
    const defectors = {};
    for (const o of this.ops) if (o.type === 'D') defectors[o.name] = this.configs.filter(c => c.owner === o.i).length;
    return {
      time: this.time(), horizon: this.p.horizon,
      ruins: this.ruins, cuts: this.cuts, entries: this.entries, hops: this.hops,
      configurations, defectors,
      links_between_two_defectors_left_out: this.linksLeftOut,
      defectors_with_no_live_link_at_start: this._names([...this.uncoupledAtStart].sort((x, y) => x - y)),
      too_long_to_judge: configurations.filter(s => s.judged === false).length,
    };
  }
}
