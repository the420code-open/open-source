# B2 draft 4 · the two figures and the made sink · 15 November 2026 · dry, never a result

For AG Opus, from WC: B2 draft 4's note, Part One, 1, 2 and 4. Every cell here is outside every grid. Nothing here is a
result, nothing is published, and no figure here is support for or against any hypothesis.

## 1. D4 and X3, judged again from their packets

`judge_controls.py` reads the third dry run's packets (`world/checks/b2-dry-run-3-2026-11-15`, kept on WC's computer at
`…\b2-dry3\runs`), with no new run. Each seed's measure is worked out from the packet alone, and
agrees with the runner's own summary, seed by seed. As B2 draft 4's section 6 says, every seed left out as too long to
judge counts as zero, and so would a seed with nothing to watch (there were none). `controls-judged-again.json`:

| Control | Engine | Seeds measured | Mean over them | Mean, every seed left out as zero (SE) | Less two SE | Judgement |
|---|---|---|---|---|---|---|
| D4 | reference | 75 | 167.13 | 125.35 (8.93) | 107.48 | a configuration lasts |
| D4 | second | 74 | 199.38 | 147.54 (13.53) | 120.49 | a configuration lasts |
| X3 | reference | 71 | 136.09 | 96.62 (7.53) | 81.56 | a configuration lasts |
| X3 | second | 64 | 158.25 | 101.28 (9.75) | 81.78 | a configuration lasts |

## 2. D1 itself, on a thousand fresh seeds in each engine

`run_d1_1000.py`: both engines at fa05337, D1 byte for byte as in the dry runs (`cells/D1.json`), 4,000 rounds,
through the probes of `world/checks/engines-part-2026-11-15`, copied here byte for byte (`probes/`). The seeds: the
next thousand unused in each engine from 1,000,000 up, 1,000,000 to 1,000,999 in each
(`seeds-from-1000000-before-the-run.txt`). Each engine draws its own random numbers from a seed, so the same seed
number gives a different network in each. All 20 parts finished. `analyse_d1.py`, with `count.py` and `drawn.py`
copied byte for byte from the engines-part check: `d1-1000-seeds.json`.

| | Reference | Second | Apart, in combined SEs |
|---|---|---|---|
| B2's measure, the mean of the per-seed largest (SE) | 0.3597 (0.0023) | 0.3578 (0.0022) | −0.59 |
| B1's measure beside it (SE) | 0.2988 (0.0018) | 0.3039 (0.0017) | 2.07 |
| Operators left alone, a seed (SE) | 6.285 (0.037) | 6.268 (0.036) | −0.33 |
| … by a counterparty's cut, every one a defector | 4.828 | 4.837 | |
| … by its own cuts, every one a careful giver | 1.096 | 1.068 | |
| … with no link as drawn, none drawn at all | 0.266 | 0.276 | |
| … with no link as drawn, drawn only to defectors, left out | 0.095 | 0.086 | |
| … by a mix of its own cut and a counterparty's | 0 | 0.001 | |
| Operators with no link at round 0, the law of the draw 0.392 (SE) | 0.361 (0.020) | 0.362 (0.020) | |
| Careful givers whose every link is to a defector, the law 0.444 (SE) | 0.465 (0.022) | 0.450 (0.022) | |
| Type C operators left alone, in all | 1,289 | 1,274 | |
| Defectors' configurations: a cut / its own ruin, alone / standing at the end | 8,319 / 4,996 / 4 | 8,076 / 4,994 / 6 | |

- **No seed was left out,** in either engine, and every seed had something to watch.
- **What the gap moves in B2's measure,** worked out as before: the gap in operators left alone is −0.017 a seed, with
  a standard error of 0.052, and B2's measure is −0.0019 apart, with a standard error of 0.0032.

## 3. The made sink, in each engine's checks

`B2.SINK`, in `world/reference/check.py` and `world/browser/check.mjs`: a ring of three type U operators, m = 3,
passive flow 0.5, no noise; A and B with drift 0.02, C with drift 0.5, each started at its steady stock, 32, 32 and
24.32. A's and B's records on their links to C, added together, are −3.2 a round. C's configuration is a sink's,
watched from round 0; no one cuts; its span is the counterparties', 13.75 rounds; at t = 4,000 it has lasted 290.9
spans, judged, in both engines. Made to fail once, on purpose, in a copy of each engine where a sink's clock never
starts: `mutate_check.py`, `mutations-*.json`.

The checks now: the reference 89 lines, 0 failed; the second engine 81 of 81 (`checks-*.txt`). In the reference's
check, the pair drawing together now fails, rather than stops the check, where no clock starts.

## The files

`runs-d1/`: every part's summary and console, and the run's log. `manifest-d1.sha256`: the fingerprints of every file
of the D1 run, the packets, logs and probes too. Those, 110 MB, are kept on WC's computer at
`…\b2-d4\runs-d1`.
