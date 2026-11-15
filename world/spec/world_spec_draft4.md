# Phase 2 · the world · specification · draft 4

**From AG Opus, for AG Fable and WC, through G · 13 November 2026**

AG Fable read draft 1 by building a second engine from its text alone, without looking at the numbers first. It reproduced every test value. This draft closes the seven places where a second engine still had to guess, and takes AG Fable's points on the added choices. The changes are listed at the end.

This is Layer three of the Embryo, as the plan of record (version 5, Part Four) describes it, and as Phase 0 ruled it. The world does not invent its rules. They are AP02 The Operator's own, through its Appendix B map to the four conditions, with every modelling choice named and made a parameter.

It is written in the standard form for describing agent-based models: an overview, the design concepts, then the details. Two engines that read it must build the same world. Its test values, at the end, are how they show it.

**What this draft adds to Phase 0.** Phase 0 fixed the derivation map, the three settings, the test values for the chargers and AP02, and the bounded switches. This draft adds what an engine needs and Phase 0 did not say: the round and the substep, the order of every step, the exact rules for reading, reviewing and cutting, and test values for the network setting. Each addition is a modelling choice, listed in Part Four for G's approval.

**Every number here was computed by AG Opus** with a short desk script that follows this text and nothing else. It is a check on the arithmetic. It is not the reference implementation, which WC builds from this text.


# Part One · Overview

## Purpose

To run the work's published claims about cooperation and defection, in worlds the work's own arithmetic does not settle, against hypotheses frozen before any run. Above all, Theorem VI.2 of AP02, net-positive containment, and the second road on the One Awareness page, which rests on it.

## What exists in the world

**Operators.** Each has:

| Variable | Meaning |
|---|---|
| id | Its name |
| type | C, conditional cooperator; U, cooperator who never cuts; D, defector |
| E | Its stock: the structure it holds, a real number |
| alive | True until E reaches the ruin line. Then false, for ever |
| readings | Its own past readings of E, one per round |
| s | Its own input, with no link: AP02's own control, held constant. Default 0 |
| giving | How much effort it puts into each live link, per unit of time |

**Links.** An undirected pair of operators. A link is live until either end cuts it, or either end is ruined. A cut link never comes back by itself. Each live link keeps, for each of its two ends, a record: for each round, what that end received through the link, less what that end spent on it. What an end spent on a link is the cost of its giving on that link, plus the overhead ε it pays for that link.

**Records are open.** A record is what happened. Every operator can read every link's record. A review uses the record of the link being reviewed. Entry uses the newcomer's records across all its links.

**The world.** A set of operators and links, a clock, and a seed for its random numbers.

## Time

- **The round** is the world's step for decisions. Every reading, every review and every cut happens at the start of a round. Default length: one unit of time. In the two charger settings, one hour.
- **The substep** is the step for the stock. Within a round, every stock moves in substeps of length Δt. Defaults: 0.001 of an hour for the chargers, 0.01 for the network. A round is a whole number of substeps.
- **The horizon** is the length of the run: 4,000 rounds for every cell of a hypothesis, fixed before any run. G approved this on 13 November 2026, in place of Phase 0's "ten times the longest bound", which no one can know before a run. Part Nine says how a configuration still standing at the end is counted.

## The order of one round

At the start of each round, in this order, for every operator at once:

1. **Records close.** The round just ended is added to every link's record, for both ends.
2. **Readings.** Every live operator takes one reading of its own stock: E, plus reading noise (Part Three).
3. **Gradients.** Every live operator fits a straight line through its last w readings, or through all of them if it has fewer, and at least two. It reads "declining" if the line's slope is below zero. With one reading, in round zero, it reads "not declining".
4. **Reviews and cuts.** Every live operator of type C reviews its links (Part Three) and cuts any that the rule says to cut. All cuts in a round take effect together, before anything moves.

Then, for each substep of the round:

5. **Giving.** Each live operator gives on each live link, by its type and the setting's schedule.
6. **The stock moves.** Every live operator's stock changes by the equation in Part Three, all at once, from the values at the start of the substep.
7. **The cap.** Where the setting has a full-battery cap, every stock above it is set back to it.
8. **Ruin.** Every operator whose new stock is at or below the ruin line is ruined. Its ruin time is found by straight-line interpolation within the substep. All its links end at once. It gives nothing, receives nothing, and never moves again.
9. **Records.** What each end of each link received and spent in the substep is added to the current round's record.


