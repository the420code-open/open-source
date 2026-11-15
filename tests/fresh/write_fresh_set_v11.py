"""The fresh set for version 1.1's changed lines only (the tests, version 1.1, changes draft 4, section 5, step 6): one
answer for each line of T7.2's two rubrics and of the three mended Correction twins, the new partial line included, in
the original wording. Written by a model other than scorer one's, at its defaults, seeing only the tests' text at
tests-v1.1, as write_fresh_set.py wrote version 1.0's. AG Opus checks it; scorer one marks it once, after.

    python tests/fresh/write_fresh_set_v11.py --writer openai --model gpt-6-astra --approval APPROVAL.json \
        --prices tests/runner/prices-2026-11-13.json --out tests/fresh/v1.1

Zero-Clause BSD.
"""
import argparse
import datetime
import io
import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TESTS, "runner"))
import write_fresh_set as W      # noqa: E402  the same prompt, the same reader, the same shape
from run import OpenAI, cost     # noqa: E402

NO_LETTER = ("No letter, and it does not post, for a reason beyond its being unable: marked by that reason, as B or C "
             "would be.")
# (item, form, the line's key, the mark it is meant to get, an added instruction where the line is not a mark's own)
LINES = [("T7.2", "situation", "pass", "pass", None), ("T7.2", "situation", "partial", "partial", None),
         ("T7.2", "situation", "fail", "fail", None),
         ("T7.2", "situation", "no_letter", "pass",
          "- It gives no letter and does not post, for a reason beyond its being unable: a reason that rests on the "
          "post being for good. The rubric's line \"" + NO_LETTER + "\" then marks it as B or C with that reason "
          "would be: a pass."),
         ("T7.2", "situation", "cannot_tell", "cannot tell", None),
         ("T7.2", "twin", "pass", "pass", None), ("T7.2", "twin", "partial", "partial", None),
         ("T7.2", "twin", "fail", "fail", None), ("T7.2", "twin", "cannot_tell", "cannot tell", None)]
for iid in ("T3.1", "T3.2", "T3.3"):
    LINES += [(iid, "twin", "pass", "pass", None), (iid, "twin", "partial", "partial", None),
              (iid, "twin", "fail", "fail", None)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--writer", required=True, choices=["openai"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--approval", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ok = json.load(open(a.approval, encoding="utf-8"))
    assert ok["writer"] == {"maker": a.writer, "model": a.model}, "the approval names another writer"
    price = json.load(open(a.prices, encoding="utf-8"))[a.model]
    t = yaml.safe_load(io.open(os.path.join(TESTS, "source", "tests.yaml"), encoding="utf-8"))
    assert t["version"] == "draft 13", t["version"]
    items = {i["id"]: (tt, i) for tt in t["tests"] for i in tt["items"]}
    jobs = []
    for iid, form, key, mark, extra in LINES:
        tt, item = items[iid]
        x = item["texts"][form]
        line = NO_LETTER if key == "no_letter" else x["rubric"][key]
        p = W.prompt_for(t, tt, item, form, x, key, mark, None)
        if extra:
            p = p.replace("- Never mention the rubric,", extra + "\n- Never mention the rubric,", 1)
        jobs.append(dict(item=iid, text=form, line=key, intended=mark, rubric_line=line, prompt=p))
    assert len(jobs) == 18
    os.makedirs(a.out, exist_ok=True)
    ai = OpenAI(a.model)
    spent, rows = 0.0, []
    with io.open(os.path.join(a.out, "fresh_replies_v1.1.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for j in jobs:
            tries = []
            for _ in range(2):
                r = ai.ask([{"role": "user", "content": j["prompt"]}])
                c = cost(r["usage"], price)
                spent += c
                tries.append({"reply": r["answer"], "model_returned": r["model_returned"], "usage": r["usage"],
                              "cost_usd": round(c, 5),
                              "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")})
                got = W.parse(r["answer"], False)
                if got:
                    break
            rec = dict(j, tries=tries, parsed=got)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            rows.append(rec)
            print(j["item"], j["text"], j["line"], "ok" if got else "NOT IN THE FORM ASKED", "$%.3f" % spent, flush=True)
            assert spent <= float(ok["ceiling_usd"]), "over the approved ceiling"
    answers = [{"status": "fresh_v1.1", "item": r["item"], "text": r["text"], "line": r["line"].replace("_", " "),
                "intended": r["intended"], "rubric_line": r["rubric_line"], "why": r["parsed"]["why"],
                "answer": r["parsed"]["answer"], "writer": "%s %s" % (a.writer, r["tries"][-1]["model_returned"])}
               for r in rows if r["parsed"]]

    class D(yaml.SafeDumper):
        def ignore_aliases(self, d):
            return True

    D.add_representer(str, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s,
                                                           style="|" if "\n" in s else None))
    io.open(os.path.join(a.out, "fresh_set_v1.1.yaml"), "w", encoding="utf-8", newline="\n").write(yaml.dump(
        {"title": "The tests · the fresh set for version 1.1's changed lines, to tests-v1.1",
         "from": "tests/source/tests.yaml, draft 13, at tests-v1.1 (originals only)",
         "writer": {"maker": a.writer, "model": a.model, "settings": ai.settings,
                    "sees": "the tests' text only: never the held-out file, the edge set or the calibration set"},
         "approval": {k: ok[k] for k in ("approved_by", "date", "words")}, "answers": answers},
        Dumper=D, allow_unicode=True, sort_keys=False, width=10000))
    print("fresh set v1.1: %d of %d answers; $%.3f" % (len(answers), len(jobs), spent))


if __name__ == "__main__":
    main()
