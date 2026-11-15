"""The desks' runner, through each maker's batch interface: the same AI, at the same settings as run.py, every
line of the suite sent at once, answered within a day, at the maker's batch price.

    python tests/runner/batch.py submit  --maker anthropic --model claude-fable-5-2 --run 1 \
        --suite tests/generated/tests.jsonl --suite held_out.jsonl \
        --approval APPROVAL.json --prices PRICES.json --dir BATCHES/ [--dry]
    python tests/runner/batch.py status  --dir BATCHES/
    python tests/runner/batch.py collect --dir BATCHES/ --maker anthropic --run 1 --out packets/NAME.jsonl
    python tests/runner/batch.py ledger  --dir BATCHES/

One batch is one run of the suite for one AI: run 1, then, only on a new approval, runs 2 and 3. The packet that
`collect` writes has the same lines as run.py's, so score.py reads it unchanged.

Nothing is sent without an approval file naming the batch, the makers, the interface, the ceiling for all the
makers together, and the last run it approves. Before a batch is sent, the runner adds what has already been spent
(the real cost of every collected batch) to the high estimate of every batch still out, and to this batch's high
estimate, at the maker's batch price; if that would pass the ceiling, nothing is sent. With --dry, the requests
are written and priced, and nothing is sent.

The key comes from the maker's usual environment variable (ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY),
which makers_key.py fills from the computer's credential store; it is never written to any file.

Settings: the maker's defaults, as run.py. Anthropic's interface requires max_tokens: 32,000, to cut nothing.
No fallback model is ever used.

Zero-Clause BSD.
"""
import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import ANTHROPIC_MAX_TOKENS, FLOOR_VERSION, cost, sha256  # noqa: E402

HIGH_OUTPUT_TOKENS = 9000     # the cost table's high figure for one answer (13 November 2026)
CHARS_PER_TOKEN = 3.0         # a cautious count of input tokens, before the maker's own


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load_lines(suites):
    lines = []
    for s in suites:
        lines += [json.loads(x) for x in io.open(s, encoding="utf-8") if x.strip()]
    return lines


def price_for(prices_path, model, today=None):
    price = dict(json.load(open(prices_path, encoding="utf-8"))[model])
    today = today or datetime.date.today().isoformat()
    for k in sorted(k for k in list(price) if k.startswith("from_")):      # a published change of price, by date
        if today >= k[5:]:
            price.update(price[k])
    mult = price.get("batch", {}).get("multiplier")
    if mult is None:
        raise SystemExit("the prices file gives no batch price for %s" % model)
    out = {"input": price["input"] * mult, "output": price["output"] * mult,
           "reasoning_separate": price.get("reasoning_separate", False)}
    return out


def high_estimate(lines, price, maker):
    tin = sum(sum(len(m["content"]) for m in ln["messages"]) for ln in lines) / CHARS_PER_TOKEN * 1.2
    per = min(HIGH_OUTPUT_TOKENS, ANTHROPIC_MAX_TOKENS) if maker == "anthropic" else HIGH_OUTPUT_TOKENS
    return cost({"input": tin, "output": per * len(lines)}, price)


def custom_ids(lines, run, part=None):
    return ["r%d%s-%04d" % (run, "-" + part if part else "", k) for k in range(len(lines))]       # every maker accepts [A-Za-z0-9_-]


def record_path(d, maker, run, part=None):
    return os.path.join(d, "%s-run%d%s.json" % (maker, run, "-" + part if part else ""))


def records(d):
    return [p for p in sorted(glob.glob(os.path.join(d, "*-run*.json")))
            if re.fullmatch(r"[a-z]+-run\d+(-[a-z0-9]+)?\.json", os.path.basename(p))]


def ledger(d):
    """What has been spent (collected batches, real cost) and what is still out (high estimates)."""
    spent, out = 0.0, 0.0
    rows = []
    for p in records(d):
        r = json.load(open(p, encoding="utf-8"))
        if r.get("dry"):
            continue
        if r.get("collected"):
            spent += r["collected"]["cost_usd"]
        else:
            out += r["estimate_high_usd"]
        rows.append((os.path.basename(p), r.get("status"), r["estimate_high_usd"],
                     r.get("collected", {}).get("cost_usd")))
    return spent, out, rows


