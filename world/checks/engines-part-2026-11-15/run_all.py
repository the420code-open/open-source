"""Dry only, never a result. Every run of this check, through the two probes, eleven at a time.

D1 (reference only: the second engine at the tag refuses uneven drift) and D1e (both engines), on the B2 dry run's
own seeds, so they line up with it; and B1's cell b1-random-3D-m3-s0-more, a thousand fresh seeds in each engine,
in parts of a hundred. The engines are those at the tag world-ref-v1.0, as B1 ran them (…\\b1-run\\code).
"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

CODE = r"…\b1-run\code\world"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"…\engines-part\runs"
B1 = "b1-random-3D-m3-s0-more"
jobs = [("reference", "D1", "2000000-2000099"), ("reference", "D1e", "2000000-2000099"), ("second", "D1e", "2100000-2100099")]
for k in range(10):
    jobs.append(("reference", B1, "%d-%d" % (4000000 + 100 * k, 4000099 + 100 * k)))
    jobs.append(("second", B1, "%d-%d" % (4100000 + 100 * k, 4100099 + 100 * k)))
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
    print("%-9s %-24s %-17s %s  %5.0f s" % (eng, cell, seeds, "ok" if r.returncode == 0 else "FAILED %d" % r.returncode,
                                           time.time() - t0), flush=True)
    return r.returncode


with ThreadPoolExecutor(11) as ex:
    codes = list(ex.map(go, jobs))
print("done:", len(jobs), "runs,", sum(c != 0 for c in codes), "failed,", "%.0f s" % (time.time() - t0), flush=True)
