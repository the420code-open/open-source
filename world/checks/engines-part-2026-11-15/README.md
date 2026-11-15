# Where the two engines part · 14 to 15 November 2026 · dry, never a result

For B2, before it is frozen (AG Opus, through G: the night rulings, Part Four, and B2's draft 2, Part Three). Every
cell here is a dry cell, outside every grid, or a check on one of B1's cells with fresh dry seeds. Nothing here is a
result, nothing is published, and no figure here is support for or against any hypothesis.

## The engines

Both are at the tag `world-ref-v1.0` (commit 6782c5f), the code B1 ran (`…\b1-run\code`), unchanged.
No engine, tag or branch was changed. The uneven-drift branch was not used.

**The second engine at the tag has no uneven drift, and refuses D1** (`run_cell.mjs`: "uneven drift is not yet in this
runner"). So the two engines meet on **D1e**, D1 with its drift even (a = 0.1), the B2 dry run's own extra cell. The
reference also runs D1 on the same seeds as its D1e, so what uneven drift moves there is seen beside it.

## The probes, and that they change nothing

Neither engine's packet lists every configuration, only those whose clock started, and the second engine's packet
counts its cuts without saying who made them. So each engine's own runner is run unchanged, and its World is read
after its run:

- `probe_reference.py` runs `run_cell.py`'s own `main()`, with `engine.World` replaced by a subclass that only keeps
  hold of the instance; then reads `cfgs`, `cut_log`, `ruin_list` and `links_left_out`.
- `probe_second.mjs` runs `run_cell.mjs` as itself, with `World.prototype.run` wrapped to call the engine's own `run`
  and then only read `configs`, `links`, `cuts`, `ruins` and `linksLeftOut`.

**Checked:** five seeds of each cell, by the runner alone and then through the probe. The packets are the same byte
for byte, less the head line's date, and the summaries are the same, less the seconds (`results/checks.json`). The
reference's D1 and D1e on seeds 2,000,000 to 2,000,099 are, seed line by seed line, the B2 dry run's own packets: 100
of 100 each.

## What was run

| Set | Cell | Engine | Seeds |
|---|---|---|---|
| First | D1 | reference | 2,000,000 to 2,000,099 (the B2 dry run's) |
| First | D1e | reference | 2,000,000 to 2,000,099 |
| First | D1e | second | 2,100,000 to 2,100,099 (the B2 dry run's) |
| First | b1-random-3D-m3-s0-more | reference | 4,000,000 to 4,000,999 |
| First | b1-random-3D-m3-s0-more | second | 4,100,000 to 4,100,999 |
| The bound | D1 and D1e | reference | 5,000,000 to 5,000,999 |
| The bound | D1e | second | 5,100,000 to 5,100,999 |
| The drawing alone | D1e, built and not run | reference | 5,000,000 to 5,019,999 |
| The drawing alone | D1e, built and not run | second | 5,100,000 to 5,119,999 |

Seeds 4,000,000 to 4,000,004 and 4,100,000 to 4,100,004 were also used for the probe's check, and gave the same as in
the runs. **The seeds:** 601 packets on this computer, the dry branch's included, were read seed line by seed line:
none used a seed from 200,001 to 200,200 or 300,001 to 300,200, B2's own ranges.

## What came out

### D1e, the two engines, 100 seeds and then 1,000

| | Reference, 100 | Second, 100 | Reference, 1,000 | Second, 1,000 |
|---|---|---|---|---|
| Operators left alone, a seed (SE) | 5.900 (0.096) | 6.390 (0.125) | 6.277 (0.036) | 6.215 (0.036) |
| … by a counterparty's cut (all defectors) | 4.85 | 4.81 | 4.819 | 4.811 |
| … by its own cuts (all careful givers) | 0.80 | 1.16 | 1.051 | 1.022 |
| … with no link as drawn: none drawn | 0.15 | 0.26 | 0.300 | 0.264 |
| … with no link as drawn: only to defectors, left out | 0.10 | 0.16 | 0.107 | 0.117 |
| B2's measure (SE) | 0.2896 (0.0065) | 0.3063 (0.0068) | 0.3052 (0.0023) | 0.3044 (0.0023) |
| B1's measure (SE) | 0.2300 (0.0040) | 0.2336 (0.0041) | 0.2333 (0.0013) | 0.2351 (0.0013) |

- **At 100 seeds** the second engine had 0.49 more operators alone a seed, 3.1 combined SEs apart, and B2's measure
  1.78 apart.
- **At 1,000 fresh seeds** the gap is 0.062 the other way, 1.2 combined SEs apart, and B2's measure is 0.0009 apart,
  0.27 combined SEs.

### What the drawn networks alone give

Built and not run, 20,000 seeds in each engine, D1e (`results/drawing-D1e-20000-seeds-each-summary.json`):

| A seed | The drawing's own law | Reference | Second | Apart, SEs |
|---|---|---|---|---|
| Operators with no link | 0.3921 | 0.4007 (0.0046) | 0.3941 (0.0045) | −1.03 |
| Careful givers whose every link is to a defector | 0.4435 | 0.4432 (0.0049) | 0.4364 (0.0049) | −0.99 |
| Defectors with a link | 4.8241 | 4.8186 (0.0029) | 4.8216 (0.0029) | 0.75 |
| Links between two careful givers | 21.0000 | 20.9981 (0.0289) | 21.0331 (0.0289) | 0.86 |
| Links between a careful giver and a defector | 15.0000 | 14.9804 (0.0243) | 14.9744 (0.0245) | −0.17 |
| Links between two defectors, left out | 2.0000 | 2.0093 (0.0089) | 2.0136 (0.0089) | 0.34 |

Both engines draw by the same law, and each agrees with it. **The B2 dry run's 100 reference networks did not:**
0.25 operators with no link a seed, against the law's 0.39, about 3 SEs low; and 0.36 careful givers tied only to
defectors, against 0.44. The second engine's 100 were near the law (0.42 and 0.49).

### Every defector's configuration, by how it ended (1,000 seeds)

| | A cut | Its own ruin, alone | Standing at the end |
|---|---|---|---|
| Reference, D1 | 8,095 | 4,991 | 9 |
| Reference, D1e | 7,965 | 4,996 | 4 |
| Second, D1e | 7,821 | 4,996 | 4 |

### B1's random cell at m = 3, the heaviest noise, 1,000 seeds each

| | Mean | SE |
|---|---|---|
| Reference | 0.42253 | 0.00185 |
| Second | 0.42188 | 0.00182 |

The second engine's mean is lower by 0.0007, 0.25 combined SEs. At 100 seeds in B1 it was lower by 0.0106. The lean
does not hold over more networks.

## Where they part

**In D1's operators left alone, they do not part.** The 100-seed gap was in the 100 networks the reference drew, not
in what the engines do with a network: the careful givers left alone by their own cuts, and the operators drawn with
no link, are what the drawing gives, and at 1,000 fresh seeds every kind agrees within its chance. No text of the
specification is touched by it: both engines draw by the same rule, and agree with it over 20,000 networks each.

**What stays open.** D1 itself, with uneven drift, can only be put through both engines on the uneven-drift branch,
which this check did not use. In the reference, uneven drift moves B2's measure by 0.054 (16.5 combined SEs, D1 against
D1e on the same 1,000 seeds) and leaves the operators alone where they were (6.272 against 6.277). So the 2.69 SEs
first seen on D1, at 100 seeds, mixes the 100 networks drawn with whatever uneven drift does in each engine. That last
part can be checked once the branch's engine is in use.

## The files

- `cells/`: D1 and D1e (from the dry branch), and B1's cell.
- `probe_reference.py`, `probe_second.mjs`: the probes. `count.py`, `drawn.py`, `links.py`: the counts.
  `drawing_reference.py`, `drawing_second.mjs`: the drawing alone. `run_all.py`, `run_bound.py`: the runs.
  `pool.py`, `measure_b2.py`: the pooled figures; `measure_b2.py` imports the B2 dry run's own `second_engine.py`.
- `results/`: every figure above, as the scripts wrote it.
- `summaries/`: every part's summary and console output, and each set's run log.
- `manifest.sha256`: the SHA-256 of every file the runs wrote (304), the packets, logs and probes among them. They
  stay on WC's computer, at `…\engines-part` (346 MB).

Terms: CC0 1.0 Universal.
