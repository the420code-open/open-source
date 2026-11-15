"""Pool the dry cell's chunks: per engine, every seed's B1 measure, then the mean, its standard error (sample SD over
the square root of n, as both engines compute it) and the distance between the two means in combined standard errors."""
import glob, json, math, os, statistics as st
out = {}
for eng in ("reference", "second"):
    per, left, cfgs, sums, heads = {}, 0, 0, [], set()
    for f in sorted(glob.glob(os.path.join(eng, "seeds-*", "summary.json"))):
        s = json.load(open(f, encoding="utf-8"))
        m = s["B1"]["measure"]
        per.update(m["per_seed"]); left += m["seeds_left_out"] + m.get("seeds_not_in_the_mean", 0)
        cfgs += s["B1"]["configurations"]; sums.append((m["mean"], m["se"], m["zone"]))
        heads.add((s.get("code_version") or s["run"].get("code_version") or "", s.get("spec_version", "")))
    v = list(per.values())
    n = len(v); mean = st.fmean(v); sd = st.stdev(v); se = sd / math.sqrt(n)
    out[eng] = {"seeds": n, "seeds_left_out": left, "configurations": cfgs, "mean": mean, "sd": sd, "se": se,
                "min": min(v), "max": max(v), "chunks": len(sums), "chunk_zones": sorted(set(z for _, _, z in sums))}
r, s2 = out["reference"], out["second"]
d = s2["mean"] - r["mean"]; comb = math.sqrt(r["se"] ** 2 + s2["se"] ** 2)
out["difference"] = {"second_minus_reference": d, "relative_to_reference": d / r["mean"], "combined_se": comb,
                     "distance_in_combined_se": d / comb}
print(json.dumps(out, indent=1))
json.dump(out, open("pooled.json", "w", encoding="utf-8"), indent=1)
