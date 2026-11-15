"""Judges B1's cells once every seed of them has run, as the frozen hypothesis hyp-B1-v1 says.

    python world/b1/judge.py RUN_DIR --out OUT_DIR

Section 7: first the premise check, seed by seed; then the mean of the measure across the seeds. At or under three
spans, mean plus two standard errors: B1 holds in this cell, and the switches hold. Over three, mean less two
standard errors: the switches fire in this cell, shown at once as "reported, being checked" (section 10). Between
the two: settles nothing, and seeds 101 to 200 are added, once; where they have run, the two hundred are judged
together. A seed left out (too long to judge) or with nothing to watch counts towards the one in ten. A cell where
the premises fail fires nothing.

Section 10: a control cell is never printed as "fires" or "holds": it is "a defector lasts" or "no defector lasts",
with "control: fires nothing" beside it.

Section 9: the second engine's 32 cells, compared with world/compare_engines.py.

Writes OUT_DIR/judgement.json (every cell, everything section 10 reports) and OUT_DIR/judgement.md.

Zero-Clause BSD.
"""
import argparse
import gzip
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")
LINE = 3.0


def zone(mean, se):
    if mean + 2 * se <= LINE:
        return "holds"
    if mean - 2 * se > LINE:
        return "fires"
    return "settles nothing"


def pooled(measures):
    """One hundred, or two hundred seeds judged together: their per-seed figures, and every seed left out."""
    vals, out, without, seeds = [], 0, 0, 0
    for m in measures:
        vals += list(m["per_seed"].values())
        out += m["seeds_left_out"]
        without += m["seeds_without_a_watched_configuration"]
        seeds += m["seeds"]
    n = len(vals)
    r = {"seeds": seeds, "seeds_measured": n, "seeds_left_out_too_long_to_judge": out,
         "seeds_with_nothing_to_watch": without}
    if n:
        mean = sum(vals) / n
        se = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) / math.sqrt(n) if n > 1 else float("inf")
        r.update(mean=mean, se=se, mean_plus_2se=mean + 2 * se, mean_less_2se=mean - 2 * se, largest_seed=max(vals),
                 zone=zone(mean, se))
    if (out + without) * 10 > seeds:
        r["zone"] = "settles nothing"
        r["why"] = "%d of %d seeds left out, more than one in ten: %d too long to judge, %d with nothing to watch" % (
            out + without, seeds, out, without)
    elif not n:
        r["zone"] = "settles nothing"
        r["why"] = "no seed has a watched configuration with a span"
    return r


def hops(log_path):
    """The entry cells: every newcomer's offers, and every hopper's offer, with its outcome, from the log's events."""
    ent = {"newcomers": 0, "offered": 0, "accepted": 0, "refused": 0, "no_capacity": 0}
    hop = {}
    with gzip.open(log_path, "rt", encoding="utf-8") as f:
        next(f)
        for ln in f:
            if '"ev":"hop"' in ln:
                e = json.loads(ln)
                hop[e["outcome"]] = hop.get(e["outcome"], 0) + 1
            elif '"ev":"entry"' in ln:
                e = json.loads(ln)
                ent["newcomers"] += 1
                for k in ("offered", "accepted", "refused", "no_capacity"):
                    ent[k] += len(e[k])
    return {"entries": ent, "hops": hop, "hops_total": sum(hop.values())}