# ---------------------------------------------------------------- submit
def submit_anthropic(model, lines, ids):
    import anthropic
    client = anthropic.Anthropic()
    reqs = [{"custom_id": cid, "params": {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS,
                                          "messages": ln["messages"]}} for cid, ln in zip(ids, lines)]
    b = client.messages.batches.create(requests=reqs)
    return {"batch_id": b.id, "status": b.processing_status}


def openai_jsonl(model, lines, ids):
    return "".join(json.dumps({"custom_id": cid, "method": "POST", "url": "/v1/responses",
                               "body": {"model": model, "input": ln["messages"]}}, ensure_ascii=False) + "\n"
                   for cid, ln in zip(ids, lines))


def submit_openai(model, lines, ids, d, name):
    import openai
    client = openai.OpenAI()
    path = os.path.join(d, name + ".requests.jsonl")
    io.open(path, "w", encoding="utf-8", newline="\n").write(openai_jsonl(model, lines, ids))
    f = client.files.create(file=open(path, "rb"), purpose="batch")
    b = client.batches.create(input_file_id=f.id, endpoint="/v1/responses", completion_window="24h")
    return {"batch_id": b.id, "status": b.status, "input_file_id": f.id}


def google_requests(lines, ids):
    out = []
    for cid, ln in zip(ids, lines):
        contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                    for m in ln["messages"]]
        out.append({"contents": contents, "metadata": {"custom_id": cid}})
    return out


def submit_google(model, lines, ids, name):
    from google import genai
    client = genai.Client()
    b = client.batches.create(model=model, src=google_requests(lines, ids), config={"display_name": name})
    return {"batch_id": b.name, "status": str(b.state)}


# ---------------------------------------------------------------- results, as run.py's answer lines
def results_anthropic(batch_id):
    import anthropic
    client = anthropic.Anthropic()
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        return b.processing_status, None
    out = {}
    for r in client.messages.batches.results(batch_id):
        if r.result.type == "succeeded":
            m = r.result.message
            out[r.custom_id] = {"answer": "".join(x.text for x in m.content if getattr(x, "type", "") == "text"),
                                "model_returned": m.model, "stop_reason": m.stop_reason,
                                "usage": {"input": m.usage.input_tokens, "output": m.usage.output_tokens}}
        else:
            out[r.custom_id] = {"answer": None, "error": "%s: %s" % (r.result.type, getattr(r.result, "error", ""))}
    return "ended", out


def parse_openai_output(text):
    out = {}
    for x in text.splitlines():
        if not x.strip():
            continue
        r = json.loads(x)
        resp = r.get("response") or {}
        body = resp.get("body") or {}
        if r.get("error") or resp.get("status_code") != 200:
            out[r["custom_id"]] = {"answer": None, "error": json.dumps(r.get("error") or body.get("error"))[:500]}
            continue
        texts = [c.get("text", "") for item in body.get("output", []) if item.get("type") == "message"
                 for c in item.get("content", []) if c.get("type") == "output_text"]
        u = body.get("usage") or {}
        out[r["custom_id"]] = {"answer": "".join(texts), "model_returned": body.get("model"),
                               "stop_reason": body.get("status"),
                               "usage": {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
                                         "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens")}}
    return out


def results_openai(batch_id):
    import openai
    client = openai.OpenAI()
    b = client.batches.retrieve(batch_id)
    if b.status not in ("completed", "failed", "expired", "cancelled"):
        return b.status, None
    out = {}
    for fid in (b.output_file_id, b.error_file_id):
        if fid:
            out.update(parse_openai_output(client.files.content(fid).text))
    return b.status, out


def parse_google_responses(responses, model):
    out = {}
    for r in responses:
        cid = (r.metadata or {}).get("custom_id")
        if r.error is not None or r.response is None:
            out[cid] = {"answer": None, "error": str(r.error)[:500]}
            continue
        g = r.response
        u = g.usage_metadata
        out[cid] = {"answer": g.text or "", "model_returned": getattr(g, "model_version", None) or model,
                    "stop_reason": str(g.candidates[0].finish_reason) if g.candidates else None,
                    "usage": {"input": u.prompt_token_count, "output": u.candidates_token_count or 0,
                              "reasoning": getattr(u, "thoughts_token_count", None)}}
    return out


