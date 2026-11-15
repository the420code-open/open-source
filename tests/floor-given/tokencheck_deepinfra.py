"""The floor-given run's first DeepInfra question: does the host add anything to what it is sent?

One published item, sent alone to DeepInfra as the run's "as shipped" column would send it: no system message, no
reasoning level, no answer length, at DeepInfra's defaults. The prompt tokens DeepInfra reports are set beside a
local count made with DeepSeek's own encoding script (encoding/encoding_dsv4.py) and tokenizer (tokenizer.json),
from the model's Hugging Face repository at the commit named below. The encoding adds only what its template says:
the start token, the turn markers, the opening of the thinking block, and in thinking mode a fixed prefix for a
"high" or "max" reasoning effort. If DeepInfra's count equals one of those exactly, nothing else was added.

    python tests/floor-given/tokencheck_deepinfra.py send  --line ID --out DIR      (sends one question)
    python -I tests/floor-given/tokencheck_deepinfra.py count --encoding DIR --out DIR (sends nothing)

The key comes from DEEPINFRA_API_KEY (makers_key.py run deepinfra), and is never written anywhere.

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
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
SUITE = os.path.join(REPO, "tests", "generated", "tests.jsonl")
MODEL = "deepseek-ai/DeepSeek-V4-Pro-0813"
HF_REVISION = "72e1d3230f6c080a530b0a1d46f8eb4602340597"
URL = "https://api.deepinfra.com/v1/openai/chat/completions"


def send(a):
    line = next(json.loads(x) for x in io.open(SUITE, encoding="utf-8") if json.loads(x)["id"] == a.line)
    assert not line.get("held_out"), "the check uses a published item only"
    body = {"model": MODEL, "messages": line["messages"]}         # nothing else: DeepInfra's defaults
    t0 = time.time()
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Authorization": "Bearer " + os.environ["DEEPINFRA_API_KEY"],
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        raw = r.read()
        headers = {k: v for k, v in r.headers.items() if k.lower().startswith(("x-", "content-type"))}
    os.makedirs(a.out, exist_ok=True)
    resp = json.loads(raw)
    rec = {"sent_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "seconds": round(time.time() - t0, 2), "line": line["id"], "request_body": body,
           "suite_sha256": hashlib.sha256(open(SUITE, "rb").read()).hexdigest(),
           "response_headers": headers, "response": resp}
    json.dump(rec, io.open(os.path.join(a.out, "deepinfra_response.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    u = resp.get("usage") or {}
    print("sent", line["id"], "| model returned", resp.get("model"), "| finish", resp["choices"][0].get("finish_reason"),
          "| usage", json.dumps(u))


def count(a):
    sys.path.insert(0, os.path.join(a.encoding, "encoding"))
    import encoding_dsv4 as E                                   # DeepSeek's own script, read before it was run
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(a.encoding, "tokenizer.json"))
    rec = json.load(io.open(os.path.join(a.out, "deepinfra_response.json"), encoding="utf-8"))
    msgs = rec["request_body"]["messages"]
    reported = (rec["response"].get("usage") or {}).get("prompt_tokens")
    rows = []
    for mode, effort in (("chat", None), ("thinking", "low"), ("thinking", "high"), ("thinking", "max")):
        prompt = E.encode_messages(msgs, thinking_mode=mode, reasoning_effort=effort)
        n = len(tok.encode(prompt, add_special_tokens=False).ids)
        rows.append({"thinking_mode": mode, "reasoning_effort": effort, "local_tokens": n,
                     "equals_deepinfra": n == reported, "prompt_head": prompt[:120], "prompt_tail": prompt[-60:]})
    files = {}
    for f in ("encoding/encoding_dsv4.py", "encoding/README.md", "tokenizer.json", "tokenizer_config.json"):
        files[f] = hashlib.sha256(open(os.path.join(a.encoding, f), "rb").read()).hexdigest()
    out = {"model": MODEL, "huggingface_revision": HF_REVISION, "files_sha256": files, "deepinfra_prompt_tokens": reported,
           "local_counts": rows, "match": [r for r in rows if r["equals_deepinfra"]]}
    json.dump(out, io.open(os.path.join(a.out, "token_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in rows:
        print("%-9s %-5s local %6d  %s" % (r["thinking_mode"], r["reasoning_effort"], r["local_tokens"],
                                          "= DeepInfra" if r["equals_deepinfra"] else "(DeepInfra %s)" % reported))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["send", "count"])
    ap.add_argument("--line", default="T1.1/situation/original")
    ap.add_argument("--encoding")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    {"send": send, "count": count}[a.cmd](a)


if __name__ == "__main__":
    main()
