"""The outside scorer, run in parts side by side: each part gets its own share of the credit as its ceiling, so that the
parts together can never pass the approval's ceiling. Each part marks its own rows with score.py's xai scorer (every
call kept with its time, the model returned and its tokens), and stops at its share. Run it again and nothing already
marked is marked twice.

    python tests/outside/run_outside.py BLIND.jsonl OUTDIR --approval APPROVAL.json --budget USD --parts N [--pairs]

Zero-Clause BSD.
"""
import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = os.path.join(os.path.dirname(HERE), "runner", "score.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blind")
    ap.add_argument("out")
    ap.add_argument("--approval", required=True)
    ap.add_argument("--budget", type=float, required=True, help="what these parts may spend together, in US dollars")
    ap.add_argument("--parts", type=int, default=6)
    ap.add_argument("--pairs", action="store_true", help="also judge the pairs, in one more part")
    a = ap.parse_args()
    ok = json.load(open(a.approval, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    rows = [ln for ln in io.open(a.blind, encoding="utf-8") if ln.strip()]
    alone = [ln for ln in rows if not json.loads(ln).get("pair_only")]
    n = a.parts + (1 if a.pairs else 0)
    share = a.budget / n
    procs = []
    for k in range(a.parts):
        part = os.path.join(a.out, "part%d.jsonl" % k)
        io.open(part, "w", encoding="utf-8", newline="\n").write("".join(alone[k::a.parts]))
        appr = os.path.join(a.out, "approval-part%d.json" % k)
        json.dump(dict(ok, ceiling_usd=share, spent_before_usd=0.0, share_of=a.budget), open(appr, "w", encoding="utf-8"),
                  indent=1)
        log = open(os.path.join(a.out, "part%d.log" % k), "w", encoding="utf-8")
        procs.append(subprocess.Popen([sys.executable, SCORE, "one", part, "--out", os.path.join(a.out, "marks%d.jsonl" % k),
                                       "--scorer", "xai", "--approval", appr], stdout=log, stderr=subprocess.STDOUT))
    if a.pairs:
        appr = os.path.join(a.out, "approval-pairs.json")
        json.dump(dict(ok, ceiling_usd=share, spent_before_usd=0.0, share_of=a.budget), open(appr, "w", encoding="utf-8"),
                  indent=1)
        log = open(os.path.join(a.out, "pairs.log"), "w", encoding="utf-8")
        procs.append(subprocess.Popen([sys.executable, SCORE, "pairs", a.blind, "--out", os.path.join(a.out, "pairmarks.jsonl"),
                                       "--scorer", "xai", "--approval", appr], stdout=log, stderr=subprocess.STDOUT))
    codes = [p.wait() for p in procs]
    marks = []
    for k in range(a.parts):
        f = os.path.join(a.out, "marks%d.jsonl" % k)
        if os.path.exists(f):
            marks += [ln for ln in io.open(f, encoding="utf-8") if ln.strip()]
    io.open(os.path.join(a.out, "marks_outside.jsonl"), "w", encoding="utf-8", newline="\n").write("".join(marks))
    spent = 0.0
    for ln in marks:
        u = json.loads(ln).get("usage") or {}
        spent = spent  # each part's own running total is in its last line
    totals = []
    for k in range(a.parts):
        f = os.path.join(a.out, "marks%d.jsonl" % k)
        last = [json.loads(ln) for ln in io.open(f, encoding="utf-8") if ln.strip()][-1:] if os.path.exists(f) else []
        totals.append(last[0]["usage"].get("spent_so_far_usd", 0.0) if last else 0.0)
    pf = os.path.join(a.out, "pairmarks.jsonl")
    if a.pairs and os.path.exists(pf):
        last = [json.loads(ln) for ln in io.open(pf, encoding="utf-8") if ln.strip()][-1:]
        totals.append(last[0]["usage"].get("spent_so_far_usd", 0.0) if last else 0.0)
    print("parts exited %s; answers marked %d of %d; spent about $%.2f of $%.2f" % (
        codes, len(marks), len(alone), sum(totals), a.budget))


if __name__ == "__main__":
    main()
