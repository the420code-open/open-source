# tests/adapters · Inspect and lm-evaluation-harness

These let open evaluation tools run the suite. Each runs every line, three times, and writes the answers in the run packet's form.

Neither scores anything. The tests are scored by their rubrics, blind, by the scorers the tests' Part A names. An automatic score from a tool would not be a result of the tests.

Neither carries any item's text. Each loads the items from the suite file it is given. A conversation's earlier AI turns reach the AI as its own earlier turns.

Terms: Zero-Clause BSD (LICENSE-0BSD).

## Inspect

```
inspect eval tests/adapters/inspect/the_tests.py --model <provider/model> -T suite=tests/generated/tests.jsonl
python tests/adapters/inspect/to_packet.py <the log> packet.jsonl
```

## lm-evaluation-harness

Run this from the repository's root, with a chat model:

```
lm_eval --model <chat model> --tasks the_420_tests --include_path tests/adapters/lm_eval \
        --apply_chat_template --log_samples --output_path OUT
```

The task's own class sends each line's conversation as turns. Without `--apply_chat_template`, a conversation can only be sent as text.

## Shown without any AI

`demo_no_ai.py` runs both adapters with a replay model that gives back the calibration set's answers:

```
python tests/adapters/demo_no_ai.py tests/generated/tests.jsonl tests/calibration/calibration_draft.yaml OUT
```

On 13 November 2026, with Inspect 0.3.289 and lm-evaluation-harness 0.4.13, each wrote 414 answers: 138 lines, three runs each. In both, the 81 answers to conversations went out as turns.
