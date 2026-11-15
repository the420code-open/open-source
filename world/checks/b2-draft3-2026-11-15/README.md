# B2 · version 1.1, draft 3, built · the checks, and B1's cells again · dry, never a result

The specification's version 1.1, draft 3 (15 November 2026), on the branch `wc/b2-points-20-22`. Nothing here is a
result, and B1's record stands as run.

## What draft 3 changed, and what the engines now do

- **Points 19 and 22 only shorten a span.** Where a configuration's counterparties' records over the last w rounds
  are below zero at its end, the counterparties' span, with their net loss taken at every sample, is taken only
  where it is the shorter. Where it is not, the span of points 2, 3 and 14 stands, and the packet says so
  (`point_19_not_applied` or `point_22_not_applied`), with the counterparties' span beside it
  (`span_counterparties_every_sample`).
- **Point 21:** neither engine's working changed. Both already turned a configuration at the start of the first
  round whose close finds the records at zero or above, and counted the sample at that moment in its span. The words
  every packet carries now say so.
- **B2's section 10, two counts, as AG Opus answered on 15 November 2026:**
  - "Lasted more than one span and then ended" counts survival as B2 measures it, less the record window where at
    least one counterparty is of type C. Before, the window was not taken off.
  - "How many configurations one round's record alone would have watched" was already counted with the
    counterparties' one-round records added together, in both engines, and is unchanged. `count_one_round.py`
    counts it again from the kept records alone, on D1 and its control: `count-one-round.json`.

## The checks

- `checks-reference.txt` (and `.json`): the reference, 88 lines, 0 failed.
- `checks-second.txt`: the second engine, 80 of 80.
- The test values, S1 among them, and the two hand checks of point 2 read the measure's own span again, as at
  version 1.0, and pass. The line that showed point 22's 25 hours beside S1 is gone.
- A new line in each, `B2.P19-22`, fails if point 19 or point 22 ever lengthens a span.
- `mutate_check.py`, `mutations-*.json`: each line for points 20 to 22 made to fail once, on purpose, in a copy of
  the engine, the engine itself never changed.

## B1's cells again

All 240 runs, by B1's own runner and judge, on the engines at fa05337. The 104 cells that could fire, and the second
engine's 32, give B1's zone, B1's judgement and B1's measure, seed by seed. The controls moved only upward, and judge
as under draft 2. `compare_b1.py` sets B1's record, draft 2 and draft 3 side by side. `b1-rerun/` holds the
comparison, the judgement, the fingerprints, and every control's figures in its README.
