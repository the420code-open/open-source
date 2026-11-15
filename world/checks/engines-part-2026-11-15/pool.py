"""Dry only, never a result. B1's cell b1-random-3D-m3-s0-more, 1,000 seeds in each engine: every seed's B1 measure
from each part's summary, pooled; the mean, its standard error (the sample SD over the square root of n, as both
engines compute it) and the distance between the two means in combined standard errors. Then the counts of count.py
over every part's probe, and the same for D1 and D1e.

    python pool.py RUNS_DIR OUT.json
"""
import glob
import json
import math
import os
import statistics as st
import subprocess
import sys

RUNS, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
B1 = "b1-random-3D-m3-s0-more"
res = {"label": "dry, never a result"}
for eng in ("reference", "second"):
    per = {}
    for f in sorted(glob.glob(os.path.join(RUNS, eng, B1, "seeds-*", "summary.json"))):
        m = json.load(open(f, encoding="utf-8"))["B1"]["measure"]
        per.update(m["per_seed"])
    v = list(per.values())
    n = len(v)
    res[eng] = {"seeds": n, "mean": st.fmean(v), "sd": st.stdev(v), "se": st.stdev(v) / math.sqrt(n),
                "min": min(v), "max": max(v)}
r, s = res["reference"], res["second"]
comb = math.sqrt(r["se"] ** 2 + s["se"] ** 2)
res["difference"] = {"second_minus_reference": s["mean"] - r["mean"], "relative": (s["mean"] - r["mean"]) / r["mean"],
                     "combined_se": comb, "distance_in_combined_se": (s["mean"] - r["mean"]) / comb}
args = []
for eng in ("reference", "second"):
    files = sorted(glob.glob(os.path.join(RUNS, eng, B1, "seeds-*", "probe.jsonl.gz")))
    args.append("%s-B1=%s" % (eng, ",".join(files)))
for eng, cell in (("reference", "D1"), ("reference", "D1e"), ("second", "D1e")):
    files = sorted(glob.glob(os.path.join(RUNS, eng, cell, "seeds-*", "probe.jsonl.gz")))
    args.append("%s-%s=%s" % (eng, cell, ",".join(files)))
cnt = os.path.join(os.path.dirname(OUT), "counts.json")
subprocess.run([sys.executable, os.path.join(HERE, "count.py"), *args, "--out", cnt], check=True, capture_output=True)
res["counts"] = json.load(open(cnt, encoding="utf-8"))
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps({k: res[k] for k in ("reference", "second", "difference")}, indent=1))
