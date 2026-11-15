# One dry cell before B2: the two engines, a thousand seeds each · 14 November 2026

**Never a result.** This cell is outside every hypothesis's grid, and nothing in it is a finding about the world. It was
asked for by AG Opus, through G, on 14 November 2026: in B1, the second engine's mean was the lower one in 25 of the 30
cells judged by the three-errors rule, by up to 4 parts in 100, and no cell was outside the rule. In B2 a verdict could
turn on less. So one cell, outside every grid, under the heaviest noise, a thousand seeds in each engine.

## The cell

`dry-b2-random-3D-m5-s0-more.json`: random links, p = 0.2 among 20, three defectors, s = 0.0, every host a careful
giver (type C), 4,000 rounds.

- **Outside every grid:** m = 5. B1's grid has m = 3 only.
- **The heaviest noise:** B1's heaviest, "more": stock noise 1, reading noise 1. This is WC's reading of "the heaviest
  noise", stated here as the choice. The earlier dry runs of Phase 0 used a stock noise of 2.0, which is outside B1's grid.
- **The code:** the world at the tag `world-ref-v1.0` (commit 6782c5f), the same files B1 ran on, unchanged. The four
  files' SHA-256 match the tag's: `engine.py` 11993a06…, `run_cell.py` 9c68c5b5…, `engine.mjs` 21853739…,
  `run_cell.mjs` a61a3b81….
- **The seeds:** the reference engine 3,000,000 to 3,000,999; the second engine 3,100,000 to 3,100,999. The two engines
  never share random numbers (Part Seven). Each ran in ten parts of 100 seeds, eleven parts at a time (`run_dry.py`), and
  every seed's value was pooled (`pool.py`). Every part finished; the whole took 535 seconds.
- **The measure:** B1's, as each engine's summary gives it: for each seed, the largest survival in spans, less the record
  window where at least one counterparty is type C, among the configurations a defector is in; then the mean across the
  seeds, and its standard error, the sample standard deviation over the square root of n, as both engines compute it.

## What came out

| | Seeds | Left out | Configurations | Mean | Standard error | Standard deviation |
|---|---|---|---|---|---|---|
| Reference engine | 1,000 | 0 | 7,910 | 0.32648 | 0.00192 | 0.0608 |
| Second engine | 1,000 | 0 | 7,850 | 0.32560 | 0.00180 | 0.0571 |

- **The second engine's mean is the lower, by 0.00087:** 0.27 parts in 100 of the reference's mean.
- **In standard errors:** the combined standard error is 0.00264, the square root of the sum of the two squared, so the
  two means are **0.33 standard errors apart.**
- **Each engine's own:** both means are far below the line at 3, the reference engine's by 1,390 of its standard errors
  and the second engine's by 1,482 of its own. Every part of 100 seeds, in both engines, was in the zone "holds". That
  is the zone of a cell outside every grid, and is not a result.

## The files

- `pooled.json`: the figures above, as `pool.py` printed them.
- `reference/seeds-*/` and `second/seeds-*/`: each part's `summary.json`, with every seed's value, and its console output.
- `manifest.sha256`: the SHA-256 of every file the run wrote, the packets and the reference engine's event logs among
  them (95 MB in all). Those stay on WC's computer, at `…\dry-b2`, and are kept.
- `run.log`: the order the parts finished in.

Terms: CC0 1.0 Universal.
