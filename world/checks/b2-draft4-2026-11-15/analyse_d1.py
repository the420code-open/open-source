"""B2 draft 4, section 9: D1 itself, on a thousand fresh dry seeds in each engine, read as "Where the two engines part"
read D1 with even drift. Dry, never a result.

- B2's measure and B1's, from each part's own summary, the parts pooled by seed: the mean of the per-seed largest,
  its standard error (the sample standard deviation over the square root of n), and how far apart the two engines
  are, in combined standard errors (the square root of the sum of the two squared standard errors).
- Every operator left alone, a seed, by how it came to be alone, from the probes, by count.py of
  world/checks/engines-part-2026-11-15, copied here byte for byte; and what the drawn networks give, by drawn.py, the
  same. Beside them, the law of the draw, as worked out there for D1's network (the drift is drawn after the links,
  so D1 and D1 with even drift draw the same networks).
- What the gap moves in B2's measure: the difference of the two engines' means, with its combined standard error, as
  there.

    python analyse_d1.py RUNS_DIR OUT.json
"""
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import count  # noqa: E402
import drawn  # noqa: E402

runs, out = sys.argv[1:3]
LAW = {"operators with no link, the defectors' links between them left out": 0.3920946425579442,
       "careful givers whose every link is to a defector": 0.4435341945518165}


def stats(v):
    n = len(v)
    m = sum(v) / n
    return {"seeds": n, "mean": m, "se": math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) / math.sqrt(n)}


def apart(a, b):
    c = math.sqrt(a["se"] ** 2 + b["se"] ** 2)
    return {"difference_second_less_reference": b["mean"] - a["mean"], "combined_se": c,
            "in_combined_se": (b["mean"] - a["mean"]) / c}


res = {"label": "dry, never a result", "cell": "D1, as written", "engines": "wc/b2-points-20-22 at fa05337"}
for eng in ("reference", "second"):
    parts = sorted(glob.glob(os.path.join(runs, eng, "D1", "seeds-*")))
    per = {"B2": {}, "B1": {}}
    left = {"B2": [0, 0], "B1": [0, 0]}
    seeds = 0
    for d in parts:
        s = json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))
        for h in ("B2", "B1"):
            m = s[h]["measure"]
            per[h].update({int(k): v for k, v in m["per_seed"].items()})
            left[h][0] += m["seeds_left_out"]
            left[h][1] += m["seeds_without_a_watched_configuration"]
        seeds += s[h]["measure"]["seeds"]
    probes = [os.path.join(d, "probe.jsonl.gz") for d in parts]
    c = count.count(probes)
    dr = drawn.run(probes)
    res[eng] = {
        "parts": [os.path.basename(d) for d in parts], "seeds": seeds,
        "B2_measure": dict(stats(list(per["B2"].values())), largest_seed=max(per["B2"].values()),
                           seeds_left_out_too_long_to_judge=left["B2"][0], seeds_with_nothing_to_watch=left["B2"][1]),
        "B1_measure": dict(stats(list(per["B1"].values())), largest_seed=max(per["B1"].values()),
                           seeds_left_out_too_long_to_judge=left["B1"][0], seeds_with_nothing_to_watch=left["B1"][1]),
        "operators_left_alone": c, "drawn": dr}
r, s = res["reference"], res["second"]
res["second engine against reference"] = {
    "B2_measure": apart(r["B2_measure"], s["B2_measure"]),
    "B1_measure": apart(r["B1_measure"], s["B1_measure"]),
    "operators_left_alone_a_seed": apart(r["operators_left_alone"]["alone_a_seed"], s["operators_left_alone"]["alone_a_seed"])}
res["the law of the draw"] = LAW
json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
for eng in ("reference", "second"):
    x = res[eng]
    print(eng, x["seeds"], "seeds | B2 %.4f (SE %.4f), left out %d, nothing %d | B1 %.4f (SE %.4f) | alone %.3f (SE %.3f)" % (
        x["B2_measure"]["mean"], x["B2_measure"]["se"], x["B2_measure"]["seeds_left_out_too_long_to_judge"],
        x["B2_measure"]["seeds_with_nothing_to_watch"], x["B1_measure"]["mean"], x["B1_measure"]["se"],
        x["operators_left_alone"]["alone_a_seed"]["mean"], x["operators_left_alone"]["alone_a_seed"]["se"]))
    for k, v in x["operators_left_alone"]["how_they_came_to_be_alone"].items():
        print("    %-60s %6d  %.3f a seed" % (k, v["all"], v["all"] / x["seeds"]))
    print("    alone at round 0, the world: %.3f (SE %.3f); in the drawing with every link: %.3f" % (
        x["operators_left_alone"]["alone_at_round_0_in_the_world_defector_links_left_out"]["mean"],
        x["operators_left_alone"]["alone_at_round_0_in_the_world_defector_links_left_out"]["se"],
        x["operators_left_alone"]["alone_at_round_0_in_the_drawing_with_every_link"]["mean"]))
    for k, v in x["drawn"].items():
        if k != "seeds":
            print("    drawn: %-58s %.3f (SE %.3f)" % (k, v["a_seed"], v["se"]))
    print("    defectors' configurations:", x["operators_left_alone"]["defectors_configurations_by_how_they_ended"])
print(json.dumps(res["second engine against reference"], indent=1))
