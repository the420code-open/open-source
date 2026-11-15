"""An Inspect log of the tests, as a run packet: a head, then one line per answer.

    python tests/adapters/inspect/to_packet.py LOG.eval OUT.jsonl

Zero-Clause BSD.
"""
import datetime
import io
import json
import sys

from inspect_ai.log import read_eval_log


def main(log_path, out):
    log = read_eval_log(log_path)
    first = log.samples[0].metadata if log.samples else {}
    rows = [{"kind": "head", "maker": log.eval.model.split("/")[0], "model_requested": log.eval.model,
             "settings": {"tool": "Inspect %s" % log.eval.packages.get("inspect_ai", ""),
                          "generate config": log.plan.config.model_dump(exclude_none=True) if log.plan else {}},
             "date": (log.eval.created or "")[:10] or datetime.date.today().isoformat(), "runs": log.eval.config.epochs,
             "versions": {"floor": (first.get("versions") or {}).get("floor"), "tests": (first.get("versions") or {}).get("tests")},
             "label": "an Inspect run", "inspect_log": log_path}]
    for s in log.samples:
        m = s.metadata
        out_model = s.output.model if s.output else None
        u = s.output.usage if s.output and s.output.usage else None
        rows.append({"kind": "answer", "id": s.id, "item": m["item"], "test": m["test"], "text": m["text"],
                     "wording": m["wording"], "held_out": m.get("held_out", False), "run": s.epoch,
                     "sent": m["messages"], "answer": s.output.completion if s.output else None,
                     "model_returned": out_model, "stop_reason": s.output.stop_reason if s.output else None,
                     "usage": {"input": u.input_tokens, "output": u.output_tokens} if u else None})
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print("%d answers -> %s" % (len(rows) - 1, out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