# Part Two · Design concepts

- **The basic principle.** AP02's operator law, read at network scale, as Theorem VI.2 states it: Ėᵢ = −aᵢEᵢ + uᵢ + Σⱼ kᵢⱼ(Eⱼ − Eᵢ).
- **What an operator is.** In AP02's words: "An operator is any sovereign agent that applies control input to hold its structure against entropic drift". The world's operators are that, and nothing more. No consciousness, no goals beyond the rules.
- **Interdependence.** An operator's input comes from what its links deliver to it, and from its own input s. In the chargers, s is zero: "a charger only the other can crank". That is the chargers' rule, not AP02's. AP02's operators carry their own control, and cover their drain "from its own control budget". So s is a parameter, and the hypotheses sweep it. Either way, what one operator does moves what another can still do.
- **Sensing.** An operator reads its own stock, with noise, once a round. It reads the record of each of its own links exactly, because a record is what happened.
- **Adaptation.** Type C operators cut links that cost them more than they bring, by the rule in Part Three. Nothing else adapts.
- **Stochasticity.** Two kinds of noise, both zero mean, both off by default: noise in the stock (AP02's Derivation V) and noise in the reading (AP02's fifth axiom). Each is a parameter.
- **Collectives.** The configuration, as Phase 0 defines it: an operator and its direct counterparties, joined to it by live links, with that set's stock and net loss. Used for measurement only. It changes nothing in the world.
- **Observation.** Every run writes its log, and every run reports the survival of each configuration in spans (Part Five).


# Part Three · Details

## The stock equation

In each substep, for each live operator i:

> E_i ← E_i + Δt × ( s + Σ_j m·g_ji − Σ_j (c·g_ij + λ·g_ij²) − ε·L_i − b − a·E_i + Σ_j k·(E_j − E_i) ) + σ_s·√Δt·Z_i

| Term | Meaning | Where it comes from |
|---|---|---|
| s | The operator's own input, with no link | A modelling choice. Default 0, the chargers' rule, not AP02's. Swept in Group B. |
| Σ_j m·g_ji | What its live links deliver to it: m times what each counterparty j gives | The page's condition: "what I give you has to be worth enough more to you than it costs me". The multiple m is a parameter, swept. |
| Σ_j (c·g_ij + λ·g_ij²) | What its own giving costs it | AP02 Derivations II and IV: effort costs as its square, at price λ. In AP02 this price sits in the operator's objective, and is charged to no one's stock. The world charges it to the giver's stock, as the chargers charge cranking. The chargers use a flat cost c instead. |
| ε·L_i | The overhead of keeping its L_i live links. Each end pays ε for each of its live links. | Theorem VI.2's "irreducible overhead ε". It is not the axiom's ε. |
| b | A flat burn | The chargers' own rule |
| a·E_i | Proportional drift | AP02 Derivation I |
| k·(E_j − E_i) | Passive flow along a live link | AP02 Derivation VI. Default 0: "k = 0 until match is verified." |
| σ_s·√Δt·Z_i | Noise in the stock. Z_i is a fresh standard normal for each operator and substep | AP02 Derivation V. Default σ_s = 0. |

Where a delivery's energy comes from: a supply outside the operators, which the giver's effort unlocks (Phase 0's map, by AP02's first axiom). The log counts what the supply gives, so energy balances with the source counted.

## The reading

> reading_i = E_i + σ_r·Z

Z is a fresh standard normal for each reading. Default σ_r = 0.

## Giving

| Type | What it gives on each live link |
|---|---|
| C | g, every substep, while the link is live |
| U | g, every substep, while the link is live. It never cuts. |
| D | Nothing. It keeps every link it can, and never cuts. |

The default give g is m ÷ 2λ in the network: the give at which each side of a pair of cooperators gains most. Each operator's total giving can never exceed its capacity u_max, from AP02's third axiom. If it would, every link's give is scaled down in proportion. In the network, u_max is 6 by default: twice what an operator on the ring gives at m = 3. The chargers need none.

**Where a cooperator settles.** With no noise, a type C operator with L live links to other cooperators settles at

