# B2's dry run, a third time, under version 1.1, draft 3 · 15 November 2026 · dry, never a result

For AG Opus, from WC. Every cell is outside every grid. Nothing here is a result, nothing is published, and no figure
here is support for or against any hypothesis. A control cell prints "a configuration lasts" or "no configuration
lasts", never "fires" or "holds", and fires nothing.

**The engines:** both from the branch `wc/b2-points-20-22` at commit fa05337: the reference, and the second engine
with its uneven drift, each with Part Nine's points 20 to 22 as version 1.1, draft 3 words them. Points 19 and 22 now
only shorten a span. Each runner was run unchanged, through the probes of `world/checks/engines-part-2026-11-15`,
copied here byte for byte under `probes/`.

**The seeds and cells:** the second dry run's, byte for byte (`cells/`): the reference 2,000,000 to 2,000,099, the
second engine 2,100,000 to 2,100,099, 4,000 rounds; D1, D2, D4, X1, D5, X3 and D6. All 14 runs finished, seven at a
time, beside B1's 240 runs again, so the wall clocks are shared and long.

## What moved from the second dry run, and why

`moved.py` sets every figure of `tables.json` beside the second dry run's, cell by cell and engine by engine:
`moved.json`. Every seed's measure was compared too, B1's and B2's.

- **No measure moved,** in any cell, on either engine, seed by seed: B2's and B1's beside it. So section 8's table
  and section 4's table stand as in the second dry run, figure for figure.
- **Point 22 applied far less often.** In the second dry run it took the counterparties' span at every end below
  zero. In most of them that span was the longer, and now it is left:

  | | D1 | D2 | X1 | D6 | D4 | D5 | X3 |
  |---|---|---|---|---|---|---|---|
  | Point 22 applied, draft 2 | 794 / 791 | 483 / 490 | 850 / 828 | 477 / 483 | 29 / 36 | 439 / 502 | 26 / 38 |
  | Point 22 applied, draft 3 | 51 / 59 | 189 / 212 | 175 / 228 | 118 / 99 | 6 / 7 | 164 / 199 | 14 / 28 |
  | Left, the longer | 743 / 732 | 294 / 278 | 675 / 600 | 359 / 384 | 23 / 29 | 275 / 303 | 12 / 10 |
  | Point 19 applied, draft 2 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 343 / 364 | 453 / 428 | 361 / 385 |
  | Point 19 applied, draft 3 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 335 / 352 | 453 / 428 | 353 / 376 |
  | Left, the longer | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 8 / 12 | 0 / 0 | 8 / 9 |

  Each figure is reference / second engine. Points 14 and 21 are unchanged.
- **Why no measure moved:** a span left as points 2, 3 and 14 give it is shorter than the one point 19 or 22 gave in
  draft 2. So that configuration's survival in spans went up, but in no seed did it become the seed's largest. And no
  bound moved past a run's end: no seed left out came in, and none went out.
- **"Lasted more than one span and then ended", counted again:** survival as B2 measures it, less the record window
  where at least one counterparty is of type C.

  | | D1 | D2 | X1 | D6 | D4 | D5 | X3 |
  |---|---|---|---|---|---|---|---|
  | Draft 2's count | 0 / 0 | 0 / 0 | 0 / 0 | 5 / 4 | 0 / 1 | 64 / 72 | 1 / 9 |
  | Draft 3, counted again | 0 / 0 | 0 / 0 | 0 / 0 | 5 / 4 | 0 / 1 | 65 / 72 | 1 / 9 |

  - Taking the window off moved no count. In the cells with type C hosts, no configuration that ended had lasted
    between one span and one span plus the window.
  - The one count that moved, D5 on the reference, moved by the limit. Seed 2,000,000, configuration 6, a defector's,
    ended at a host's ruin after 47.13 rounds. In draft 2, point 22 gave it the counterparties' span, 54.68, so 0.86
    spans. Now its span is the longer of points 2 and 14's, 27.71, so 1.70 spans.
- **"How many configurations one round's record alone would have watched":** unchanged. Both engines already counted
  it with the counterparties' one-round records added together. The figures are 810 / 792 in D1, 483 / 490 in D2,
  852 / 831 in X1, 477 / 483 in D6, 512 / 522 in D4, 892 / 930 in D5 and 511 / 525 in X3. See
  `world/checks/b2-draft3-2026-11-15/count-one-round.json` for the count again from the kept records.
- **Every other count of section 10 is unchanged:** outside the premises, returns below zero again, cuts of one type
  C operator by another, defectors standing, falls in no watched configuration, watched sinks.

## Section 8's table, as in the second dry run

| Dry cell | Engine | Watched a seed | Mean of the per-seed largest | SE | Largest seed | Seeds left out | Drawn: no link / hosts tied only to defectors, a seed |
|---|---|---|---|---|---|---|---|
| D1, random links | reference | 13.91 | 0.3357 | 0.0069 | 0.5222 | 0 | 0.25 / 0.36 |
| | second | 14.31 | 0.3633 | 0.0076 | 0.5981 | 0 | 0.42 / 0.49 |
| D2, the ring | reference | 10.62 | 0.3790 | 0.0081 | 0.6791 | 0 | 0.25 / 0.79 |
| | second | 10.65 | 0.3731 | 0.0081 | 0.6715 | 0 | 0.20 / 0.75 |
| X1, random links, m = 3.5 | reference | 14.01 | 0.3753 | 0.0068 | 0.6666 | 0 | 0.25 / 0.36 |
| | second | 14.13 | 0.3755 | 0.0055 | 0.5588 | 0 | 0.42 / 0.49 |
| D6, the ring, near the line | reference | 11.37 | 0.6134 | 0.0249 | 2.2492 | 0 | 0.25 / 0.79 |
| | second | 11.40 | 0.5971 | 0.0172 | 1.2029 | 0 | 0.20 / 0.75 |
| D4, D1's control | reference | 5.42 | 167.13, over 75 seeds | 6.92 | 351.00 | 25 | 0.25 / 0.36 |
| | second | 5.66 | 199.38, over 74 seeds | 13.92 | 974.10 | 26 | 0.42 / 0.49 |
| D5, D4 with passive flow off | reference | 9.52 | 247.75 | 18.42 | 1,215.81 | 0 | 0.25 / 0.36 |
| | second | 10.30 | 270.64 | 38.48 | 3,699.97 | 0 | 0.42 / 0.49 |
| X3, X1's control | reference | 5.40 | 136.09, over 71 seeds | 6.02 | 276.42 | 29 | 0.25 / 0.36 |
| | second | 5.73 | 158.25, over 64 seeds | 9.50 | 525.34 | 36 | 0.42 / 0.49 |

The engines apart, in combined standard errors (second less reference): D1 2.69; D2 −0.51; X1 0.02; D6 −0.54;
D5 0.54; D4 2.08 and X3 1.97 over the seeds each measured. All as in the second dry run.

## The files

- `run_dry3.py`, the runner; `tables.py`, the tables; `moved.py`, the comparison with the second dry run.
- `tables.json`, `moved.json`; `runs/`, each run's summary and console, and `runs/run.log`.
- `manifest.sha256`: the fingerprints of every file of the run, the packets, logs and probes too. Those, 82 MB, are
  kept on WC's computer at `…\b2-dry3\runs`.
