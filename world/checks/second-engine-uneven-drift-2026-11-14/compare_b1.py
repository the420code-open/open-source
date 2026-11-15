"""Compare B1's 32 second-engine cells: the run of 13 November 2026 against the rerun on the branch.

1. Summaries, figure by figure: every leaf of each summary.json (flattened to its JSON path), compared for exact
   equality (floats as parsed from the JSON text, so equal means the same double). Lists every path that differs,
   and every path present in one and not the other.
2. Packets: the original packet.jsonl (checked first against the run's manifest.sha256) against the rerun's,
   line by line: the 100 seed lines byte for byte; the head line field by field.
"""
import hashlib
import json
import os
import sys

ORIG_SUM = sys.argv[1]      # world/b1/run-2026-11-13/summaries/second
ORIG_RUN = sys.argv[2]      # the run's own folder: second/seeds-100001-100100
MANIFEST = sys.argv[3]      # world/b1/run-2026-11-13/manifest.sha256
NEW_RUN = sys.argv[4]       # the rerun: second/seeds-100001-100100
CELLS = json.load(open(sys.argv[5], encoding="utf-8"))["second_engine"]


def flat(x, path=""):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(flat(v, path + "/" + k))
        if not x:
            out[path] = {}
        return out
    if isinstance(x, list):
        out = {}
        for i, v in enumerate(x):
            out.update(flat(v, "%s[%d]" % (path, i)))
        if not x:
            out[path] = []
        return out
    return {path: x}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


man = {}
for line in open(MANIFEST, encoding="utf-8"):
    h, p = line.strip().split(" *", 1)
    man[p] = h

expected_diff = {"/code", "/run/seconds", "/files/packet.jsonl"}
report = {"cells": len(CELLS), "summary_leaves_compared": 0, "summary_leaves_equal": 0, "unexpected": [],
          "differing_paths_seen": {}, "seed_lines_compared": 0, "seed_lines_equal": 0, "head_fields_differing": {},
          "per_cell": []}
for cid in CELLS:
    a = json.load(open(os.path.join(ORIG_SUM, cid + ".json"), encoding="utf-8"))
    b = json.load(open(os.path.join(NEW_RUN, cid, "summary.json"), encoding="utf-8"))
    # the repository's summary is the run's own, by the manifest
    assert sha(os.path.join(ORIG_SUM, cid + ".json")) == man["second/seeds-100001-100100/%s/summary.json" % cid], cid
    fa, fb = flat(a), flat(b)
    keys = set(fa) | set(fb)
    diff = sorted(k for k in keys if k not in fa or k not in fb or fa[k] != fb[k] or type(fa[k]) != type(fb[k]))
    report["summary_leaves_compared"] += len(keys)
    report["summary_leaves_equal"] += len(keys) - len(diff)
    for k in diff:
        report["differing_paths_seen"][k] = report["differing_paths_seen"].get(k, 0) + 1
        if k not in expected_diff:
            report["unexpected"].append((cid, k, fa.get(k), fb.get(k)))
    # packets
    pa = os.path.join(ORIG_RUN, cid, "packet.jsonl")
    pb = os.path.join(NEW_RUN, cid, "packet.jsonl")
    assert sha(pa) == man["second/seeds-100001-100100/%s/packet.jsonl" % cid], cid
    assert sha(pb) == b["files"]["packet.jsonl"], cid
    la = open(pa, "rb").read().split(b"\n")
    lb = open(pb, "rb").read().split(b"\n")
    assert len(la) == len(lb) == 102, (cid, len(la), len(lb))     # head, 100 seeds, and the final newline
    seeds_a, seeds_b = la[1:101], lb[1:101]
    same_lines = sum(1 for x, y in zip(seeds_a, seeds_b) if x == y)
    report["seed_lines_compared"] += len(seeds_a)
    report["seed_lines_equal"] += same_lines
    if same_lines != len(seeds_a) or la[101] != lb[101]:
        report["unexpected"].append((cid, "packet seed lines differ", len(seeds_a) - same_lines))
    ha, hb = flat(json.loads(la[0])), flat(json.loads(lb[0]))
    for k in sorted(set(ha) | set(hb)):
        if ha.get(k, "<absent>") != hb.get(k, "<absent>"):
            report["head_fields_differing"].setdefault(k, set()).add(
                (json.dumps(ha.get(k, "<absent>"))[:100], json.dumps(hb.get(k, "<absent>"))[:100]))
    m, n = a["B1"]["measure"], b["B1"]["measure"]
    report["per_cell"].append({"cell": cid, "mean_was": m.get("mean"), "mean_now": n.get("mean"), "se_was": m.get("se"),
                               "se_now": n.get("se"), "largest_was": m.get("largest_seed"), "largest_now": n.get("largest_seed"),
                               "zone_was": m.get("zone"), "zone_now": n.get("zone"), "leaves": len(keys), "differing": diff,
                               "seconds_was": a["run"]["seconds"], "seconds_now": b["run"]["seconds"]})
report["head_fields_differing"] = {k: sorted(v) for k, v in report["head_fields_differing"].items()}
print(json.dumps(report, indent=1, default=str))