> E* = ( s + L·(m·g − λ·g² − ε) ) ÷ a

At the default give, m·g − λ·g² − ε is m² ÷ 4λ − ε. It is viable only where E* is above the ruin line. At the network's defaults:

| m | Each link adds, at a = 0.1 | E* with 1 link, s = 0 | with 2 links, s = 0 | with 1 link, s = 0.5 | alone, s = 0.5 |
|---|---|---|---|---|---|
| 2 | 9.9 | 9.9, not viable | 19.8 | 14.9 | 5, not viable |
| 3 | 22.4 | 22.4 | 44.8 | 27.4 | 5, not viable |
| 4 | 39.9 | 39.9 | 79.8 | 44.9 | 5, not viable |

So at m = 2 and s = 0, a cooperator left with one link falls by arithmetic. That is a true feature of the world, not the theorem failing, and anyone can see it before a run. And an operator alone can cover its own drain at the ruin line only where s is at least a·E_r, which is 1 at the defaults. Phase 0 places such an operator outside the bound.

## Reviews and cuts: the three premises of Theorem VI.2

Theorem VI.2 holds for operators that can "(i) read and act on its own viability gradient …, (ii) condition each link on the accumulated record of its counterparty, and (iii) set kᵢⱼ = 0 (sever / exit)". Type C operators have all three, by these rules:

1. **(i) The gradient.** A type C operator that reads "declining" reviews every one of its live links, on whatever record the link has, if it has at least one round.
2. **(ii) The record.** A type C operator that does not read declining reviews only the links that are at least w rounds old, on their last w rounds.
3. **(iii) The cut.** In a review, a link is cut if its record over the rounds reviewed is below zero for the reviewer: what the reviewer received through it is less than what it spent on it, overhead included.

Default w = 5, as Phase 0 set it. Both the gradient rule and the record rule are modelling choices: AP02 itself names them "a modelling floor for gradient-reading and record-conditioning". They stand in for the owed criterion of Debt D1, and no run claims to pay that debt.

A world in which some operators lack any of the three is outside the theorem's premises, and is labelled so. Type U and type D operators lack them by design.

## Who is linked to whom

- **The ring,** by default: N operators in a circle, each linked to its two neighbours.
- **Random links,** swept: each pair linked with probability p, with the seed.
- **Closed** by default: no new links form during a run.
- **Open,** as a setting: a new operator enters every q rounds and offers links to n operators chosen with the seed. A type C operator refuses a link to any operator whose record shows it took through a link more than it gave. That is the theorem's corollary on open networks: "persistence further requires each operator to condition its links on the counterparty's record".

## Ruin and the cap

- **The ruin line** is E_r. At or below it, an operator is ruined for ever: AP02's sixth axiom, "Ruin is real and permanent."
- **The cap**, where a setting has one, is E_max. Off by default.

## The three settings

One engine, three settings, as Phase 0 ruled. One implementation passes all the test values, or none.

| Parameter | The page's charger | Paper D's charger | AP02's network |
|---|---|---|---|
| Operators | A and B, linked | A and B, linked | N on a ring. Default N = 20 |
| Starting stock | 100 each | 100 each | 50 each |
| Burn b | 12 an hour | 12 an hour | 0 |
| Drift a | 0 | 0 | 0.1 |
| Who gives when | Both, all the time | Turns. Hours count from 0, and the first hour is A's: A in even hours, B in odd hours | Every live link, every substep |
| Give g | 1 while cranking | 1 while cranking | m ÷ 2λ = 1.5 |
| Delivery multiple m | 10 | 30 | 3 |
| Flat cost c | 4 | 4 | 0 |
| Effort price λ | 0 | 0 | 1 |
| Link overhead ε | 0 | 0 | 0.01 |
| Passive flow k | 0 | 0 | 0 |
| Ruin line E_r | 0 | 10 | 10 |
| Cap E_max | None | 100 | None |
| Types | U, or D | U, or D | C by default; one or more D in Group B |
| Round, substep | 1 hour, 0.001 | 1 hour, 0.001 | 1, 0.01 |
| Own input s | 0 | 0 | 0 by default; swept in Group B |
| Capacity u_max | None | None | 6 |
| Noise σ_s, σ_r | 0, 0 | 0, 0 | 0, 0 by default; swept in Group B |

