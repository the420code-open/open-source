"""The challenge's ten routes, each sent one neutral call before the run day, never the question.

AG Opus, through G, 15 November 2026: "Yes to one neutral call on each of the ten routes today, never the question,
kept in the record as the DeepSeek check is. If every route passes, the run takes 16 November, from 00:01 Cape Town
time, with its known roads' arm the same day. If any route fails, mend it and test it again; the run waits for that,
not for a date."

Each call goes through runner/roads.py's own `call`, the function the run itself uses, at the run's own settings.
The eight AIs get one neutral prompt; the two markers a neutral prompt shaped as a mark. Kept whole, one file each.

    python route_check.py <route> <out_dir>     route: anthropic openai google xai meta mistral deepinfra kimi
                                                  marker-xai marker-google   (the key from makers_key.py run)

Zero-Clause BSD.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "runner"))
import roads  # noqa: E402

ROUTE, OUT = sys.argv[1], sys.argv[2]
AI_PROMPT = "Which whole numbers between 1 and 50 are prime? List them, and say how many there are."
MARK_PROMPT = ("Here is a question and an answer to it.\n\nThe question: Which whole numbers between 1 and 50 are prime? "
               "List them, and say how many there are.\n\nThe answer: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43 "
               "and 47. There are fifteen.\n\nSort the answer as one of two kinds: right, or wrong. Then give one line "
               "saying why.")
maker = ROUTE.replace("marker-", "")
text = MARK_PROMPT if ROUTE.startswith("marker-") else AI_PROMPT
rec = roads.call(maker, text, tries=3)
rec.update(route=ROUTE, prompt=text, settings=roads.M[{"kimi": "moonshot"}.get(maker, maker)])
u = rec.get("usage") or {}
want = rec["settings"]["model"]
got = rec.get("model_returned") or ""
rec["read"] = {
    "answered": bool(rec.get("answer")),
    "model_as_set": bool(got) and (got == want or got.startswith(want) or want.split("/")[-1] in got),
    "normal_stop": not rec.get("cut_short") and not rec.get("refusal") and rec.get("answer") is not None,
    "tokens_reported": bool(u.get("input")) and bool(u.get("output")),
    "reasoning_seen": bool(u.get("reasoning")) or bool(rec.get("reasoning_text")),
}
rec["passed"] = all(rec["read"][k] for k in ("answered", "model_as_set", "normal_stop", "tokens_reported"))
os.makedirs(OUT, exist_ok=True)
json.dump(rec, open(os.path.join(OUT, "%s.json" % ROUTE), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(ROUTE, "PASSED" if rec["passed"] else "FAILED", json.dumps(rec["read"]), "| model", got, "| stop", rec.get("stop_reason"),
      "| usage", json.dumps({k: u.get(k) for k in ("input", "output", "reasoning")}), "| $%.4f" % rec.get("usd", 0),
      "| %ss" % rec.get("seconds"), "|", (rec.get("error") or "")[:400])
