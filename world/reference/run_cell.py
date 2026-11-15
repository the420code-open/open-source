"""Runs one cell of the world for its seeds, and writes its packet, its summary and its log.

    python world/reference/run_cell.py CELL.json --seeds 0-99 --out DIR [--log sample:5|full|events|none]

The cell file names the setting, its overrides, the network, the types, the noise, entry and the label. Every
cell runs 4,000 rounds (the specification's Part Nine, point 4), unless it is a cell outside every hypothesis
that names its own "rounds" or "horizon". The packet is JSON Lines: a head, then one line per seed. The summary
gives, for each set of configurations the hypotheses watch, Part Nine's measure: for each seed, the largest
survival in spans, less the record window where at least one counterparty is type C; then their mean across
seeds,
its standard error and its zone. A seed with any watched configuration too long to judge in this run is left
out whole, counted and reported; so is a seed left with nothing to watch (B1, section 7, draft 3); if more than
one seed in ten is left out, the two counted together, the cell settles nothing. The log is
JSON Lines, gzipped: by default (Part Nine, point 11) every event for every seed, and the round lines, one per
live operator per round, for the first five seeds.

Zero-Clause BSD.
"""
import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import engine  # noqa: E402

SPEC_FILE = os.path.join(HERE, "..", "spec", "world_spec_v1.0.md")
CODE_FILES = ("engine.py", "run_cell.py")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def code_version():
    h = hashlib.sha256()
    for name in CODE_FILES:
        h.update(open(os.path.join(HERE, name), "rb").read())
    return h.hexdigest()


def parse_seeds(text):
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


class Log:
    """full: a line per live operator per round, for every seed, and every event.
    sample:K: those round lines for the first K seeds only, and every event for every seed.
    events: every event, no round lines. none: no log."""

    def __init__(self, path, level, head):
        self.level = level
        self.k = int(level.split(":")[1]) if level.startswith("sample:") else None
        self.f = gzip.open(path, "wt", encoding="utf-8", compresslevel=6) if level != "none" else None
        self._nb, self._ver = None, None
        if self.f:
            self.f.write(json.dumps(head, separators=(",", ":")) + "\n")

    def event(self, ev):
        if self.f:
            self.f.write(json.dumps(ev, separators=(",", ":"), default=float) + "\n")

    def rounds(self, W):
        if self.level != "full" and self.k is None:
            return
        n_seeds = W.S if self.k is None else min(self.k, W.S)
        if self._ver != (W.links_version, W.N):
            nb = [{} for _ in range(n_seeds)]
            lv = W.elive
            for si in range(n_seeds):
                d = nb[si]
                for e in np.nonzero(lv[si])[0]:
                    i, j = int(W.ei[si, e]), int(W.ej[si, e])
                    d.setdefault(i, []).append(W.names[j])
                    d.setdefault(j, []).append(W.names[i])
                for key in d:
                    d[key] = json.dumps(sorted(d[key], key=str))
            self._nb, self._ver = nb, (W.links_version, W.N)
        nb = self._nb
        rows = []
        for si, i in zip(*np.nonzero(W.alive[:n_seeds])):
            sl = W.slope[si, i]
            rows.append('{"seed":%d,"r":%d,"op":%s,"type":"%s","E":%.10g,"reading":%.10g,"slope":%s,'
                        '"declining":%s,"links":%s}' % (
                            W.seeds[si], W.r, json.dumps(W.names[i]), engine.TNAME[W.typ[si, i]], W.E[si, i],
                            W.reading[si, i], "null" if math.isnan(sl) else "%.10g" % sl,
                            "true" if W.declining[si, i] else "false",
                            nb[si].get(int(i), "[]")))
        self.f.write("\n".join(rows) + "\n")

    def close(self):
        if self.f:
            self.f.close()


CONTROL_WORDS = {"fires": "a defector lasts", "holds": "no defector lasts"}
CONTROL_WORDS_B2 = {"fires": "a configuration lasts", "holds": "no configuration lasts"}
FIRES_NOTHING = "control: fires nothing"


def is_control(cell):
    """A control cell, outside the premises: one that says so, or one whose every host is of type U."""
    return bool(cell.get("control")) or cell.get("types", {}).get("hosts") == "U"


