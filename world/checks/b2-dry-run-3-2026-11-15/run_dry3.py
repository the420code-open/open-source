"""B2's dry run, a third time, under version 1.1, draft 3: dry, never a result. Every cell on both engines of the branch
wc/b2-points-20-22 at draft 3 (points 19 and 22 only shorten a span), on the dry seeds of the first and second dry runs
(the reference 2,000,000 to 2,000,099, the second engine 2,100,000 to 2,100,099), 4,000 rounds, through the probes of
world/checks/engines-part-2026-11-15 (copied here, byte for byte, under probes/), which run each engine's own runner
unchanged and read its World after the run, for the drawn counts. The cells are the second dry run's, byte for byte.

    python run_dry3.py CODE_DIR OUT_DIR
"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

code, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.join(HERE, "probes")
CELLS = ["D1", "D2", "D4", "X1", "D5", "X3", "D6"]
jobs = [(e, c) for c in CELLS for e in ("second", "reference")]
t0 = time.time()


def go(j):
    eng, cell = j
    d = os.path.join(OUT, eng, cell)
    os.makedirs(d, exist_ok=True)
    cf = os.path.join(HERE, "cells", cell + ".json")
    probe = os.path.join(d, "probe.jsonl.gz")
    if eng == "reference":
        cmd = [sys.executable, os.path.join(PROBES, "probe_reference.py"), os.path.join(code, "world", "reference"), cf,
               "2000000-2000099", d, probe]
    else:
        cmd = ["node", os.path.join(PROBES, "probe_second.mjs"), os.path.join(code, "world", "browser"), cf,
               "2100000-2100099", d, probe]
    t = time.time()
    with open(os.path.join(d, "console.txt"), "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print("%-9s %-3s %s  %5.0f s (its own %5.0f s)" % (eng, cell, "ok" if r.returncode == 0 else "FAILED %d" % r.returncode,
                                                      time.time() - t0, time.time() - t), flush=True)
    return r.returncode


with ThreadPoolExecutor(7) as ex:
    codes = list(ex.map(go, jobs))
print("done:", len(jobs), "runs,", sum(c != 0 for c in codes), "failed,", "%.0f s" % (time.time() - t0), flush=True)
