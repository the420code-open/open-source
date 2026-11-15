"""The tests in lm-evaluation-harness: a task class that sends each line's own conversation, so that a
conversation's earlier AI turns reach the AI as its own earlier turns. Zero-Clause BSD."""
import json

from lm_eval.api.task import ConfigurableTask


def doc_to_text(doc):
    """Without a chat template, a conversation can only be sent as text: Person: ... / AI: ..."""
    msgs = doc["messages"]
    if len(msgs) == 1:
        return msgs[0]["content"]
    return "\n".join(("Person: " if m["role"] == "user" else "AI: ") + m["content"] for m in msgs)


def process_results(doc, results):
    return {"recorded": 1.0 if results and results[0] is not None else 0.0}


class TheTests(ConfigurableTask):
    def __init__(self, config=None, **kw):
        config = dict(config or {})
        config.pop("class", None)       # the harness passes its own routing key along; the task config has no such field
        super().__init__(config=config, **kw)

    def fewshot_context(self, doc, num_fewshot, system_instruction=None, apply_chat_template=False,
                        fewshot_as_multiturn=False, chat_template=None, gen_prefix=None, **kw):
        if apply_chat_template and chat_template:
            return chat_template([{"role": m["role"], "content": m["content"]} for m in doc["messages"]],
                                 add_generation_prompt=True)
        return doc_to_text(doc)
