"""Dry only, never a result. Runs the reference engine's own runner, run_cell.py, unchanged, and keeps hold of the
World it builds, by a subclass that only records the instance. After the run, it reads what the engine already keeps
(every configuration, every cut with who made it, every ruin, the links left out between two defectors) and writes
it, one line per seed, to PROBE. The engine's numbers, the packet and the summary are run_cell.py's own.

    python probe_reference.py REFERENCE_DIR CELL.json SEEDS OUT_DIR PROBE.jsonl.gz
"""
import gzip
import json
import sys

ref, cell, seeds, out, probe = sys.argv[1:6]
sys.path.insert(0, ref)
import engine      # noqa: E402  (the engine at REFERENCE_DIR)
import run_cell    # noqa: E402

CAP = []


class Kept(engine.World):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        CAP.append(self)


engine.World = Kept
sys.argv = ["run_cell.py", cell, "--seeds", seeds, "--out", out]
run_cell.main()

W = CAP[0]
name = lambda x: str(x)
with gzip.open(probe, "wt", encoding="utf-8") as f:
    for si, s in enumerate(W.seeds):
        f.write(json.dumps({
            "seed": int(s),
            "ops": [{"name": name(W.names[i]), "type": engine.TNAME[int(W.typ[si, i])], "alive": bool(W.alive[si, i])}
                    for i in range(W.N)],
            "left_out": [[name(a), name(b)] for a, b in W.links_left_out[si]],
            "ruins": [{"op": name(r["op"]), "t": float(r["t"])} for r in W.ruin_list if r["seed"] == s],
            "cuts": [{"round": int(c["round"]), "by": name(c["by"]), "link": [name(x) for x in c["link"]]}
                     for c in W.cut_log if c["seed"] == s],
            "cfgs": [{"owner": name(c.owner), "members": [name(x) for x in c.members], "start": float(c.start),
                      "end": None if c.end is None else float(c.end), "reason": c.reason,
                      "clock": None if c.clock is None else float(c.clock)}
                     for c in W.cfgs if c.seed == s],
        }) + "\n")
print("probe written:", probe, len(W.seeds), "seeds")
