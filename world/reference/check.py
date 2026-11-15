"""Runs every line of world/test-values.json on the reference engine, and a few checks of its own.

Exit code 1 if any line fails. `--json PATH` also writes every line's result as JSON.

Zero-Clause BSD.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine  # noqa: E402
import formulas  # noqa: E402

TV = os.path.join(HERE, "..", "test-values.json")


def run_case(case):
    cell = {"setting": case["setting"], "overrides": case.get("overrides", {}), "types": case.get("types", {})}
    if case.get("topology"):
        cell["topology"] = case["topology"]
    if case.get("operators"):
        cell["operators"] = case["operators"]
    return engine.World(cell, [0], track_minmax=True).run(run_to=case["run_to"])


def line(case_id, what, expected, got, tol, ok=None, note=""):
    if ok is None:
        ok = got is not None and expected is not None and abs(got - expected) <= tol + 1e-12
    return {"id": case_id, "what": what, "expected": expected, "got": got, "tol": tol, "pass": bool(ok), "note": note}


def check_case(case):
    out = []
    W = None
    if case.get("setting"):
        W = run_case(case)
        idx = {nm: k for k, nm in enumerate(W.names)}
    for ch in case["checks"]:
        w = ch["what"]
        tol = ch.get("tol", 0)
        if w == "ruin_time":
            t = W.ruin_t[0, idx[ch["operator"]]]
            out.append(line(case["id"], "ruin time of %s" % ch["operator"], ch["value"],
                            None if math.isnan(t) else float(t), tol))
        elif w == "never_ruined":
            t = W.ruin_t[0, idx[ch["operator"]]]
            out.append(line(case["id"], "%s never ruined to %s" % (ch["operator"], case["run_to"]), "never",
                            "never" if math.isnan(t) else float(t), 0, ok=math.isnan(t)))
        elif w == "stock_at":
            assert abs(ch["t"] - case["run_to"]) < 1e-12
            out.append(line(case["id"], "stock of %s at %s" % (ch["operator"], ch["t"]), ch["value"],
                            float(W.E[0, idx[ch["operator"]]]), tol))
        elif w == "stock_min":
            out.append(line(case["id"], "lowest stock of %s" % ch["operator"], ch["value"],
                            float(W.Emin[0, idx[ch["operator"]]]), tol))
        elif w == "stock_max":
            out.append(line(case["id"], "highest stock of %s" % ch["operator"], ch["value"],
                            float(W.Emax_seen[0, idx[ch["operator"]]]), tol))
        elif w == "configuration":
            found = None
            for c in W.cfgs:
                if c.owner == ch["operator"] and sorted(c.members) == sorted(ch["members"]) and \
                        c.clock is not None and abs(c.clock - ch["clock_start"]) <= tol:
                    found = c.as_dict(W.R, W.P["w"])
                    break
            label = "configuration of %s, members %s, clock from %s" % (ch["operator"], ",".join(ch["members"]),
                                                                          ch["clock_start"])
            if not found:
                out.append(line(case["id"], label, "found", "not found", 0, ok=False))
                continue
            for key, fk in (("stock_above_ruin", "stock_above_ruin"), ("net_loss_per_round", "net_loss_per_round"),
                            ("span", "span"), ("end", "end")):
                out.append(line(case["id"], "%s: %s" % (label, key), ch[key], found.get(fk), tol))
        elif w == "no_cut":
            out.append(line(case["id"], "no cut", 0, len(W.cut_log), 0, ok=not W.cut_log))
        elif w == "cut":
            hit = [c for c in W.cut_log if c["round"] == ch["round"] and c["by"] == ch["by"] and
                   sorted(c["link"]) == sorted(ch["link"]) and c["rounds"] == ch["record_rounds"]]
            out.append(line(case["id"], "cut at round %d by %s, on %d round of record" % (
                ch["round"], ch["by"], ch["record_rounds"]), "1 cut", "%d cut%s; all cuts: %s" % (
                len(hit), "" if len(hit) == 1 else "s", W.cut_log), 0, ok=len(hit) == 1 and len(W.cut_log) == 1))
        elif w == "formula":
            got = formulas.evaluate(ch["name"], ch["inputs"], ch.get("output"))
            out.append(line(case["id"], "%s %s" % (ch["name"], ch.get("output", "")), ch["value"], got, tol))
        elif w == "engine_lone":
            cell = {"setting": ch["setting"], "overrides": ch["overrides"], "operators": ["X"], "topology": "none"}
            L = engine.World(cell, [0]).run(run_to=ch["t"])
            out.append(line(case["id"], "lone operator by the engine, t = %s" % ch["t"], ch["value"],
                            float(L.E[0, 0]), tol))
        else:
            raise KeyError(w)
    return out


def own_checks():
    """Checks of the engine beyond the test values: AP02's steady states reached by the engine itself."""
    out = []
    # Theorem VI.1 through the engine: own effort as own input, a passive link, no giving.
    r = formulas.coupled_steady_state(0.2, 0.6, 1.0, 0.1)
    cell = {"setting": "network", "operators": ["1", "2"], "topology": "pair", "types": {"1": "U", "2": "U"},
            "overrides": {"g": 0.0, "eps": 0.0, "k": 0.1, "E_r": -1e9, "E0": 1.0, "lam": 1.0},
            "own": {"a": {"1": 0.2, "2": 0.6}, "s": {"1": r["u1"], "2": r["u2"]}}}
    W = engine.World(cell, [0]).run(run_to=400)
    out.append(line("own.VI.1", "E1 by the engine", r["E1"], float(W.E[0, 0]), 1e-6))
    out.append(line("own.VI.1", "E2 by the engine", r["E2"], float(W.E[0, 1]), 1e-6))
    # Theorem II.1 through the engine: a lone operator at its least-cost effort settles at x = u/a.
    u = formulas.least_cost_effort(0.5, 2.0)
    cell = {"setting": "network", "operators": ["X"], "topology": "none",
            "overrides": {"a": 0.5, "s": u, "E_r": -1e9, "E0": 0.0}}
    W = engine.World(cell, [0]).run(run_to=100)
    out.append(line("own.II.1", "least-cost point by the engine", formulas.least_cost_point(0.5, 2.0),
                    float(W.E[0, 0]), 1e-6))
    out.extend(part_nine_checks())
    return out


