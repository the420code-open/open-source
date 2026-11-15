"""Dry only, never a result. The reference engine's drawn networks alone, at round 0, with no run: World built as
run_cell.py builds it, for a batch of seeds at once, then read. The same counts per seed as drawing_second.mjs.

    python drawing_reference.py REFERENCE_DIR CELL.json FIRST LAST OUT.json
"""
import json
import sys

ref, cell_path, first, last, out = sys.argv[1:6]
sys.path.insert(0, ref)
import engine  # noqa: E402

cell = json.load(open(cell_path, encoding="utf-8"))
rows = []
seeds = list(range(int(first), int(last) + 1))
for k in range(0, len(seeds), 1000):
    W = engine.World(cell, seeds[k:k + 1000])
    for si in range(W.S):
        nb = {i: [] for i in range(W.N)}
        cc = cd = 0
        for e in range(int(W.ecount[si])):
            if not W.elive[si, e]:
                continue
            i, j = int(W.ei[si, e]), int(W.ej[si, e])
            nb[i].append(j); nb[j].append(i)
            if W.typ[si, i] == engine.TYPES["C"] and W.typ[si, j] == engine.TYPES["C"]:
                cc += 1
            else:
                cd += 1
        C, D = engine.TYPES["C"], engine.TYPES["D"]
        alone = sum(1 for i in range(W.N) if not nb[i])
        c_all_d = sum(1 for i in range(W.N) if W.typ[si, i] == C and nb[i] and all(W.typ[si, q] == D for q in nb[i]))
        d_linked = sum(1 for i in range(W.N) if W.typ[si, i] == D and nb[i])
        rows.append([alone, c_all_d, d_linked, cc, cd, len(W.links_left_out[si])])
json.dump({"engine": "reference", "cell": cell["id"], "first": int(first), "last": int(last),
           "columns": ["alone", "careful_givers_every_link_to_a_defector", "defectors_linked", "links_CC", "links_CD",
                       "links_left_out"], "rows": rows}, open(out, "w", encoding="utf-8"))
print("drawn:", len(rows), "seeds")