**One reading, stated as a rule.** In the substep in which an operator is ruined, it still gives for the whole substep. In Paper D's charger, this is the reading under which the defector is ruined at 13.4375 hours: in the partial hour before the partner dies, the defector is still being charged, and the cap does not bind. Phase 0 states the same reading.


# Part Four · The modelling choices this draft adds

Phase 0's derivation map stands, as G ruled it. These are the choices this draft adds. Each is a parameter or a stated rule.

**Approved by G on 13 November 2026, as they stand,** with the seven lines that close where a second engine would guess, and the two notes in this table: own input s, swept in the grid, and the price of effort, moved from AP02's objective to the stock.

| Choice | The default | Why |
|---|---|---|
| The round and the substep | Decisions once a round; the stock in substeps | Phase 0's windows count rounds ("the last five readings"). A stock needs a fine step to match AP02's closed forms. Two time scales keep both. |
| The order of a round | As in Part One | Two engines that order the same rules differently build two worlds. |
| Synchronous moves | Every stock moves at once, from the substep's start | No operator gets an edge from where it sits in a list. That is Symmetry, in the world's own code. |
| Own input s | 0, and swept in Group B | 0 is the chargers' rule, not AP02's. AP02's operators have their own control. With s = 0, any operator cut off falls by starvation, so the hypotheses also run s = 0.5, below the drain at the ruin line: a lone operator still falls, but by the margin, not by starvation. Where s is at least a·E_r, an operator cut off covers its own drain, and Phase 0 places it outside the bound. |
| The cost of giving | c·g + λ·g², charged to the giver's stock | The chargers use a flat cost; AP02 a square cost. One formula holds both. AP02 puts the price in the operator's objective, charged to no one's stock. The world moves it to the stock, as the chargers do, so that effort has a cost the operator must cover. |
| Capacity in the network | u_max = 6 | AP02's third axiom: substrates are finite. Twice the ring's need, so it binds only on operators with many links. |
| The default give | m ÷ 2λ | The give at which a pair of cooperators gains most. Swept. |
| The gradient's role | A declining reading triggers an immediate review of every link | Premise (i) must do work, or the world leaves it out. |
| The review | A link is cut when its record is below zero for the reviewer | Phase 0's rule, stated for every case. |
| The record | Exact | A record is what happened. Only readings of the stock carry noise. |
| Capacity | Giving scaled down in proportion | AP02's third axiom: substrates are finite. |
| Ruin time | Straight-line interpolation within the substep | So that ruin times do not depend on the substep's size. |
| The ruined operator's last substep | It gives for the whole substep | Phase 0's reading of Paper D, made the rule for all settings. |


# Part Five · What every run reports

## The log

One line per operator per round, and one line per event, in JSON Lines:

- **round lines:** the round, the operator, its type, E, its reading, its slope, whether it read declining, and its live links;
- **event lines:** every cut (the round, who cut, which link, and the record that decided it), every ruin (the operator, and its interpolated time), every entry, and every configuration that starts or ends;
- **the run's head:** the version of this specification, every parameter, the seed, and the version of the code.

## Configurations and spans

As Phase 0, Part Three, rules, and the registry's notes of 11 November 2026 on KS-COUP.1 and KS-BAR.9 state, with their dated addition of 13 November 2026:

- **A configuration** is an operator and its direct counterparties, joined to it by live links. Every cut and every new link starts a new one, with a fresh clock.
- **Its clock starts** when the operator's own links, taken together, turn net-negative for its counterparties: at the first round in which its counterparties' records on their links to it, added together, are below zero, overhead included. Not in raw units: every cooperator receives m times what it gives, so raw units would start every clock at once.
- **Its span** is its stock above the ruin line, divided by its net loss per round, with the loss taken at its smallest along the way down. Where the configuration gains as a whole, the span is taken over its counterparties alone, as Part Nine sets out.
- **Its bound** is three spans, plus its counterparties' record window where they are defended, that is, where they are type C.
- **Every run reports** the survival of each configuration in spans, as a number, which of the two spans it used, and the number of configurations each defector passed through. Part Nine says how a run is measured and judged.


# Part Six · The test values

Any implementation reproduces every one of these, to the tolerance shown, before it reports anything. Each value was computed by AG Opus's desk script from this text alone.