def judge_cell(run, cell):
    cid = cell["id"]
    base = os.path.join(run, "reference")
    paths = [os.path.join(base, d, cid) for d in ("seeds-1-100", "seeds-101-200")
             if os.path.exists(os.path.join(base, d, cid, "summary.json"))]
    sums = [json.load(open(os.path.join(p, "summary.json"), encoding="utf-8")) for p in paths]
    if not sums:
        return None
    b1 = [x["B1"] for x in sums]
    r = {"cell": cid, "label": cell["label"], "grid": cell["grid"], "control": cell["control"],
         "seeds": "1-100" if len(sums) == 1 else "1-200 (101-200 added, once, as section 7 says)"}
    r.update(pooled([x["measure"] for x in b1]))
    pc = [x["premise_check"] for x in sums]
    r["premise_check"] = {
        "hosts_all_type_C": all(p["hosts_all_type_C"] for p in pc),
        "drift_irreversible": all(p["drift_irreversible"] for p in pc),
        "defectors": sum(p["defectors"] for p in pc),
        "defectors_coupled_at_start": sum(p["defectors_coupled_at_start"] for p in pc),
        "defectors_with_no_live_link_at_start_reported_not_watched": sum(
            len(u["defectors"]) for p in pc for u in p["defectors_with_no_live_link_at_start_reported_not_watched"]),
        "links_between_two_defectors_left_out": sum(p["links_between_two_defectors_left_out"]["links"] for p in pc)}
    premises = r["premise_check"]["hosts_all_type_C"] and r["premise_check"]["drift_irreversible"]
    z = r["zone"]
    if cell["control"]:
        r["judgement"] = {"fires": "a defector lasts", "holds": "no defector lasts"}.get(z, z)
        r["control"] = "control: fires nothing"
    elif not premises:
        r["judgement"] = "fires nothing: the premises fail"
    else:
        r["judgement"] = {"holds": "B1 holds in this cell, and the switches hold",
                          "fires": "the switches fire in this cell: reported, being checked",
                          "settles nothing": "settles nothing"}[z]
    r["needs_seeds_101_200"] = z == "settles nothing" and len(sums) == 1
    r["watched"] = {
        "configurations": sum(x["configurations"] for x in b1),
        "span_used": {k: sum(x["span_used"].get(k, 0) for x in b1) for k in set().union(*[x["span_used"] for x in b1])},
        "still_standing_at_end": sum(x["still_standing_at_end"] for x in b1),
        "too_long_to_judge": sum(x["too_long_to_judge"] for x in b1),
        "within_bound": sum(x["within_bound"] for x in b1),
        "ended_by": {k: sum(x["ended_by"].get(k, 0) for x in b1) for k in set().union(*[x["ended_by"] for x in b1])},
        "point_19": {"applied": sum(x.get("point_19", {}).get("applied", 0) for x in b1)}}
    r["defectors"] = {"defectors": sum(x["defectors"]["defectors"] for x in sums),
                      "ruined": sum(x["defectors"]["ruined"] for x in sums),
                      "configurations_passed_through_mean": sum(x["defectors"]["configurations_passed_through"]["mean"]
                                                                * x["defectors"]["defectors"] for x in sums)
                      / max(1, sum(x["defectors"]["defectors"] for x in sums)),
                      "configurations_passed_through_max": max(x["defectors"]["configurations_passed_through"]["max"]
                                                               for x in sums)}
    r["end_of_run"] = {"ruined": {k: sum(x["end_of_run"]["ruined"][k] for x in sums) for k in "CUD"},
                       "cuts": sum(x["end_of_run"]["cuts"] for x in sums)}
    r["left_out"] = [lo for x in b1 for lo in x["measure"]["left_out"]]
    if cell.get("entry"):
        h = [hops(os.path.join(p, "log.jsonl.gz")) for p in paths]
        r["entry"] = {"entries": {k: sum(x["entries"][k] for x in h) for k in h[0]["entries"]},
                      "hops": {k: sum(x["hops"].get(k, 0) for x in h) for k in set().union(*[x["hops"] for x in h])},
                      "hops_total": sum(x["hops_total"] for x in h)}
    r["files"] = [os.path.relpath(p, run) for p in paths]
    return r


def second_engine(run, idx):
    out = []
    for cid in idx["second_engine"]:
        ref = [os.path.join(run, "reference", d, cid, "summary.json") for d in ("seeds-1-100", "seeds-101-200")]
        brw = [os.path.join(run, "second", d, cid, "summary.json") for d in ("seeds-100001-100100", "seeds-100101-100200")]
        ref = [p for p in ref if os.path.exists(p)]
        brw = [p for p in brw if os.path.exists(p)]
        if not brw:
            out.append({"cell": cid, "verdict": "not yet run"})
            continue
        n = min(len(ref), len(brw))
        cmd = [sys.executable, os.path.join(HERE, "..", "compare_engines.py"), os.path.join(CELLS, cid + ".json")]
        for p in ref[:n]:
            cmd += ["--reference", p]
        for p in brw[:n]:
            cmd += ["--browser", p]
        res = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
        res["cell"] = cid
        res["hundreds"] = n
        out.append(res)
    return out


