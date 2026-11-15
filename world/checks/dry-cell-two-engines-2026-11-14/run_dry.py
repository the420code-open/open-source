"""The dry cell before B2: 1,000 seeds in each engine, in chunks of 100, 11 at a time. Never a result."""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
CODE = r"…\b1-run\code"
HERE = os.path.dirname(os.path.abspath(__file__))
CELL = os.path.join(HERE, "dry-b2-random-3D-m5-s0-more.json")
jobs = []
for k in range(10):
    a = 3000000 + 100 * k
    jobs.append(("reference", f"{a}-{a+99}", [sys.executable, os.path.join(CODE, "world", "reference", "run_cell.py"), CELL,
                 "--seeds", f"{a}-{a+99}", "--out", os.path.join(HERE, "reference", f"seeds-{a}-{a+99}")]))
    b = 3100000 + 100 * k
    jobs.append(("second", f"{b}-{b+99}", ["node", os.path.join(CODE, "world", "browser", "run_cell.mjs"), CELL,
                 "--seeds", f"{b}-{b+99}", "--out", os.path.join(HERE, "second", f"seeds-{b}-{b+99}")]))
t0 = time.time()
def go(j):
    eng, seeds, cmd = j
    os.makedirs(cmd[-1], exist_ok=True)
    with open(os.path.join(cmd[-1], "console.txt"), "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print(f"{eng:9s} {seeds:17s} {'ok' if r.returncode == 0 else 'FAILED %d' % r.returncode}  {time.time()-t0:6.0f} s", flush=True)
    return r.returncode
with ThreadPoolExecutor(11) as ex:
    codes = list(ex.map(go, jobs))
print("done", sum(c != 0 for c in codes), "failed", f"{time.time()-t0:.0f} s", flush=True)
