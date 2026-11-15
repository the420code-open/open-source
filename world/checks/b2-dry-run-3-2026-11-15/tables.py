"""B2's dry run, a third time, under version 1.1, draft 3: the tables. Dry, never a result.

Section 8's table (watched configurations a seed, the mean of the per-seed largest, its standard error, the largest
seed, seeds left out); WC's six figures (watched by kind; the measure; seeds left out and why; where points 14, 19,
21 and 22 applied; what lasted more than one span and then ended; wall clock); section 4's table (in each control
cell, whether a configuration lasts, kind by kind); every comparison of the two engines with the drawn counts beside
it (operators with no link, and hosts tied only to defectors, from round 0 of every seed); and section 10's reports.

    python tables.py RUN_DIR OUT.json
"""
import gzip
import json
import math
import os
import sys

run, out = sys.argv[1:3]
CELLS = ["D1", "D2", "D4", "X1", "D5", "X3", "D6"]
KINDS = ["a defector's", "a sink's", "an operator alone"]


def drawn(probe):
    alone = only_d = n = 0
    for ln in gzip.open(probe, "rt", encoding="utf-8"):
        s = json.loads(ln)
        n += 1
        typ = {o["name"]: o["type"] for o in s["ops"]}
        for c in s["cfgs"]:
            if c["start"] > 1e-9:
                continue
            cps = c["members"][1:]
            if not cps:
                alone += 1
            elif typ[c["owner"]] != "D" and all(typ[q] == "D" for q in cps):
                only_d += 1
    return {"operators_with_no_link_a_seed": alone / n, "hosts_tied_only_to_defectors_a_seed": only_d / n}


def packet_alone_types(d):
    p = os.path.join(d, "packet.jsonl")
    cnt = {}
    for ln in open(p, encoding="utf-8").read().splitlines()[1:]:
        s = json.loads(ln)
        for c in s["configurations"]:
            if c.get("kind") == "an operator alone":
                t = c.get("owner_type") or c.get("type")
                cnt[t] = cnt.get(t, 0) + 1
    return cnt


res = {"label": "dry, never a result", "cells": {}}
for cell in CELLS:
    row = {}
    for eng in ("reference", "second"):
        d = os.path.join(run, eng, cell)
        s = json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))
        b2, b1, rep = s["B2"], s["B1"], s["B2_reports"]
        m = b2["measure"]
        nseeds = m["seeds"]
        row[eng] = {
            "watched_a_seed": b2["configurations"] / nseeds,
            "by_kind_a_seed": {k: b2["kinds"].get(k, 0) / nseeds for k in KINDS},
            "operators_alone_by_type": packet_alone_types(d),
            "mean": m.get("mean"), "se": m.get("se"), "largest_seed": m.get("largest_seed"),
            "seeds_measured": m.get("seeds_measured"), "seeds_left_out": m.get("seeds_left_out"),
            "seeds_without": m.get("seeds_without_a_watched_configuration"), "zone": m.get("zone"), "why": m.get("why"),
            "too_long_to_judge_by_kind": {},
            "points_applied": {"14": b2["point_14"]["applied"], "19": b2["point_19"]["applied"],
                               "21": b2["point_21"]["applied"], "22": b2["point_22"]["applied"]},
            # version 1.1, draft 3: where point 19 or 22 was left, the counterparties' span being the longer
            "points_left_not_the_shorter": {"19": b2["point_19"].get("not_the_shorter"),
                                            "22": b2["point_22"].get("not_the_shorter")},
            "lasted_more_than_one_span_then_ended": rep["lasted_more_than_one_span_then_ended"],
            "wall_clock_seconds": s["run"].get("seconds"),
            "B1_measure_for_comparison": {k: b1["measure"].get(k) for k in ("mean", "se", "seeds_measured", "zone")},
            "by_kind": {k: {x: b2["measure_by_kind"][k].get(x) for x in ("mean", "se", "seeds_measured", "seeds_left_out",
                                                                       "zone", "largest_seed")} for k in KINDS},
            "reports": rep,
            "drawn": drawn(os.path.join(d, "probe.jsonl.gz")),
        }
        for lo in m.get("left_out", []):
            for x in lo["too_long_to_judge"]:
                # the kind of each configuration too long to judge, from the packet
                pass
        # the kinds of what was too long to judge, from the packet
        kinds = {}
        for ln in open(os.path.join(d, "packet.jsonl"), encoding="utf-8").read().splitlines()[1:]:
            sl = json.loads(ln)
            for c in sl["configurations"]:
                if c.get("span") and c.get("judged") is False and not c.get("outside_the_premises"):
                    kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        row[eng]["too_long_to_judge_by_kind"] = kinds
    r, s2 = row["reference"], row["second"]
    if r["mean"] is not None and s2["mean"] is not None and r["se"] and s2["se"]:
        c = math.sqrt(r["se"] ** 2 + s2["se"] ** 2)
        row["engines_apart_in_combined_se"] = (s2["mean"] - r["mean"]) / c
    res["cells"][cell] = row
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
for cell, row in res["cells"].items():
    for eng in ("reference", "second"):
        x = row[eng]
        print(f"{cell:3s} {eng:9s} watched {x['watched_a_seed']:6.2f} | {', '.join(f'{v:.2f}' for v in x['by_kind_a_seed'].values())} | "
              f"mean {x['mean'] if x['mean'] is None else round(x['mean'], 4)} SE {x['se'] if x['se'] is None else round(x['se'], 4)} "
              f"largest {x['largest_seed'] if x['largest_seed'] is None else round(x['largest_seed'], 4)} in {x['seeds_measured']} out {x['seeds_left_out']} "
              f"| pts {x['points_applied']} left {x['points_left_not_the_shorter']} | lasted {x['lasted_more_than_one_span_then_ended']} | {x['wall_clock_seconds']:.0f} s "
              f"| drawn {x['drawn']['operators_with_no_link_a_seed']:.2f}/{x['drawn']['hosts_tied_only_to_defectors_a_seed']:.2f}")
    if "engines_apart_in_combined_se" in row:
        print(f"    apart: {row['engines_apart_in_combined_se']:.2f} combined SEs")
