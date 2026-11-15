"""B1's cells under points 20 to 22, as a check, never a result: every cell of B1's run (…\\b1-run,
13 to 14 November 2026) beside the same cell run again on the branch wc/b2-points-20-22, on B1's own seeds. For the
104 cells that could fire and the second engine's 32: the zone, and B1's measure seed by seed, must be the same. For
the 104 controls: how their figures moved under point 22.

    python compare_b1.py OLD_RUN_DIR NEW_RUN_DIR OUT.json
"""
import glob
import json
import math
import os
import sys

old_dir, new_dir, out = sys.argv[1:4]
res = {"label": "dry, never a result: B1's record stands as run", "cells": {}}
same_fire = same_ctl = n_fire = n_ctl = 0
moved = []
for eng, sub in (("reference", "seeds-1-100"), ("second", "seeds-100001-100100")):
    for f in sorted(glob.glob(os.path.join(old_dir, eng, sub, "*", "summary.json"))):
        cell = os.path.basename(os.path.dirname(f))
        g = os.path.join(new_dir, eng, sub, cell, "summary.json")
        if not os.path.exists(g):
            res["cells"][eng + "/" + cell] = {"error": "not run again"}
            continue
        a, b = json.load(open(f, encoding="utf-8")), json.load(open(g, encoding="utf-8"))
        ma, mb = a["B1"]["measure"], b["B1"]["measure"]
        pa, pb = ma.get("per_seed", {}), mb.get("per_seed", {})
        seeds_same = set(pa) == set(pb) and all(abs(pa[s] - pb[s]) <= 1e-12 * max(1.0, abs(pa[s])) for s in pa)
        control = "control" in cell
        row = {"engine": eng, "control": control, "zone": [ma.get("zone"), mb.get("zone")],
               "mean": [ma.get("mean"), mb.get("mean")], "se": [ma.get("se"), mb.get("se")],
               "seeds_measured": [ma.get("seeds_measured"), mb.get("seeds_measured")],
               "seeds_left_out": [ma.get("seeds_left_out"), mb.get("seeds_left_out")],
               "measure_seed_by_seed_the_same": seeds_same, "zone_the_same": ma.get("zone") == mb.get("zone"),
               "point_19_then": a["B1"].get("point_19", {}).get("applied"),
               "point_19_now": b["B1"].get("point_19", {}).get("applied"),
               "point_22_now": b["B1"].get("point_22", {}).get("applied"),
               "point_21_now": b["B1"].get("point_21", {}).get("applied")}
        if not seeds_same:
            row["seeds_that_moved"] = {s: [pa.get(s), pb.get(s)] for s in sorted(set(pa) | set(pb), key=int)
                                       if pa.get(s) is None or pb.get(s) is None or abs(pa[s] - pb[s]) > 1e-12 * max(1.0, abs(pa[s]))}
        res["cells"][eng + "/" + cell] = row
        if control:
            n_ctl += 1
            same_ctl += seeds_same and row["zone_the_same"]
            if not (seeds_same and row["zone_the_same"]):
                moved.append(eng + "/" + cell)
        else:
            n_fire += 1
            same_fire += seeds_same and row["zone_the_same"]
res["cells that could fire, and the second engine's"] = {"cells": n_fire, "the_same_zone_and_measure_seed_by_seed": same_fire}
res["controls"] = {"cells": n_ctl, "unchanged": same_ctl, "moved": moved}
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "cells"}, indent=1))
