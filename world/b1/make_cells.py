"""B1's 208 cells, as the frozen hypothesis hyp-B1-v1 (frozen/hyp-B1-v1_the_defector_does_not_last.md), section 4,
sets them out. Written before any cell of B1 runs; no cell is added after a result is seen.

    python world/b1/make_cells.py        writes world/b1/cells/*.json and world/b1/cells/index.json

The main grid, closed to entry, 96 cells: a ring of 20, or random links with p = 0.2 among 20; one defector or three,
at places chosen by the seed; m = 2, 3, 4; own input s = 0 or 0.5; four noise conditions. The entry grid, 8 cells: the
ring, one defector, m = 3, both values of s, all four noise conditions, a new type C operator every 10 rounds offering
2 links, and the hopper. The two controls: the same 96 and the same 8, with every host of type U (in the entry grid,
newcomers too). Every cell runs 4,000 rounds.

Zero-Clause BSD.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cells")
NOISE = {"quiet": (0.0, 0.0), "some": (0.5, 1.0), "more": (1.0, 1.0), "reading": (0.0, 2.0)}
NOISE_WORDS = {"quiet": "quiet", "some": "some noise (stock 0.5, reading 1)", "more": "more noise (stock 1, reading 1)",
               "reading": "reading only (reading 2)"}
S_NAME = {0.0: "s0", 0.5: "s05"}


def cell(net, d, m, s, noise, control, entry=False):
    ss, sr = NOISE[noise]
    host = "U" if control else "C"
    cid = "b1-%s%s-%dD-m%d-%s-%s%s" % ("entry-" if entry else "", net, d, m, S_NAME[s], noise, "-control" if control else "")
    label = "B1, hyp-B1-v1: %s, %s, m = %d, s = %s, %s%s%s" % (
        "a ring of 20" if net == "ring" else "random links, p = 0.2 among 20",
        "one defector" if d == 1 else "three defectors", m, s, NOISE_WORDS[noise],
        "; open to entry: a type %s newcomer every 10 rounds offering 2 links, and the hopper" % host if entry else "",
        "; the control: every %s of type U, outside the premises, fires nothing" % (
            "operator but the defector, newcomers included," if entry else "host") if control else "")
    c = {"id": cid, "label": label, "hypothesis": "hyp-B1-v1", "grid": "entry" if entry else "main",
         "control": control, "setting": "network",
         "overrides": {"m": float(m), "s": s, "sigma_s": ss, "sigma_r": sr},
         "topology": net, "types": {"hosts": host, "defectors": d}, "rounds": 4000}
    if net == "random":
        c["p"] = 0.2
    if entry:
        c["entry"] = {"q": 10, "n": 2, "type": host, "hopper": True}
    return c


cells = []
for control in (False, True):
    for net in ("ring", "random"):
        for d in (1, 3):
            for m in (2, 3, 4):
                for s in (0.0, 0.5):
                    for noise in NOISE:
                        cells.append(cell(net, d, m, s, noise, control))
    for s in (0.0, 0.5):
        for noise in NOISE:
            cells.append(cell("ring", 1, 3, s, noise, control, entry=True))
assert len(cells) == 208 and len({c["id"] for c in cells}) == 208
assert sum(c["control"] for c in cells) == 104
second = [c["id"] for c in cells if c["grid"] == "main" and not c["control"] and c["overrides"]["m"] == 3.0]
assert len(second) == 32
os.makedirs(OUT, exist_ok=True)
for c in cells:
    with open(os.path.join(OUT, c["id"] + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(c, f, indent=1, ensure_ascii=False)
        f.write("\n")
with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"hypothesis": "hyp-B1-v1", "cells": [c["id"] for c in cells],
               "can_fire": [c["id"] for c in cells if not c["control"]],
               "controls": [c["id"] for c in cells if c["control"]],
               "second_engine": second,
               "seeds": {"reference": "1-100", "reference_added_where_a_cell_settles_nothing": "101-200",
                         "second_engine": "100001-100100", "second_hundred_on_disagreement": {
                             "reference": "101-200", "second_engine": "100101-100200"}}}, f, indent=1)
    f.write("\n")
print("%d cells: %d can fire, %d controls; %d on the second engine" % (
    len(cells), sum(not c["control"] for c in cells), sum(c["control"] for c in cells), len(second)))
