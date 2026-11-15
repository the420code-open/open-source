"""Dry only, never a result. The bound on the gap in operators left alone: D1e in both engines and D1 in the reference,
on 1,000 fresh dry seeds each, through the two probes, eleven at a time. Reference 5,000,000 to 5,000,999; second
engine 5,100,000 to 5,100,999 (the coordinator's ranges, 14 November 2026). The second engine at the tag world-ref-v1.0
has no uneven drift and refuses D1, so the two engines meet on D1e, D1 with its drift even; the reference runs D1 too,
on the same seeds as its D1e, so what uneven drift moves in the reference is seen beside it.
"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

CODE = r"…\b1-run\code\world"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"…\engines-part\runs-bound"
jobs = []
for k in range(10):
    jobs.append(("second", "D1e", "%d-%d" % (5100000 + 100 * k, 5100099 + 100 * k)))
    jobs.append(("reference", "D1e", "%d-%d" % (5000000 + 100 * k, 5000099 + 100 * k)))
    jobs.append(("reference", "D1", "%d-%d" % (5000000 + 100 * k, 5000099 + 100 * k)))
t0 = time.time()


def go(j):
    eng, cell, seeds = j
    d = os.path.join(OUT, eng, cell, "seeds-" + seeds)
    os.makedirs(d, exist_ok=True)
    cf = os.path.join(HERE, "cells", cell + ".json")
    probe = os.path.join(d, "probe.jsonl.gz")
    if eng == "reference":
        cmd = [sys.executable, os.path.join(HERE, "probe_reference.py"), os.path.join(CODE, "reference"), cf, seeds, d, probe]
    else:
        cmd = ["node", os.path.join(HERE, "probe_second.mjs"), os.path.join(CODE, "browser"), cf, seeds, d, probe]
    with open(os.path.join(d, "console.txt"), "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print("%-9s %-5s %-17s %s  %5.0f s" % (eng, cell, seeds, "ok" if r.returncode == 0 else "FAILED %d" % r.returncode,
                                          time.time() - t0), flush=True)
    return r.returncode


with ThreadPoolExecutor(11) as ex:
    codes = list(ex.map(go, jobs))
print("done:", len(jobs), "runs,", sum(c != 0 for c in codes), "failed,", "%.0f s" % (time.time() - t0), flush=True)