def results_google(batch_id, model):
    from google import genai
    client = genai.Client()
    b = client.batches.get(name=batch_id)
    state = b.state.name if hasattr(b.state, "name") else str(b.state)
    if state not in ("JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"):
        return state, None
    return state, parse_google_responses(b.dest.inlined_responses or [], model)


# ---------------------------------------------------------------- commands
def cmd_submit(a):
    lines = load_lines(a.suite)
    os.makedirs(a.dir, exist_ok=True)
    if not a.approval or not os.path.exists(a.approval):
        raise SystemExit("no approval file: nothing is sent to any AI until G approves the batch's cost")
    ok = json.load(open(a.approval, encoding="utf-8"))
    for key in ("approved_by", "date", "words", "ceiling_usd_total", "makers", "interface", "last_run_approved"):
        if not ok.get(key):
            raise SystemExit("the approval file has no %r" % key)
    if ok["interface"] != "batch":
        raise SystemExit("the approval is not for the batch interface")
    if a.maker not in ok["makers"] or ok["makers"][a.maker].get("model") != a.model:
        raise SystemExit("the approval file does not approve %s %s" % (a.maker, a.model))
    if a.run > int(ok["last_run_approved"]):
        raise SystemExit("run %d is not approved: the approval stops after run %s, for the real tokens and cost "
                         "to be reported first" % (a.run, ok["last_run_approved"]))
    rp = record_path(a.dir, a.maker, a.run, a.part)
    if os.path.exists(rp) and not json.load(open(rp, encoding="utf-8")).get("dry"):
        raise SystemExit("%s was already sent: %s" % (os.path.basename(rp), rp))
    price = price_for(a.prices, a.model)
    est = high_estimate(lines, price, a.maker)
    spent, out, _ = ledger(a.dir)
    total = spent + out + est
    ceiling = float(ok["ceiling_usd_total"])
    name = "%s-run%d%s" % (a.maker, a.run, "-" + a.part if a.part else "")
    ids = custom_ids(lines, a.run, a.part)
    rec = {"maker": a.maker, "model": a.model, "run": a.run, "lines": len(lines), "custom_ids": dict(zip(ids,
           [ln["id"] for ln in lines])), "suite_sha256": {os.path.basename(s): sha256(s) for s in a.suite},
           "price_batch_per_million": price, "estimate_high_usd": round(est, 4),
           "ledger_before": {"spent_usd": round(spent, 4), "out_high_usd": round(out, 4)},
           "ceiling_usd_total": ceiling, "approval": {k: ok[k] for k in ("approved_by", "date", "words")},
           "settings": {"max_tokens": ANTHROPIC_MAX_TOKENS} if a.maker == "anthropic" else
                       {"everything": "the maker's defaults"}, "interface": "batch"}
    if total > ceiling + 1e-9:
        raise SystemExit("not sent: spent $%.2f + out $%.2f + this batch's high $%.2f = $%.2f, over the ceiling $%.2f"
                         % (spent, out, est, total, ceiling))
    if a.dry:
        rec.update(dry=True, status="dry: nothing sent", at=now())
        if a.maker == "openai":
            io.open(os.path.join(a.dir, name + ".requests.jsonl"), "w", encoding="utf-8",
                    newline="\n").write(openai_jsonl(a.model, lines, ids))
        elif a.maker == "google":
            json.dump(google_requests(lines, ids), io.open(os.path.join(a.dir, name + ".requests.json"), "w",
                                                           encoding="utf-8"), ensure_ascii=False)
        else:
            json.dump([{"custom_id": c, "params": {"model": a.model, "max_tokens": ANTHROPIC_MAX_TOKENS,
                                                   "messages": ln["messages"]}} for c, ln in zip(ids, lines)],
                      io.open(os.path.join(a.dir, name + ".requests.json"), "w", encoding="utf-8"), ensure_ascii=False)
    else:
        if a.maker == "anthropic":
            rec.update(submit_anthropic(a.model, lines, ids))
        elif a.maker == "openai":
            rec.update(submit_openai(a.model, lines, ids, a.dir, name))
        else:
            rec.update(submit_google(a.model, lines, ids, name))
        rec["sent_at"] = now()
    json.dump(rec, io.open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s %s: %d lines, high estimate $%.2f at batch prices; ledger after: $%.2f of $%.2f%s" % (
        "dry" if a.dry else "sent", name, len(lines), est, total, ceiling,
        "" if a.dry else "; batch " + rec["batch_id"]))


