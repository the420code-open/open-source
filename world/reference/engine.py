"""The world's reference engine, from the specification alone (world/spec/world_spec_v1.0.md, with its
Part Nine, "How a run is measured", settled 13 November 2026).

One engine, four settings: the page's charger, Paper D's charger, AP02's network, and the lone
operator that B3 needs. Every seed of a cell runs together, as arrays, so a cell runs in minutes.

Zero-Clause BSD.
"""
import math

import numpy as np

SPEC = "Phase 2 · the world · specification · version 1.1, 15 November 2026"
ROUNDS = 4000          # Part Nine, point 4: every cell of a hypothesis runs 4,000 rounds, fixed before any run
TYPES = {"C": 0, "U": 1, "D": 2}
POINT_19 = "still standing at the end, its counterparties' records on their links to it below zero over the last w rounds: the counterparties' span, the shorter (Part Nine, point 19)"
POINT_21 = "turned net-positive by the record, without a cut, at the start of the first round whose close found the records at zero or above: survival measured to that moment, its span over the samples up to it, the sample at that moment included (Part Nine, point 21)"
POINT_22 = "ended with its counterparties' records on their links to it below zero over the last w rounds, just before its end: the counterparties' span, the shorter (Part Nine, point 22)"
# version 1.1, draft 3: points 19 and 22 can only shorten a span, never lengthen one
NOT_SHORTER = "below zero, but the counterparties' span is not the shorter: the span of points 2, 3 and 14 stands (Part Nine, points 19 and 22, version 1.1, draft 3)"
TNAME = "CUD"

# The three settings, from the specification's Part Three, "The three settings", and the fourth, for B3.
SETTINGS = {
    "page_charger": dict(names=["A", "B"], topology="pair", E0=100.0, b=12.0, a=0.0, schedule="both",
                         g=1.0, m=10.0, c=4.0, lam=0.0, eps=0.0, k=0.0, E_r=0.0, E_max=None,
                         round=1.0, dt=0.001, s=0.0, u_max=None, sigma_s=0.0, sigma_r=0.0, w=5),
    "paperD_charger": dict(names=["A", "B"], topology="pair", E0=100.0, b=12.0, a=0.0, schedule="turns",
                           g=1.0, m=30.0, c=4.0, lam=0.0, eps=0.0, k=0.0, E_r=10.0, E_max=100.0,
                           round=1.0, dt=0.001, s=0.0, u_max=None, sigma_s=0.0, sigma_r=0.0, w=5),
    "network": dict(N=20, topology="ring", E0=50.0, b=0.0, a=0.1, schedule="always",
                    g=None, m=3.0, c=0.0, lam=1.0, eps=0.01, k=0.0, E_r=10.0, E_max=None,
                    round=1.0, dt=0.01, s=0.0, u_max=6.0, sigma_s=0.0, sigma_r=0.0, w=5),
    # B3's lone operator (Part Nine, point 13): it starts at 50, with a ruin line at 10, drift 0.1, a price of
    # effort lambda = 1, counted and reported, not taken from the stock; its effort is its own input s, set each
    # round by its policy, never above its own capacity u_max, which B3 sweeps. The network's u_max does not apply.
    "lone": dict(N=1, topology="none", E0=50.0, b=0.0, a=0.1, schedule="always",
                 g=0.0, m=0.0, c=0.0, lam=1.0, eps=0.0, k=0.0, E_r=10.0, E_max=None,
                 round=1.0, dt=0.01, s=0.0, u_max=None, sigma_s=0.0, sigma_r=0.0, w=5),
}


def params_for(setting, overrides=None):
    P = dict(SETTINGS[setting])
    P.update(overrides or {})
    if P.get("g") is None or P.get("g") == "m/(2*lam)":
        P["g"] = P["m"] / (2.0 * P["lam"])  # the default give, m / 2 lambda
    for key in ("E0", "E_r"):
        if P.get(key) is None:
            raise ValueError("the setting %s needs %s; the specification does not fix it" % (setting, key))
    return P


def _scatter(idx, w, size):
    return np.bincount(idx.ravel(), weights=w.ravel(), minlength=size)


class Config:
    """A configuration: an operator and its direct counterparties, joined to it by live links."""

    def as_dict(self, R, w):
        d = {"id": self.id, "owner": self.owner, "owner_type": self.owner_type, "members": self.members,
             "start": self.start, "clock_start": self.clock, "end": self.end, "end_reason": self.reason,
             "defended": self.defended, "has_defector": self.has_defector,
             "has_watched_defector": self.has_watched_defector,
             # B2, section 6: a defector's, where its operator is a defector with a counterparty; a sink's, where its
             # operator is not, with a counterparty; an operator alone, of any type
             "kind": "an operator alone" if len(self.members) == 1 else
                     "a defector's" if self.owner_type == "D" else "a sink's",
             "one_round_record_alone_would_watch": bool(getattr(self, "would1", False))}
        turn = getattr(self, "turn", None)
        if self.clock is not None:
            d["returned_and_went_below_again"] = list(getattr(self, "redips", []))
            d["outside_the_premises"] = getattr(self, "outside", None)
            if getattr(self, "sink_start_records", None) is not None:
                d["sink_records_when_its_clock_started"] = self.sink_start_records
            minloss, cp_minloss, cp_minall = self.minloss, self.cp_minloss, getattr(self, "cp_minall", math.inf)
            if turn is not None:
                # point 21: measured to the start of the first round whose close found the records at zero or above,
                # as point 20 starts a clock, and its span over the samples up to it, the sample at that moment
                # included (the round's start, after its cuts)
                minloss, cp_minloss, cp_minall = self.ts
            # Part Nine, point 2: where the configuration loses as a whole, its span is its stock above the ruin
            # line over its net loss; where it gains as a whole, its span is taken over its counterparties alone,
            # their stock above the ruin line over their net loss through their links to the operator. Both are
            # taken at their smallest along the way (point 3), and both are reported.
            whole = math.isfinite(minloss) and minloss > 0
            cp = self.cp_stock0 is not None and math.isfinite(cp_minloss) and cp_minloss > 0
            d["stock_above_ruin"] = self.stock0
            d["net_loss_per_round"] = minloss * R if whole else None
            d["counterparties_stock_above_ruin"] = self.cp_stock0
            d["counterparties_net_loss_per_round"] = cp_minloss * R if cp else None
            d["span_whole"] = self.stock0 / minloss if whole else None
            d["span_counterparties"] = self.cp_stock0 / cp_minloss if cp else None
            d["point_14"] = bool(whole and cp)
            d["point_21"] = POINT_21 if turn is not None else None
            d["turned_net_positive_at"] = turn
            if whole or cp:
                # point 14 (draft 5): at each sample the span that applies is the whole's where the whole loses and
                # the counterparties' where it gains; the configuration's span is the longest of those that applied
                if whole and cp:
                    d["span_used"] = "both applied; the longer, the " + (
                        "whole's" if d["span_whole"] >= d["span_counterparties"] else "counterparties'")
                    span = max(d["span_whole"], d["span_counterparties"])
                else:
                    d["span_used"] = "whole" if whole else "counterparties"
                    span = d["span_whole"] if whole else d["span_counterparties"]       # in units of time
                # point 19: a configuration still standing at the end, whose counterparties' records on their links
                # to the operator, added together over the last w rounds, are below zero, takes the counterparties'
                # span of point 2: their stock above the ruin line when the clock started, over their smallest net
                # loss through their links to the operator, taken at every sample (point 3), where that span is the
                # shorter; where it is not, the span of points 2, 3 and 14 stands (version 1.1, draft 3: points 19
                # and 22 only shorten a span, never lengthen one). Point 14's span is kept beside it.
                rec = getattr(self, "cp_record_w", None)
                d["counterparties_records_last_w_rounds"] = rec
                d["point_19"] = None
                d["point_22"] = None
                # point 22: point 19 at every end, whenever it comes; at the run's end it is point 19 itself. A
                # configuration that turned net-positive (point 21) stood at zero or above to its end, and is not read.
                at_end = self.reason == "run ended"
                if turn is None and rec is not None and rec < 0:
                    which = "point_19" if at_end else "point_22"
                    cpa = cp_minall
                    if self.cp_stock0 is not None and math.isfinite(cpa) and cpa > 0:
                        span_cp = self.cp_stock0 / cpa
                        d["counterparties_net_loss_per_round_every_sample"] = cpa * R
                        d["span_counterparties_every_sample"] = span_cp
                        if span_cp < span:
                            d["span_by_point_14"] = span
                            d["span_used_by_point_14"] = d["span_used"]
                            span = span_cp
                            d["span_counterparties_" + which] = span
                            d["span_used"] = "counterparties (%s)" % which.replace("_", " ")
                            d[which] = POINT_19 if at_end else POINT_22
                        else:
                            d[which + "_not_applied"] = NOT_SHORTER
                    else:
                        d[which] = "applies, but the counterparties lost at no sample: no span"
                window = w * R if self.defended else 0.0     # point 5: where at least one counterparty is type C
                surv = (turn if turn is not None else self.end) - self.clock
                bound = 3.0 * span + window
                d.update(span=span, bound=bound, survival=surv, survival_spans=surv / span,
                         survival_spans_net=max(0.0, surv - window) / span,
                         within_bound=surv <= bound + 1e-9)
                # point 4: one still standing when the run ends, whose bound has not yet come, is too long to judge;
                # one that turned net-positive is judged to its turn (point 21)
                d["judged"] = turn is not None or not (self.reason == "run ended" and surv < bound - 1e-9)
            else:
                d["span_used"] = None
                d["span"] = None
        return d


