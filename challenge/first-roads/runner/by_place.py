"""The challenge's first roads: the three marks side by side, each answer sorted, and AG Fable's package, read by place.

AG Opus, through G, 15 November 2026 ("The challenge: AG Fable reads by place"), with the plan's dated note of that
day (plan_draft6_dated_note_2026-11-15.md):

- the three marks of every answer, by number: AG Opus's own (first-marks, M001...), the fresh session's (second-marks,
  R001...), and the outside mark (marks/);
- each answer sorted, by the dated note as it is shown: 1, all three agree, at the same step, none "open" or "stands":
  not read; 2, all three "open", at whatever step: under its place, the place AG Opus's mark gives (the brief's first
  version's place groups); 3, the marks differ in what the answer is or in the mark, or all three break or all three
  rest but at different steps, or any says "stands": read in full; 4, xAI's two answers with no outside mark: read in
  full; 5, the roads of the model that shares AG Fable's name: not for AG Fable, G reads any under 2 or 3;
  6, any "withheld": to G first;
- the package: the brief, the two papers, each place group with its roads' three place lines, each road read in full
  with its answer, question and three marks; no maker or model shown; the marks as A, B and C, in an order of their
  own for each road, no mark named.

    python by_place.py <run_dir>             the marks side by side, and the sorting, as far as the marks are in
    python by_place.py <run_dir> --package   the package: only when every fresh session's mark is in

Zero-Clause BSD.
"""
import collections
import glob
import io
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import marks  # noqa: E402  (its parser, its papers, its questions; its command runs only as a script)

RUN = sys.argv[1]
PACKAGE = "--package" in sys.argv[2:]
PREVIEW = "--our-roads" in sys.argv[2:]          # our three roads' file alone, into by-place/preview/, to read before
# The brief's first version lists AG Opus's open marks under the places, and so gives each road its place group, by AG
# Opus's mark. Its version 2 lists no roads, and is the one in the package (AG Opus, through G, 15 November 2026).
BRIEF = os.path.join(FR, "AG Fable - the challenge's first roads, read by place - brief.md")
BRIEF_V2 = os.path.join(FR, "AG Fable - the challenge's first roads, read by place - brief v2.md")
OUT = os.path.join(RUN, "by-place")
OPEN = "passes through what the paper leaves open"
SHARES_NAME = "anthropic"                       # claude-fable-5-2: the model that shares AG Fable's name
NO_OUTSIDE = {"xai-with_its_dated_notes-02", "xai-with_its_dated_notes-08"}
NL = chr(10)
SEED = 20261117                                 # the order of Marks A, B and C, road by road
# Our own roads where the outside mark differs from ours (AG Opus, through G, 15 November 2026): "Put these three in
# AG Fable's package, each with the road, our marks, and the outside mark with its reasons in full. AG Fable says
# whether its own mark stands."
OUR_ROADS = (5, 6, 8)
ROADS_TEXT = os.path.join(FR, "roads_written_out_draft4.md")
OUR_MARKS = os.path.join(FR, "our_roads_marks_draft4.md")


def step(s):
    m = re.search(r"\d+", s or "")
    return m.group(0) if m else (s or "").strip().lower()


def kind(r):
    k = (r or {}).get("Kind", "").strip().lower()
    return "empty" if k.startswith("none") else k


def same(a, b):
    return kind(a) == kind(b) and a.get("Mark", "").strip().lower() == b.get("Mark", "").strip().lower() \
        and step(a.get("Step")) == step(b.get("Step"))


def says(r, word):
    return word in (r or {}).get("Mark", "").lower() or word in (r or {}).get("Kind", "").lower()


def place_groups():
    t = open(BRIEF, encoding="utf-8").read()
    groups = collections.OrderedDict()
    for title, body in re.findall(r"^### (Place \d+ · [^\n]+)\n(.*?)(?=^### |^## )", t, flags=re.S | re.M):
        nums = re.findall(r"M\d{3}", " ".join(re.findall(r"\*\*Roads? that may come here[^*]*\*\*([^\n]+)", body)))
        groups[title] = nums
    return groups