## The chargers: exact

Tolerance: 0.0001 hours.

| Case | Setting | Value |
|---|---|---|
| Both crank | The page | Each is ruined at 16.666667 hours: sixteen hours and forty minutes |
| B defects | The page | A is ruined at 6.25 hours. B at 13.541667 hours. The page gives thirteen hours and thirty-two minutes. |
| The boundary | The page, B defects, delivery m swept | At m = 8 the pair and the defector are both ruined at 12.5 hours. At m = 7: the pair at 11.111111, the defector at 11.979167. At m = 9: the pair at 14.285714, the defector at 13.020833. At m = 10: as above. |
| Both take turns | Paper D | Nobody is ruined. At 30 hours, A holds 100 and B 84. Both stay between 84 and 100. |
| B defects | Paper D | A is ruined at 6.375 hours. B at 13.4375 hours. |

## The spans of the page's case

From Phase 0, as the test of span-keeping. Tolerance 0.0001.

| Configuration | Stock above ruin | Net loss an hour | Span |
|---|---|---|---|
| The pair, from the moment B defects | 200 | 18 | 11.1111 hours |
| B alone, from A's ruin | 87.5 | 12 | 7.2917 hours |

The pair is ruined inside one span, at 6.25 hours. B alone is ruined exactly one span after A, at 13.541667 hours.

## AP02's results: at their own formulas

Tolerance: 0.000001, except where shown.

| Result | Test | Value |
|---|---|---|
| Theorem I.1, drift | a = 0.1, E₀ = 1, no giving, t = 10 | E = e^(−1) = 0.367879 by the closed form. With the network's substep of 0.01, within 0.0002 of it. |
| Theorem II.1, discipline | a = 0.5, λ = 2 | Least-cost point x = 1/(1 + λa²) = 0.666667, with effort u = a/(1 + λa²) = 0.333333 |
| Theorem III.1, the event horizon | a = 0.5, u_max = 0.3 | x_H = u_max ÷ a = 0.6. Above it, the stock falls even at full effort. |
| Theorem IV.1, the impulse | Two schedules with the same mean effort, 0.5: steady, and alternating 0 and 1 | Mean cost of effort, λ = 1: steady 0.25, alternating 0.5 |
| Theorem VI.1, the coupling tax | a₁ = 0.2, a₂ = 0.6, λ = 1, each operator's own effort held at its least-cost level, uᵢ = aᵢ/(1 + λaᵢ²), and a passive link k = 0.1 | Efforts u₁ = 0.192308, u₂ = 0.441176. Coupled steady state E₁ = 0.893665, E₂ = 0.757919. A standing flow of 0.013575 per unit of time, from the lower-drift operator to the higher: "a permanent tax on the more efficient agent". |

## The network setting: the engine's own check

These check that an engine runs the network setting's equation, its order and its review rule as written. Tolerance: 0.0001. The closed forms beside them show how close the substep comes.

| Case | Value | The closed form |
|---|---|---|
| N1 · Two type C operators, linked, no noise | Neither cuts. At t = 10, each holds 32.548394 | 22.4 + 27.6·e^(−1) = 32.553473 |
| N2 · A type C and a type D, linked, no noise | At the start of round 1, A reads declining, reviews the link on its one round of record, and cuts it. A is ruined at 15.5993. B is ruined at 16.9888. | A at 15.6070, B at 16.9970 |

N2 is the theorem's own picture at its smallest. The cooperator sees the loss and cuts. The defector, cut off, has nothing to take, and is ruined. So is the cooperator, because in a world of two it has nobody else. In a ring, it keeps its other links.


# Part Seven · Two engines, and noise

Without noise, two engines that follow this text agree exactly, to the tolerances of Part Six. With noise, they cannot: two engines with different random generators never share a seed. So with noise, two engines agree when their means agree within their standard errors, cell by cell, never seed by seed. A second implementation is never told it disagrees for drawing different random numbers.

# Part Eight · What the specification does not fix

- **Debt D1.** The exact conditions under which a link is net-positive are owed by AP02. The review rule stands in for them, and no run claims to pay the debt.
- **The exact collapse rates.** Also owed under D1. So every bound counts in spans, never in an exact rate.
- **Anything about real people.** A run tests whether the theorem's conclusion follows from its premises in a world that meets them. It fires a switch written about the theorem only when it meets those premises. It cannot, on its own, fire a claim about people.


