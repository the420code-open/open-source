"""One real answer first (the tests, version 1.1, changes draft 3, section 3): every item new or changed in a version,
the situation and the twin, in every wording, gets one real answer from an AI outside the baseline, sent as the
baseline is sent: the same route, no system message, no tools, at the maker's defaults.

    python tests/one-real-answer/ask.py LINES.jsonl --maker xai --model grok-4.7 --approval APPROVAL.json \
        --out PACKET.jsonl [--dry]

xAI's own interface (api.x.ai, OpenAI's format), through the openai SDK, with its own base address. One message from
the person; nothing else is set. The key comes from XAI_API_KEY, which makers_key.py fills; it is never written.

Zero-Clause BSD.
"""
import argparse
import datetime
import io
import json
import os

PRICE = {"grok-4.7": {"input": 2.0, "output": 6.0}}       # per million tokens, docs.x.ai/docs/models, 14 November 2026


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("--maker", required=True, choices=["xai"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--approval", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    ok = json.load(open(a.approval, encoding="utf-8"))
    assert ok["maker"] == a.maker and ok["model"] == a.model, "the approval names another AI"
    lines = [json.loads(x) for x in io.open(a.lines, encoding="utf-8") if x.strip()]
    assert len(lines) <= ok["questions"], "more questions than approved"
    if a.dry:
        for ln in lines:
            print(ln["id"], "|", ln["messages"][0]["content"][:90])
        return
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    spent = 0.0
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"kind": "head", "maker": a.maker, "model_requested": a.model,
                            "interface": "xAI's own interface, chat completions, api.x.ai/v1",
                            "settings": {"everything": "the maker's defaults", "system message": "none",
                                         "tools": "none"},
                            "date": now()[:10], "approval": {k: ok[k] for k in ("approved_by", "date", "words")},
                            "label": "one real answer first, version 1.1"}, ensure_ascii=False) + "\n")
        for ln in lines:
            t = now()
            try:
                r = client.chat.completions.create(model=a.model, messages=ln["messages"])
                u = r.usage
                det = getattr(u, "completion_tokens_details", None)
                usage = {"input": u.prompt_tokens, "output": u.completion_tokens,
                         "reasoning": getattr(det, "reasoning_tokens", None) if det else None}
                x = {"answer": r.choices[0].message.content, "model_returned": r.model,
                     "stop_reason": r.choices[0].finish_reason, "usage": usage}
                billed_out = usage["output"] + (usage["reasoning"] or 0)     # reasoning counted as output, to be safe
                spent += (usage["input"] * PRICE[a.model]["input"] + billed_out * PRICE[a.model]["output"]) / 1e6
            except Exception as e:      # noqa: BLE001
                x = {"answer": None, "error": "%s: %s" % (type(e).__name__, str(e)[:500])}
            x.update(kind="answer", id=ln["id"], item=ln["item"], text=ln["text"], wording=ln["wording"],
                     sent=ln["messages"], at=t)
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
            print(ln["id"], "ok" if x.get("answer") else "ERROR " + x.get("error", ""))
            assert spent <= ok["ceiling_usd"], "over the approved ceiling"
    print("spent about $%.4f" % spent)


if __name__ == "__main__":
    main()
