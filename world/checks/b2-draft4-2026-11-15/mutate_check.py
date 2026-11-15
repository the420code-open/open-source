"""B2 draft 4: the made sink's line, B2.SINK, made to fail once, on purpose, in each engine: a copy of the engine in
which a sink's clock never starts (only a defector's configuration is watched by the record), run through the engine's
own check. The engine itself is never changed.

    python mutate_check.py reference|second OUT.json
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.normpath(os.path.join(HERE, "..", ".."))
which, out = sys.argv[1], sys.argv[2]

MUT = {
    "reference": ("reference", "engine.py", [
        ("a sink's clock never starts", "start_now = has & ~clocked & hascp & (cpw < 0)",
         "start_now = has & ~clocked & hascp & (cpw < 0) & (self.typ == TYPES[\"D\"])", "B2.SINK"),
    ]),
    "second": ("browser", "engine.mjs", [
        ("a sink's clock never starts", "          if (recW < 0) {",
         "          if (recW < 0 && o.type === 'D') {", "B2.SINK"),
    ]),
}

folder, fname, muts = MUT[which]
res = []
for what, old, new, line_id in muts:
    tmp = tempfile.mkdtemp(prefix="mut-")
    shutil.copytree(os.path.join(WORLD, folder), os.path.join(tmp, folder))
    shutil.copy(os.path.join(WORLD, "test-values.json"), os.path.join(tmp, "test-values.json"))
    p = os.path.join(tmp, folder, fname)
    src = open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        res.append({"mutation": what, "error": "the line to break was found %d times" % n})
        continue
    open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
    if which == "reference":
        j = os.path.join(tmp, "lines.json")
        r = subprocess.run([sys.executable, os.path.join(tmp, folder, "check.py"), "--json", j], capture_output=True)
        if not os.path.exists(j):
            res.append({"mutation": what, "line_meant_to_fail": line_id, "error": "the check did not finish: " +
                        r.stderr.decode("utf-8", "replace")[-600:]})
            continue
        lines = json.load(open(j, encoding="utf-8"))["lines"]
        failed = [r["id"] + " " + r["what"] for r in lines if not r["pass"]]
    else:
        r = subprocess.run(["node", os.path.join(tmp, folder, "check.mjs")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        # the second engine's check prints each line's verdict last
        failed = [" ".join(ln.split()[:1]) + " " + ln.strip()[:120] for ln in r.stdout.splitlines()
                  if ln.strip().split() and ln.strip().split()[-1].lower() == "fail"]
    res.append({"mutation": what, "line_meant_to_fail": line_id, "failed": failed,
                "the_meant_line_failed": any(f.split()[0] == line_id for f in failed)})
    shutil.rmtree(tmp, ignore_errors=True)
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
for r in res:
    print("%-40s meant %-7s failed as meant: %s | every failing line: %s" % (
        r["mutation"], r.get("line_meant_to_fail"), r.get("the_meant_line_failed"), r.get("failed", r.get("error"))))
