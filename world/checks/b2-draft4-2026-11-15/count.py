"""Dry only, never a result. Reads the probes' files and counts, per engine:

1. every operator left alone (a configuration of one), by how it came to be alone:
   - with no link as drawn: alone at round 0; split into "no link drawn at all" and "drawn links only to defectors,
     which the world leaves out";
   - by its own cuts; by a counterparty's cut; cut at both ends at once; by a counterparty's ruin; or a mix of these,
     read from the links that ended at the moment it was left alone (the configuration before it, less the operator);
   - all of them, and those whose clock started (B2's watched set takes only those);
2. what the drawn networks alone would give: operators alone at round 0, in the drawing with every link, and in the
   world, once the links between two defectors are left out;
3. every defector's configuration by how it ended: a cut, its own ruin, a counterparty's ruin, standing at the end.

    python count.py LABEL=PROBE.jsonl.gz[,PROBE2...] [LABEL=...] --out COUNTS.json
"""
import collections
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


def how_alone(seed, L, cfgs, cuts, ruin_t):
    o = L["owner"]
    prev = [c for c in cfgs if c["owner"] == o and c is not L and c["end"] is not None and abs(c["end"] - L["start"]) < EPS]
    if not prev:
        return "not explained", []
    P = prev[0]
    lost = [q for q in P["members"] if q != o]
    parts = []
    for q in lost:
        if q in ruin_t and abs(ruin_t[q] - L["start"]) < 1e-6:
            parts.append("ruin")
            continue
        bys = {c["by"] for c in cuts if set(c["link"]) == {o, q}}
        parts.append({frozenset([o]): "own", frozenset([q]): "cp", frozenset([o, q]): "both"}.get(frozenset(bys), "unknown"))
    kinds = set(parts)
    if kinds == {"ruin"}:
        return "by a counterparty's ruin", parts
    if kinds == {"own"}:
        return "by its own cuts", parts
    if kinds == {"cp"}:
        return "by a counterparty's cut", parts
    if kinds == {"both"}:
        return "cut at both ends at once", parts
    return "a mix: " + "+".join(sorted(kinds)), parts


def count(files):
    by = collections.Counter()           # (category, type, watched) -> n
    per_seed_alone = []                  # all lone configurations a seed
    per_seed_watched = []
    drawn0, world0 = [], []
    dcfg = collections.Counter()
    seeds = 0
    first_alone_t = collections.defaultdict(list)
    for p in files:
        for s in jl(p):
            seeds += 1
            typ = {o["name"]: o["type"] for o in s["ops"]}
            ruin_t = {r["op"]: r["t"] for r in s["ruins"]}
            left = {x for pair in s.get("left_out", []) for x in pair}
            cfgs = s["cfgs"]
            alone = [c for c in cfgs if len(c["members"]) == 1]
            per_seed_alone.append(len(alone))
            per_seed_watched.append(sum(1 for c in alone if c["clock"] is not None))
            a0 = [c for c in alone if c["start"] < EPS]
            world0.append(len(a0))
            drawn0.append(sum(1 for c in a0 if c["owner"] not in left))
            for L in alone:
                if L["start"] < EPS:
                    cat = "no link as drawn: drawn links only to defectors, left out" if L["owner"] in left \
                        else "no link as drawn: none drawn at all"
                else:
                    cat, _ = how_alone(s["seed"], L, cfgs, s["cuts"], ruin_t)
                    first_alone_t[cat].append(L["start"])
                by[(cat, typ[L["owner"]], L["clock"] is not None)] += 1
            for c in cfgs:
                if typ[c["owner"]] != "D":
                    continue
                r = c["reason"]
                r = {"cut": "a cut", "ruin": "its own ruin", "counterparty ruined": "a counterparty's ruin",
                     "run ended": "standing at the end", None: "standing at the end", "new link": "a new link",
                     "link": "a new link"}.get(r, r)
                dcfg[(r, len(c["members"]) == 1)] += 1
    def ms(v):
        n = len(v); m = sum(v) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) if n > 1 else float("nan")
        return {"mean": m, "se": sd / math.sqrt(n), "total": sum(v)}
    cats = sorted({k[0] for k in by})
    table = {}
    for c in cats:
        row = {}
        for t in ("C", "D", "U"):
            a = by[(c, t, True)] + by[(c, t, False)]
            if a:
                row[t] = {"all": a, "watched": by[(c, t, True)]}
        row["all"] = sum(v["all"] for v in row.values())
        row["watched"] = sum(v["watched"] for k, v in row.items() if isinstance(v, dict))
        table[c] = row
    return {"seeds": seeds, "alone_a_seed": ms(per_seed_alone), "watched_alone_a_seed": ms(per_seed_watched),
            "alone_at_round_0_in_the_drawing_with_every_link": ms(drawn0),
            "alone_at_round_0_in_the_world_defector_links_left_out": ms(world0),
            "how_they_came_to_be_alone": table,
            "median_round_left_alone": {c: sorted(v)[len(v) // 2] for c, v in first_alone_t.items() if v},
            "defectors_configurations_by_how_they_ended": {f"{r}{' (alone)' if a else ''}": n for (r, a), n in sorted(dcfg.items())}}


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1]
    res = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            label, files = arg.split("=", 1)
            res[label] = count(files.split(","))
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    print(json.dumps(res, indent=1)[:4000])
