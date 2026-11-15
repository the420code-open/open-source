"""Shows that both adapters run every line of the suite and write run packets, with no AI called: a replay
model gives back the calibration set's answers, as an AI's answers would come back.

    python tests/adapters/demo_no_ai.py SUITE.jsonl CALIBRATION.yaml OUT_DIR

Zero-Clause BSD.
"""
import io
import json
import os
import shutil
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def load(suite, cal):
    lines = [json.loads(x) for x in io.open(suite, encoding="utf-8") if x.strip()]
    answers = {}
    for a in yaml.safe_load(io.open(cal, encoding="utf-8"))["answers"]:
        if a["intended"] == "pass":
            answers[(a["item"], a["text"])] = a["answer"]
    by_messages = {json.dumps(l["messages"], ensure_ascii=False): l for l in lines}
    return lines, answers, by_messages


def inspect_demo(suite, lines, answers, by_messages, out):
    from inspect_ai import eval as inspect_eval
    from inspect_ai.model import ModelOutput, get_model
    sys.path.insert(0, os.path.join(HERE, "inspect"))
    from the_tests import the_tests
    from to_packet import main as to_packet

    def reply(messages, tools, tool_choice, config):
        key = json.dumps([{"role": m.role, "content": m.text} for m in messages], ensure_ascii=False)
        line = by_messages[key]
        return ModelOutput.from_content(model="replay", content=answers[(line["item"], line["text"])])

    model = get_model("mockllm/model", custom_outputs=reply)
    logs = inspect_eval(the_tests(suite=suite, runs=3), model=model, log_dir=os.path.join(out, "inspect-logs"),
                        display="none")
    to_packet(logs[0].location, os.path.join(out, "packet-inspect.jsonl"))


def lm_eval_demo(suite, lines, answers, by_messages, out):
    import lm_eval
    from lm_eval.api.model import LM
    from lm_eval.tasks import TaskManager

    class Replay(LM):
        def apply_chat_template(self, chat_history, add_generation_prompt=True):
            return json.dumps(chat_history, ensure_ascii=False)

        @property
        def tokenizer_name(self):
            return "replay"

        def chat_template(self, chat_template=False):
            return "replay"

        def generate_until(self, requests, disable_tqdm=False):
            out_ = []
            for r in requests:
                line = by_messages[json.dumps(r.doc["messages"], ensure_ascii=False)]
                sent = json.loads(r.args[0])
                assert sent == line["messages"], "the harness did not send the line's own conversation"
                out_.append(answers[(line["item"], line["text"])])
            return out_

        def loglikelihood(self, requests):
            raise NotImplementedError

        def loglikelihood_rolling(self, requests):
            raise NotImplementedError

    # the task reads tests/generated/tests.jsonl from where it runs
    work = os.path.join(out, "lm-eval-work")
    os.makedirs(os.path.join(work, "tests", "generated"), exist_ok=True)
    shutil.copyfile(suite, os.path.join(work, "tests", "generated", "tests.jsonl"))
    cwd = os.getcwd()
    os.chdir(work)
    try:
        tm = TaskManager(include_path=os.path.join(HERE, "lm_eval"))
        res = lm_eval.simple_evaluate(model=Replay(), tasks=["the_420_tests"], task_manager=tm,
                                      apply_chat_template=True, log_samples=True)
    finally:
        os.chdir(cwd)
    rows = [{"kind": "head", "maker": "replay", "model_requested": "replay of the calibration set",
             "settings": {"tool": "lm-evaluation-harness %s" % lm_eval.__version__, "apply_chat_template": True},
             "runs": 3, "label": "an lm-evaluation-harness run, replayed: no AI was called"}]
    for s in res["samples"]["the_420_tests"]:
        d = s["doc"]
        resps = s["resps"]
        flat = resps[0] if len(resps) == 1 and isinstance(resps[0], list) else [r[0] if isinstance(r, list) else r for r in resps]
        for run, resp in enumerate(flat, 1):          # the harness's repeats: one answer per run
            rows.append({"kind": "answer", "id": d["id"], "item": d["item"], "test": d["test"], "text": d["text"],
                         "wording": d["wording"], "held_out": d.get("held_out", False), "run": run,
                         "sent": d["messages"], "answer": resp})
    with io.open(os.path.join(out, "packet-lm-eval.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("%d answers -> %s" % (len(rows) - 1, os.path.join(out, "packet-lm-eval.jsonl")))
    print("recorded:", res["results"]["the_420_tests"])


if __name__ == "__main__":
    suite, cal, out = (os.path.abspath(x) for x in sys.argv[1:4])
    os.makedirs(out, exist_ok=True)
    lines, answers, by_messages = load(suite, cal)
    inspect_demo(suite, lines, answers, by_messages, out)
    lm_eval_demo(suite, lines, answers, by_messages, out)
