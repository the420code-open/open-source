"""The challenge's settings, point 1: does DeepInfra take DeepSeek's own highest setting, `max`, and does reasoning come
back? AG Opus, through G, 15 November 2026: "Before the run day, send one test call on a neutral prompt, never the
question, and check that DeepInfra takes `max` and that reasoning tokens come back. If it refuses `max`, use `high`,
and check the same. If no setting gives reasoning, DeepSeek is asked as the host serves it, and the record says so,
in DeepInfra's words."

One neutral prompt, nothing of the paper or the question. Nothing else is sent: no system message, no length, no
temperature. Every request and every reply is kept here, whole.

    python deepinfra_max_check.py <out_dir>        (the key from DEEPINFRA_API_KEY, makers_key.py run deepinfra)

Zero-Clause BSD.
"""
import datetime
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT = sys.argv[1]
URL = "https://api.deepinfra.com/v1/openai/chat/completions"
MODEL = "deepseek-ai/DeepSeek-V4-Pro-0813"
PROMPT = "Which whole numbers between 1 and 50 are prime? List them, and say how many there are."


def call(effort):
    body = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}], "reasoning_effort": effort}
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Authorization": "Bearer " + os.environ["DEEPINFRA_API_KEY"],
                                          "Content-Type": "application/json"})
    t0 = time.time()
    rec = {"sent_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "request_body": body}
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            rec["status"] = r.status
            rec["response"] = json.loads(r.read())
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        rec["error"] = e.read().decode("utf-8", "replace")
    rec["seconds"] = round(time.time() - t0, 2)
    resp = rec.get("response") or {}
    if resp:
        msg = resp["choices"][0]["message"]
        u = resp.get("usage") or {}
        rec["read"] = {"model_returned": resp.get("model"), "finish_reason": resp["choices"][0].get("finish_reason"),
                       "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                       "reasoning_chars": len(msg.get("reasoning_content") or msg.get("reasoning") or ""),
                       "answer": msg.get("content"), "usage": u}
    json.dump(rec, io.open(os.path.join(OUT, "deepinfra_%s.json" % effort), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print(effort, "| HTTP", rec["status"], "|", json.dumps(rec.get("read") or rec.get("error"), ensure_ascii=False)[:700])
    return rec


os.makedirs(OUT, exist_ok=True)
r = call("max")
ok = r["status"] == 200 and ((r.get("read") or {}).get("reasoning_tokens") or (r.get("read") or {}).get("reasoning_chars"))
if not ok:
    call("high")
