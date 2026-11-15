# world/reference · the reference implementation

The world, in Python, from its specification alone: `world/spec/`. It passes every line of `world/test-values.json`, in the workflow `world check`, on every change under `world/`.

Terms: Zero-Clause BSD (LICENSE-0BSD).

## The files

| File | What it does |
|---|---|
| engine.py | The one engine: the page's charger, Paper D's charger, AP02's network, and the lone operator that B3 needs. Every seed of a cell runs together, as arrays. |
| formulas.py | AP02's results at their own formulas: Theorems I.1, II.1, III.1, IV.1 and VI.1. |
| check.py | Runs every line of the test values, and checks of its own: AP02's steady states, and the specification's Part Nine on cases small enough to work out by hand. Exit code 1 if any line fails. |
| run_cell.py | Runs one cell for its seeds, 4,000 rounds, and writes its packet, its summary with Part Nine's measure, and its log. |
| ../compare_engines.py | B1's section 9: the two engines' summaries of one cell, compared, with the rerun a disagreement needs. |
| cells/ | Cell files. Only the dry run's, until a hypothesis is frozen. |

## Running it

```
python -m pip install "numpy>=2.1,<3"
python world/reference/check.py
python world/reference/run_cell.py world/reference/cells/dry-run-network-m5.json --seeds 0-99 --out OUT
```

## How a run is measured

The specification's Part Nine, settled on 13 November 2026, closed every place where the text had left a choice; its draft 5 added points 14 to 18, where the two engines had read the text apart, and they now read it the same. This code follows it:

- An operator alone is a configuration of one, of any type. Its clock starts when it is left alone, if its own net change is a loss.
- The span, two ways. Where the configuration loses as a whole, its stock above the ruin line over its net loss. Where it gains as a whole, its counterparties' stock above the ruin line over their net loss through their links to the operator. Both are taken at their smallest along the way; both are reported, with `span_used`. Point 14: where the whole loses at some samples and gains at others, the span is the longest of those that applied, the whole's taken where the whole lost and the counterparties' where it gained.
- The net loss is the members' rate of change, from that seed's own state, without the stock's noise, sampled at every round's start and end and at the configuration's end; the smallest above zero sets the span.
- Point 19, as AG Fable proposed it on 13 November 2026: a watched configuration still standing at the end of the run, whose counterparties' records on their links to the operator, added together over the last w rounds, are below zero, takes the counterparties' span of point 2. A configuration that lasts settles, its whole's loss touches zero, and by points 3 and 14 alone its span would run past any run. Their net loss is taken at every sample here (point 3), so the span exists where the whole lost at every sample too. Each configuration's record says where the point applied (`point_19`), keeps point 14's span beside it (`span_by_point_14`), and gives the records it was judged on (`counterparties_records_last_w_rounds`). An operator alone has no counterparty, and the point does not apply to it.
- Every cell runs 4,000 rounds. A watched configuration whose bound ends inside the run is judged; one still standing at the end whose bound has passed counts at the run's length; one still standing whose bound has not yet come is "too long to judge in this run", and its seed is left out of the mean whole. If more than one seed in ten is left out, the cell settles nothing.
- Survival is measured less the record window where at least one counterparty is type C (version 1.0), and nothing is subtracted elsewhere.
- B1's premise check, seed by seed: every host type C, drift irreversible, and each defector coupled, starting with at least one live link. A defector that starts with no live link draws on no one: it is reported, and not watched. A seed left with nothing to watch is left out of the mean, counted and reported, and it counts towards the one in ten (B1, draft 3, section 7).
- No link joins two defectors: nothing passes between them, since neither gives. Where the ring or the random drawing would join two defectors, that link is left out, after the drawing, so every seed's random numbers are drawn as before. Each seed's packet line names the links left out, and the summary counts them. A hopper's offer to another defector makes no link either.
- A seed's measure is the largest survival in spans among the configurations a hypothesis watches; the judgement takes their mean and standard error across the seeds.
- A review on a declining reading uses the link's last w rounds, or all of them if it has fewer.
- A link's record includes the passive flow received or paid through it.
- Entry: a newcomer enters after the round's cuts, every q rounds from round q, of the type the cell names (type C by default), and takes its first reading the round after. Every type C operator, newcomers included, refuses a link to any operator whose counterparties' records on their links to it, added together over its whole record, are below zero. With `"hopper": true`, a defector left with no live links offers a link to one operator, chosen with the seed, every q rounds.
- Capacity: an operator accepts a new link only while its capacity still covers the default give on every link, the new one included. A defector gives nothing, so capacity never binds it. Links drawn at the start stand as drawn.
- The log, by default: every event for every seed, and the round lines for the first five seeds.
- The random numbers: numpy's PCG64, one generator per seed, `default_rng(seed)`. First the random links, the defectors' places and the uneven drift; then, each round, the reading noise, an entry's choices (the newcomer's, then each hopper's) and the stock noise.
- B3's lone operator starts at 50, with a ruin line at 10, drift 0.1, and a price of effort λ = 1, counted and reported, never taken from the stock. Its panic policy is on below its lower line and off above its upper line, 10 higher. The network's u_max does not apply to it.
- Points 15 to 18 (draft 5): an operator left alone has its clock tested once, when it is left alone, by its own net change then; a configuration's end is sampled at the state just before the cut, the new link or the ruin that ends it; capacity is measured against the setting's give g; a newcomer's type comes from the cell, type C in an entry cell and type U in its control.