def fmt(x, nd=3):
    return "—" if x is None else ("%.*f" % (nd, x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    idx = json.load(open(os.path.join(CELLS, "index.json"), encoding="utf-8"))
    cells = {c: json.load(open(os.path.join(CELLS, c + ".json"), encoding="utf-8")) for c in idx["cells"]}
    res = [judge_cell(a.run, cells[c]) for c in idx["cells"]]
    not_run = [c for c, r in zip(idx["cells"], res) if r is None]
    res = [r for r in res if r is not None]
    sec = second_engine(a.run, idx)
    os.makedirs(a.out, exist_ok=True)
    tally = {}
    for r in res:
        k = ("control" if r["control"] else "can fire", r["judgement"])
        tally[k] = tally.get(k, 0) + 1
    doc = {"hypothesis": "hyp-B1-v1", "label": "the desks' own run", "cells": res, "not_yet_run": not_run,
           "second_engine": sec,
           "tally": [{"kind": k[0], "judgement": k[1], "cells": v} for k, v in sorted(tally.items())],
           "needs_seeds_101_200": [r["cell"] for r in res if r["needs_seeds_101_200"]],
           "engines_disagree": [x["cell"] for x in sec if x.get("verdict") not in ("agree", "not yet run")]}
    json.dump(doc, open(os.path.join(a.out, "judgement.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    md = ["# B1 · hyp-B1-v1 · every cell's judgement", "", "The desks' own run. Reference engine at world-ref-v1.0; "
          "seeds 1 to 100 (101 to 200 added, once, where a cell settled nothing).", "",
          "| Kind | Judgement | Cells |", "|---|---|---|"]
    md += ["| %s | %s | %d |" % (t["kind"], t["judgement"], t["cells"]) for t in doc["tally"]]
    md += ["", "| Cell | Judgement | Mean | SE | Mean + 2 SE | Mean − 2 SE | Largest seed | Seeds measured | Left out | "
           "Defectors ruined | Premises |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        pc = r["premise_check"]
        md.append("| %s | %s%s | %s | %s | %s | %s | %s | %d of %d | %d | %d of %d | %s |" % (
            r["cell"], r["judgement"], ("; " + r["control"]) if r.get("control") else "", fmt(r.get("mean")),
            fmt(r.get("se")), fmt(r.get("mean_plus_2se")), fmt(r.get("mean_less_2se")), fmt(r.get("largest_seed"), 2),
            r["seeds_measured"], r["seeds"], r["seeds_left_out_too_long_to_judge"] + r["seeds_with_nothing_to_watch"],
            r["defectors"]["ruined"], r["defectors"]["defectors"],
            "met" if pc["hosts_all_type_C"] and pc["drift_irreversible"] else "not met (control)" if r["control"]
            else "NOT MET"))
    md += ["", "## The second engine, section 9", "", "| Cell | Rule | Reference | Second engine | Verdict |",
           "|---|---|---|---|---|"]
    for x in sec:
        if x.get("verdict") == "not yet run":
            md.append("| %s | | | | not yet run |" % x["cell"])
            continue
        md.append("| %s | %s | %s (%s) | %s (%s) | %s |" % (
            x["cell"], x.get("rule", ""), fmt(x.get("reference_mean"), 4), fmt(x.get("reference_se"), 4),
            fmt(x.get("browser_mean"), 4), fmt(x.get("browser_se"), 4), x.get("verdict")))
    txt = "\n".join(md) + "\n"
    # G's rule (11 November 2026): the judgement never carries the phrase. The guard is built in two parts, so
    # that this file never spells it either (15 November 2026).
    assert not re.search("auth" + r"or[’'`]?\s?s\s+(?:two\s+)?rulings?", txt, re.I)
    open(os.path.join(a.out, "judgement.md"), "w", encoding="utf-8", newline="\n").write(txt)
    print(json.dumps({"tally": doc["tally"], "not_yet_run": len(not_run), "needs_seeds_101_200": doc["needs_seeds_101_200"],
                      "engines_disagree": doc["engines_disagree"]}, indent=1))


if __name__ == "__main__":
    main()