def cmd_status(a):
    for p in records(a.dir):
        r = json.load(open(p, encoding="utf-8"))
        if r.get("dry") or r.get("collected"):
            print(os.path.basename(p), r.get("status"), "collected" if r.get("collected") else "")
            continue
        st, _ = {"anthropic": lambda: results_anthropic(r["batch_id"]), "openai": lambda: results_openai(r["batch_id"]),
                 "google": lambda: results_google(r["batch_id"], r["model"])}[r["maker"]]()
        print(os.path.basename(p), st)


def cmd_collect(a):
    rp = record_path(a.dir, a.maker, a.run, a.part)
    r = json.load(open(rp, encoding="utf-8"))
    if r.get("dry"):
        raise SystemExit("a dry batch has nothing to collect")
    st, res = {"anthropic": lambda: results_anthropic(r["batch_id"]), "openai": lambda: results_openai(r["batch_id"]),
               "google": lambda: results_google(r["batch_id"], r["model"])}[r["maker"]]()
    if res is None:
        raise SystemExit("not finished yet: %s" % st)
    lines = {ln["id"]: ln for ln in load_lines(a.suite)}
    spent, n_err, tok = 0.0, 0, {"input": 0, "output": 0, "reasoning": 0}
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"kind": "head", "maker": r["maker"], "model_requested": r["model"], "settings": r["settings"],
                            "interface": "the maker's batch interface", "batch_id": r["batch_id"],
                            "date": r["sent_at"][:10], "runs": 3, "this_run": r["run"],
                            "versions": {"floor": FLOOR_VERSION, "suite_sha256": r["suite_sha256"]},
                            "label": "the desks' own run"}, ensure_ascii=False) + "\n")
        for cid, line_id in r["custom_ids"].items():
            ln = lines[line_id]
            x = res.get(cid, {"answer": None, "error": "no result returned"})
            x.update(kind="answer", id=line_id, item=ln["item"], test=ln["test"], text=ln["text"], wording=ln["wording"],
                     held_out=ln.get("held_out", False), run=r["run"], sent=ln["messages"], seconds=None,
                     at=r["sent_at"])
            if x.get("usage"):
                spent += cost(x["usage"], r["price_batch_per_million"])
                for k in tok:
                    tok[k] += x["usage"].get(k) or 0
            n_err += x.get("answer") is None
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    r["status"] = st
    r["collected"] = {"at": now(), "packet": os.path.abspath(a.out), "packet_sha256": sha256(a.out),
                      "answers": len(r["custom_ids"]) - n_err, "errors": n_err, "tokens": tok,
                      "cost_usd": round(spent, 4)}
    json.dump(r, io.open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("collected %s-run%d: %d answers, %d errors; tokens in %d, out %d (thinking reported apart: %d); "
          "cost at batch prices $%.2f" % (r["maker"], r["run"], len(r["custom_ids"]) - n_err, n_err, tok["input"],
                                          tok["output"], tok["reasoning"], spent))


def cmd_ledger(a):
    spent, out, rows = ledger(a.dir)
    for row in rows:
        print("%-22s %-20s high $%8.2f   real %s" % (row[0], row[1], row[2], "$%.2f" % row[3] if row[3] is not None
                                                     else "-"))
    print("spent $%.2f; still out (high) $%.2f" % (spent, out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--maker", required=True, choices=["anthropic", "openai", "google"])
    s.add_argument("--model", required=True)
    s.add_argument("--run", type=int, required=True)
    s.add_argument("--part", help="a part of a run sent apart, such as a changed item's new texts")
    s.add_argument("--suite", action="append", required=True)
    s.add_argument("--approval", required=True)
    s.add_argument("--prices", required=True)
    s.add_argument("--dir", required=True)
    s.add_argument("--dry", action="store_true")
    st = sub.add_parser("status")
    st.add_argument("--dir", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--dir", required=True)
    c.add_argument("--maker", required=True)
    c.add_argument("--run", type=int, required=True)
    c.add_argument("--part")
    c.add_argument("--suite", action="append", required=True)
    c.add_argument("--out", required=True)
    lg = sub.add_parser("ledger")
    lg.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"submit": cmd_submit, "status": cmd_status, "collect": cmd_collect, "ledger": cmd_ledger}[a.cmd](a)


if __name__ == "__main__":
    main()
