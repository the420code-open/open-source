"""B1's cells under version 1.1, draft 3, as a check, never a result: every cell of B1's run (13 to 14 November 2026)
beside the same cell run again on the branch wc/b2-points-20-22 at draft 3, on B1's own seeds, and beside the run
under draft 2 (15 November 2026). For the 104 cells that could fire and the second engine's 32: the zone, the
judgement, and B1's measure seed by seed must be B1's. For the 104 controls: their figures, under B1, draft 2 and
draft 3, and their judgements.

    python compare_b1.py B1_RUN_DIR DRAFT3_RUN_DIR DRAFT2_RUN_DIR B1_JUDGEMENT.json DRAFT3_JUDGEMENT.json
                         DRAFT2_JUDGEMENT.json OUT.json
"""
import glob
import json
import os
import sys

b1_dir, d3_dir, d2_dir, j1, j3, j2, out = sys.argv[1:8]


def judgements(path):
    d = json.load(open(path, encoding="utf-8"))
    res = {}
    for key in ("cells", "second_engine"):
        for c in d.get(key) or []:
            if isinstance(c, dict) and "cell" in c:
                eng = "second" if key == "second_engine" else "reference"
                # the second engine's 32 are compared with the reference's, as section 9 says: their verdict
                res[eng + "/" + c["cell"]] = c.get("verdict") if eng == "second" else c.get("judgement")
    return res


J1, J3, J2 = judgements(j1), judgements(j3), judgements(j2)


def same_per_seed(pa, pb):
    return set(pa) == set(pb) and all(abs(pa[s] - pb[s]) <= 1e-12 * max(1.0, abs(pa[s])) for s in pa)


res = {"label": "dry, never a result: B1's record stands as run", "cells": {}}
fire = {"cells": 0, "zone_and_measure_seed_by_seed_as_B1": 0, "judgement_as_B1": 0, "not_as_B1": []}
ctl = {"cells": 0, "measure_seed_by_seed_as_B1": 0, "judgement_as_B1": 0, "judgement_moved_from_B1": [],
       "measure_as_draft_2": 0, "judgement_moved_from_draft_2": []}
tally = {"B1": {}, "draft 2": {}, "draft 3": {}}
for eng, sub in (("reference", "seeds-1-100"), ("second", "seeds-100001-100100")):
    for f in sorted(glob.glob(os.path.join(b1_dir, eng, sub, "*", "summary.json"))):
        cell = os.path.basename(os.path.dirname(f))
        key = eng + "/" + cell
        g, h = os.path.join(d3_dir, eng, sub, cell, "summary.json"), os.path.join(d2_dir, eng, sub, cell, "summary.json")
        if not os.path.exists(g):
            res["cells"][key] = {"error": "not run again under draft 3"}
            continue
        a, b = json.load(open(f, encoding="utf-8")), json.load(open(g, encoding="utf-8"))
        c2 = json.load(open(h, encoding="utf-8")) if os.path.exists(h) else None
        ma, mb = a["B1"]["measure"], b["B1"]["measure"]
        m2 = c2["B1"]["measure"] if c2 else {}
        pa, pb, p2 = ma.get("per_seed", {}), mb.get("per_seed", {}), m2.get("per_seed", {})
        control = "control" in cell
        row = {"engine": eng, "control": control,
               "zone": {"B1": ma.get("zone"), "draft 2": m2.get("zone"), "draft 3": mb.get("zone")},
               "judgement": {"B1": J1.get(key), "draft 2": J2.get(key), "draft 3": J3.get(key)},
               "mean": {"B1": ma.get("mean"), "draft 2": m2.get("mean"), "draft 3": mb.get("mean")},
               "se": {"B1": ma.get("se"), "draft 2": m2.get("se"), "draft 3": mb.get("se")},
               "seeds_measured": {"B1": ma.get("seeds_measured"), "draft 2": m2.get("seeds_measured"),
                                  "draft 3": mb.get("seeds_measured")},
               "seeds_left_out": {"B1": ma.get("seeds_left_out"), "draft 2": m2.get("seeds_left_out"),
                                  "draft 3": mb.get("seeds_left_out")},
               "measure_seed_by_seed_as_B1": same_per_seed(pa, pb),
               "measure_seed_by_seed_as_draft_2": same_per_seed(p2, pb) if c2 else None,
               "point_19": {"B1": a["B1"].get("point_19", {}).get("applied"), "draft 3": b["B1"].get("point_19", {})},
               "point_22": {"draft 2": (c2 or {}).get("B1", {}).get("point_22", {}).get("applied"),
                            "draft 3": b["B1"].get("point_22", {})},
               "point_21": {"draft 3": b["B1"].get("point_21", {}).get("applied")}}
        if not row["measure_seed_by_seed_as_B1"]:
            row["seeds_that_moved_from_B1"] = {s: [pa.get(s), pb.get(s)] for s in sorted(set(pa) | set(pb), key=int)
                                               if pa.get(s) is None or pb.get(s) is None or
                                               abs(pa[s] - pb[s]) > 1e-12 * max(1.0, abs(pa[s]))}
        res["cells"][key] = row
        for who in ("B1", "draft 2", "draft 3"):
            if eng == "reference":
                k = ("control: " if control else "can fire: ") + str(row["judgement"][who])
                tally[who][k] = tally[who].get(k, 0) + 1
        if control:
            ctl["cells"] += 1
            ctl["measure_seed_by_seed_as_B1"] += row["measure_seed_by_seed_as_B1"]
            ctl["measure_as_draft_2"] += bool(row["measure_seed_by_seed_as_draft_2"])
            if row["judgement"]["draft 3"] == row["judgement"]["B1"]:
                ctl["judgement_as_B1"] += 1
            else:
                ctl["judgement_moved_from_B1"].append(key)
            if row["judgement"]["draft 3"] != row["judgement"]["draft 2"]:
                ctl["judgement_moved_from_draft_2"].append(key)
        else:
            fire["cells"] += 1
            ok = row["measure_seed_by_seed_as_B1"] and row["zone"]["B1"] == row["zone"]["draft 3"]
            fire["zone_and_measure_seed_by_seed_as_B1"] += ok
            fire["judgement_as_B1"] += row["judgement"]["draft 3"] == row["judgement"]["B1"]
            if not (ok and row["judgement"]["draft 3"] == row["judgement"]["B1"]):
                fire["not_as_B1"].append(key)
res["cells that could fire, and the second engine's"] = fire
res["controls"] = ctl
res["judgements, the reference's 208 cells"] = tally
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "cells"}, indent=1))
