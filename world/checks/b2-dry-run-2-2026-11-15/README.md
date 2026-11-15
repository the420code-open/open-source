# B2's dry run, again, with points 20 to 22 · 15 November 2026 · dry, never a result

For AG Opus, from WC: B2's draft 2 note, Part Two. Every cell is outside every grid. Nothing here is a result, nothing
is published, and no figure here is support for or against any hypothesis. A control cell prints "a configuration
lasts" or "no configuration lasts", never "fires" or "holds", and fires nothing.

**The engines:** both from the branch `wc/b2-points-20-22` (commit 826af60): the reference, and the second engine with
its uneven drift, each with Part Nine's points 20 to 22 (version 1.1, draft 2) built from the text alone. Each runner
was run unchanged, through the probes of `world/checks/engines-part-2026-11-15`, which read each World after its run
for the drawn counts.

**The seeds:** the first dry run's, the reference 2,000,000 to 2,000,099 and the second engine 2,100,000 to 2,100,099.
4,000 rounds. All 14 runs finished; seven at a time, so the wall clocks are shared.

**The cells** (`cells/`): D1, D2, D4 and X1 as before; and new, as the note defines them: **D5**, D4 with passive flow
off; **X3**, X1 with every host of type U; **D6**, the ring of 20, five defectors, m = 3.5, s = 0, uneven drift from
0.06 to 0.27, passive flow off, the noise "more". At m = 3.5 a link brings each end 3.0525 a round, so an operator with
one link and a drift of 0.27 settles at 11.31, against the ruin line at 10.

## Section 8's table

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

**The two engines, apart, in combined standard errors** (second less reference), with the drawn counts beside each, as
AG Opus ruled: D1 2.69; D2 −0.51; X1 0.02; D6 −0.54; D5 0.54; D4 2.08 and X3 1.97 over the seeds each measured (both
settle nothing). The drawn counts in the random cells are the same networks in every random cell of an engine, since
each engine draws a seed's network first: the reference's 100 have 0.25 operators with no link a seed and 0.36 hosts
tied only to defectors; the second engine's 0.42 and 0.49. Over 20,000 networks each, both engines draw the same law,
0.39 and 0.44 (`world/checks/engines-part-2026-11-15`).

## Six figures, cell by cell

| | D1 | D2 | X1 | D6 | D4 | D5 | X3 |
|---|---|---|---|---|---|---|---|
| **1.** A defector's, a seed (ref / second) | 8.01 / 7.92 | 4.83 / 4.90 | 8.47 / 8.23 | 4.77 / 4.83 | 5.13 / 5.22 | 8.92 / 9.30 | 5.11 / 5.25 |
| a sink's | 0 / 0 | 0 / 0 | 0.03 / 0.06 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| an operator alone | 5.90 / 6.39 | 5.79 / 5.75 | 5.51 / 5.84 | 6.60 / 6.57 | 0.29 / 0.44 | 0.60 / 1.00 | 0.29 / 0.48 |
| ... of them type C (ref / second, in all) | 91 / 139 | 79 / 75 | 51 / 84 | 160 / 157 | | | |
| **2.** Mean of the per-seed largest | above | | | | | | |
| B1's measure beside it, for comparison (ref / second) | 0.2960 / 0.2998 | 0.3158 / 0.3172 | 0.3630 / 0.3580 | 0.4421 / 0.4521 | | | |
| **3.** Seeds left out, too long to judge | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 25 / 26 | 0 / 0 | 29 / 36 |
| ... the configurations that made them so | | | | | 28 / 29 a defector's | | 31 / 42 a defector's |
| **4.** Point 14 applied | 27 / 24 | 26 / 38 | 98 / 69 | 0 / 0 | 364 / 391 | 576 / 534 | 416 / 450 |
| Point 19 applied | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 343 / 364 | 453 / 428 | 361 / 385 |
| Point 21 applied | 7 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 141 / 122 | 0 / 0 | 124 / 102 |
| Point 22 applied | 794 / 791 | 483 / 490 | 850 / 828 | 477 / 483 | 29 / 36 | 439 / 502 | 26 / 38 |
| **5.** Lasted more than one span, then ended | 0 / 0 | 0 / 0 | 0 / 0 | 5 / 4 | 0 / 1 | 64 / 72 | 1 / 9 |
| **6.** Wall clock, seconds, seven runs at a time | 229 / 828 | 179 / 566 | 225 / 858 | 98 / 439 | 230 / 1,150 | 93 / 884 | 258 / 912 |

In the cells that can fire, point 22 moved no measure: D1's and D2's are the first dry run's, figure for figure. A
configuration its type C hosts cut within the window scores no survival less the window, whatever its span.

## Section 4's table: in each control cell, whether a configuration lasts, kind by kind

| Control | A defector's (ref / second) | A sink's |
|---|---|---|
| D4, passive flow on | **Settles nothing** in both: 25 and 26 seeds of 100 too long to judge, more than one in ten. Over the seeds measured, means of 167.1 and 199.4. | None watched, in either engine |
| D5, passive flow off | **A configuration lasts** in both: 247.8 (SE 18.4) and 270.6 (SE 38.5), all 100 seeds measured | None watched |
| X3, passive flow on, m = 3.5 | **Settles nothing** in both: 29 and 36 seeds too long to judge. Means of 136.1 and 158.2 over the seeds measured. | None watched |

D4's first dry run left 90 seeds out; under points 20 and 21, 25 and 26. No control watched a sink: X1 watched three
and six, and X3, its control on the same networks, none.

## Section 10's reports, in all (ref / second)

| | D1 | D2 | X1 | D6 | D4 | D5 | X3 |
|---|---|---|---|---|---|---|---|
| Outside the premises, left out of the measure | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Returned to zero or above, then below again | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 32 / 43 | 0 / 0 | 43 / 51 |
| Cuts of one type C operator by another | 104 / 118 | 0 / 0 | 22 / 38 | 0 / 0 | | | |
| Defectors standing at the end | 1 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 482 / 479 | 453 / 428 | 482 / 476 |
| Falls in no watched configuration | 0 / 0 | 0 / 0 | 0 / 0 | 333 / 341 | 25 / 34 | 427 / 470 | 26 / 39 |
| Watched sinks, with records less passive flow | 0 / 0 | 0 / 0 | 3 / 6 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Watched by the window (point 20) | 801 / 792 | 483 / 490 | 850 / 829 | 477 / 483 | 513 / 522 | 892 / 930 | 511 / 525 |
| ... by one round's record alone | 810 / 792 | 483 / 490 | 852 / 831 | 477 / 483 | 512 / 522 | 892 / 930 | 511 / 525 |

Every list is in full, seed by seed, in each run's packet, and its counts in each run's summary.

## The files

- `cells/`: the seven dry cells. `run_dry2.py`: the runs. `tables.py`: the tables, into `tables.json`.
- `runs/<engine>/<cell>/`: each run's summary and console output, and the order the runs finished in.
- `manifest.sha256`: the SHA-256 of every file the runs wrote (64), the packets, logs and probes among them. They stay on
  WC's computer, at `…\b2-dry2\runs` (82 MB).

Terms: CC0 1.0 Universal.
