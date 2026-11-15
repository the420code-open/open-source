"""Runs B1's cells, as the frozen hypothesis hyp-B1-v1 says: every cell of the 208 on the reference, seeds 1 to 100;
the 32 cells of section 9 on the second engine, seeds 100,001 to 100,100. Every seed of a cell runs in full before
anything in that cell is judged: this only runs; world/b1/judge.py judges.

    python world/b1/run_b1.py --code CODE_DIR --out OUT_DIR [--jobs 11]
        [--only reference|second] [--cells ID,ID,...] [--ref-seeds 1-100] [--second-seeds 100001-100100]

CODE_DIR holds the world at the tag world-ref-v1.0 (git archive world-ref-v1.0 world). A cell already run, with its
summary written, is not run again. Each run's console output is kept beside it.

Zero-Clause BSD.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=11)
    ap.add_argument("--only", choices=["reference", "second"])
    ap.add_argument("--cells")
    ap.add_argument("--ref-seeds", default="1-100")
    ap.add_argument("--second-seeds", default="100001-100100")
    a = ap.parse_args()
    idx = json.load(open(os.path.join(CELLS, "index.json"), encoding="utf-8"))
    want = set(a.cells.split(",")) if a.cells else None
    jobs = []
    if a.only in (None, "reference"):
        for cid in idx["cells"]:
            if want is None or cid in want:
                d = os.path.join(a.out, "reference", "seeds-" + a.ref_seeds, cid)
                jobs.append((cid, "reference", [sys.executable, os.path.join(a.code, "world", "reference", "run_cell.py"),
                                               os.path.join(CELLS, cid + ".json"), "--seeds", a.ref_seeds, "--out", d], d))
    if a.only in (None, "second"):
        for cid in idx["second_engine"]:
            if want is None or cid in want:
                d = os.path.join(a.out, "second", "seeds-" + a.second_seeds, cid)
                jobs.append((cid, "second", ["node", os.path.join(a.code, "world", "browser", "run_cell.mjs"),
                                             os.path.join(CELLS, cid + ".json"), "--seeds", a.second_seeds, "--out", d], d))
    # the slowest first: entry cells grow by a newcomer every 10 rounds; then the second engine; then the rest
    jobs.sort(key=lambda j: (0 if "-entry-" in j[0] else 1 if j[1] == "second" else 2, j[0]))
    todo = [j for j in jobs if not os.path.exists(os.path.join(j[3], "summary.json"))]
    print("%d runs, %d already done, %d to run, %d at a time" % (len(jobs), len(jobs) - len(todo), len(todo), a.jobs),
          flush=True)
    t0 = time.time()

    def run(job):
        cid, engine, cmd, d = job
        os.makedirs(d, exist_ok=True)
        t = time.time()
        with open(d + ".txt", "w", encoding="utf-8") as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        return cid, engine, r.returncode, time.time() - t

    done = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for fut in as_completed([ex.submit(run, j) for j in todo]):
            cid, engine, rc, sec = fut.result()
            done += 1
            print("%3d/%d  %-9s %-44s %s  %4.0f s  (%.0f min in)" % (done, len(todo), engine, cid,
                  "ok" if rc == 0 else "FAILED rc=%d" % rc, sec, (time.time() - t0) / 60), flush=True)
    print("all runs done in %.0f min" % ((time.time() - t0) / 60), flush=True)


if __name__ == "__main__":
    main()