def control_words(summary):
    """B1, section 10: a control cell is never printed as "fires" or "holds". It is printed as "a defector lasts" or
    "no defector lasts", with "control: fires nothing" beside it."""
    for name, v in summary.items():
        if isinstance(v, dict):
            # B2, section 10: "a configuration lasts", with its kind, or "no configuration lasts"
            words = CONTROL_WORDS_B2 if name == "B2" else CONTROL_WORDS
            subs = [x for x in v.values() if isinstance(x, dict)]
            subs += [y for x in subs for y in x.values() if isinstance(y, dict)]
            for m in [v] + subs:
                if "zone" in m:
                    m["zone"] = words.get(m["zone"], m["zone"])
                    m["control"] = FIRES_NOTHING
    return summary


def zone(mean, se, line=3.0):
    if mean + 2 * se <= line:
        return "holds"
    if mean - 2 * se > line:
        return "fires"
    return "settles nothing"


def measure(seeds, chosen, key):
    """Part Nine, points 4 and 6. For each seed, the largest survival in spans among its watched configurations.
    A seed with any watched configuration too long to judge in this run is left out of the mean whole. A seed
    left with nothing to watch is left out of the mean, counted and reported, and it counts towards the one in
    ten (B1, section 7). If more than one seed in ten is left out, the cell settles nothing."""
    by = {s: [] for s in seeds}
    for c in chosen:
        if c.get("span"):
            by[c["seed"]].append(c)
    vals, left_out, without, per_seed = [], [], 0, {}
    for s in seeds:
        cs = by[s]
        if not cs:
            without += 1
            continue
        too_long = [c for c in cs if not c["judged"]]
        if too_long:
            left_out.append({"seed": s, "too_long_to_judge": [
                {"cfg": c["id"], "owner": c["owner"], "survival_so_far": c["survival"], "span": c["span"],
                 "bound": c["bound"], "survival_spans_so_far": c[key]} for c in too_long]})
            continue
        vals.append(max(c[key] for c in cs))
        per_seed[s] = vals[-1]
    n = len(vals)
    out = {"seeds": len(seeds), "seeds_measured": n, "seeds_without_a_watched_configuration": without,
           "seeds_left_out": len(left_out), "left_out": left_out,
           "seeds_not_in_the_mean": len(left_out) + without, "per_seed": per_seed}
    if n:
        mean = float(np.mean(vals))
        se = float(np.std(vals, ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
        out.update(mean=mean, se=se, largest_seed=float(max(vals)),
                   zone=zone(mean, se if math.isfinite(se) else float("inf")))
    if (len(left_out) + without) * 10 > len(seeds):
        out["zone"] = "settles nothing"
        out["why"] = ("%d of %d seeds left out, more than one in ten: %d too long to judge, %d with nothing to "
                      "watch" % (len(left_out) + without, len(seeds), len(left_out), without))
    elif not n:
        out["zone"] = "settles nothing"
        out["why"] = "no seed has a watched configuration with a span"
    return out


def summarise(W, cfg_dicts, seconds):
    S = W.S
    out = {}
    watch = {
        "B1": lambda c: c["has_watched_defector"],     # a defector that starts with no live link is not watched
        # B2, section 6: every configuration whose clock started, less those outside the premises (reported in full)
        "B2": lambda c: not c.get("outside_the_premises"),
    }
    for name, keep in watch.items():
        chosen = [c for c in cfg_dicts if c.get("clock_start") is not None and keep(c)]
        timed = [c for c in chosen if c.get("span")]
        used = {}
        for c in chosen:
            used[c.get("span_used") or "none"] = used.get(c.get("span_used") or "none", 0) + 1
        reasons = {}
        for c in chosen:
            reasons[c["end_reason"]] = reasons.get(c["end_reason"], 0) + 1
        out[name] = {
            "watched": "configurations with a defector in them, from their clock's start; a defector that "
                       "starts with no live link is reported, and not watched" if name == "B1" else
                       "every configuration whose clock started (net-negative for any reason)",
            "configurations": len(chosen),
            "span_used": used,
            "no_span": len(chosen) - len(timed),
            "still_standing_at_end": sum(c["end_reason"] == "run ended" for c in chosen),
            "too_long_to_judge": sum(1 for c in timed if not c["judged"]),
            "point_19": {"applied": sum(1 for c in chosen if c.get("span_used") == "counterparties (point 19)"),
                         "applies_with_no_span": sum(1 for c in chosen if c.get("point_19") == "applies, but the counterparties lost at no sample: no span"),
                         "not_the_shorter": sum(1 for c in chosen if c.get("point_19_not_applied"))},
            "point_14": {"applied": sum(1 for c in chosen if c.get("point_14"))},
            "point_21": {"applied": sum(1 for c in chosen if c.get("point_21"))},
            "point_22": {"applied": sum(1 for c in chosen if c.get("span_used") == "counterparties (point 22)"),
                         "applies_with_no_span": sum(1 for c in chosen if c.get("point_22") == "applies, but the counterparties lost at no sample: no span"),
                         "not_the_shorter": sum(1 for c in chosen if c.get("point_22_not_applied"))},
            "kinds": {k: sum(1 for c in chosen if c.get("kind") == k)
                      for k in ("a defector's", "a sink's", "an operator alone")},
            "measure_by_kind": {k: measure(W.seeds, [c for c in chosen if c.get("kind") == k], "survival_spans_net")
                                for k in ("a defector's", "a sink's", "an operator alone")},
            "ended_by": reasons,
            "within_bound": sum(bool(c.get("within_bound")) for c in timed),
            "measure": measure(W.seeds, chosen, "survival_spans_net"),
            "for_reference_without_the_window": measure(W.seeds, chosen, "survival_spans"),
        }
    # defectors
    D = engine.TYPES["D"]
    dcount = []
    for si in range(S):
        for i in range(W.N):
            if W.typ[si, i] == D:
                dcount.append(sum(1 for c in cfg_dicts if c["seed"] == W.seeds[si] and c["owner"] == W.names[i]))
    druin = [r["t"] for r in W.ruin_list if r["type"] == "D"]
    n_def = int((W.typ == D).sum())
    out["defectors"] = {
        "defectors": n_def,
        "ruined": len(druin),
        "mean_ruin_time": float(np.mean(druin)) if druin else None,
        "configurations_passed_through": {"mean": float(np.mean(dcount)) if dcount else None,
                                          "max": int(max(dcount)) if dcount else None},
    }
    # B2's end-of-run counts: links net-positive for both ends, on their last w rounds; the stocks still standing
    w = W.P["w"]
    lv = W.elive
    n_rec = np.minimum(W.eage, w)
    rec = W.ebuf.sum(-1)
    both = lv & (rec[..., 0] > 0) & (rec[..., 1] > 0) & (n_rec > 0)
    standing = W.E[W.alive]
    out["end_of_run"] = {
        "live_links": int(lv.sum()),
        "share_net_positive_both_ends": float(both.sum() / lv.sum()) if lv.sum() else None,
        "operators_standing": int(W.alive.sum()),
        "stock_standing": {"mean": float(standing.mean()) if standing.size else None,
                           "min": float(standing.min()) if standing.size else None,
                           "max": float(standing.max()) if standing.size else None},
        "ruined": {"C": sum(r["type"] == "C" for r in W.ruin_list), "U": sum(r["type"] == "U" for r in W.ruin_list),
                   "D": len(druin)},
        "cuts": len(W.cut_log),
    }
    # B1's premise check, seed by seed: every host type C, drift irreversible, and each defector coupled, starting
    # with at least one live link. A defector that starts with no live link is reported, and not watched.
    hosts_c = [bool(((W.typ[si] == engine.TYPES["C"]) | (W.typ[si] == D)).all()) for si in range(S)]
    drift = [bool((W.a[si] > 0).all()) for si in range(S)]
    unc = [{"seed": W.seeds[si], "defectors": [W.names[i] for i in sorted(W.uncoupled_defectors[si])]}
           for si in range(S) if W.uncoupled_defectors[si]]
    out["premise_check"] = {
        "hosts_all_type_C": all(hosts_c),
        "seeds_with_a_host_not_type_C": [W.seeds[si] for si in range(S) if not hosts_c[si]],
        "drift_irreversible": all(drift),
        "defectors": n_def,
        "defectors_coupled_at_start": n_def - sum(len(u["defectors"]) for u in unc),
        "defectors_with_no_live_link_at_start_reported_not_watched": unc,
        "seeds_with_every_defector_coupled": S - len(unc),
        "seeds_network_connected_at_start_for_information": int(sum(W.premise_coupled)),
        "links_between_two_defectors_left_out": {
            "seeds": sum(1 for x in W.links_left_out if x), "links": sum(len(x) for x in W.links_left_out)},
    }
    out["run"] = {"t_end": W.t_end, "rounds": W.r, "longest_bound": W.longest_bound(),
                  "horizon_cap_reached": getattr(W, "reached_cap", False), "seconds": seconds}
    rep = b2_reports(W, cfg_dicts)
    out["B2_reports"] = {
        "configurations_left_out_as_outside_the_premises": sum(len(v) for v in rep["outside_the_premises"].values()),
        "configurations_returned_to_zero_or_above_and_below_again": sum(len(v) for v in rep["returned_and_went_below_again"].values()),
        "cuts_of_one_type_C_operator_by_another": sum(len(v) for v in rep["cuts_of_C_by_C"].values()),
        "defectors_standing_at_the_end": sum(len(v) for v in rep["defectors_standing"].values()),
        "falls_in_no_watched_configuration": sum(len(v) for v in rep["falls_in_no_watched_configuration"].values()),
        "watched_sinks_with_their_records_less_passive_flow": sum(len(v) for v in rep["watched_sinks"].values()),
        "configurations_with_a_counterparty": rep["with_a_counterparty"],
        "watched_by_the_window_point_20": rep["watched_by_the_window"],
        "watched_by_one_round_record_alone": rep["one_round_would_watch"],
        "lasted_more_than_one_span_then_ended": rep["lasted_more_than_one_span_then_ended"],
    }
    W.b2_reports = rep
    return out


def b2_reports(W, cfg_dicts):
    """B2's section 10, seed by seed: what every packet reports beside the configurations."""
    S, D, C = W.S, engine.TYPES["D"], engine.TYPES["C"]
    by = {s: [] for s in W.seeds}
    for c in cfg_dicts:
        by[c["seed"]].append(c)
    typ = {(W.seeds[si], W.names[i]): engine.TNAME[W.typ[si, i]] for si in range(S) for i in range(W.N)}
    rep = {k: {} for k in ("outside_the_premises", "returned_and_went_below_again", "cuts_of_C_by_C",
                           "defectors_standing", "falls_in_no_watched_configuration", "watched_sinks")}
    with_cp = watched_w = would1 = lasted = 0
    for si, s in enumerate(W.seeds):
        cs = by[s]
        rep["outside_the_premises"][s] = [c for c in cs if c.get("outside_the_premises")]
        rep["returned_and_went_below_again"][s] = [{"cfg": c["id"], "owner": c["owner"], "dips": c["returned_and_went_below_again"]}
                                                    for c in cs if c.get("returned_and_went_below_again")]
        rep["cuts_of_C_by_C"][s] = [x for x in W.cut_log if x["seed"] == s and typ[(s, x["link"][0])] == "C"
                                    and typ[(s, x["link"][1])] == "C"]
        rep["watched_sinks"][s] = [{"cfg": c["id"], "owner": c["owner"], "clock_start": c["clock_start"],
                                    **c["sink_records_when_its_clock_started"]}
                                   for c in cs if c.get("clock_start") is not None and c.get("kind") == "a sink's"
                                   and c.get("sink_records_when_its_clock_started")]
        rep["falls_in_no_watched_configuration"][s] = [f for f in W.falls_unwatched if f["seed"] == s]
        stand = []
        for i in range(W.N):
            if W.typ[si, i] == D and W.alive[si, i]:
                hosts = []
                for e in np.nonzero(W.elive[si] & ((W.ei[si] == i) | (W.ej[si] == i)))[0]:
                    end = 1 if W.ei[si, e] == i else 0          # the host's end
                    h = int(W.ej[si, e]) if end == 1 else int(W.ei[si, e])
                    hosts.append({"host": W.names[h], "type": engine.TNAME[W.typ[si, h]],
                                  "record_last_w_rounds": float(W.ebuf[si, e, end].sum()),
                                  "record_whole": float(W.etotal[si, e, end])})
                stand.append({"defector": W.names[i], "stock": float(W.E[si, i]), "hosts": hosts})
        rep["defectors_standing"][s] = stand
        for c in cs:
            if len(c["members"]) > 1:
                with_cp += 1
                watched_w += c.get("clock_start") is not None
                would1 += bool(c.get("one_round_record_alone_would_watch"))
            # AG Opus, 15 November 2026: survival as B2 measures it, less the record window where at least one
            # counterparty is of type C
            if c.get("span") and c.get("end_reason") != "run ended" and c.get("survival_spans_net", 0) > 1:
                lasted += 1
    rep.update(with_a_counterparty=with_cp, watched_by_the_window=watched_w, one_round_would_watch=would1,
               lasted_more_than_one_span_then_ended=lasted)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell")
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", default="sample:5", help="sample:K (Part Nine: sample:5), full, events or none")
    a = ap.parse_args()
    cell = json.load(open(a.cell, encoding="utf-8"))
    seeds = parse_seeds(a.seeds)
    os.makedirs(a.out, exist_ok=True)
    P = engine.params_for(cell["setting"], cell.get("overrides"))
    head = {"kind": "world run", "label": cell.get("label", ""), "cell": cell.get("id"),
            "specification": engine.SPEC, "specification_sha256": sha256(SPEC_FILE),
            "code": "world/reference (" + ", ".join(CODE_FILES) + ")", "code_sha256": code_version(),
            "parameters": P, "cell_definition": cell, "seeds": seeds,
            "generator": "numpy %s default_rng(seed), PCG64; per seed: random links, defectors' places, uneven "
                         "drift; then each round: reading noise, an entry's choices, stock noise" % np.__version__,
            "python": platform.python_version(), "date": time.strftime("%Y-%m-%d"), "log_level": a.log}
    if is_control(cell):
        head["control"] = FIRES_NOTHING
    log = Log(os.path.join(a.out, "log.jsonl.gz"), a.log, head)
    t0 = time.time()
    W = engine.World(cell, seeds, log=log)
    if cell.get("horizon"):          # only a cell outside every hypothesis, timed as Phase 0 had it
        run_to, horizon = None, cell["horizon"]
    else:
        run_to, horizon = cell.get("run_to", cell.get("rounds", engine.ROUNDS) * engine.params_for(
            cell["setting"], cell.get("overrides"))["round"]), None
    W.run(horizon=horizon, run_to=run_to,
          progress=lambda w: print("  round %d, t = %.0f, longest bound %.1f, %.0f s" % (
              w.r, w.r * w.R, w.longest_bound(), time.time() - t0), flush=True))
    seconds = time.time() - t0
    log.close()
    cfg_dicts = []
    for c in W.cfgs:
        d = c.as_dict(W.R, W.P["w"])
        d["seed"] = c.seed
        cfg_dicts.append(d)
    summary = summarise(W, cfg_dicts, seconds)
    with open(os.path.join(a.out, "packet.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(head) + "\n")
        for si, s in enumerate(seeds):
            f.write(json.dumps({
                "seed": s,
                "network_connected_at_start": W.premise_coupled[si],
                "defectors_with_no_live_link_at_start": [W.names[i] for i in sorted(W.uncoupled_defectors[si])],
                "links_between_two_defectors_left_out": W.links_left_out[si],
                "defectors": [W.names[i] for i in range(W.N) if W.typ[si, i] == engine.TYPES["D"]],
                "ruins": [r for r in W.ruin_list if r["seed"] == s],
                "cuts": [c for c in W.cut_log if c["seed"] == s],
                "configurations": [c for c in cfg_dicts if c["seed"] == s and c.get("clock_start") is not None],
                "configurations_total": sum(1 for c in cfg_dicts if c["seed"] == s),
                "standing": {str(W.names[i]): float(W.E[si, i]) for i in range(W.N) if W.alive[si, i]},
                # B2's section 10, seed by seed
                "configurations_outside_the_premises": [c["id"] for c in W.b2_reports["outside_the_premises"][s]],
                "returned_to_zero_or_above_and_below_again": W.b2_reports["returned_and_went_below_again"][s],
                "cuts_of_one_type_C_operator_by_another": W.b2_reports["cuts_of_C_by_C"][s],
                "defectors_standing_at_the_end": W.b2_reports["defectors_standing"][s],
                "falls_in_no_watched_configuration": W.b2_reports["falls_in_no_watched_configuration"][s],
                "watched_sinks_records_when_their_clocks_started": W.b2_reports["watched_sinks"][s],
                "one_round_record_alone_would_watch": sum(1 for c in cfg_dicts if c["seed"] == s and
                                                          c.get("one_round_record_alone_would_watch")),
            }, default=float) + "\n")
    if is_control(cell):
        control_words(summary)
    summary = {"label": cell.get("label", ""), "cell": cell.get("id"), "seeds": len(seeds),
               **({"control": FIRES_NOTHING} if is_control(cell) else {}), **summary,
               "files": {"packet.jsonl": sha256(os.path.join(a.out, "packet.jsonl"))}}
    if a.log != "none":
        summary["files"]["log.jsonl.gz"] = sha256(os.path.join(a.out, "log.jsonl.gz"))
        summary["log_bytes"] = os.path.getsize(os.path.join(a.out, "log.jsonl.gz"))
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