# Part Nine · How a run is measured, settled 13 November 2026

Both engines were built from draft 3, blind. They agreed on every test value, and where they read the text differently, the text had left a choice. These rules close every one. AG Fable read them. G approved the run's length.

1. **An operator alone** is a configuration of one, of any type. Its clock starts when it is left alone, if its own net change is a loss.
2. **The span, two ways.** Where the configuration loses as a whole, its span is its stock above the ruin line, over its net loss: the page's test value, 200 over 18. Where it gains as a whole, its span is taken over its counterparties alone: their stock above the ruin line, over their net loss through their links to the operator. Every run reports which span each watched configuration used. The registry's notes on KS-COUP.1 and KS-BAR.9 carry the same, by a dated addition of 13 November 2026.
3. **The net loss** is the members' rate of change, from that seed's own state, without the stock's noise. Its reading noise and its cuts are part of it. It is taken at every round's start and end, and at the configuration's end, and the smallest above zero sets the span.
4. **The run's length** is 4,000 rounds for every cell, fixed before any run. A watched configuration whose bound ends inside the run is judged. One still standing at the end, whose bound has passed, counts at the run's length. One still standing whose bound has not yet come is "too long to judge in this run". A seed with any such configuration is left out of the mean whole, counted and reported. If more than one seed in ten is left out, the cell settles nothing.
5. **Survival** is measured less the record window, where the counterparties are defended, that is, where they are type C. Elsewhere, no window is subtracted.
6. **The measure for a seed** is the largest survival in spans among the configurations a hypothesis watches. The judgement takes the mean and the standard error of that across the seeds.
7. **A review on a declining reading** uses the link's last w rounds, or all of them if it has fewer.
8. **Passive flow** counts in the record, as received or as paid through the link.
9. **Entry.** A newcomer enters after the round's cuts, every q rounds from round q, and takes its first reading the round after. Every type C operator, newcomers included, refuses a link to any operator whose counterparties' records on their links to it, added together over its whole record, are below zero. In the entry setting, a defector left with no live links offers a link to one operator, chosen with the seed, every q rounds.
10. **Capacity** is u_max = 6. An operator accepts a new link only while its capacity still covers the default give on every link: 4 links at m = 3, 6 at m = 2, and 3 at m = 4. Links drawn at the start of a random network stand as drawn, and capacity scales them as Part Three says.
11. **The log** is kept at the sample level: every event for every seed, and the round lines for the first five seeds of each cell.
12. **The reference's random numbers:** numpy's PCG64, one generator per seed, seeded with the seed. First the random links, the defectors' places and the uneven drift. Then, each round, the reading noise, an entry's choices, and the stock noise. Other engines are not bound by this, as Part Seven says.
13. **The lone operator,** for B3: it starts at 50, with a ruin line at 10, drift 0.1, a price of effort λ = 1, counted and reported, and an effort set each round by its policy, never above its own capacity u_max, which B3 sweeps. The network's u_max of 6 does not apply to it. The policies are in the hypotheses.

# What changed since draft 1

From AG Fable's reading, all taken:

- **Seven places a second engine had to guess,** each closed: hours in Paper D count from 0, and the first is A's; what an end spent on a link; when a configuration's clock starts, by the counterparties' records; the network's capacity; that records are open to every operator; round zero reads "not declining"; and how two engines agree under noise (Part Seven).
- **Own input s:** the chargers' rule, not AP02's, and now said so. The hypotheses sweep it.
- **The price of effort:** AP02 puts it in the objective; the world moves it to the stock, and says so.
- **Where a cooperator settles:** a closed form, and a table showing which cells are viable before any run.

No test value changes. The desk script was run again on this text, and gives the same numbers.


## Draft 3, 13 November 2026

One change: G approved the added choices in Part Four, as they stand. No rule and no test value changes. This text becomes version 1.0 of the specification, tagged world-spec-v1.0, on the day B1 is frozen, and every frozen document names that version.

## Draft 4, 13 November 2026

Part Nine added: the readings both engines found, settled, with AG Fable's four changes, and the run's length G approved. Part Five points to it. No test value changes.