class Events:
    def __init__(self):
        self.evs = []

    def event(self, ev):
        self.evs.append(ev)

    def rounds(self, W):
        pass


def cfg_of(W, owner):
    return [c.as_dict(W.R, W.P["w"]) for c in W.cfgs if c.owner == owner and c.clock is not None]


def part_nine_checks():
    """The specification's Part Nine, through the engine, on cases small enough to work out by hand."""
    out = []
    # Point 2: a configuration that gains as a whole but is net-negative for its counterparties. A ring of three,
    # D with two type C hosts, at m = 5: g = 2.5, each host pays 2.5^2 + 0.01 on its link to D, so the hosts lose
    # 12.52 a round through their links to D, while D gains 25 - 5 and each host -5.02: the whole gains 9.96.
    # The span is the hosts' stock above the ruin line, 2 x 40, over 12.52.
    cell = {"setting": "network", "operators": ["D", "H1", "H2"], "topology": "ring", "overrides": {"m": 5},
            "types": {"D": "D", "H1": "C", "H2": "C"}}
    W = engine.World(cell, [0]).run(run_to=3)
    c = cfg_of(W, "D")[0]
    out.append(line("own.IX.2", "gains as a whole: span used", "counterparties", c["span_used"], 0,
                    ok=c["span_used"] == "counterparties"))
    out.append(line("own.IX.2", "the counterparties' span, rounds", 80 / 12.52, c["span"], 1e-9))
    out.append(line("own.IX.5", "window subtracted where hosts are type C", 0.0, c["survival_spans_net"], 1e-12))
    # The page's case, the whole configuration losing: its span is the whole's, 200 over 18.
    cell = {"setting": "page_charger", "types": {"A": "U", "B": "D"}}
    W = engine.World(cell, [0]).run(run_to=20)
    c = cfg_of(W, "B")[0]
    out.append(line("own.IX.2", "loses as a whole: span used", "whole", c["span_used"], 0,
                    ok=c["span_used"] == "whole"))
    out.append(line("own.IX.2", "the whole's span, 200 over 18", 200 / 18, c["span"], 1e-6))
    out.append(line("own.IX.5", "no window where the counterparty is type U", c["survival_spans"],
                    c["survival_spans_net"], 1e-12))
    # B1's premise check, seed by seed: a defector that starts with no live link draws on no one. It is reported,
    # and not watched. Two defectors and a type C host, none linked.
    cell = {"setting": "network", "operators": ["D1", "D2", "H"], "topology": "none",
            "types": {"D1": "D", "D2": "D", "H": "C"}}
    W = engine.World(cell, [0])
    unc = sorted(W.names[i] for i in W.uncoupled_defectors[0])
    out.append(line("own.B1.7", "defectors with no live link at the start, reported", "['D1', 'D2']", str(unc), 0,
                    ok=unc == ["D1", "D2"]))
    W.run(run_to=3)
    watched = [c for c in W.cfgs if c.clock is not None and c.has_watched_defector]
    alone = [c for c in W.cfgs if c.clock is not None and c.has_defector]
    out.append(line("own.B1.7", "...and not watched, though alone their clocks start", "0 watched of %d" % len(alone),
                    "%d watched of %d" % (len(watched), len(alone)), 0, ok=not watched and len(alone) == 2))
    cell = {"setting": "network", "operators": ["D", "H1", "H2"], "topology": "ring", "overrides": {"m": 5},
            "types": {"D": "D", "H1": "C", "H2": "C"}}
    W = engine.World(cell, [0]).run(run_to=3)
    watched = [c for c in W.cfgs if c.clock is not None and c.has_watched_defector]
    out.append(line("own.B1.7", "a defector with live links at the start is watched", ">0 watched", len(watched), 0,
                    ok=len(watched) > 0 and not W.uncoupled_defectors[0]))
    # B1's section 7: a seed left with nothing to watch is left out of the mean, counted, and counts towards the one
    # in ten. Twenty seeds: one with nothing to watch, one too long to judge; then a second with nothing to watch.
    import run_cell
    def cfg(seed, v, judged=True):
        return {"seed": seed, "span": 1.0, "judged": judged, "id": seed, "owner": "D", "survival": v, "bound": 3.0,
                "survival_spans_net": v}
    chosen = [cfg(s, 0.5) for s in range(2, 20)] + [cfg(1, 0.2, judged=False)]
    m = run_cell.measure(list(range(20)), chosen, "survival_spans_net")
    out.append(line("own.B1.7", "nothing to watch: out of the mean, counted, two of twenty", "18 in, 2 out, not settled",
                    "%d in, %d out, %s" % (m["seeds_measured"], m["seeds_not_in_the_mean"],
                                         "not settled" if m["zone"] != "settles nothing" else "settles nothing"), 0,
                    ok=m["seeds_measured"] == 18 and m["seeds_not_in_the_mean"] == 2 and m["zone"] != "settles nothing"))
    m = run_cell.measure(list(range(20)), chosen[1:], "survival_spans_net")
    out.append(line("own.B1.7", "...a second with nothing to watch: over one in ten", "settles nothing", m["zone"], 0,
                    ok=m["zone"] == "settles nothing" and m["seeds_not_in_the_mean"] == 3))
    # No link joins two defectors. A ring of D1, D2, H: the ring would join D1 and D2; that link is left out, and
    # each defector keeps its link to H. A ring of D1, D2, D3, H: D1 - D2 and D2 - D3 are left out, so D2 starts
    # with no live link, and is reported and not watched.
    cell = {"setting": "network", "operators": ["D1", "D2", "H"], "topology": "ring",
            "types": {"D1": "D", "D2": "D", "H": "C"}}
    W = engine.World(cell, [0])
    nb = {W.names[i]: [W.names[j] for j in W.neighbours(0, i)] for i in range(3)}
    out.append(line("own.links", "ring D1 D2 H: D1 - D2 left out", "[['D1', 'D2']]; D1: H, D2: H",
                    "%s; D1: %s, D2: %s" % (W.links_left_out[0], ", ".join(nb["D1"]), ", ".join(nb["D2"])), 0,
                    ok=W.links_left_out[0] == [["D1", "D2"]] and nb["D1"] == ["H"] and nb["D2"] == ["H"]))
    cell = {"setting": "network", "operators": ["D1", "D2", "D3", "H"], "topology": "ring",
            "types": {"D1": "D", "D2": "D", "D3": "D", "H": "C"}}
    W = engine.World(cell, [0])
    unc = sorted(W.names[i] for i in W.uncoupled_defectors[0])
    out.append(line("own.links", "ring D1 D2 D3 H: two left out, D2 with no live link", "2 left out; ['D2']",
                    "%d left out; %s" % (len(W.links_left_out[0]), unc), 0,
                    ok=len(W.links_left_out[0]) == 2 and unc == ["D2"]))
    # ...and a hopper's offer to another defector makes no link: two lone defectors, newcomers of type D.
    ev = Events()
    cell = {"setting": "network", "operators": ["D1", "D2"], "topology": "none", "types": {"D1": "D", "D2": "D"},
            "entry": {"q": 10, "n": 0, "hopper": True, "type": "D"}}
    W = engine.World(cell, [0, 1], log=ev).run(run_to=31)
    hops = [e for e in ev.evs if e["ev"] == "hop"]
    out.append(line("own.links", "hops between defectors: no link", ">0, all 'no link joins two defectors'",
                    "%d, %d" % (len(hops), sum(e["outcome"] == "no link joins two defectors" for e in hops)), 0,
                    ok=bool(hops) and all(e["outcome"] == "no link joins two defectors" for e in hops) and not W.elive.any()))
    # Point 19, worked by hand. D and four type U hosts, all linked (p = 1), m = 5: each host's give of 2.5 a link
    # is scaled by capacity to 6/4 = 1.5, so on its link to D a host spends 1.5^2 + 0.01 = 2.26 a round, and gets
    # nothing back. The counterparties' net loss through their links to D is 4 x 2.26 = 9.04 at every sample; their
    # records over the last 5 rounds add to 4 x 5 x -2.26 = -45.2. No host is ruined.
    hosts = {"D": "D", "H1": "U", "H2": "U", "H3": "U", "H4": "U"}
    cell = {"setting": "network", "operators": list(hosts), "topology": "random", "p": 1.0, "types": hosts,
            "overrides": {"m": 5, "sigma_s": 2.0, "sigma_r": 1.0}}
    W = engine.World(cell, [0, 1, 2, 3]).run(run_to=400)
    cs = [c.as_dict(W.R, W.P["w"]) for c in W.cfgs if c.owner == "D" and c.clock is not None]
    # with noise, from 50: the counterparties' span is 160 / 9.04 = 17.699; at t = 400, 22.6 spans, judged. By
    # point 14 alone the whole's span ran past the run in every seed, and it was too long to judge.
    out.append(line("own.P19", "D and four U hosts, noise: the counterparties' span, 160/9.04", 160 / 9.04,
                    max(c["span"] for c in cs), 1e-9,
                    ok=len(cs) == 4 and all(abs(c["span"] - 160 / 9.04) < 1e-9 and c["point_19"] == engine.POINT_19
                                            for c in cs)))
    out.append(line("own.P19", "...records over the last 5 rounds, -45.2; point 14's span past the run", -45.2,
                    max(c["counterparties_records_last_w_rounds"] for c in cs), 1e-9,
                    ok=all(abs(c["counterparties_records_last_w_rounds"] + 45.2) < 1e-9 and c["span_by_point_14"] > 400
                           for c in cs)))
    out.append(line("own.P19", "...at t = 400: 22.6 spans, judged", 22.6, min(c["survival_spans_net"] for c in cs),
                    1e-9, ok=all(abs(c["survival_spans_net"] - 22.6) < 1e-9 and c["judged"] for c in cs)))
    # quiet, every stock from 200: the whole loses at every sample, so point 14's counterparties' span never applied;
    # point 19 takes their net loss at every sample: 760 / 9.04 = 84.071, and 400 / 84.071 = 4.758 spans, judged
    cell = {"setting": "network", "operators": list(hosts), "topology": "random", "p": 1.0, "types": hosts,
            "overrides": {"m": 5, "E0": 200.0}}
    W = engine.World(cell, [0]).run(run_to=400)
    c = cfg_of(W, "D")[0]
    out.append(line("own.P19", "quiet, from 200: the whole loses throughout; 760/9.04", 760 / 9.04, c["span"], 1e-9,
                    ok=abs(c["span"] - 760 / 9.04) < 1e-9 and c["span_counterparties"] is None
                    and c["span_used_by_point_14"] == "whole" and c["span_by_point_14"] > 400))
    out.append(line("own.P19", "...at t = 400: 4.758 spans, judged", 400 * 9.04 / 760, c["survival_spans_net"], 1e-9,
                    ok=abs(c["survival_spans_net"] - 400 * 9.04 / 760) < 1e-9 and c["judged"]))
    # an operator alone has no counterparty: a lone defector with own input 1.5 settles at 15, still too long to judge
    cell = {"setting": "network", "operators": ["D"], "topology": "none", "types": {"D": "D"}, "overrides": {"s": 1.5}}
    W = engine.World(cell, [0]).run(run_to=400)
    c = cfg_of(W, "D")[0]
    out.append(line("own.P19", "an operator alone: point 19 does not apply", "not applied, too long to judge",
                    "%s, %s" % ("applied" if c["point_19"] else "not applied",
                                "judged" if c["judged"] else "too long to judge"), 0,
                    ok=c["point_19"] is None and not c["judged"]))
    # B1, section 10: a control cell prints "a defector lasts" or "no defector lasts", never "fires" or "holds", with
    # "control: fires nothing" beside it; a cell of B1 keeps "fires" and "holds".
    sys.path.insert(0, HERE)
    import run_cell
    seeds = list(range(20))
    ctl = {"seeds": seeds, "zone": None}
    hi = run_cell.measure(seeds, [{"seed": s, "span": 1, "judged": True, "id": s, "owner": "D", "survival": 9,
                                   "bound": 3, "survival_spans_net": 9.0 + s % 2} for s in seeds], "survival_spans_net")
    lo = run_cell.measure(seeds, [{"seed": s, "span": 1, "judged": True, "id": s, "owner": "D", "survival": 0.3,
                                   "bound": 3, "survival_spans_net": 0.3 + 0.01 * (s % 2)} for s in seeds],
                          "survival_spans_net")
    words = [run_cell.control_words({"B1": {"measure": dict(m)}})["B1"]["measure"] for m in (hi, lo)]
    out.append(line("own.B1.10", "a control: 'a defector lasts', 'no defector lasts', and fires nothing",
                    "a defector lasts, no defector lasts; control: fires nothing",
                    "%s, %s; %s" % (words[0]["zone"], words[1]["zone"], words[0].get("control")), 0,
                    ok=words[0]["zone"] == "a defector lasts" and words[1]["zone"] == "no defector lasts"
                    and all(w.get("control") == "control: fires nothing" for w in words)
                    and (hi["zone"], lo["zone"]) == ("fires", "holds")
                    and run_cell.is_control({"types": {"hosts": "U", "defectors": 1}})
                    and not run_cell.is_control({"types": {"hosts": "C", "defectors": 1}})))
    # Point 4: one still standing at the end, whose bound has not yet come, is too long to judge.
    cell = {"setting": "network", "operators": ["D", "U1", "U2"], "topology": "ring",
            "types": {"D": "D", "U1": "U", "U2": "U"}}
    W = engine.World(cell, [0]).run(run_to=5)
    c = cfg_of(W, "D")[0]
    out.append(line("own.IX.4", "standing, bound not come: too long to judge", False, c["judged"], 0,
                    ok=c["judged"] is False and c["end_reason"] == "run ended"))
    # Point 9: the hopper, refused by the record wherever type C is offered it.
    ev = Events()
    cell = {"setting": "network", "operators": ["D", "H1", "H2", "H3"], "topology": "ring",
            "types": {"D": "D", "H1": "C", "H2": "C", "H3": "C"}, "entry": {"q": 10, "n": 2, "hopper": True}}
    W = engine.World(cell, [0, 1, 2, 3], log=ev).run(run_to=60)
    hops = [e for e in ev.evs if e["ev"] == "hop"]
    out.append(line("own.IX.9", "hops by a cut-off defector, all refused by the record", ">0, all refused",
                    "%d, %d refused" % (len(hops), sum(e["outcome"] == "refused by the record" for e in hops)), 0,
                    ok=bool(hops) and all(e["outcome"] == "refused by the record" for e in hops)))
    # ... and accepted where type U is offered it: a defector with no links, beside one type U operator.
    ev = Events()
    cell = {"setting": "network", "operators": ["D", "U"], "topology": "none", "types": {"D": "D", "U": "U"},
            "entry": {"q": 10, "n": 0, "hopper": True, "type": "U"}}
    W = engine.World(cell, [0], log=ev).run(run_to=11)
    hops = [e for e in ev.evs if e["ev"] == "hop"]
    out.append(line("own.IX.9", "the hopper's control: accepted by type U", "accepted",
                    hops[0]["outcome"] if hops else None, 0, ok=bool(hops) and hops[0]["outcome"] == "accepted"))
    # Point 10: capacity. At m = 3, g = 1.5 and u_max = 6: no operator ever accepts a fifth link.
    cell = {"setting": "network", "N": 6, "topology": "ring", "types": {"hosts": "C"},
            "entry": {"q": 2, "n": 2}}
    W = engine.World(cell, [0, 1], log=None)
    most = 0
    W.r = 0
    W._start_round(first=True)
    for _ in range(60):
        W._substeps()
        W.r += 1
        W._start_round()
        for si in range(W.S):
            most = max(most, max(W._n_links(si, j) for j in range(W.N)))
    out.append(line("own.IX.10", "most links on one operator at m = 3", 4, most, 0, ok=most <= 4))
    # Point 13: B3's lone operator, from 50 at its steady effort 0.1 x 50 / (1 + 0.1^2), settles at u / a, 49.50.
    u = 0.1 * 50 / (1 + 1.0 * 0.1 ** 2)
    cell = {"setting": "lone", "operators": ["L"], "policy": {"kind": "steady", "u": u}, "overrides": {"u_max": 3 * u}}
    W = engine.World(cell, [0]).run(run_to=200)
    out.append(line("own.IX.13", "lone operator at steady effort, stock at t = 200", 49.5049505, float(W.E[0, 0]),
                    1e-4))
    return out


