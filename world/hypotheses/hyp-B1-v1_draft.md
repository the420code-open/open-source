# B1 · The defector does not last · the frozen hypothesis, hyp-B1-v1

**From AG Opus, for AG Fable, WC and G · 13 November 2026**

**Draft, for AG Fable's reading.** It is frozen on the day it is tagged hyp-B1-v1, and never edited afterwards. A correction is a dated supersession, in the open, and the old version stays.


## 1. What it tests

**The work's sentence.** One Awareness: "Cruelty does not last. Not as a hope. As geometry."

**The theorem under it.** AP02 The Operator, Theorem VI.2: net-negative configurations, pure defection among them, "each reach the no-return surface in finite time, on the order of budget ÷ (drain − surplus) steps."

**The switches.** KS-BAR.9 and KS-COUP.1, as the Master Kill Switch Registry, version 5.40, bounds them: their dated notes of 11 November 2026, with the dated addition of 13 November 2026.

**What a run reaches.** The theorem's conclusion, in a world that meets its premises. It can fire a switch written about the theorem. It cannot, on its own, fire a claim about real people. G checked the match of this hypothesis to its sentence on 13 November 2026.


## 2. The claim, made operational

In a world that meets Theorem VI.2's premises, a sustained defector is ruined within the bound of every configuration it passes through.


## 3. The world

- **The specification:** the world's specification, version 1.0, tagged world-spec-v1.0. Every rule, every default and every reading of Part Nine is as it gives them.
- **The reference engine:** the commit tagged world-ref-v1.0, which passes every test value and every case of Part Nine.
- **The second engine:** the browser engine at the same tag, written from the specification's text alone.
- **The setting:** the network setting. Every operator is of type C, except the defectors. Type C reads its own gradient, conditions each link on its counterparty's record, and cuts. Those are the theorem's three premises.


## 4. The grid

**The main grid,** closed to entry. 96 cells:

| Dimension | Values |
|---|---|
| Network | A ring of 20; random links with p = 0.2 among 20 |
| Defectors | One, at a position chosen by the seed; and three |
| Delivery multiple m | 2, 3, 4 |
| Own input s | 0; and 0.5, below the drain at the ruin line |
| Noise | The four conditions below |

| Condition | Noise in the stock σ_s | Noise in the reading σ_r |
|---|---|---|
| Quiet | 0 | 0 |
| Some | 0.5 | 1 |
| More | 1 | 1 |
| Reading only | 0 | 2 |

**The entry grid.** 8 cells: the ring, one defector, m = 3, both values of s, all four noise conditions, open to entry. A new type C operator enters every 10 rounds, offering 2 links.

**The hopper.** In the entry grid, a defector left with no live links offers a link to one operator, chosen with the seed, every 10 rounds. Every type C operator refuses it by the record. Records are exact, so the refusal is certain. It shows the premise at work, and is labelled so, never as a result.

**The two controls,** outside the premises, which fire nothing:

- **The main grid's control:** the same 96 cells, with every host of type U, cooperators who never cut. AP02's corollary says such a network "is invadable by a defector". The control shows that the world can show a defector lasting.
- **The entry grid's control:** the same 8 cells, with every operator but the defector of type U, newcomers included. It shows a hopper succeeding.

**In all:** 208 cells, of which 104 can fire and 104 are controls.


## 5. Seeds and run length

- **Every cell:** seeds 1 to 100. Where a cell settles nothing, seeds 101 to 200 are added, once.
- **The second engine:** seeds 100,001 to 100,100.
- **Never used for B1:** every seed from 1,000,000 up. The dry runs and the drawing of network shapes used those.
- **Every cell runs 4,000 rounds,** fixed before any run, as G approved on 13 November 2026.
- **Every seed of a cell runs in full** before anything in that cell is judged.


## 6. What is watched, and how it is measured

**What is watched:** every configuration a defector is in, from its own clock's start.

- **A configuration** is an operator and its direct counterparties, joined to it by live links. Every cut and every new link starts a new one. An operator left alone is a configuration of one.
- **Its clock starts** when the operator's own links, taken together, turn net-negative for its counterparties, by their records.
- **Its span** is its stock above the ruin line over its net loss per round, taken at the smallest loss along the way. Where the whole configuration gains, the span is taken over its counterparties alone: their stock above the ruin line, over their net loss through their links to the operator. Where the whole loses at some samples and gains at others, the longest span that applied is used. Every packet carries both spans.
- **Its bound** is three spans, plus the record window where its counterparties are of type C.
- **Its survival** is measured in spans, less the record window where the counterparties are of type C.

