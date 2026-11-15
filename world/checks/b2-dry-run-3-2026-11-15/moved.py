"""B2's dry run, a third time, beside the second: which figures moved from version 1.1, draft 2 to draft 3. Dry,
never a result. Every figure of tables.json, cell by cell and engine by engine, but the wall clock; a figure that
moved is listed with both values.

    python moved.py TABLES_DRY_RUN_2.json TABLES_DRY_RUN_3.json OUT.json
"""
import json
import sys

a, b, out = sys.argv[1:4]
A, B = json.load(open(a, encoding="utf-8")), json.load(open(b, encoding="utf-8"))
SKIP = {"wall_clock_seconds", "reports"}


def flat(d, pre=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if pre == "" and k in SKIP:
                continue
            o.update(flat(v, pre + "/" + str(k) if pre else str(k)))
    else:
        o[pre] = d
    return o


def same(x, y):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        return abs(x - y) <= 1e-9 * max(1.0, abs(x))
    return x == y


res = {"label": "dry, never a result", "cells": {}}
for cell in B["cells"]:
    for eng in ("reference", "second"):
        x, y = flat(A["cells"][cell][eng]), flat(B["cells"][cell][eng])
        # the reports' counts, but not their lists
        for src, dst in ((A["cells"][cell][eng]["reports"], x), (B["cells"][cell][eng]["reports"], y)):
            for k, v in src.items():
                if isinstance(v, (int, float)):
                    dst["reports/" + k] = v
        moved = {k: [x.get(k), y.get(k)] for k in sorted(set(x) | set(y)) if not same(x.get(k), y.get(k))}
        res["cells"].setdefault(cell, {})[eng] = moved
    ra, rb = A["cells"][cell].get("engines_apart_in_combined_se"), B["cells"][cell].get("engines_apart_in_combined_se")
    if not same(ra, rb):
        res["cells"][cell]["engines_apart_in_combined_se"] = [ra, rb]
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
for cell, r in res["cells"].items():
    for eng in ("reference", "second"):
        print(cell, eng, len(r[eng]), "moved:", ", ".join(sorted(r[eng]))[:600])
