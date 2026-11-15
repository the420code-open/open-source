"""B2 draft 4, section 6: the dry controls D4 and X3 judged again from their packets, with no new run. Dry, never a
result. In a control, every seed left out as too long to judge is counted as zero, and a seed left with nothing to
watch is counted as zero too; the control is judged on all its seeds. It reads "a configuration lasts" where that
mean, less two standard errors, is over three spans; "no configuration lasts" only as before (the mean over the seeds
measured, plus two standard errors, at or under three, with no more than one seed in ten left out); and otherwise
settles nothing.

Each seed's measure is worked out from the packet alone: the largest survival in spans, less the window, among the
configurations whose clock started, less those outside the premises; a seed with one too long to judge is left out.
It is checked against the runner's own summary, seed by seed.

    python judge_controls.py RUNS_DIR OUT.json
"""
import json
import math
import os
import sys

runs, out = sys.argv[1:3]
KEY = {"reference": "survival_spans_net", "second": "survival_less_window"}
LINE = 3.0


def per_seed(eng, cell):
    p = os.path.join(runs, eng, cell, "packet.jsonl")
    lines = open(p, encoding="utf-8").read().splitlines()
    seeds, measured, left_out, without = [], {}, [], []
    for ln in lines[1:]:
        s = json.loads(ln)
        seed = s["seed"]
        seeds.append(seed)
        cs = [c for c in s["configurations"] if c.get("span") and not c.get("outside_the_premises")
              and c.get("clock_start") is not None]
        if not cs:
            without.append(seed)
        elif any(c.get("judged") is False for c in cs):
            left_out.append(seed)
        else:
            measured[seed] = max(c[KEY[eng]] for c in cs)
    return seeds, measured, left_out, without


def stats(v):
    n = len(v)
    m = sum(v) / n
    se = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) / math.sqrt(n)
    return m, se


res = {"label": "dry, never a result", "cells": {}}
for cell in ("D4", "X3"):
    for eng in ("reference", "second"):
        seeds, meas, lo, wo = per_seed(eng, cell)
        summ = json.load(open(os.path.join(runs, eng, cell, "summary.json"), encoding="utf-8"))["B2"]["measure"]
        ps = {int(k): v for k, v in summ["per_seed"].items()}
        agrees = set(ps) == set(meas) and all(abs(ps[s] - meas[s]) <= 1e-12 * max(1.0, abs(ps[s])) for s in ps)
        m_meas, se_meas = stats(list(meas.values()))
        allv = [meas.get(s, 0.0) for s in seeds]
        m0, se0 = stats(allv)
        lasts = m0 - 2 * se0 > LINE
        none_before = (len(lo) + len(wo)) * 10 <= len(seeds) and m_meas + 2 * se_meas <= LINE
        judgement = "a configuration lasts" if lasts else "no configuration lasts" if none_before else "settles nothing"
        res["cells"].setdefault(cell, {})[eng] = {
            "seeds": len(seeds), "seeds_measured": len(meas), "seeds_left_out_too_long_to_judge": len(lo),
            "seeds_with_nothing_to_watch": len(wo),
            "mean_over_the_seeds_measured": m_meas, "se_over_the_seeds_measured": se_meas,
            "mean_with_every_seed_left_out_as_zero": m0, "se_with_every_seed_left_out_as_zero": se0,
            "that_mean_less_two_se": m0 - 2 * se0, "judgement": judgement,
            "the_packet_gives_the_runner's_measure_seed_by_seed": agrees,
            "seeds_left_out": lo, "seeds_with_nothing_to_watch_list": wo}
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
for cell, r in res["cells"].items():
    for eng, x in r.items():
        print("%s %-9s measured %d, out %d, without %d | mean %.4f (SE %.4f) | as zero %.4f (SE %.4f) | less 2 SE %.4f | %s | packet = runner: %s" % (
            cell, eng, x["seeds_measured"], x["seeds_left_out_too_long_to_judge"], x["seeds_with_nothing_to_watch"],
            x["mean_over_the_seeds_measured"], x["se_over_the_seeds_measured"], x["mean_with_every_seed_left_out_as_zero"],
            x["se_with_every_seed_left_out_as_zero"], x["that_mean_less_two_se"], x["judgement"],
            x["the_packet_gives_the_runner's_measure_seed_by_seed"]))
