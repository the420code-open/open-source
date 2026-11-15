"""Dry only, never a result. Every link at round 0, by its two ends' types (C-C or C-D), and how it ended: cut by
one end (which type), cut by both at once, the ruin of an end, or standing at the end. Read the same way from both
engines' probes: the links at round 0 from the configurations that start at 0, cuts from the cut records, ruins from
the ruin records. Also every careful giver's degree at round 0, and the defectors' degree.

    python links.py LABEL=PROBE[,PROBE...] ... --out LINKS.json
"""
import collections, gzip, json, sys
EPS = 1e-9
def jl(p):
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for ln in f:
            if ln.strip(): yield json.loads(ln)
def run(files):
    out = collections.Counter(); deg = {"C": collections.Counter(), "D": collections.Counter()}; n = 0
    for p in files:
        for s in jl(p):
            n += 1
            typ = {o["name"]: o["type"] for o in s["ops"]}
            ruin_t = {r["op"]: r["t"] for r in s["ruins"]}
            links = set()
            for c in s["cfgs"]:
                if c["start"] < EPS:
                    deg[typ[c["owner"]]][len(c["members"]) - 1] += 1
                    for q in c["members"][1:]:
                        links.add(frozenset((c["owner"], q)))
            cutby = collections.defaultdict(set)
            for c in s["cuts"]:
                cutby[frozenset(c["link"])].add(c["by"])
            for l in links:
                a, b = sorted(l); kind = "-".join(sorted((typ[a], typ[b])))
                if l in cutby:
                    bys = cutby[l]
                    how = "cut at both ends" if len(bys) == 2 else "cut by its %s end" % typ[next(iter(bys))]
                elif a in ruin_t or b in ruin_t:
                    how = "an end's ruin"
                else:
                    how = "standing at the end"
                out[(kind, how)] += 1
    return {"seeds": n, "links": {f"{k} | {h}": v for (k, h), v in sorted(out.items())},
            "degree_at_round_0": {t: dict(sorted(d.items())) for t, d in deg.items()}}
res = {}
for arg in sys.argv[1:]:
    if "=" in arg:
        lab, fs = arg.split("=", 1); res[lab] = run(fs.split(","))
json.dump(res, open(sys.argv[sys.argv.index("--out") + 1], "w", encoding="utf-8"), indent=1)
for lab, r in res.items():
    print("=====", lab, r["seeds"], "seeds")
    for k, v in r["links"].items(): print(f"  {k:45s} {v:7d}  {v / r['seeds']:.3f} a seed")
    print("  degree of C at round 0:", r["degree_at_round_0"]["C"])
    print("  degree of D at round 0:", r["degree_at_round_0"]["D"])
