"""The desks' runner: sends every line of the suite to one AI, through its maker's own interface, at the maker's
default settings, three times, and records everything in a run packet.

    python tests/runner/run.py --maker anthropic --model claude-fable-5-2 \
        --suite tests/generated/tests.jsonl [--suite held_out.jsonl] --runs 3 \
        --approval APPROVAL.json --prices PRICES.json --out packets/NAME.jsonl [--stop-after-run 1]

    python tests/runner/run.py --maker replay --replay ANSWERS.yaml --suite ... --out ...   (no AI is called)

The key comes from the maker's usual environment variable (ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY).
Nothing is sent without an approval file naming the batch, the maker and a ceiling in US dollars; the runner stops
before the cost of what it has run, at the maker's published prices, passes that ceiling. The packet is written
line by line, so a stopped run carries on where it stopped.

Settings: the maker's defaults. Two are not defaults, and are recorded: Anthropic's interface requires max_tokens,
so it is set high (32,000) to cut nothing; no fallback model is ever used, so every answer is the named AI's own.

Zero-Clause BSD.
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import sys
import time

FLOOR_VERSION = "1.0 (floor-v1.0)"
ANTHROPIC_MAX_TOKENS = 32000


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- the makers' interfaces
class Anthropic:
    name = "anthropic"

    def __init__(self, model):
        import anthropic  # the maker's own SDK
        self.client, self.model = anthropic.Anthropic(), model
        self.settings = {"max_tokens": ANTHROPIC_MAX_TOKENS, "everything else": "the maker's defaults",
                         "fallbacks": "none"}

    def ask(self, messages):
        with self.client.messages.stream(model=self.model, max_tokens=ANTHROPIC_MAX_TOKENS,
                                         messages=messages) as s:
            m = s.get_final_message()
        text = "".join(b.text for b in m.content if getattr(b, "type", "") == "text")
        return {"answer": text, "model_returned": m.model, "stop_reason": m.stop_reason,
                "usage": {"input": m.usage.input_tokens, "output": m.usage.output_tokens}}


class OpenAI:
    name = "openai"

    def __init__(self, model):
        import openai
        self.client, self.model = openai.OpenAI(), model
        self.settings = {"everything": "the maker's defaults"}

    def ask(self, messages):
        r = self.client.responses.create(model=self.model, input=messages)
        u = r.usage
        return {"answer": r.output_text, "model_returned": r.model, "stop_reason": r.status,
                "usage": {"input": u.input_tokens, "output": u.output_tokens,
                          "reasoning": getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None)}}


class Google:
    name = "google"

    def __init__(self, model):
        from google import genai
        self.client, self.model = genai.Client(), model
        self.settings = {"everything": "the maker's defaults"}

    def ask(self, messages):
        from google.genai import types
        contents = [types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part(text=m["content"])])
                    for m in messages]
        r = self.client.models.generate_content(model=self.model, contents=contents)
        u = r.usage_metadata
        return {"answer": r.text or "", "model_returned": getattr(r, "model_version", None) or self.model,
                "stop_reason": str(r.candidates[0].finish_reason) if r.candidates else None,
                "usage": {"input": u.prompt_token_count, "output": (u.candidates_token_count or 0),
                          "reasoning": getattr(u, "thoughts_token_count", None)}}


class Replay:
    """Stored answers, by line ID or by item and text: for testing the packet with no AI called."""
    name = "replay"

    def __init__(self, path):
        import yaml
        d = yaml.safe_load(io.open(path, encoding="utf-8"))
        self.by = {}
        for a in d["answers"]:
            self.by.setdefault((a["item"], a["text"]), []).append(a)
        self.model, self.settings = "replay of " + os.path.basename(path), {"no AI": "stored answers"}
        self.pick = 0

    def ask(self, messages, line=None):
        options = self.by.get((line["item"], line["text"]), [])
        a = options[self.pick % len(options)] if options else {"answer": ""}
        return {"answer": a["answer"], "model_returned": self.model, "stop_reason": "replay",
                "usage": {"input": 0, "output": 0}, "intended": a.get("intended")}


def cost(usage, price):
    out = (usage.get("output") or 0) + (usage.get("reasoning") or 0 if price.get("reasoning_separate") else 0)
    return (usage.get("input") or 0) / 1e6 * price["input"] + out / 1e6 * price["output"]


# ---------------------------------------------------------------- the run
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maker", required=True, choices=["anthropic", "openai", "google", "replay"])
    ap.add_argument("--model")
    ap.add_argument("--suite", action="append", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--approval")
    ap.add_argument("--prices")
    ap.add_argument("--replay")
    ap.add_argument("--stop-after-run", type=int)
    a = ap.parse_args()

    lines = []
    for s in a.suite:
        lines += [json.loads(x) for x in io.open(s, encoding="utf-8") if x.strip()]
    if a.maker == "replay":
        ai, ceiling, price = Replay(a.replay), None, None
    else:
        if not a.approval or not os.path.exists(a.approval):
            raise SystemExit("no approval file: nothing is sent to any AI until G approves the batch's cost")
        ok = json.load(open(a.approval, encoding="utf-8"))
        if a.maker not in ok.get("makers", {}) or not ok.get("approved_by") or not ok.get("date"):
            raise SystemExit("the approval file does not approve %s" % a.maker)
        ceiling = float(ok["makers"][a.maker]["ceiling_usd"])
        price = dict(json.load(open(a.prices, encoding="utf-8"))[a.model])
        today = datetime.date.today().isoformat()
        for k in sorted(k for k in list(price) if k.startswith("from_")):     # a published change of price, by date
            if today >= k[5:]:
                price.update(price[k])
        ai = {"anthropic": Anthropic, "openai": OpenAI, "google": Google}[a.maker](a.model)

    done, spent = set(), 0.0
    if os.path.exists(a.out):
        for x in io.open(a.out, encoding="utf-8"):
            r = json.loads(x)
            if r.get("kind") == "answer":
                done.add((r["id"], r["run"]))
                if price:
                    spent += cost(r["usage"], price)
    f = io.open(a.out, "a", encoding="utf-8", newline="\n")
    if not done:
        f.write(json.dumps({
            "kind": "head", "maker": a.maker, "model_requested": a.model or ai.model, "settings": ai.settings,
            "date": datetime.date.today().isoformat(), "runs": a.runs,
            "versions": {"floor": FLOOR_VERSION, "tests": lines[0]["versions"]["tests"] if lines else None,
                         "suite_sha256": {os.path.basename(s): sha256(s) for s in a.suite}},
            "label": "replay: no AI was called" if a.maker == "replay" else "the desks' own run",
        }, ensure_ascii=False) + "\n")
    for run in range(1, a.runs + 1):
        if isinstance(ai, Replay):
            ai.pick = run - 1
        for line in lines:
            if (line["id"], run) in done:
                continue
            if ceiling is not None and spent >= ceiling:
                f.close()
                raise SystemExit("stopped at the approved ceiling, $%.2f, after $%.2f" % (ceiling, spent))
            t0 = time.time()
            try:
                r = ai.ask(line["messages"], line) if isinstance(ai, Replay) else ai.ask(line["messages"])
            except Exception as e:      # recorded, never retried silently into a different answer
                r = {"answer": None, "error": "%s: %s" % (type(e).__name__, str(e)[:500])}
            r.update(kind="answer", id=line["id"], item=line["item"], test=line["test"], text=line["text"],
                     wording=line["wording"], held_out=line.get("held_out", False), run=run,
                     sent=line["messages"], seconds=round(time.time() - t0, 2),
                     at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
            if price and r.get("usage"):
                spent += cost(r["usage"], price)
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
        if a.stop_after_run and run >= a.stop_after_run:
            f.close()
            print("stopped after run %d, as asked; spent $%.2f at published prices" % (run, spent))
            return
    f.close()
    print("done: %d lines x %d runs; spent $%.2f at published prices" % (len(lines), a.runs, spent))


if __name__ == "__main__":
    main()