def main():
    tv = json.load(open(TV, encoding="utf-8"))
    rows = []
    # the settings in the file are the engine's own
    for name, S in tv["settings"].items():
        P = engine.params_for(name)
        for key, val in S.items():
            if key in ("name", "schedule_note", "operators", "topology", "N"):
                continue
            want = P["m"] / (2 * P["lam"]) if val == "m/(2*lam)" else val
            ok = (P.get(key) == want) or (isinstance(want, (int, float)) and P.get(key) is not None and
                                          abs(P[key] - want) < 1e-12)
            if not ok:
                rows.append(line("settings", "%s.%s" % (name, key), want, P.get(key), 0, ok=False))
    t0 = time.time()
    for case in tv["cases"]:
        rows.extend(check_case(case))
    rows.extend(own_checks())
    took = time.time() - t0
    width = max(len(r["what"]) for r in rows)
    for r in rows:
        print("%-5s %-16s %-*s expected %-12s got %s" % ("PASS" if r["pass"] else "FAIL", r["id"], width, r["what"],
                                                          r["expected"], r["got"]))
    n_fail = sum(not r["pass"] for r in rows)
    print("%d lines, %d failed, in %.1f s" % (len(rows), n_fail, took))
    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"lines": rows, "failed": n_fail, "seconds": took}, open(path, "w", encoding="utf-8"), indent=1)
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
