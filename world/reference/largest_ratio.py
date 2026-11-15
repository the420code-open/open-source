"""The largest ratio of stock noise to net loss in B1's and B2's grids, from the specification's formulas alone.

    python world/reference/largest_ratio.py [--draws 20000] [--json OUT]

No cell of either grid is run: nothing here steps the world in time. The net loss of each kind of configuration
the hypotheses watch is worked out at its formulas (Part Three's flows, Part Five's configuration, Part Nine's
two spans), at the states the specification fixes: every stock at E0 when a defector's configuration starts, and
the ruin line E_r where an operator alone is at its smallest loss. A random network's shape is drawn only to count
which configurations its links make, on seeds 1,000,000 and up, never a run's seeds.

The ratio is the stock noise over one round, sigma_s times the root of the round, over the net loss per round
that sets the span. It is given for one operator's noise, and for the noise of the members whose stock the span
counts (the root of their number times sigma_s).

Zero-Clause BSD.
"""
import argparse
import itertools
import json
import math

import numpy as np

E0, ER, LAM, EPS, UMAX, N = 50.0, 10.0, 1.0, 0.01, 6.0, 20
NOISE = {"quiet": (0.0, 0.0), "some": (0.5, 1.0), "more": (1.0, 1.0), "reading only": (0.0, 2.0)}


def gives(m, deg):
    """The give per link: m / 2 lambda, scaled down in proportion where the links would pass the capacity."""
    g = m / (2 * LAM)
    return np.where(deg * g > UMAX, UMAX / np.maximum(deg, 1), g)


def defector_configs(adj, typ, m, s, a):
    """For each defector: (members, whole rate, counterparties' net loss through their links to it), at E0."""
    deg = adj.sum(1)
    g = np.where(typ == 2, 0.0, gives(m, deg))
    n = len(typ)
    rate = np.zeros(n)
    for i in range(n):
        r = s - a[i] * E0
        for j in np.nonzero(adj[i])[0]:
            r += m * g[j] - (LAM * g[i] ** 2 + EPS)        # c = 0 in the network
        rate[i] = r
    out = []
    for d in np.nonzero(typ == 2)[0]:
        nb = np.nonzero(adj[d])[0]
        if len(nb) == 0:
            continue
        whole = rate[d] + rate[nb].sum()
        cp_loss = sum((LAM * g[j] ** 2 + EPS) - m * g[d] for j in nb)   # what the counterparties lose on links to d
        out.append((1 + len(nb), whole, cp_loss, len(nb)))
    return out


def span_loss(whole, cp_loss, members):
    """Part Nine, point 2: the whole's loss where it loses, else the counterparties' through their links."""
    if whole < 0:
        return -whole, members, "whole"
    if cp_loss > 0:
        return cp_loss, members - 1, "counterparties"
    return None, 0, None


def ring(n):
    A = np.zeros((n, n), bool)
    for i in range(n):
        A[i, (i + 1) % n] = A[(i + 1) % n, i] = True
    return A


def random_net(rng, n, p):
    u = rng.random((n, n))
    A = np.triu(u < p, 1)
    return A | A.T


def place(rng, n, d):
    t = np.zeros(n, np.int8)
    t[rng.choice(n, size=d, replace=False)] = 2
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=20000)
    ap.add_argument("--json")
    A = ap.parse_args()
    rows = []
    # ---- B1: the main grid and the entry grid (equal drift, a = 0.1; k = 0)
    cells = []
    for net, dfc, m, s, nz in itertools.product(["ring", "random"], [1, 3], [2, 3, 4], [0.0, 0.5], NOISE):
        cells.append(("B1", net, {"defectors": dfc}, m, s, nz, "equal", 0.0))
    for s, nz in itertools.product([0.0, 0.5], NOISE):
        cells.append(("B1 entry", "ring", {"defectors": 1}, 3, s, nz, "equal", 0.0))
    # ---- B2: both networks, m = 3, both s, quiet and more; share of defectors, drift, passive flow
    for net, s, nz, share, drift, k in itertools.product(["ring", "random"], [0.0, 0.5], ["quiet", "more"],
                                                          [0.1, 0.25], ["equal", "uneven"], [0.0, 0.05]):
        cells.append(("B2", net, {"share": share}, 3, s, nz, drift, k))

    cache = {}
    for hyp, net, D, m, s, nz, drift, k in cells:
        sig_s = NOISE[nz][0]
        dcount = D.get("defectors") or int(round(D["share"] * N))
        key = (net, dcount, m, s, drift)
        if key not in cache:
            rng = np.random.default_rng(1_000_000 + hash(key) % 1_000_000)
            smallest = (math.inf, None, None, None)
            draws = 1 if (net == "ring" and drift == "equal" and dcount == 1) else A.draws
            for _ in range(draws):
                adj = ring(N) if net == "ring" else random_net(rng, N, 0.2)
                typ = place(rng, N, dcount)
                a = np.full(N, 0.1) if drift == "equal" else rng.uniform(0.05, 0.2, N)
                for members, whole, cp, k_nb in defector_configs(adj, typ, m, s, a):
                    loss, n_noise, used = span_loss(whole, cp, members)
                    if loss is not None and loss < smallest[0]:
                        smallest = (loss, n_noise, used, k_nb)
            # an operator alone, at the ruin line: a E_r - s, at its smallest drift
            a_lo = 0.1 if drift == "equal" else 0.05
            cache[key] = (smallest, a_lo * ER - s)
        (lossA, nA, usedA, kA), lossB = cache[key]
        row = {"hypothesis": hyp, "network": net, **D, "m": m, "s": s, "noise": nz, "sigma_s": sig_s,
               "drift": drift, "k": k,
               "defector_with_hosts": {"smallest_loss_per_round": lossA, "span_used": usedA, "hosts": kA,
                                       "ratio_one_operator": sig_s / lossA if lossA else None,
                                       "ratio_members": sig_s * math.sqrt(nA) / lossA if lossA else None},
               "operator_alone_at_the_ruin_line": {"loss_per_round": lossB,
                                                   "ratio": (sig_s / lossB) if lossB > 0 else
                                                   (math.inf if sig_s else 0.0)}}
        rows.append(row)

    def top(sel, key):
        best = None
        for r in rows:
            if not sel(r):
                continue
            v = r[key[0]][key[1]]
            if v is not None and (best is None or v > best[0]):
                best = (v, r)
        return best

    out = {}
    for hyp in ("B1", "B2"):
        sel = (lambda r, h=hyp: r["hypothesis"].startswith(h))
        out[hyp] = {
            "defector_with_hosts_one_operator": top(sel, ("defector_with_hosts", "ratio_one_operator")),
            "defector_with_hosts_members": top(sel, ("defector_with_hosts", "ratio_members")),
            "operator_alone": top(sel, ("operator_alone_at_the_ruin_line", "ratio")),
        }
    for hyp, d in out.items():
        print("==", hyp)
        for name, best in d.items():
            if best is None:
                print("  %-36s none" % name)
                continue
            v, r = best
            print("  %-36s %8.3g   at %s, %s, m=%s, s=%s, %s noise (sigma_s %s), drift %s, k %s" % (
                name, v, r["network"], r.get("defectors", r.get("share")), r["m"], r["s"], r["noise"], r["sigma_s"],
                r["drift"], r["k"]))
    if A.json:
        json.dump({"rows": rows, "largest": {h: {k: (v[0] if v else None) for k, v in d.items()}
                                              for h, d in out.items()}},
                  open(A.json, "w", encoding="utf-8"), indent=1, default=float)


if __name__ == "__main__":
    main()
