"""The tests, as an Inspect task. Every line of the suite, each run three times (epochs), at the model's own defaults.

    inspect eval tests/adapters/inspect/the_tests.py --model <provider/model> -T suite=tests/generated/tests.jsonl
    python tests/adapters/inspect/to_packet.py LOG.eval OUT.jsonl     (the answers, in the run packet's form)

This adapter scores nothing. The tests are scored by their rubrics, blind, by the scorers the tests' Part A names;
an automatic score here would not be a result of the tests. A conversation's earlier AI turns are sent as the
AI's own earlier turns. The adapter carries no item text: it loads every item from the suite file it is given.

Zero-Clause BSD.
"""
from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.model import ChatMessageAssistant, ChatMessageUser
from inspect_ai.solver import generate

KEEP = ("item", "test", "test_name", "text", "wording", "works_words", "floor_lines", "held_out", "rubric", "versions")


def record_to_sample(r):
    messages = [ChatMessageUser(content=m["content"]) if m["role"] == "user" else ChatMessageAssistant(content=m["content"])
                for m in r["messages"]]
    return Sample(id=r["id"], input=messages, metadata={k: r.get(k) for k in KEEP} | {"messages": r["messages"]})


@task
def the_tests(suite: str = "tests/generated/tests.jsonl", runs: int = 3):
    return Task(dataset=json_dataset(suite, record_to_sample), solver=generate(), scorer=None, epochs=runs)