**The measure, for each seed:** the largest survival in spans among the configurations it watches. KS-BAR.9's note counts a defector's viability as preserved if it is still standing when the configuration it is in has passed its bound, in any configuration it passes through. So a seed's worst configuration is its measure.

**A configuration still standing at the end:**

- **If its bound has already passed,** it counts at the run's length. That leans towards a fire, never away from one.
- **If its bound has not yet come,** it is "too long to judge in this run". A seed with any such configuration is left out of the mean whole, counted and reported.
- **If more than one seed in ten is left out,** the cell settles nothing, and says why.

**A configuration ended by its type C hosts' cut,** within the record window, scores no survival less the window. It can never be a seed's largest.


## 7. The judgement, cell by cell

**First, the premise check.** Every host is of type C, with the three premises. The network is coupled. Drift is irreversible. A cell that fails the check fires nothing.

**Then, on the mean of the measure across the seeds:**

| What the seeds show | What it means |
|---|---|
| The mean survival, plus two standard errors, at or under three spans | B1 holds in this cell, and the switches hold |
| The mean survival, less two standard errors, over three spans | The switches fire in this cell, subject to section 10 |
| Between the two | Settles nothing. Seeds 101 to 200 are added, once. If it is still between, it is reported as settling nothing. |

**Each cell is judged on its own, and every cell is reported.** No cell is added after a result is seen.

**The m = 2 cells.** At m = 2 and s = 0, a cooperator left with one link settles below the ruin line, and falls. That is arithmetic, shown in the specification before any run. Such a cooperator is not in a defector's configuration. Its fall is reported, and fires nothing.


## 8. The largest of many, measured before freezing

The measure takes the largest of a seed's configurations. Under noise, the largest of many runs higher than any one of them. So the margin was measured, not assumed.

- **The largest ratio of stock noise to net loss** in this grid, among configurations not ended by a cut within the window, is **2.0**: an operator left alone at the ruin line, with s = 0.5, under the stock noise of 1. It was worked out from the specification's formulas alone, with no cell of B1 run.
- **The dry run,** at that ratio, on cells outside every grid, at m = 5, 100 seeds each, 4,000 rounds, never a result:

| Dry cell | Watched configurations a seed | Mean of the per-seed largest, in spans | Standard error |
|---|---|---|---|
| The ring, one defector | 2 | 0.323 | 0.007 |
| Random links, three defectors | 8.3 | 0.513 | 0.039 |

With about eight configurations a seed to take the largest of, the mean plus two standard errors is 0.59. The line for a fire is at three.


## 9. Two engines

The second engine runs the 32 cells of the main grid at m = 3, with its own seeds.

- **In the two quiet cells of the ring with one defector,** nothing is random, and the two engines must agree to 0.000001.
- **In the other 30,** they agree when the difference of their means is within three of their combined standard errors. By chance alone, that is exceeded in about one cell in 370.
- **A cell where they disagree** is reported as "engines disagree". The cause is looked for in the open, and no cell of B1 is judged until it is found and recorded.


## 10. What a result does

- **B1 holds in a cell:** it is recorded, and the switches stand.
- **A cell fires:** Phase 0's rule, Part Four. It is shown at once as "reported, being checked". It is rerun from its packet, and checked against the premises. AG Fable reads it, and G decides it for the registry. A switch that fires stays fired.
- **A cell settles nothing:** it is reported, with why.

**Reported for every cell, whatever the judgement:** every watched configuration's survival in spans, as a number, and which span it used; the number of configurations each defector passed through; how many defectors were ruined; how many seeds were left out, and why; the premise check; in the entry cells, every hopper's offer and every refusal; and both controls' results in full.

**Every packet goes into the record,** labelled as the desks' own run. Group B is never mixed with Group A.


## 11. Freezing

On the day it is frozen:

1. The specification is tagged world-spec-v1.0, and the reference engine world-ref-v1.0.
2. This document is committed under the tag hyp-B1-v1, with the SHA-256 fingerprint of the file. It goes into the public store as soon as the store stands, under the same tag, unchanged.
3. It is deposited, with a DOI, on the open archive the work's own deposits use. That deposit is its public date.
4. Only then does any cell of B1 run.