class World:
    """All the seeds of one cell, run together."""

    def __init__(self, cell, seeds, log=None, track_minmax=False):
        self.cell = cell
        P = self.P = params_for(cell["setting"], cell.get("overrides"))
        self.S = S = len(seeds)
        self.seeds = [int(s) for s in seeds]
        self.rngs = [np.random.default_rng(s) for s in self.seeds]
        self.R = P["round"]
        self.dt = P["dt"]
        self.n_sub = int(round(self.R / self.dt))
        if abs(self.n_sub * self.dt - self.R) > 1e-9:
            raise ValueError("a round must be a whole number of substeps")
        self.log = log
        self.track_minmax = track_minmax
        self.cfgs = []
        self.ruin_list, self.cut_log = [], []
        self.max_bound_ended = 0.0
        self.links_version = 0           # counts every change to the live links

        names = cell.get("operators") or P.get("names")
        N = len(names) if names else int(cell.get("N", P.get("N", 1)))
        self.names = list(names) if names else list(range(N))
        self.N = N
        topology = cell.get("topology", P["topology"])

        # Per seed, in this order, from the seed's own generator: the random links, the defectors' places,
        # the uneven drift. Then, each round: the reading noise, an entry's choices, the stock noise.
        typ = np.zeros((S, N), np.int8)
        a = np.full((S, N), float(P["a"]))
        edges = []
        self.links_left_out = []          # per seed: the drawn links that would join two defectors
        T = cell.get("types", {})
        for si, rng in enumerate(self.rngs):
            if topology == "pair":
                ed = [(0, 1)]
            elif topology == "ring":
                ed = [(i, (i + 1) % N) for i in range(N)] if N > 2 else [(0, 1)]
            elif topology == "random":
                u = rng.random(N * (N - 1) // 2)
                pairs = [(i, j) for i in range(N) for j in range(i + 1, N)]
                ed = [pr for pr, x in zip(pairs, u) if x < cell["p"]]
            elif topology == "none":
                ed = []
            else:
                raise ValueError(topology)
            edges.append(ed)
            if "hosts" in T:
                typ[si, :] = TYPES[T["hosts"]]
                d = T.get("defectors", 0)
                if "defector_share" in T:
                    d = int(round(T["defector_share"] * N))
                if d:
                    typ[si, rng.choice(N, size=d, replace=False)] = TYPES["D"]
            else:
                for nm, ty in T.items():
                    typ[si, self.names.index(nm)] = TYPES[ty]
            if cell.get("drift", {}).get("uneven"):
                lo, hi = cell["drift"]["uneven"]
                a[si, :] = rng.uniform(lo, hi, size=N)
            # No link joins two defectors: nothing passes between them, since neither gives. A drawn link that
            # would join two is left out, after the drawing, so the seed's random numbers are drawn as before.
            dd = [pr for pr in ed if typ[si, pr[0]] == TYPES["D"] and typ[si, pr[1]] == TYPES["D"]]
            if dd:
                edges[-1] = [pr for pr in ed if pr not in dd]
            self.links_left_out.append([[self.names[x], self.names[y]] for x, y in dd])
        self.typ, self.a = typ, a
        self.s_in = np.full((S, N), float(P["s"]))
        own = cell.get("own", {})            # per-operator drift and own input, for AP02's own checks
        for nm, val in own.get("a", {}).items():
            self.a[:, self.names.index(nm)] = val
        for nm, val in own.get("s", {}).items():
            self.s_in[:, self.names.index(nm)] = val
        self.E = np.full((S, N), float(P["E0"]))
        self.alive = np.ones((S, N), bool)
        self.ruin_t = np.full((S, N), np.nan)
        self.premise_coupled = [self._connected(ed, N) for ed in edges]     # the whole network, for information
        # B1's premise check, seed by seed: the defector is coupled, starting with at least one live link. A
        # defector that starts with no live link draws on no one: it is reported, and not watched.
        self.uncoupled_defectors = []
        for si, ed in enumerate(edges):
            linked = {x for pr in ed for x in pr}
            self.uncoupled_defectors.append(
                {i for i in range(N) if typ[si, i] == TYPES["D"] and i not in linked})

        width = max(1, max(len(e) for e in edges))
        self.ei = np.zeros((S, width), np.int64)
        self.ej = np.zeros((S, width), np.int64)
        self.elive = np.zeros((S, width), bool)
        self.eused = np.zeros((S, width), bool)
        for si, ed in enumerate(edges):
            for e, (i, j) in enumerate(ed):
                self.ei[si, e], self.ej[si, e] = i, j
                self.elive[si, e] = self.eused[si, e] = True
        self.ecount = np.array([len(ed) for ed in edges], np.int64)
        w = P["w"]
        self.eage = np.zeros((S, width), np.int64)       # closed rounds of record
        self.ebuf = np.zeros((S, width, 2, w))           # per end, the last w rounds' records, newest last
        self.etotal = np.zeros((S, width, 2))            # per end, the whole record
        self.elast = np.zeros((S, width, 2))             # per end, the round just closed
        self.erate = np.zeros((S, width, 2))             # per end, received less spent, per unit of time
        self.eacc = np.zeros((S, width, 2))              # per end, the record of the round so far
        self.eact = np.zeros((S, width), bool)           # live at the start of this round
        # B2's section 10: the part of each record that is passive flow, kept apart so that a sink's record can be
        # read without it. It is never read by any rule of the world.
        self.eacc_pf = np.zeros((S, width, 2))
        self.ebuf_pf = np.zeros((S, width, 2, w))
        self.elast_pf = np.zeros((S, width, 2))

        self.rbuf = np.zeros((S, N, w))                  # the last w readings, newest last
        self.rcount = np.zeros((S, N), np.int64)
        self.slope = np.full((S, N), np.nan)
        self.declining = np.zeros((S, N), bool)
        self.reading = np.full((S, N), np.nan)
        self.cost_effort = np.zeros((S, N))              # B3: lam u^2, counted, never taken from the stock
        if track_minmax:
            self.Emin = self.E.copy()
            self.Emax_seen = self.E.copy()

        # each live operator's current configuration, as arrays
        self.cfg_of = np.full((S, N), -1, np.int64)
        self.k_clock = np.full((S, N), np.nan)
        self.k_stock0 = np.full((S, N), np.nan)
        self.k_minloss = np.full((S, N), np.inf)
        self.k_roundmin = np.full((S, N), np.inf)
        self.k_stock_start = np.zeros((S, N))
        self.k_start = np.zeros((S, N))
        self.k_defended = np.zeros((S, N), bool)
        self.k_cpstock_start = np.full((S, N), np.nan)   # the counterparties' stock above the ruin line, at the start
        self.k_cpstock0 = np.full((S, N), np.nan)        # ... and when the clock started
        self.k_cpminloss = np.full((S, N), np.inf)       # their smallest net loss through their links to the operator
        self.k_cproundmin = np.full((S, N), np.inf)
        self.k_cpminall = np.full((S, N), np.inf)        # point 19: the same, at every sample, whatever the whole
        self.k_cproundall = np.full((S, N), np.inf)
        # Part Nine, point 21: the start of the round from which the counterparties' records over the window have
        # stood at zero or above at every round's close (nan while they have not), and the samples up to it
        self.k_turn = np.full((S, N), np.nan)
        self.k_rs = np.full((3, S, N), np.inf)          # at the current round's start: minloss, cpminloss, cpminall
        self.k_ts = np.full((3, S, N), np.inf)          # ... as they stood at the start of the turn's round
        self.k_would1 = np.zeros((S, N), bool)          # one round's record alone below zero at some close
        self.k_outside = np.full((S, N), np.nan)        # a defector counterparty's own record over the window below 0
        self.falls_unwatched = []                        # every fall of an operator in no watched configuration
        self.panic_on = np.zeros((S, N), bool)           # B3's panic: on below the lower line, off above the upper
        self.r = 0
        self.sub_mark = 0

    # ---------- structure ----------
    @staticmethod
    def _connected(ed, N):
        if N <= 1:
            return True
        adj = {i: [] for i in range(N)}
        for i, j in ed:
            adj[i].append(j)
            adj[j].append(i)
        seen, todo = {0}, [0]
        while todo:
            x = todo.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        return len(seen) == N

    def _grow_ops(self, n_new, typ="C"):
        S = self.S

        def pad(arr, fill):
            return np.concatenate([arr, np.full((S, n_new) + arr.shape[2:], fill, arr.dtype)], axis=1)
        self.typ = pad(self.typ, TYPES[typ])
        self.a = pad(self.a, float(self.P["a"]))
        self.s_in = pad(self.s_in, float(self.P["s"]))
        self.E = pad(self.E, float(self.P["E0"]))
        self.alive = pad(self.alive, True)
        self.ruin_t = pad(self.ruin_t, np.nan)
        self.rbuf, self.rcount = pad(self.rbuf, 0.0), pad(self.rcount, 0)
        self.slope, self.declining = pad(self.slope, np.nan), pad(self.declining, False)
        self.reading, self.cost_effort = pad(self.reading, np.nan), pad(self.cost_effort, 0.0)
        self.cfg_of = pad(self.cfg_of, -1)
        self.k_clock, self.k_stock0 = pad(self.k_clock, np.nan), pad(self.k_stock0, np.nan)
        self.k_minloss, self.k_roundmin = pad(self.k_minloss, np.inf), pad(self.k_roundmin, np.inf)
        self.k_stock_start, self.k_start = pad(self.k_stock_start, 0.0), pad(self.k_start, 0.0)
        self.k_defended = pad(self.k_defended, False)
        self.k_cpstock_start, self.k_cpstock0 = pad(self.k_cpstock_start, np.nan), pad(self.k_cpstock0, np.nan)
        self.k_cpminloss, self.k_cproundmin = pad(self.k_cpminloss, np.inf), pad(self.k_cproundmin, np.inf)
        self.k_cpminall, self.k_cproundall = pad(self.k_cpminall, np.inf), pad(self.k_cproundall, np.inf)
        self.k_turn, self.k_would1, self.k_outside = pad(self.k_turn, np.nan), pad(self.k_would1, False), \
            pad(self.k_outside, np.nan)
        self.k_rs = np.concatenate([self.k_rs, np.full((3, S, n_new), np.inf)], axis=2)
        self.k_ts = np.concatenate([self.k_ts, np.full((3, S, n_new), np.inf)], axis=2)
        self.panic_on = pad(self.panic_on, False)
        self.E_snap = pad(self.E_snap, float(self.P["E0"]))
        for attr in ("F", "A1", "B1", "L", "g_now"):
            if hasattr(self, attr):
                setattr(self, attr, pad(getattr(self, attr), 0.0))
        if self.track_minmax:
            self.Emin = pad(self.Emin, float(self.P["E0"]))
            self.Emax_seen = pad(self.Emax_seen, float(self.P["E0"]))
        self.names.extend(range(self.N, self.N + n_new))
        self.N += n_new

    def _grow_edges(self, n_new):
        S = self.S

        def cat(arr, fill):
            return np.concatenate([arr, np.full((S, n_new) + arr.shape[2:], fill, arr.dtype)], axis=1)
        self.ei, self.ej = cat(self.ei, 0), cat(self.ej, 0)
        self.elive, self.eused = cat(self.elive, False), cat(self.eused, False)
        self.eage, self.ebuf, self.etotal = cat(self.eage, 0), cat(self.ebuf, 0.0), cat(self.etotal, 0.0)
        self.elast, self.erate, self.eacc = cat(self.elast, 0.0), cat(self.erate, 0.0), cat(self.eacc, 0.0)
        self.eact = cat(self.eact, False)
        self.eacc_pf, self.ebuf_pf, self.elast_pf = cat(self.eacc_pf, 0.0), cat(self.ebuf_pf, 0.0), \
            cat(self.elast_pf, 0.0)

    def _flat(self, idx):
        return idx + (np.arange(self.S) * self.N)[:, None]

    def _to_ops(self, w0, w1):
        """Adds a per-edge quantity to its ends: w0 to end i, w1 to end j."""
        S, N = self.S, self.N
        return (_scatter(self._flat(self.ei), w0, S * N) + _scatter(self._flat(self.ej), w1, S * N)).reshape(S, N)

    def neighbours(self, si, i):
        m = self.elive[si]
        return sorted(set(self.ej[si][m & (self.ei[si] == i)].tolist()) |
                      set(self.ei[si][m & (self.ej[si] == i)].tolist()))

    # ---------- the flows of one round ----------
    def _gives(self):
        """What each operator gives on each of its live links, by type, schedule and capacity."""
        P = self.P
        giver = (self.typ != TYPES["D"]) & self.alive
        if P["schedule"] == "turns":
            turn = np.zeros(self.N, bool)
            turn[self.r % 2] = True       # hours count from 0, and the first hour is A's
            giver &= turn[None, :]
        g = np.where(giver, float(P["g"]), 0.0)
        if P["u_max"] is not None:
            total = g * self.L
            g = g * np.where(total > P["u_max"], P["u_max"] / np.maximum(total, 1e-300), 1.0)
        return g

    def _compute_flows(self):
        P, S, N = self.P, self.S, self.N
        live = self.elive.astype(float)
        self.L = self._to_ops(live, live)
        if self.cell.get("policy"):
            self._apply_policy()
        g = self._gives()
        gi = np.take_along_axis(g, self.ei, 1)
        gj = np.take_along_axis(g, self.ej, 1)
        spend_i = P["c"] * gi + P["lam"] * gi * gi + P["eps"]
        spend_j = P["c"] * gj + P["lam"] * gj * gj + P["eps"]
        r0 = np.where(self.elive, P["m"] * gj - spend_i, 0.0)
        r1 = np.where(self.elive, P["m"] * gi - spend_j, 0.0)
        self.erate[..., 0], self.erate[..., 1] = r0, r1
        F = self.s_in - P["b"] + self._to_ops(r0, r1)
        self.F = np.where(self.alive, F, 0.0)
        self.g_now = g
        self.A1 = np.where(self.alive, 1.0 - self.dt * self.a, 1.0)
        self.B1 = self.dt * self.F
        if P["k"]:
            W = np.zeros((S, N, N))
            sidx = np.repeat(np.arange(S)[:, None], self.ei.shape[1], 1)
            lv = self.elive
            W[sidx[lv], self.ei[lv], self.ej[lv]] = 1.0
            W[sidx[lv], self.ej[lv], self.ei[lv]] = 1.0
            self.W = W

    def det_rate(self, E):
        """The stock's rate of change without its noise: F - a E + k sum_j (E_j - E_i)."""
        D = self.F - self.a * E
        if self.P["k"]:
            D = D + self.P["k"] * (np.matmul(self.W, E[..., None])[..., 0] - self.L * E)
        return np.where(self.alive, D, 0.0)

    def _apply_policy(self):
        """B3's lone operator: its effort is its own input, set each round by its policy, never above u_max."""
        pol = self.cell["policy"]
        if pol["kind"] == "steady":
            u = np.full((self.S, self.N), float(pol["u"]))
        elif pol["kind"] == "panic":
            # Part Nine, point 13, and the hypotheses: on below the lower line, off above the upper, 10 higher
            rd = np.nan_to_num(self.reading, nan=np.inf)
            lower = float(pol["lower"])
            upper = float(pol.get("upper", lower + 10.0))
            self.panic_on = np.where(rd < lower, True, np.where(rd > upper, False, self.panic_on))
            u = np.where(self.panic_on, float(pol["u_full"]), 0.0)
        elif pol["kind"] == "schedule":
            seq = pol["u"]
            u = np.full((self.S, self.N), float(seq[self.r % len(seq)]))
        else:
            raise ValueError(pol["kind"])
        if self.P["u_max"] is not None:
            u = np.minimum(u, self.P["u_max"])
        self.s_in = np.where(self.alive, u, 0.0)
        self.cost_effort += np.where(self.alive, self.P["lam"] * u * u * self.R, 0.0)

    def _bank(self, upto):
        """Adds the round's records so far, at the present rates, for every live link."""
        n = upto - self.sub_mark
        if n > 0:
            self.eacc += np.where(self.elive[..., None], self.erate * (n * self.dt), 0.0)
        self.sub_mark = upto

    # ---------- configurations ----------
    def _cfg_loss(self, D):
        """Each live operator's configuration's net loss per unit of time: minus the sum of its members' rates."""
        lv = self.elive
        nb = self._to_ops(np.where(lv, np.take_along_axis(D, self.ej, 1), 0.0),
                          np.where(lv, np.take_along_axis(D, self.ei, 1), 0.0))
        return np.where(self.alive, -(D + nb), np.nan)

    def _link_rates(self, E):
        """Each live link's rate for each end: received less spent, plus the passive flow through it (point 8)."""
        r0, r1 = self.erate[..., 0], self.erate[..., 1]
        if self.P["k"]:
            Ei = np.take_along_axis(E, self.ei, 1)
            Ej = np.take_along_axis(E, self.ej, 1)
            r0 = r0 + self.P["k"] * (Ej - Ei)
            r1 = r1 + self.P["k"] * (Ei - Ej)
        return np.where(self.elive, r0, 0.0), np.where(self.elive, r1, 0.0)

    def _cp_loss(self, E):
        """Each operator's counterparties' net loss per unit of time through their links to it."""
        r0, r1 = self._link_rates(E)
        return np.where(self.alive & (self.L > 0), -self._to_ops(r1, r0), np.nan)

    def _cp_loss_row(self, si, i, E_row):
        lv = self.elive[si]
        tot = 0.0
        for e in np.nonzero(lv & ((self.ei[si] == i) | (self.ej[si] == i)))[0]:
            end = 1 if self.ei[si, e] == i else 0       # the counterparty's end of the link
            rate = float(self.erate[si, e, end])
            if self.P["k"]:
                a, b = int(self.ei[si, e]), int(self.ej[si, e])
                rate += self.P["k"] * ((E_row[a] - E_row[b]) if end == 1 else (E_row[b] - E_row[a]))
            tot += rate
        return -tot

    def _new_cfg(self, si, i, t, E_row, D_row):
        nb = self.neighbours(si, i)
        c = Config()
        c.id = len(self.cfgs)
        c.seed = self.seeds[si]
        c.si, c.i = si, i
        c.owner = self.names[i]
        c.midx = [i] + nb
        c.members = [self.names[j] for j in c.midx]
        c.owner_type = TNAME[self.typ[si, i]]
        c.start, c.end, c.reason = t, None, None
        c.defended = bool(any(self.typ[si, j] == TYPES["C"] for j in nb))
        c.has_defector = bool(any(self.typ[si, j] == TYPES["D"] for j in c.midx))
        c.has_watched_defector = bool(any(self.typ[si, j] == TYPES["D"] and j not in self.uncoupled_defectors[si]
                                          for j in c.midx))
        c.clock, c.stock0, c.minloss = None, None, np.inf
        c.cp_stock0, c.cp_minloss = None, np.inf
        # its own links, as they stand when it opens: point 22 reads them just before its end, whatever ends it
        c.eidx = [int(e) for e in np.nonzero(self.elive[si] & ((self.ei[si] == i) | (self.ej[si] == i)))[0]]
        c.redips, c.turn, c.outside, c.sink_start_records = [], None, None, None
        self.k_turn[si, i], self.k_would1[si, i], self.k_outside[si, i] = np.nan, False, np.nan
        self.k_rs[:, si, i] = np.inf
        self.k_ts[:, si, i] = np.inf
        self.cfgs.append(c)
        loss = -float(sum(D_row[j] for j in c.midx))
        stock = float(sum(E_row[j] - self.P["E_r"] for j in c.midx))
        if nb:
            cpl = self._cp_loss_row(si, i, E_row)
            self.k_cpstock_start[si, i] = float(sum(E_row[j] - self.P["E_r"] for j in nb))
            self.k_cproundmin[si, i] = cpl if (cpl > 0 and loss <= 0) else np.inf   # point 14: where the whole gains
            self.k_cproundall[si, i] = cpl if cpl > 0 else np.inf                   # point 19: at every sample
        else:
            self.k_cpstock_start[si, i] = np.nan
            self.k_cproundmin[si, i] = np.inf
            self.k_cproundall[si, i] = np.inf
        self.cfg_of[si, i] = c.id
        self.k_start[si, i] = t
        self.k_stock_start[si, i] = stock
        self.k_defended[si, i] = c.defended
        self.k_roundmin[si, i] = loss if loss > 0 else np.inf
        self.k_clock[si, i], self.k_stock0[si, i], self.k_minloss[si, i] = np.nan, np.nan, np.inf
        self.k_cpstock0[si, i], self.k_cpminloss[si, i] = np.nan, np.inf
        self.k_cpminall[si, i] = np.inf
        self._event({"ev": "cfg_start", "seed": c.seed, "cfg": c.id, "owner": c.owner,
                     "members": c.members, "t": t})
        if not nb and loss > 0:
            # Part Nine, point 1: an operator alone is a configuration of one, of any type; its clock starts
            # when it is left alone, if its own net change is a loss ("B alone, from A's ruin").
            self._start_clock(si, i, t, stock, self.k_roundmin[si, i], why="alone")
        return c

    def _start_clock(self, si, i, t, stock, minloss, why, record=None, cp_stock=np.nan, cp_minloss=np.inf,
                     cp_minall=np.inf):
        self.k_clock[si, i], self.k_stock0[si, i], self.k_minloss[si, i] = t, stock, minloss
        self.k_cpstock0[si, i], self.k_cpminloss[si, i] = cp_stock, cp_minloss
        self.k_cpminall[si, i] = cp_minall
        c = self.cfgs[self.cfg_of[si, i]]
        ev = {"ev": "clock", "seed": c.seed, "cfg": c.id, "owner": c.owner, "t": t,
              "stock_above_ruin": stock, "why": why}
        if record is not None:
            ev["record"] = record
        self._event(ev)

    def _end_cfg(self, si, i, t, reason, D_row=None, E_row=None):
        cid = self.cfg_of[si, i]
        if cid < 0:
            return
        c = self.cfgs[cid]
        if not math.isnan(self.k_clock[si, i]):
            if D_row is not None:
                loss = -float(sum(D_row[j] for j in c.midx))
                if loss > 0:
                    self.k_minloss[si, i] = min(self.k_minloss[si, i], loss)
                if E_row is not None and len(c.midx) > 1:
                    cpl = self._cp_loss_row(si, i, E_row)
                    if cpl > 0 and loss <= 0:          # point 14: the counterparties' span applies where the whole gains
                        self.k_cpminloss[si, i] = min(self.k_cpminloss[si, i], cpl)
                    if cpl > 0:                        # point 19: at every sample
                        self.k_cpminall[si, i] = min(self.k_cpminall[si, i], cpl)
            c.clock = float(self.k_clock[si, i])
            c.stock0 = float(self.k_stock0[si, i])
            c.minloss = float(self.k_minloss[si, i])
            c.cp_stock0 = None if math.isnan(self.k_cpstock0[si, i]) else float(self.k_cpstock0[si, i])
            c.cp_minloss = float(self.k_cpminloss[si, i])
            c.cp_minall = float(self.k_cpminall[si, i])
            if len(c.midx) > 1:
                # points 19 and 22: the counterparties' records over the last w rounds, on the configuration's own
                # links, as they stood just before its end (the round just closed included, a part-round not)
                c.cp_record_w = self._cp_record_cfg(si, i, c)
            if not math.isnan(self.k_turn[si, i]):
                c.turn = float(self.k_turn[si, i])
                c.ts = tuple(float(x) for x in self.k_ts[:, si, i])
            if not math.isnan(self.k_outside[si, i]):
                c.outside = {"found_at": float(self.k_outside[si, i]),
                             "why": "a counterparty whose record over the window is below zero is a defector"}
            spans = []
            if math.isfinite(c.minloss) and c.minloss > 0:
                spans.append(c.stock0 / c.minloss)
            if c.cp_stock0 is not None and math.isfinite(c.cp_minloss) and c.cp_minloss > 0:
                spans.append(c.cp_stock0 / c.cp_minloss)
            span = max(spans) if spans else None
            if span is not None:
                self.max_bound_ended = max(self.max_bound_ended, 3.0 * span +
                                           (self.P["w"] * self.R if c.defended else 0.0))
        c.would1 = bool(self.k_would1[si, i])
        c.end, c.reason = t, reason
        self.cfg_of[si, i] = -1
        self._event({"ev": "cfg_end", "seed": c.seed, "cfg": c.id, "owner": c.owner, "t": t, "reason": reason})

    def _cp_record_cfg(self, si, i, c):
        """Points 19 and 22: the counterparties' records on the configuration's own links to operator i, added
        together over the last w rounds (all of them, if a link has fewer), as the closed rounds stand."""
        tot = 0.0
        for e in c.eidx:
            end = 1 if self.ei[si, e] == i else 0       # the counterparty's end of the link
            tot += float(self.ebuf[si, e, end].sum())
        return tot

    def _cp_record_last_w(self, si, i):
        """Point 19: the counterparties' records on their links to operator i, added together over the last w
        rounds (all of them, if a link has fewer)."""
        lv = self.elive[si]
        tot = 0.0
        for e in np.nonzero(lv & ((self.ei[si] == i) | (self.ej[si] == i)))[0]:
            end = 1 if self.ei[si, e] == i else 0       # the counterparty's end of the link
            tot += float(self.ebuf[si, e, end].sum())
        return tot

    def _event(self, ev):
        if self.log is not None:
            self.log.event(ev)

    def longest_bound(self):
        clocked = ~np.isnan(self.k_clock) & (self.cfg_of >= 0) & np.isfinite(self.k_minloss)
        best = self.max_bound_ended
        if clocked.any():
            b = 3.0 * self.k_stock0[clocked] / self.k_minloss[clocked] + \
                np.where(self.k_defended[clocked], self.P["w"] * self.R, 0.0)
            best = max(best, float(b.max()))
        return best

    # ---------- the round ----------
    def _close_round(self):
        """Step 1: the round just ended is added to every link's record, for both ends."""
        self._bank(self.n_sub)
        act = self.eact
        rec = np.where(act[..., None], self.eacc, 0.0)
        self.ebuf[act] = np.concatenate([self.ebuf[act][..., 1:], rec[act][..., None]], axis=-1)
        self.elast = rec
        self.etotal += rec
        self.eage += act
        self.eacc[:] = 0.0
        rpf = np.where(act[..., None], self.eacc_pf, 0.0)          # the passive flow in it, kept apart
        self.ebuf_pf[act] = np.concatenate([self.ebuf_pf[act][..., 1:], rpf[act][..., None]], axis=-1)
        self.elast_pf = rpf
        self.eacc_pf[:] = 0.0
        self.sub_mark = 0

        # the end-of-round sample of every configuration's loss, then the clocks
        loss = self._cfg_loss(self.det_rate(self.E))
        pos = np.where(loss > 0, loss, np.inf)
        has = self.alive & (self.cfg_of >= 0)
        self.k_roundmin = np.where(has, np.minimum(self.k_roundmin, pos), np.inf)
        clocked = has & ~np.isnan(self.k_clock)
        self.k_minloss = np.where(clocked, np.minimum(self.k_minloss, pos), self.k_minloss)
        cpl = self._cp_loss(self.E)
        cpos = np.where((cpl > 0) & ~(loss > 0), cpl, np.inf)     # point 14: only where the whole gains
        self.k_cproundmin = np.where(has, np.minimum(self.k_cproundmin, cpos), np.inf)
        self.k_cpminloss = np.where(clocked, np.minimum(self.k_cpminloss, cpos), self.k_cpminloss)
        cposall = np.where(cpl > 0, cpl, np.inf)                  # point 19: at every sample
        self.k_cproundall = np.where(has, np.minimum(self.k_cproundall, cposall), np.inf)
        self.k_cpminall = np.where(clocked, np.minimum(self.k_cpminall, cposall), self.k_cpminall)
        lv = self.elive
        # Part Nine, point 20: each link's record over its last w rounds, or all of them where it has fewer, added
        # together, overhead and passive flow included: the record a type C operator reviews. Read by whole rounds,
        # back to the link's start, also for a configuration that opened inside the round just closed.
        recw = self.ebuf.sum(-1)
        cpw = self._to_ops(np.where(lv, recw[..., 1], 0.0), np.where(lv, recw[..., 0], 0.0))
        # one round's record alone, as version 1.0 read it: only counted, for B2's section 10
        cp1 = self._to_ops(np.where(lv, self.elast[..., 1], 0.0), np.where(lv, self.elast[..., 0], 0.0))
        hascp = has & (self.L > 0)
        self.k_would1 |= hascp & (cp1 < 0)
        r_prev = self.r - 1
        t_prev = r_prev * self.R
        # Part Nine, point 21: a clocked configuration whose counterparties' records over the window stand at zero or
        # above at this close has turned at the start of this round, if they stay so at every close to its end; a
        # second dip below zero cancels the turn, and the whole stretch counts
        on = clocked & hascp
        new_turn = on & (cpw >= 0) & np.isnan(self.k_turn)
        if new_turn.any():
            self.k_turn = np.where(new_turn, t_prev, self.k_turn)
            self.k_ts = np.where(new_turn[None], self.k_rs, self.k_ts)
        dip = on & (cpw < 0) & ~np.isnan(self.k_turn)
        for si, i in zip(*np.nonzero(dip)):
            c = self.cfgs[self.cfg_of[si, i]]
            c.redips.append({"stood_at_zero_or_above_from": float(self.k_turn[si, i]),
                             "below_zero_again_in_the_round_from": float(t_prev), "record": float(cpw[si, i])})
            self.k_turn[si, i] = np.nan
            self.k_ts[:, si, i] = np.inf
        start_now = has & ~clocked & hascp & (cpw < 0)
        for si, i in zip(*np.nonzero(start_now)):
            # the clock starts at the start of the first round whose close finds the counterparties' records on their
            # links to the operator below zero, read as point 20 says; no earlier than the configuration's own start
            t0 = max(self.k_start[si, i], t_prev)
            c = self.cfgs[self.cfg_of[si, i]]
            midx = c.midx
            if self.k_start[si, i] >= t_prev:
                stock = float(self.k_stock_start[si, i])
                cp_stock = float(self.k_cpstock_start[si, i])
            else:
                stock = float(sum(self.E_snap[si, j] - self.P["E_r"] for j in midx))
                cp_stock = float(sum(self.E_snap[si, j] - self.P["E_r"] for j in midx[1:]))
            self._start_clock(si, i, float(t0), stock, float(self.k_roundmin[si, i]), why="record",
                              record=float(cpw[si, i]), cp_stock=cp_stock, cp_minloss=float(self.k_cproundmin[si, i]),
                              cp_minall=float(self.k_cproundall[si, i]))
            if self.typ[si, i] != TYPES["D"]:
                # B2's section 10: for every watched sink, its counterparties' records in the round its clock started,
                # with the passive flow left out, beside the records as read
                pfw = sum(float(self.ebuf_pf[si, e, 1 if self.ei[si, e] == i else 0].sum()) for e in c.eidx)
                pf1 = sum(float(self.elast_pf[si, e, 1 if self.ei[si, e] == i else 0]) for e in c.eidx)
                c.sink_start_records = {"over_the_window": float(cpw[si, i]),
                                        "over_the_window_less_passive_flow": float(cpw[si, i]) - pfw,
                                        "that_round_alone": float(cp1[si, i]),
                                        "that_round_alone_less_passive_flow": float(cp1[si, i]) - pf1}
        # B2's section 6: a watched configuration where any counterparty whose record over the window is below zero
        # is a defector lies outside the premises; it is reported in full and left out of the measure
        clocked_now = has & ~np.isnan(self.k_clock)
        if clocked_now.any():
            D = TYPES["D"]
            tj = np.take_along_axis(self.typ, self.ej, 1) == D
            ti = np.take_along_axis(self.typ, self.ei, 1) == D
            bad = self._to_ops(np.where(lv & tj & (recw[..., 1] < 0), 1.0, 0.0),
                               np.where(lv & ti & (recw[..., 0] < 0), 1.0, 0.0)) > 0
            first = clocked_now & bad & np.isnan(self.k_outside)
            if first.any():
                self.k_outside = np.where(first, t_prev, self.k_outside)

    def _readings(self):
        P = self.P
        rd = self.E.copy()
        if P["sigma_r"]:
            Z = np.empty((self.S, self.N))
            for si, rng in enumerate(self.rngs):
                Z[si] = rng.standard_normal(self.N)
            rd += P["sigma_r"] * Z
        self.reading = np.where(self.alive, rd, np.nan)
        upd = self.alive
        self.rbuf[upd] = np.concatenate([self.rbuf[upd][:, 1:], rd[upd][:, None]], axis=1)
        self.rcount += upd

    def _gradients(self):
        w = self.P["w"]
        n_eff = np.minimum(self.rcount, w)
        slope = np.full((self.S, self.N), np.nan)
        for n in range(2, w + 1):
            sel = (n_eff == n) & self.alive
            if not sel.any():
                continue
            y = self.rbuf[sel][:, w - n:]
            xc = np.arange(n, dtype=float) - (n - 1) / 2.0
            slope[sel] = (y * xc).sum(1) / (xc * xc).sum()
        self.slope = slope
        self.declining = np.nan_to_num(slope, nan=0.0) < 0

    def _reviews(self):
        """Step 4: type C operators review their links, and cut any whose record is below zero for them."""
        w = self.P["w"]
        live = self.elive
        cuts = np.zeros_like(live)
        found = []
        if not live.any():
            return cuts, found
        rev = np.cumsum(self.ebuf[..., ::-1], axis=-1)        # rev[..., n-1]: the last n rounds
        for end, opidx in ((0, self.ei), (1, self.ej)):
            op_typ = np.take_along_axis(self.typ, opidx, 1)
            op_alive = np.take_along_axis(self.alive, opidx, 1)
            op_decl = np.take_along_axis(self.declining, opidx, 1)
            isC = live & op_alive & (op_typ == TYPES["C"])
            # (i) declining: every live link with at least one round, on its record (its last w rounds at most);
            # (ii) not declining: only links at least w rounds old, on their last w rounds.
            n_rev = np.where(op_decl, np.minimum(self.eage, w), np.where(self.eage >= w, w, 0))
            do = isC & (n_rev >= 1)
            if not do.any():
                continue
            idx = np.clip(n_rev - 1, 0, w - 1)
            recsum = np.take_along_axis(rev[:, :, end, :], idx[..., None], 2)[..., 0]
            cut = do & (recsum < 0)
            cuts |= cut
            for si, e in zip(*np.nonzero(cut)):
                found.append((si, e, int(opidx[si, e]), float(recsum[si, e]), int(n_rev[si, e]),
                              bool(op_decl[si, e])))
        return cuts, found

    def _took_more(self, si, j):
        """Whether j's record shows it took through its links more than it gave: its counterparties' whole
        records on their links to j, added together, below zero."""
        used = self.eused[si] & (self.eage[si] > 0)
        tot = self.etotal[si, used & (self.ei[si] == j), 1].sum() + self.etotal[si, used & (self.ej[si] == j), 0].sum()
        has = bool((used & ((self.ei[si] == j) | (self.ej[si] == j))).any())
        return has and tot < 0

    def _n_links(self, si, j):
        return int((self.elive[si] & ((self.ei[si] == j) | (self.ej[si] == j))).sum())

    def _room(self, si, j, extra=1):
        """Part Nine, point 10: an operator accepts a new link only while its capacity still covers the default
        give on every link, the new one included. A defector gives nothing, so capacity never binds it."""
        um = self.P["u_max"]
        if um is None or self.typ[si, j] == TYPES["D"]:
            return True
        return (self._n_links(si, j) + extra) * float(self.P["g"]) <= um + 1e-9

    def _refuses(self, si, x, other):
        """Point 9: every type C operator, newcomers included, refuses a link to any operator whose
        counterparties' records on their links to it, added together over its whole record, are below zero."""
        return self.typ[si, x] == TYPES["C"] and self._took_more(si, other)

    def _entry(self, t):
        """Point 9: a newcomer enters after the round's cuts, every q rounds from round q, offering links to n
        operators chosen with the seed; it takes its first reading the round after. In the entry setting, a
        defector left with no live links offers a link to one operator, chosen with the seed, every q rounds:
        the hopper."""
        en = self.cell.get("entry")
        if not en or self.r == 0 or self.r % en["q"]:
            return []
        new = self.N
        self._grow_ops(1, typ=en.get("type", "C"))
        changed = [(si, new) for si in range(self.S)]
        add = []
        for si, rng in enumerate(self.rngs):
            cand = [j for j in range(new) if self.alive[si, j]]
            pick = rng.choice(len(cand), size=min(en["n"], len(cand)), replace=False) if cand else []
            offered = [cand[x] for x in pick]
            accepted, refused, full = [], [], []
            for j in offered:
                if self._refuses(si, new, j) or self._refuses(si, j, new):
                    refused.append(j)
                elif not (self._room(si, j) and self._room(si, new, extra=len(accepted) + 1)):
                    full.append(j)
                else:
                    accepted.append(j)
            for j in accepted:
                add.append((si, new, j))
                changed.append((si, j))
            self._event({"ev": "entry", "seed": self.seeds[si], "round": self.r, "t": t, "op": new,
                         "type": en.get("type", "C"),
                         "offered": [self.names[j] for j in offered], "accepted": [self.names[j] for j in accepted],
                         "refused": [self.names[j] for j in refused], "no_capacity": [self.names[j] for j in full]})
            if en.get("hopper"):
                linked = {x for (z, x, y) in add if z == si} | {y for (z, x, y) in add if z == si}
                for d in range(new):
                    if not (self.alive[si, d] and self.typ[si, d] == TYPES["D"]) or self._n_links(si, d) or d in linked:
                        continue
                    others = [j for j in range(new + 1) if j != d and self.alive[si, j]]
                    if not others:
                        continue
                    j = others[int(rng.integers(len(others)))]
                    if self.typ[si, j] == TYPES["D"]:
                        outcome = "no link joins two defectors"      # nothing would pass between them
                    elif self._refuses(si, j, d):
                        outcome = "refused by the record"
                    elif not self._room(si, j, extra=1 + sum(1 for (z, x, y) in add if z == si and j in (x, y))):
                        outcome = "no capacity"
                    else:
                        outcome = "accepted"
                        add.append((si, d, j))
                        changed.append((si, d))
                        changed.append((si, j))
                    self._event({"ev": "hop", "seed": self.seeds[si], "round": self.r, "t": t,
                                 "defector": self.names[d], "offered": self.names[j], "outcome": outcome})
        if add:
            per_seed = np.bincount([x[0] for x in add], minlength=self.S)
            need = int((self.ecount + per_seed).max() - self.ei.shape[1])
            if need > 0:
                self._grow_edges(max(need, 16))
            for si, i, j in add:
                e = int(self.ecount[si])
                self.ei[si, e], self.ej[si, e] = i, j
                self.elive[si, e] = self.eused[si, e] = True
                self.ecount[si] += 1
        self.links_version += 1
        return changed

    def _start_round(self, first=False):
        t = self.r * self.R
        changed = set()
        if not first:
            self._close_round()
        self._readings()
        self._gradients()
        if not first:
            cuts, found = self._reviews()
            if cuts.any():
                D_end = self.det_rate(self.E)   # the state as the round closed, before the cuts
                for si, e, by, rec, n, decl in found:
                    i, j = int(self.ei[si, e]), int(self.ej[si, e])
                    self._event({"ev": "cut", "seed": self.seeds[si], "round": self.r, "t": t,
                                 "by": self.names[by], "link": [self.names[i], self.names[j]],
                                 "record": rec, "rounds": n, "declining": decl})
                    self.cut_log.append({"seed": self.seeds[si], "round": self.r, "by": self.names[by],
                                         "link": [self.names[i], self.names[j]], "record": rec, "rounds": n})
                for si, e in zip(*np.nonzero(cuts)):
                    for x in (int(self.ei[si, e]), int(self.ej[si, e])):
                        if self.alive[si, x]:
                            changed.add((si, x))
                self.elive &= ~cuts
                self.links_version += 1
                for si, x in sorted(changed):
                    self._end_cfg(si, x, t, "cut", D_row=D_end[si], E_row=self.E[si])
            for si, x in self._entry(t):
                if self.cfg_of[si, x] >= 0:
                    self._end_cfg(si, x, t, "new link")
                changed.add((si, x))
        # the round's flows, then the round's samples
        self.eact = self.elive.copy()
        self._compute_flows()
        D = self.det_rate(self.E)
        if first:
            changed = {(si, i) for si in range(self.S) for i in range(self.N)}
        for si, x in sorted(changed):
            if self.alive[si, x]:
                self._new_cfg(si, x, t, self.E[si], D[si])
        loss = self._cfg_loss(D)
        pos = np.where(loss > 0, loss, np.inf)
        has = self.alive & (self.cfg_of >= 0)
        clocked = has & ~np.isnan(self.k_clock)
        self.k_minloss = np.where(clocked, np.minimum(self.k_minloss, pos), self.k_minloss)
        self.k_roundmin = np.where(has, pos, np.inf)
        cpl = self._cp_loss(self.E)
        cpos = np.where((cpl > 0) & ~(loss > 0), cpl, np.inf)     # point 14: only where the whole gains
        self.k_cpminloss = np.where(clocked, np.minimum(self.k_cpminloss, cpos), self.k_cpminloss)
        self.k_cproundmin = np.where(has, cpos, np.inf)
        cposall = np.where(cpl > 0, cpl, np.inf)                  # point 19: at every sample
        self.k_cpminall = np.where(clocked, np.minimum(self.k_cpminall, cposall), self.k_cpminall)
        self.k_cproundall = np.where(has, cposall, np.inf)
        # point 21: the samples up to this round's start, kept, in case this round's close finds the turn
        self.k_rs = np.where(clocked[None], np.stack([self.k_minloss, self.k_cpminloss, self.k_cpminall]), np.inf)
        self.E_snap = self.E.copy()
        if self.log is not None:
            self.log.rounds(self)

    def _ruin(self, hit, E_old, E_new, n, t0):
        """Step 8: ruin, with its time found by straight-line interpolation within the substep."""
        P = self.P
        frac = np.where(hit, (E_old - P["E_r"]) / np.where(hit, E_old - E_new, 1.0), 0.0)
        t_hit = t0 + (n + frac) * self.dt
        self._bank(n + 1)                      # every link was live through this substep
        self.links_version += 1
        pending = []
        for si in np.nonzero(hit.any(1))[0]:
            ops = np.nonzero(hit[si])[0]
            tr = float(t_hit[si, ops].min())
            fr = (tr - t0) / self.dt - n       # the state at the moment of ruin, by the same interpolation
            E_at = E_old[si] + (E_new[si] - E_old[si]) * fr
            D_at = self.F[si] - self.a[si] * E_at
            if P["k"]:
                D_at = D_at + P["k"] * (self.W[si] @ E_at - self.L[si] * E_at)
            affected = set()
            for i in ops:
                ti = float(t_hit[si, i])
                self.ruin_t[si, i] = ti
                self._event({"ev": "ruin", "seed": self.seeds[si], "op": self.names[i], "t": ti})
                self.ruin_list.append({"seed": self.seeds[si], "op": self.names[i], "t": ti,
                                       "type": TNAME[self.typ[si, i]]})
                if self.cfg_of[si, i] >= 0 and math.isnan(self.k_clock[si, i]):
                    # B2's section 7: a fall in no watched configuration, reported with its links and drift; it fires
                    # nothing. Its own records over the last w rounds on each live link.
                    own = []
                    for e in np.nonzero(self.elive[si] & ((self.ei[si] == i) | (self.ej[si] == i)))[0]:
                        mine = 0 if self.ei[si, e] == i else 1
                        other = int(self.ej[si, e]) if mine == 0 else int(self.ei[si, e])
                        own.append({"to": self.names[other], "to_type": TNAME[self.typ[si, other]],
                                    "its_record_last_w_rounds": float(self.ebuf[si, e, mine].sum()),
                                    "theirs": float(self.ebuf[si, e, 1 - mine].sum())})
                    self.falls_unwatched.append({"seed": self.seeds[si], "op": self.names[i], "t": ti,
                                                 "type": TNAME[self.typ[si, i]], "drift": float(self.a[si, i]),
                                                 "links": own})
                self._end_cfg(si, i, ti, "ruin", D_row=D_at, E_row=E_at)
                for e in np.nonzero(self.elive[si] & ((self.ei[si] == i) | (self.ej[si] == i)))[0]:
                    self.elive[si, e] = False
                    other = int(self.ej[si, e]) if self.ei[si, e] == i else int(self.ei[si, e])
                    if not hit[si, other]:
                        affected.add(other)
            self.alive[si, ops] = False
            for x in sorted(affected):
                self._end_cfg(si, x, tr, "counterparty ruined", D_row=D_at, E_row=E_at)
            pending.append((si, sorted(affected), tr, E_at))
        self._compute_flows()                  # the flows change from the next substep
        for si, aff, tr, E_at in pending:
            D_row = self.F[si] - self.a[si] * E_at
            if P["k"]:
                D_row = D_row + P["k"] * (self.W[si] @ E_at - self.L[si] * E_at)
            for x in aff:
                self._new_cfg(si, x, tr, E_at, D_row)

    def _substeps(self):
        P, dt = self.P, self.dt
        t0 = self.r * self.R
        noise = P["sigma_s"] > 0
        if noise:
            Z = np.empty((self.S, self.n_sub, self.N))
            for si, rng in enumerate(self.rngs):
                Z[si] = rng.standard_normal((self.n_sub, self.N))
            sq = P["sigma_s"] * math.sqrt(dt)
        k = P["k"]
        E_r, E_max = P["E_r"], P["E_max"]
        E = self.E
        for n in range(self.n_sub):
            En = E * self.A1 + self.B1
            if noise:
                En += sq * Z[:, n, :] * self.alive
            if k:
                En += (dt * k) * (np.matmul(self.W, E[..., None])[..., 0] - self.L * E) * self.alive
                lv = self.elive
                Ei = np.take_along_axis(E, self.ei, 1)
                Ej = np.take_along_axis(E, self.ej, 1)
                flow = np.where(lv, (dt * k) * (Ej - Ei), 0.0)
                self.eacc[..., 0] += flow           # passive flow received through the link, per end
                self.eacc[..., 1] -= flow
                self.eacc_pf[..., 0] += flow        # the same, kept apart for B2's section 10
                self.eacc_pf[..., 1] -= flow
            if E_max is not None:
                np.minimum(En, E_max, out=En)
            hit = En <= E_r
            hit &= self.alive
            if hit.any():
                self._ruin(hit, E, En, n, t0)
            if self.track_minmax:
                np.minimum(self.Emin, En, out=self.Emin)
                np.maximum(self.Emax_seen, En, out=self.Emax_seen)
            E = En
        self.E = E

    def run(self, run_to=None, horizon=None, progress=None):
        """Runs to a fixed time: a hypothesis's cell runs ROUNDS rounds (Part Nine, point 4). The horizon of
        Phase 0, ten times the longest bound, is kept only to time cells outside every hypothesis."""
        self.r = 0
        self._start_round(first=True)
        self.reached_cap = False
        while True:
            self._substeps()
            self.r += 1
            t = self.r * self.R
            if run_to is not None and t >= run_to - 1e-12:
                self._close_round()
                break
            if horizon is not None:
                need = max(horizon["min_rounds"] * self.R, horizon["factor"] * self.longest_bound())
                if t >= need - 1e-12 or self.r >= horizon["max_rounds"]:
                    self.reached_cap = self.r >= horizon["max_rounds"] and t < need - 1e-12
                    self._close_round()
                    break
            if progress and self.r % 200 == 0:
                progress(self)
            self._start_round()
        self.t_end = self.r * self.R
        for si in range(self.S):
            for i in range(self.N):
                if self.cfg_of[si, i] >= 0:
                    self._end_cfg(si, i, self.t_end, "run ended")
        return self