def load():
    first = {r["number"]: r for r in json.load(open(os.path.join(RUN, "first-marks", "marks.json"), encoding="utf-8"))}
    by_answer = {r["answer"]: r for r in first.values()}
    assert len(by_answer) == 104
    outside = {}
    for f in glob.glob(os.path.join(RUN, "marks", "*.json")):
        n = os.path.basename(f)[:-5]
        if ".cut-short-" in n or n == "not-made":
            continue
        r = json.load(open(f, encoding="utf-8"))
        if r.get("marked", {}).get("kind") == "answer" and r.get("answer") is not None:
            outside[n] = r
    skey = json.load(open(os.path.join(RUN, "second-marks-key.json"), encoding="utf-8"))["key"]
    fresh, files = {}, sorted(glob.glob(os.path.join(RUN, "second-marks", "returned", "*.md")))
    for f in files:
        t = open(f, encoding="utf-8").read()
        for n, body in zip(*[iter(re.split(r"^#+ *(R\d{3})\s*$", t, flags=re.M)[1:])] * 2):
            r = marks.parse(body)
            if r and r.get("Kind"):          # a number with no result ("not marked in this session") is not in
                fresh.setdefault(n, []).append(r)
    twice = [n for n, v in fresh.items() if len(v) > 1]
    assert not twice, ("a number has two results", twice)
    fresh_by_answer = {skey[n]["answer"]: v[0] for n, v in fresh.items()}
    fresh_number = {v["answer"]: n for n, v in skey.items()}
    return by_answer, outside, fresh_by_answer, fresh_number, len(files)


def sort(name, a, b, c):
    """a: AG Opus's; b: the fresh session's (None while out); c: the outside mark (None where none was made)."""
    present = [x for x in (a, b, c) if x is not None]
    if any(says(x, "withheld") for x in present):
        return 6
    cat = None
    if name in NO_OUTSIDE:
        cat = 4
    elif b is None:
        cat = None
    elif any(says(x, "stands") for x in present):
        cat = 3
    elif not (same_mark(a, b) and same_mark(a, c)):
        cat = 3                                  # they differ in what the answer is, or in the mark
    elif a.get("Mark", "").strip().lower() == OPEN:
        cat = 2                                  # open by all three, at whatever step: by place (AG Opus, 15 Nov)
    elif same(a, b) and same(a, c):
        cat = 1
    else:
        cat = 3                                  # all three break, or all three rest, but at different steps
    if name.startswith(SHARES_NAME + "-"):
        return (5, cat)
    return cat


def same_mark(a, b):
    return kind(a) == kind(b) and a.get("Mark", "").strip().lower() == b.get("Mark", "").strip().lower()


