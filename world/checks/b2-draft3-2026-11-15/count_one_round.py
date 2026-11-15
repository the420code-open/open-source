"""B2's section 10, "how many configurations one round's record alone would have watched", counted again from the kept
records alone, as AG Opus answered on 15 November 2026: the counterparties' one-round records on their links to the
operator, added together, as Part Five's clock read before point 20; not any one counterparty's. Dry, never a result.
On the reference engine, B2's dry cell D1 and its control with type U hosts, six seeds, 400 rounds, as the checks run
them: for every configuration with a counterparty, whether some close while it was open found that sum below zero,
beside the engine's own count, and, for comparison only, the count by any one counterparty's record.

    python count_one_round.py REFERENCE_DIR OUT.json
"""
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
import check  # noqa: E402  (the reference's own checks, for its Recorded world and D1)

d1 = {"setting": "network", "overrides": {"m": 5.0, "s": 0.5, "sigma_s": 1.0, "sigma_r": 1.0, "k": 0.05},
      "topology": "random", "p": 0.2, "types": {"hosts": "C", "defector_share": 0.25},
      "drift": {"uneven": [0.06, 0.2]}}
d4 = dict(d1, types={"hosts": "U", "defector_share": 0.25})
res = {"label": "dry, never a result", "cells": {}}
for name, cell in (("D1, type C hosts", d1), ("D1's control, type U hosts", d4)):
    X = check.Recorded(cell, list(range(2000000, 2000006))).run(run_to=400)
    n = together = engine_count = agree = any_one = 0
    for c in X.cfgs:
        if len(c.midx) < 2:
            continue
        si = X.seeds.index(c.seed)
        n += 1
        closes = [(t, last, ei) for t, last, ei, ej in X.closes if c.start < t <= c.end + 1e-9]
        ends = lambda last, ei: [float(last[si, e, 1 if ei[si, e] == c.i else 0]) for e in c.eidx]
        tog = any(sum(ends(last, ei)) < 0 for t, last, ei in closes)
        one = any(min(ends(last, ei)) < 0 for t, last, ei in closes)
        together += tog
        any_one += one
        engine_count += bool(c.would1)
        agree += tog == bool(c.would1)
    res["cells"][name] = {"configurations_with_a_counterparty": n,
                          "by_the_records_added_together": together,
                          "the_engine_reports": engine_count,
                          "configurations_where_the_two_agree": agree,
                          "for_comparison_only_by_any_one_counterparty": any_one}
json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(json.dumps(res, indent=1))
