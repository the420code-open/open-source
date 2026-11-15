"""Each new line of the checks made to fail once, on purpose: a copy of the engine with one of points 20, 21, 22 or
B2's naming of kinds broken, run through the engine's own check. The engine itself is never changed.

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
        ("point 20 read on one round's record", "start_now = has & ~clocked & hascp & (cpw < 0)",
         "start_now = has & ~clocked & hascp & (cp1 < 0)", "B2.P20"),
        ("point 21 never applied", "new_turn = on & (cpw >= 0) & np.isnan(self.k_turn)",
         "new_turn = on & (cpw >= 0) & np.isnan(self.k_turn) & False", "B2.P21"),
        ("point 22 only at the run's end", "if turn is None and rec is not None and rec < 0:",
         "if turn is None and rec is not None and rec < 0 and at_end:", "B2.P22"),
        ("an operator alone named a defector's", '"kind": "an operator alone" if len(self.members) == 1 else',
         '"kind": "a defector\'s" if len(self.members) == 1 else', "B2.10"),
    ]),
    "second": ("browser", "engine.mjs", [
        ("point 20 read on one round's record", "const recW = this._cpRecordWindow(c, true);",
         "const recW = c.accum;", "B2.P20"),
        ("point 21 never applied", "if (recW >= 0) { if (c.turn === null) {",
         "if (recW >= 0) { if (false) {", "B2.P21"),
        ("point 22 only at the run's end", "if (span14 !== null && recW !== null && recW < 0 && c.turn === null) {",
         "if (span14 !== null && recW !== null && recW < 0 && c.turn === null && c.end === null) {", "B2.P22"),
        ("an operator alone named a defector's", "kind: c.counterparties.length === 0 ? 'an operator alone'",
         "kind: c.counterparties.length === 0 ? \"a defector's\"", "B2.10"),
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
        subprocess.run([sys.executable, os.path.join(tmp, folder, "check.py"), "--json", j], capture_output=True)
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
