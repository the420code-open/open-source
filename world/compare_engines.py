"""The two engines, cell by cell: B1's section 9.

    python world/compare_engines.py CELL.json --reference REF/summary.json --browser BRW/summary.json
        [--reference REF2/summary.json --browser BRW2/summary.json]

Each summary is a run_cell summary (world/reference/run_cell.py or world/browser/run_cell.mjs) of the same cell.

- In the quiet cells of the ring with one defector, every place on the ring is the same, so every seed gives the same
  value: there the two engines must agree to 0.000001, seed by seed.
- In every other cell they agree when the difference of their means is within three of their combined standard
  errors, sqrt(se1^2 + se2^2). By chance alone that is exceeded in about one cell in 370.
- A cell where they disagree is run again in both engines, once, with a second hundred seeds each: 101 to 200 for the
  reference and 100,101 to 100,200 for the second engine. Given both hundreds, the two hundred of each engine are
  pooled. If they agree, it is recorded as chance. If not, it is reported as "engines disagree", the cause is looked
  for in the open, and no cell of B1 is judged until it is found and recorded.

Zero-Clause BSD.
"""
import argparse
import json
import math

EXACT = 1e-6
SECOND_HUNDRED = {"reference": "101-200", "browser": "100101-100200"}


def per_seed(paths):
    vals, out, without = [], 0, 0
    for p in paths:
        m = json.load(open(p, encoding="utf-8"))["B1"]["measure"]
        vals += [float(v) for v in m["per_seed"].values()]
        out += m["seeds_left_out"]
        without += m["seeds_without_a_watched_configuration"]
    return vals, out, without


def stats(vals):
    n = len(vals)
    mean = sum(vals) / n
    se = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) / math.sqrt(n) if n > 1 else float("nan")
    return mean, se


def exact_cell(cell):
    ov = cell.get("overrides", {})
    t = cell.get("types", {})
    return (cell.get("topology", "ring") == "ring" and t.get("defectors") == 1 and not cell.get("entry")
            and not ov.get("sigma_s") and not ov.get("sigma_r"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell")
    ap.add_argument("--reference", action="append", required=True)
    ap.add_argument("--browser", action="append", required=True)
    a = ap.parse_args()
    cell = json.load(open(a.cell, encoding="utf-8"))
    if len(a.reference) != len(a.browser) or len(a.reference) > 2:
        raise SystemExit("give one hundred of each engine, or two hundreds of each")
    second = len(a.reference) == 2
    rv, rout, rwo = per_seed(a.reference)
    bv, bout, bwo = per_seed(a.browser)
    count = lambda paths: sum(json.load(open(p, encoding="utf-8"))["seeds"] for p in paths)
    res = {"cell": cell.get("id"), "runs": "first and second hundred" if second else "first hundred",
           "seeds_run": {"reference": count(a.reference), "browser": count(a.browser)},
           "reference": {"seeds_measured": len(rv), "left_out": rout, "without_a_watched_configuration": rwo},
           "browser": {"seeds_measured": len(bv), "left_out": bout, "without_a_watched_configuration": bwo}}
    if not rv or not bv:
        res["verdict"] = "cannot compare: an engine has no measured seed"
    elif exact_cell(cell):
        spread = max(rv + bv) - min(rv + bv)
        res.update(rule="the quiet ring with one defector: every seed the same, to 0.000001",
                   reference_values=[min(rv), max(rv)], browser_values=[min(bv), max(bv)], spread=spread)
        agree = spread <= EXACT
    else:
        (rm, rse), (bm, bse) = stats(rv), stats(bv)
        comb = math.sqrt(rse ** 2 + bse ** 2)
        res.update(rule="the difference of the means within three combined standard errors",
                   reference_mean=rm, reference_se=rse, browser_mean=bm, browser_se=bse,
                   difference=abs(rm - bm), combined_se=comb, in_combined_se=abs(rm - bm) / comb if comb else None)
        agree = abs(rm - bm) <= 3 * comb
    if "verdict" not in res:
        if agree:
            res["verdict"] = "agree, recorded as chance after a second hundred" if second else "agree"
        elif not second:
            res["verdict"] = ("disagree: run again in both, once, with a second hundred seeds each: the reference "
                              "%s, the second engine %s" % (SECOND_HUNDRED["reference"], SECOND_HUNDRED["browser"]))
        else:
            res["verdict"] = ("engines disagree: the cause is looked for in the open, and no cell of B1 is judged "
                              "until it is found and recorded")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
