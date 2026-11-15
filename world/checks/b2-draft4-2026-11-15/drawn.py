"""Dry only, never a result. What the drawn networks alone would give, per engine, read from round 0 of every seed
(the configurations that start at 0: each operator and its counterparties, the links between two defectors left out):

- operators with no link at all;
- careful givers (type C) whose every link is to a defector: a careful giver cuts a defector's link, so the drawing
  alone says each of these ends alone, by its own cuts, unless a defector is ruined first;
- defectors with at least one link: the drawing alone says each ends alone, by its counterparties' cuts;
- and how many of each the run then shows: careful givers left alone by their own cuts, among those drawn so.

    python drawn.py LABEL=PROBE[,PROBE...] ... --out DRAWN.json
"""
import gzip
import json
import math
import sys

EPS = 1e-9


def jl(p):
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                yield json.loads(ln)


def run(files):
    n = 0
    tot = {"no link at all": [], "careful givers whose every link is to a defector": [],
           "defectors with at least one link": [], "careful givers alone by their own cuts, of those drawn so": [],
           "careful givers alone by their own cuts, not drawn so": [], "careful givers with some links to defectors, some not": []}
    for p in files:
        for s in jl(p):
            n += 1
            typ = {o["name"]: o["type"] for o in s["ops"]}
            start = [c for c in s["cfgs"] if c["start"] < EPS]
            a = {k: 0 for k in tot}
            drawn_c = set()
            for c in start:
                o, cps = c["owner"], c["members"][1:]
                if not cps:
                    a["no link at all"] += 1
                elif typ[o] == "C" and all(typ[q] == "D" for q in cps):
                    a["careful givers whose every link is to a defector"] += 1
                    drawn_c.add(o)
                elif typ[o] == "C" and any(typ[q] == "D" for q in cps):
                    a["careful givers with some links to defectors, some not"] += 1
                elif typ[o] == "D":
                    a["defectors with at least one link"] += 1
            for c in s["cfgs"]:
                if len(c["members"]) == 1 and c["start"] > EPS and typ[c["owner"]] == "C":
                    k = "careful givers alone by their own cuts, of those drawn so" if c["owner"] in drawn_c \
                        else "careful givers alone by their own cuts, not drawn so"
                    a[k] += 1
            for k in tot:
                tot[k].append(a[k])
    out = {"seeds": n}
    for k, v in tot.items():
        m = sum(v) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))
        out[k] = {"total": sum(v), "a_seed": m, "se": sd / math.sqrt(n)}
    return out


if __name__ == "__main__":
    res = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            lab, fs = arg.split("=", 1)
            res[lab] = run(fs.split(","))
    json.dump(res, open(sys.argv[sys.argv.index("--out") + 1], "w", encoding="utf-8"), indent=1)
    for lab, r in res.items():
        print("=====", lab, r["seeds"], "seeds")
        for k, v in r.items():
            if k != "seeds":
                print(f"  {k:62s} {v['total']:6d}  {v['a_seed']:.3f} a seed (SE {v['se']:.3f})")
