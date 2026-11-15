"""The challenge's first roads: AG Opus's own marks, read in.

AG Opus, through G, 15 November 2026: "13 files, one for each batch you made ... Each answer is under its own number,
M001 to M104, in Part One's result form." The files are kept as they came, in first-marks/returned/. This reads each
result with marks.py's own parser, checks that every number of every batch has exactly one result, joins each to its
answer by the key kept apart (first-marks-key.json), checks every quotation under "Lines" word for word against the
paper that answer was given, and writes the marks and the tally.

    python first_marks_in.py <run_dir>

Zero-Clause BSD.
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import marks  # noqa: E402  (its parser and its papers; its command runs only as a script)

RUN = sys.argv[1]
FM = os.path.join(RUN, "first-marks")
KINDS = ("a road", "no road found", "a refusal")


def norm(s):
    for q in "’‘'“”\"":
        s = s.replace(q, "'")
    return re.sub(r"\s+", " ", s.replace("**", "")).strip()


def quotations(lines):
    if not lines or lines.strip().lower() == "none":
        return []
    return [q for q in re.findall(r'"([^"]+)"', lines)]


def main():
    key = json.load(open(os.path.join(RUN, "first-marks-key.json"), encoding="utf-8"))["key"]
    batches = json.load(open(os.path.join(FM, "batches.json"), encoding="utf-8"))
    out, seen = {}, collections.Counter()
    for j, b in enumerate(batches, 1):
        f = os.path.join(FM, "returned", "AG Opus marks batch %d of %d.md" % (j, len(batches)))
        t = open(f, encoding="utf-8").read()
        parts = re.split(r"^## (M\d{3})\s*$", t, flags=re.M)
        got = {}
        for n, body in zip(parts[1::2], parts[2::2]):
            seen[n] += 1
            got[n] = marks.parse(body)
        assert sorted(got) == sorted(b["answers"]), (f, sorted(set(got) ^ set(b["answers"])))
        out.update(got)
    assert all(v == 1 for v in seen.values()) and len(out) == 104, "a number has no result, or two"
    rows, missing = [], []
    for n in sorted(out):
        r, k = out[n], key[n]
        paper = norm(marks.read(marks.ARMS[k["arm"]][1]))
        qs = quotations(r.get("Lines"))
        bad = [q for q in qs if norm(q) not in paper]
        missing += [(n, q) for q in bad]
        rows.append({"number": n, "answer": k["answer"], "maker": k["maker"], "arm": k["arm"], "k": k["k"],
                     "result": r, "lines_found": len(qs) - len(bad), "lines_not_found": bad})
    kind = lambda r: r["result"].get("Kind", "")  # noqa: E731
    tally = collections.OrderedDict()
    for kd in KINDS:
        sub = [r for r in rows if kind(r) == kd]
        tally[kd] = {"answers": len(sub),
                     "marks": dict(collections.Counter(r["result"].get("Mark", "") for r in sub))}
    tally["other"] = dict(collections.Counter(kind(r) for r in rows if kind(r) not in KINDS))
    by_maker = collections.defaultdict(collections.Counter)
    for r in rows:
        by_maker[r["maker"]][kind(r) + " · " + r["result"].get("Mark", "")] += 1
    json.dump(rows, io.open(os.path.join(FM, "marks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"tally": tally, "by_maker": {m: dict(c) for m, c in sorted(by_maker.items())},
               "lines_not_found": missing}, io.open(os.path.join(FM, "tally.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(tally, ensure_ascii=False, indent=1))
    print("quotations under Lines: %d found word for word, %d not" % (sum(r["lines_found"] for r in rows), len(missing)))
    for n, q in missing:
        print("  not found:", n, q[:120])


main()