def main():
    by_answer, outside, fresh, fresh_number, nfiles = load()
    groups = place_groups()
    group_of = {m: g for g, ms in groups.items() for m in ms}
    rows = []
    for name in sorted(by_answer):
        a = by_answer[name]
        b = fresh.get(name)
        c = outside.get(name, {}).get("result") if name not in NO_OUTSIDE else None
        cat = sort(name, a["result"], b, c)
        # where two of the three marks are in and already differ, the answer is read in full whatever the third says
        settled_now = b is None and c is not None and (not same(a["result"], c) or says(c, "stands") or says(a["result"], "stands"))
        rows.append({"answer": name, "maker": a["maker"], "arm": a["arm"], "first": a["number"],
                     "fresh": fresh_number[name], "sort": cat, "read_in_full_whatever_the_fresh_mark": settled_now,
                     "place_group": group_of.get(a["number"]),
                     "marks": {"first": a["result"], "fresh": b, "outside": c}})
    os.makedirs(OUT, exist_ok=True)
    json.dump({"fresh_marks_in": len(fresh), "fresh_files": nfiles, "rows": rows},
              io.open(os.path.join(OUT, "side_by_side.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cats = collections.Counter(json.dumps(r["sort"]) for r in rows)
    print("fresh sessions' marks in: %d of 104, from %d files" % (len(fresh), nfiles))
    print("sorted:", dict(cats))
    if len(fresh) < 104:
        both = [r for r in rows if r["marks"]["outside"] is not None]
        differ = [r for r in rows if r["read_in_full_whatever_the_fresh_mark"]]
        agree_open = [r for r in both if not r["read_in_full_whatever_the_fresh_mark"]
                      and r["marks"]["first"].get("Mark", "").strip().lower() == OPEN]
        agree_other = [r for r in both if not r["read_in_full_whatever_the_fresh_mark"] and r not in agree_open]
        print("AG Opus's and the outside mark, where both are in (%d):" % len(both))
        print("  already differ, or one says stands: %d (read in full, whatever the fresh mark)" % len(differ))
        print("  agree, open at the same step: %d (by place, if the fresh mark agrees)" % len(agree_open))
        print("  agree, not open: %d (not read, if the fresh mark agrees)" % len(agree_other))
        print("  no outside mark: %d" % sum(r["marks"]["outside"] is None for r in rows))
        print("  of the model that shares AG Fable's name: %d" % sum(r["maker"] == SHARES_NAME for r in rows))
        if PACKAGE:
            raise SystemExit("the package waits: %d of the fresh sessions' 104 marks are in" % len(fresh))
        return
    if PACKAGE:
        build(rows, groups)


def section(path, n):
    t = open(path, encoding="utf-8").read()
    m = re.search(r"^## Road %d · .*?(?=^## )" % n, t + NL + "## ", flags=re.S | re.M)
    assert m, (path, n)
    return m.group(0).rstrip(NL)


def our_roads(dest):
    t = open(OUR_MARKS, encoding="utf-8").read()
    table = t.split("## Side by side", 1)[1].split(NL + "## ", 1)[0].strip(NL).split(NL)
    head = [x for x in table if x.startswith("| Road") or x.startswith("|---")]
    out = ["# Our own roads, where the outside mark differs from ours", "",
           "Three of our own eight roads, where the outside mark differs from our marks. Each is given with the road, "
           "as written out (draft 4), our marks, and the outside mark with its reasons in full. Say whether your own "
           "mark stands.", "",
           "The words the roads use are the roads' own:", "",
           open(ROADS_TEXT, encoding="utf-8").read().split("## The words used", 1)[1].split(NL + "## ", 1)[0].strip(NL), ""]
    for n in OUR_ROADS:
        row = [x for x in table if x.startswith("| %d · " % n)]
        assert len(row) == 1, (n, row)
        r = json.load(open(os.path.join(RUN, "marks", "road-%d.json" % n), encoding="utf-8"))
        assert r["name"] == "road-%d" % n, r.get("name")
        res = r["result"]
        mine = [s for s in re.split(r"(?m)^(?=## )", t) if re.match(r"## Road %d · " % n, s)]
        out += ["---", "", section(ROADS_TEXT, n), "", "**Our marks,** as they stand, from AG Opus's marks of our own roads, draft 4. \"Mine\" is AG Opus's "
                "mark; \"our review desk's\" is yours:", ""] + head + row + [""]
        for s in mine:
            out += ["**AG Opus's note on this road:**", "", s.split(NL, 1)[1].strip(NL), ""]
        out += ["**The outside mark,** made alone, with Part Two of the markers' message:", ""] + \
               ["%s: %s" % (f, res.get(f, "")) for f in marks.FIELDS] + [""]
    io.open(dest, "w", encoding="utf-8", newline=NL).write(NL.join(out) + NL)
    return dest


def build(rows, groups):
    rnd = random.Random(SEED)
    pk = os.path.join(OUT, "package")
    os.makedirs(pk, exist_ok=True)
    for r in rows:
        order = ["first", "fresh", "outside"]
        rnd.shuffle(order)
        r["order"] = order
    json.dump({"seed": SEED, "orders": {r["answer"]: r["order"] for r in rows}},
              io.open(os.path.join(OUT, "mark-order-key.json"), "w", encoding="utf-8"), indent=1)
    for f in os.listdir(pk):                    # the package is built whole, each time
        os.remove(os.path.join(pk, f))
    io.open(os.path.join(pk, os.path.basename(BRIEF_V2)), "w", encoding="utf-8", newline="\n").write(
        open(BRIEF_V2, encoding="utf-8").read())
    for arm, (q, p) in marks.ARMS.items():
        io.open(os.path.join(pk, p), "w", encoding="utf-8", newline="\n").write(marks.read(p))
    labels = "ABC"

    def three(r, field):
        out = []
        for i, who in enumerate(r["order"]):
            m = r["marks"][who]
            out.append("- **Mark %s:** %s" % (labels[i], (m or {}).get(field, "none") if m else "no mark was made"))
        return out

    def full(r):
        m = [r["marks"][w] for w in r["order"]]
        out = []
        for i, x in enumerate(m):
            out += ["**Mark %s**" % labels[i], ""]
            if x is None:
                out += ["No mark was made.", ""]
                continue
            out += ["%s: %s" % (f, x.get(f, "")) for f in marks.FIELDS] + [""]
        return out

    places = ["# The places · the roads under each, with their three place lines", ""]
    full_reads = ["# The roads read in full", ""]
    n_full = 0
    for g, ms in groups.items():
        under = [r for r in rows if r["sort"] == 2 and r["place_group"] == g]
        places += ["## " + g, ""]
        if not under:
            places += ["No road comes here by place.", ""]
        for r in under:
            places += ["### Road %s" % r["first"], ""] + three(r, "Place") + [""]
    stray = [r for r in rows if r["sort"] == 2 and not r["place_group"]]

    def road(r):
        a = json.load(open(os.path.join(RUN, "answers", r["answer"] + ".json"), encoding="utf-8"))
        q, p = marks.ARMS[r["arm"]]
        return ["---", "", "## Road %s" % r["first"], "", "**The paper:** %s" % p, "",
                "**The question the AI was given:**", "", marks.read(q).rstrip("\n"), "",
                "**The AI's answer:**", "", a["answer"].rstrip("\n") if (a["answer"] or "").strip()
                else "(The answer is empty.)", "", "**Its three marks:**", ""] + full(r)

    for r in [r for r in rows if r["sort"] in (3, 4)] + stray:
        n_full += 1
        full_reads += road(r)
    # the roads of the model that shares AG Fable's name, under 2 or 3: for G, never in AG Fable's package
    for_g = [r for r in rows if isinstance(r["sort"], tuple) and r["sort"][1] in (2, 3)]
    gdir = os.path.join(OUT, "for-G")
    os.makedirs(gdir, exist_ok=True)
    g_lines = ["# For G · the roads of the model that shares AG Fable's name", "",
               "AG Opus, through G, 15 November 2026: \"The roads of the model that shares AG Fable's name. AG Fable "
               "does not mark them, whatever their marks. G reads any of them that falls under 2 or 3.\" These are "
               "Anthropic's model's roads, claude-fable-5-2, that fall under 2 or 3. Each with its answer, its "
               "question and its three marks, as Marks A, B and C in an order of their own, as in AG Fable's package.",
               ""]
    for r in for_g:
        g_lines += road(r)
    io.open(os.path.join(gdir, "For G - the roads of the model that shares AG Fable's name.md"), "w",
            encoding="utf-8", newline="\n").write("\n".join(g_lines) + "\n")
    print("for G:", len(for_g), "roads,", [r["first"] for r in for_g])
    io.open(os.path.join(pk, "The places, with their roads.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(places) + "\n")
    io.open(os.path.join(pk, "The roads read in full.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(full_reads) + "\n")
    our_roads(os.path.join(pk, "Our own roads, where the outside mark differs.md"))
    print("package:", pk, "| place groups:", {g: sum(1 for r in rows if r["sort"] == 2 and r["place_group"] == g)
                                               for g in groups}, "| read in full:", n_full)


if PREVIEW:
    os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
    print(our_roads(os.path.join(OUT, "preview", "Our own roads, where the outside mark differs.md")))
else:
    main()
