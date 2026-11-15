# world/browser · the browser world

The world, in JavaScript, for the page at /open-source/the-world/. It was written from the specification alone (`world/spec/`), as a second reading of the same text, not as a port of the reference. That is why it must agree with the reference.

It passes every line of `world/test-values.json` under Node, in the workflow `world check`:

```
cd world/browser
node check.mjs
```

Terms: Zero-Clause BSD (LICENSE-0BSD).

| File | What it does |
|---|---|
| engine.mjs | The engine, with no dependencies. It runs in a browser and under Node. |
| check.mjs | Runs every line of the test values, then the engine's own checks of Part Nine. Exit code 1 if any line fails. |
| run_cell.mjs | Runs one of the reference's cell files under Node, with this engine's own seeds and random numbers, and writes a packet and a summary with B1's measure, for the comparison of section 9. |
| index.html, world.js, world.css | The page: the world on a ring, the sliders, the page's charger with its two lifetimes crossing at 8, and each configuration's clock with its bound. |

The page sends nothing anywhere. Its settings go into the address after a hash, and nothing else does. The plain words under the world are still to be written.

## Part Nine: how a run is measured

Draft 4 of the specification adds Part Nine. The engine reads it from the text, as it read the rest, not from the reference.

- **An operator alone** is a configuration of one, of any type. Its clock starts when it is left alone, if its own net change then is a loss. If it is not, no clock starts for it.
- **The net loss** is the members' rate of change, from the run's own state, without the stock's noise. It is sampled at every round's start (after the round's cuts), at every round's end, and at the configuration's end (as it last stood, before the cut, link or ruin that ended it). The smallest above zero sets the span, with no floor: a loss counts however small, as the text says and the reference reads it.
- **The span, two ways.** Where the whole lost at any sample while its clock ran, the span is the whole's stock above the ruin line over its net loss: the page's 200 over 18. Otherwise the whole gains, and the span is the counterparties' stock above the ruin line over their net loss through their links to the operator. Each configuration reports both, and `span_used`: `whole` or `counterparties`.
- **Survival** is reported in full (`survival_spans`) and less the record window (`survival_less_window`), which subtracts the window only where at least one counterparty is type C, and is never below zero.
- **The run's length** is 4,000 rounds: `run()` goes to `horizon`. A configuration still standing whose bound has not come reports `judged: false`, too long to judge in this run; `report().too_long_to_judge` counts them. The page keeps its own 200 rounds.
- **Entry** (`open: { q, n, type, hopper }`): a newcomer, type C unless set, enters every q rounds from round q, after the cuts. Every type C refuses a link to an operator whose counterparties' records on their links to it, over its whole record, are below zero. With `hopper` (on unless set false), a defector with no live link offers one link, every q rounds, to one operator chosen with the seed.
- **Capacity** binds on a new link: an operator that gives accepts only while u_max covers the default give on every link, the new one included. A defector's never binds. Links drawn at the start stand as drawn.
- **The lone operator of B3** (point 13) is not in this engine. It has no lone setting with an effort policy.
- **Uneven drift** (point 12): a cell's `"drift": {"uneven": [lo, hi]}` (`drift_uneven` in the engine) gives each operator the world starts with its own drift a, uniform on [lo, hi], drawn with the seed from its own stream, after the links and the defectors' places and before anything in a round, so that it moves no other draw. A newcomer keeps the setting's a: the text draws the uneven drift first, and no drift in a round. Each seed's drifts are in its packet line.

**Point 19** (AG Fable's, 13 November 2026): a configuration still standing at the end, whose counterparties' records on their links to the operator, added together over the last w rounds, are below zero, takes the counterparties' span of point 2, their net loss taken at every sample. Its summary says where the point applied (`point_19`), with point 14's span beside it (`span_by_point_14`) and the records (`counterparties_records_last_w_rounds`). An operator alone has no counterparty, and the point does not apply.

No link joins two defectors: a drawn link that would join two is left out after its draw (`links_between_two_defectors_left_out`), and a hopper's offer to another defector makes no link. Its checks, P9.1 to P9.10, P9.12, B1.7, LINKS and P19 in `check.mjs`, are cases worked by hand from the text. B1.7 is B1's premise check: a defector that starts with no live link is reported (`defectors_with_no_live_link_at_start`), and not watched (`watched_b1`). None depends on the random draw: two engines never share one (Part Seven).
