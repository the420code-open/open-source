"""Dry only, never a result. B2's measure and B1's, from each engine's packets, by the B2 dry run's own code
(world/checks/b2-dry-run-2026-11-14/second_engine.py, on the branch dry/b2-2026-11-14, imported, not copied): every
part's packet read the same way for both engines, the parts pooled by seed, then the mean, its standard error and
the distance between the engines in combined standard errors. Also, per seed, whether its largest is an operator
alone, and the gap in operators left alone, from the probes.

    python measure_b2.py DRY_BRANCH_CHECK_DIR RUNS_DIR OUT.json
"""
import glob
import gzip
import json
import math
import os
import sys

dry, runs, out = sys.argv[1:4]
sys.path.insert(0, dry)
import second_engine as SE  # noqa: E402  (the dry run's own reading of the two packets)


def pooled(eng, cell):
    b2, b1, kinds, n = {}, {}, {"defector": 0, "sink": 0, "alone": 0}, 0
    for d in sorted(glob.glob(os.path.join(runs, eng, cell, "seeds-*"))):
        x2, x1, k, m = (SE.ref if eng == "reference" else SE.brw)(d)
        b2.update(x2); b1.update(x1); n += m
        for a in kinds:
            kinds[a] += k[a]
    return b2, b1, kinds, n


def alone_per_seed(eng, cell):
    v = []
    for p in sorted(glob.glob(os.path.join(runs, eng, cell, "seeds-*", "probe.jsonl.gz"))):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for ln in f:
                s = json.loads(ln)
                v.append(sum(1 for c in s["cfgs"] if len(c["members"]) == 1))
    n = len(v)
    m = sum(v) / n
    return {"seeds": n, "mean": m, "se": math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) / math.sqrt(n)}


def apart(a, b):
    c = math.sqrt(a["se"] ** 2 + b["se"] ** 2)
    return {"difference": b["mean"] - a["mean"], "combined_se": c, "distance_in_combined_se": (b["mean"] - a["mean"]) / c}


res = {"label": "dry, never a result"}
for eng, cell in (("reference", "D1"), ("reference", "D1e"), ("second", "D1e")):
    b2, b1, kinds, n = pooled(eng, cell)
    res[f"{eng}-{cell}"] = {"seeds": n, "B2_measure": SE.measure(b2), "B1_measure": SE.measure(b1),
                           "watched_a_seed": {k: v / n for k, v in kinds.items()},
                           "operators_left_alone_a_seed": alone_per_seed(eng, cell)}
r, s = res["reference-D1e"], res["second-D1e"]
res["D1e, second engine against reference"] = {
    "B2_measure": apart(r["B2_measure"], s["B2_measure"]),
    "B1_measure": apart(r["B1_measure"], s["B1_measure"]),
    "operators_left_alone": apart(r["operators_left_alone_a_seed"], s["operators_left_alone_a_seed"])}
rd = res["reference-D1"]
res["reference, D1 against D1e (uneven drift against even, same seeds)"] = {
    "B2_measure": apart(r["B2_measure"], rd["B2_measure"]),
    "operators_left_alone": apart(r["operators_left_alone_a_seed"], rd["operators_left_alone_a_seed"])}
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps(res, indent=1))
