# tests/runner · the runner and the scoring

Terms: Zero-Clause BSD (LICENSE-0BSD).

| File | What it does |
|---|---|
| generate.py | Makes the suite from the tests' source: one line for every text and every wording, and the scorer's instructions word for word. |
| run.py | Sends every line to one AI through its maker's own interface, at the maker's defaults, three times, and writes a run packet. |
| batch.py | The same, through each maker's batch interface: one run of the suite for one AI, sent at once, answered within a day, at half the price. `submit`, `status`, `collect` (a packet in run.py's shape) and `ledger`. |
| score.py | Blinds and shuffles the answers; runs scorer one, on each answer and, for Authority and Windows, on each pair side by side; picks scorer two's sample; computes agreement and Cohen's kappa; tallies the scores; and runs the calibration set (`calibrate`, `calcheck`). |

## The run packet

A head, then one line for each answer.

- **The head:** the maker, the model as requested, the settings, the date, the number of runs, and the versions of the floor, the tests and the suite.
- **Each answer:** its line ID, its run, the text exactly as sent, the full answer, the model's name as its maker returned it, and the tokens used.
- **Marks** are added once the answers are scored.

## What the runner will not do

- **Send without approval.** Nothing goes to any AI without an approval file. The file names the batch, the maker and a ceiling in US dollars.
- **Pass the ceiling.** It stops before the cost of what it has run, at the maker's published prices, passes that ceiling.
- **Use another model.** No fallback model is ever used, so every answer is the named AI's own.
- **Run on past the first run, if asked.** It can stop after run 1 for the cost check: `--stop-after-run 1`.
- **Use outside settings.** Each maker's defaults hold. One setting is not a default, and it is recorded: Anthropic's interface requires `max_tokens`, so it is set to 32,000, which cuts nothing.

## What the scorer is given

The scorer's instructions, word for word as tests.yaml holds them; the situation; the answer; and the rubric's whole text, never only its split lines, with the item's note for scorers where it has one. For Authority and Windows, the pair is also scored with both answers side by side, the situation's and the twin's, or form A's and form B's, with the test's pair rule; the pair's one mark is the pair's score, and a hard fail in either answer alone stays a hard fail.

## Through the batch interface

The desks' baseline runs through each maker's batch interface (G's approval, 13 November 2026): the same model, at the same settings, at half the price, with answers within a day.

- **One batch is one run.** Run 1 is sent first; runs 2 and 3 only on a new approval, once run 1's real tokens and cost have been reported.
- **The ceiling, for all the makers together.** Before a batch is sent, the runner adds the real cost of every batch already collected to the high estimate of every batch still out, and of this one, at the batch price. If that would pass the ceiling, nothing is sent.
- **The approval file** names who approved, the date, their words, the ceiling for all the makers together, each maker's model, the interface, and the last run it approves.
- `--dry` writes and prices the requests, and sends nothing.

## The keys

Each maker's key comes from its usual environment variable:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

Anyone may run the suite on their own account, at their own cost, and send in the packet as an independent run.

## Without any AI

`run.py --maker replay` and `score.py one --scorer replay` give back stored answers and marks, such as the calibration set's. Every step can then be checked with no AI called.
