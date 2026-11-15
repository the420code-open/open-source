"""B2 draft 4, section 9: D1 itself, as written, on a thousand fresh dry seeds in each engine, through the two probes,
eleven at a time. Dry, never a result. Both engines at commit fa05337 of wc/b2-points-20-22 (CODE_DIR holds its world,
by git archive). D1 exactly as in the dry run (cells/D1.json, byte for byte): random links, p = 0.2 among 20, m = 5, a
quarter of the operators defectors, uneven drift from 0.06 to 0.2, passive flow 0.05, s = 0.5, the noise "more", 4,000
rounds. The seeds: the next thousand unused in each engine from 1,000,000 up, 1,000,000 to 1,000,999 in each. Each
engine draws its own random numbers from a seed, so the same seed number gives different networks in the two.

    python run_d1_1000.py CODE_DIR OUT_DIR
"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

code, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
jobs = []
for k in range(10):
    seeds = "%d-%d" % (1000000 + 100 * k, 1000099 + 100 * k)
    jobs.append(("second", seeds))
    jobs.append(("reference", seeds))
t0 = time.time()


def go(j):
    eng, seeds = j
    d = os.path.join(OUT, eng, "D1", "seeds-" + seeds)
    os.makedirs(d, exist_ok=True)
    cf = os.path.join(HERE, "cells", "D1.json")
    probe = os.path.join(d, "probe.jsonl.gz")
    if eng == "reference":
        cmd = [sys.executable, os.path.join(HERE, "probes", "probe_reference.py"), os.path.join(code, "world", "reference"),
               cf, seeds, d, probe]
    else:
        cmd = ["node", os.path.join(HERE, "probes", "probe_second.mjs"), os.path.join(code, "world", "browser"), cf, seeds,
               d, probe]
    t = time.time()
    with open(os.path.join(d, "console.txt"), "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print("%-9s D1 %-15s %s  %5.0f s (its own %5.0f s)" % (eng, seeds, "ok" if r.returncode == 0 else "FAILED %d" % r.returncode,
                                                        time.time() - t0, time.time() - t), flush=True)
    return r.returncode


with ThreadPoolExecutor(11) as ex:
    codes = list(ex.map(go, jobs))
print("done:", len(jobs), "runs,", sum(c != 0 for c in codes), "failed,", "%.0f s" % (time.time() - t0), flush=True)
