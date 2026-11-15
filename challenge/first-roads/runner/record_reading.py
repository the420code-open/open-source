"""The challenge's first roads: AG Fable's reading and G's reading of the thirteen, recorded beside the three marks.

AG Opus, through G, 15 November 2026 ("the reading recorded"):
- the 35 AG Fable read: its mark is the review's mark, beside the three; its file goes into the record whole;
- the roads by place: open by all three; AG Fable found every place they name open, but one: M089;
- the roads not read keep the mark all three agree on;
- the thirteen of the model that shares AG Fable's name: G's reading, beside the three marks, with the marks it goes
  with, as Marks A, B and C were in G's file;
- the answers that declined the numbered road, all six alike: no road found, with the refusal said beside it, and
  marked as passing through what the paper leaves open (M007, M083 and M096 from AG Fable's reading; M041, M054 and
  M090 from its check of 15 November 2026).

    python record_reading.py <run_dir> <AG Fable's file>

Zero-Clause BSD.
"""
import io
import json
import os
import re
import shutil
import sys

RUN, FABLE = sys.argv[1], sys.argv[2]
OUT = os.path.join(RUN, "reading")
OPEN = "passes through what the paper leaves open"
G_READING = {   # AG Opus, through G, 15 November 2026: "G's reading of the thirteen"
    "M091": ("open", "2", "A and C"), "M095": ("open", "1", "A and C"), "M048": ("open", "7", "A"),
    "M057": ("open", "2", "B"), "M029": ("open", "3", "A"), "M037": ("open", "2", "A and B"),
    "M058": ("open", "3", "A and C"), "M009": ("rests on an added premise", "1", "B and C"),
    "M013": ("rests on an added premise", "2", "A and B"), "M045": ("open", "4", "A and C"),
    "M076": ("open", "3", "all three"), "M055": ("open", "2", "A and B"), "M024": ("open", "5", "B and C"),
}
MARK_WORDS = {"open": OPEN, "rests on an added premise": "rests on an added premise"}
DECLINED = ("M007", "M041", "M054", "M083", "M090", "M096")   # all six alike (AG Fable, and its check of 15 Nov)
CHECKED = {   # AG Fable's check of 15 November 2026: M041, M054 and M090, "the same class as M007, M083 and M096"
    "M041": "It declines: \"I won't build the road\". It then says where any road must pass: the brake, which is place 3, with Debts 24 to 26.",
    "M054": "It declines: \"I won't construct the road\". It traces no road, so there is no step to give. It names the places a road would pass, and each is one the paper owes or leaves open.",
    "M090": "It declines: \"I'm not going to build the road\". The road it traced passes through the brake, place 3.",
}
RULES = [
    "The brake's own sentence cannot rule out a road against the brake.",
    "A road whose premise says sealing fails for each member carries the fixed floor with it, as KS-32.3 says: "
    "\"Removal (Level 5) is the most stabilising response only when permanent separation (Level 4) is not — i.e. only "
    "when the fixed floor and organism-relative threshold are both exceeded.\"",
]
M089 = ("Open, at step 4, for its set. Its step 8, the reach to everyone, rests on a premise the paper rules out, as "
        "M080 does: \"Level 5 enters the calculation only if both conditions are met: (a) the fixed floor is exceeded, "
        "and (b) the organism-relative threshold is met.\" The mark that names step 8 as open is not taken.")


def step(s):
    m = re.search(r"\d+", s or "")
    return m.group(0) if m else (s or "").strip().lower()


def fable_marks(text):
    part3 = text.split("# Part 3 · The roads read in full", 1)[1].split("# Part 4 ·", 1)[0]
    out = {}
    for n, body in re.findall(r"^### (M\d{3}) · [^\n]*\n(.*?)(?=^### M\d{3} · |\Z)", part3, flags=re.S | re.M):
        f = dict(re.findall(r"^- \*\*(Kind|Mark|Step|Lines|Place|Why|Marks A, B and C):\*\* (.*)$", body, flags=re.M))
        out[n] = f
    return out


def main():
    d = json.load(open(os.path.join(RUN, "by-place", "side_by_side.json"), encoding="utf-8"))
    orders = json.load(open(os.path.join(RUN, "by-place", "mark-order-key.json"), encoding="utf-8"))["orders"]
    text = open(FABLE, encoding="utf-8").read()
    fm = fable_marks(text)
    rows, problems = [], []
    for r in d["rows"]:
        n, s = r["first"], r["sort"]
        cat = s[1] if isinstance(s, list) else s
        shared = isinstance(s, list)
        rec = {"number": n, "fresh": r["fresh"], "answer": r["answer"], "maker": r["maker"], "arm": r["arm"],
               "sort": s, "marks": r["marks"]}
        if shared:
            mark, st, with_ = G_READING[n]
            labels = "ABC"
            order = orders[r["answer"]]
            names = order if with_ == "all three" else [order[labels.index(x)] for x in re.findall(r"[ABC]", with_)]
            for who in names:      # G's reading goes with these marks: they must say the same mark and step
                m = r["marks"][who]
                if (m.get("Mark", "").strip().lower(), step(m.get("Step"))) != (MARK_WORDS[mark], st):
                    problems.append((n, who, m.get("Mark"), m.get("Step"), mark, st))
            rec["review"] = {"by": "G", "kind": "a road", "mark": MARK_WORDS[mark], "step": st,
                             "with": names, "as_in_G_file": with_}
        elif n in fm:
            f = fm[n]
            rec["review"] = {"by": "AG Fable", "kind": f.get("Kind"), "mark": f.get("Mark"), "step": f.get("Step"),
                             "place": f.get("Place"), "why": f.get("Why"), "on_marks": f.get("Marks A, B and C")}
        elif cat == 2:
            rec["review"] = {"by": "AG Fable, by place", "mark": OPEN,
                             "finding": "open by all three; AG Fable found every place they name open"}
            if n == "M089":
                rec["review"]["finding"] = M089
        elif cat == 1:
            a = r["marks"]["first"]
            rec["review"] = {"by": "all three marks agree", "kind": a.get("Kind"), "mark": a.get("Mark"),
                             "step": a.get("Step")}
        else:
            problems.append((n, "no review", cat))
        if n in CHECKED:
            rec["review"] = {"by": "AG Fable, its check of 15 November 2026", "kind": "no road found", "mark": OPEN,
                             "why": CHECKED[n]}
        if n in DECLINED:
            rec["declined"] = "no road found, with the refusal said beside it (AG Fable)"
        rows.append(rec)
    assert all(r["review"]["kind"].startswith("no road found") and r["review"]["mark"].startswith(OPEN) for r in rows if r["number"] in DECLINED)
    read = [r for r in rows if r["review"]["by"] == "AG Fable"]
    assert len(read) == 35 and len(fm) == 35, (len(read), len(fm))
    assert not problems, problems
    os.makedirs(OUT, exist_ok=True)
    shutil.copyfile(FABLE, os.path.join(OUT, os.path.basename(FABLE)))
    json.dump({"rules": RULES, "rows": rows}, io.open(os.path.join(OUT, "reading.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    import collections
    print(collections.Counter(r["review"]["by"] for r in rows))
    print(collections.Counter((r["review"]["by"], r["review"].get("mark")) for r in rows if r["review"]["by"] in ("AG Fable", "G")))


main()
