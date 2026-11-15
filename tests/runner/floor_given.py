"""Phase 2, the floor given: every line of both suites, three runs, in three columns, for six AIs, as the plan of
record says (tests/floor-given/plan.md, tagged floor-given-plan-v1, before any question is sent).

    python tests/runner/floor_given.py dry     --dir DIR [--maker M]          writes and prices every request; sends nothing
    python tests/runner/floor_given.py submit  --dir DIR --maker M --column C batch makers: one batch per column
    python tests/runner/floor_given.py sync    --dir DIR --maker M [--concurrency N]   one call per answer
    python tests/runner/floor_given.py status  --dir DIR
    python tests/runner/floor_given.py collect --dir DIR --maker M --column C
    python tests/runner/floor_given.py ledger  --dir DIR

The three columns (plan, section 4):
    as_shipped         no system message
    short_instruction  tests/floor-given/control.txt, word for word, as the system message, with no wrapper
    floor              floor/generated/floor.txt, version 1.0, byte for byte, as the system message, with no wrapper
then the situation exactly as the baseline sent it. Each text's SHA-256 is checked against tests/floor-given/run.json
before anything is written or sent, and recorded with every answer.

Routes (plan, section 5): Anthropic, OpenAI, Google and Mistral through their batch services; Meta and DeepInfra
(DeepSeek's open weights) one call per answer through the standard interface, a few at a time, never a batch.
Prompt caching only where it changes the price and not what the AI reads: Anthropic's floor text is marked for its
cache; OpenAI, Google, Meta, Mistral and DeepInfra cache a repeated prefix on their own.

Settings: each maker's defaults. Anthropic's interface requires max_tokens: 32,000, as the baseline. Nothing else is
set: no reasoning level, no answer length, no temperature. No fallback model is ever used.

Ceilings (tests/floor-given/approval.json): one for each maker, together no more than G's approved cap. A batch is
sent only if what that maker has spent, plus the high estimate of its batches still out, plus this batch's high
estimate, stays within its ceiling. A one-call maker stops before its real spend passes its ceiling.

Retries: only where no answer came back (a refused connection, a rate limit, a server error), up to five times, each
attempt recorded. An answer that came back is never asked again.

Keys come from each maker's usual environment variable (makers_key.py run <maker> -- ...); none is ever written.

Zero-Clause BSD.
"""
import argparse
import concurrent.futures
import datetime
import glob
import hashlib
import io
import json
import os
import random
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
CONFIG = os.path.join(REPO, "tests", "floor-given", "run.json")
APPROVAL = os.path.join(REPO, "tests", "floor-given", "approval.json")
ANTHROPIC_MAX_TOKENS = 32000
COLUMNS = ("as_shipped", "short_instruction", "floor")
CODE = {"as_shipped": "s", "short_instruction": "i", "floor": "f"}
BATCH = ("anthropic", "openai", "google", "mistral")
ONE_CALL = ("meta", "deepinfra")
PLAN_TAG = "floor-given-plan-v1"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(open(p, "rb").read())


def jl(p):
    return [json.loads(x) for x in io.open(p, encoding="utf-8") if x.strip()] if os.path.exists(p) else []


# ---------------------------------------------------------------- the run's fixed parts, checked every time
def load_config():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    texts = {}
    for col in COLUMNS:
        c = cfg["columns"][col]
        if c.get("file") is None:
            texts[col] = None
            continue
        raw = open(os.path.join(REPO, c["file"]), "rb").read()
        if sha256_bytes(raw) != c["sha256"]:
            raise SystemExit("%s is not the text of record: %s" % (col, c["file"]))
        texts[col] = raw.decode("utf-8")
    lines = []
    for s in cfg["suites"]:
        p = os.path.join(REPO, s["file"])
        if sha256_file(p) != s["sha256"]:
            raise SystemExit("the suite is not the one of record: %s" % s["file"])
        lines += jl(p)
    if len(lines) != cfg["lines"]:
        raise SystemExit("expected %d lines, found %d" % (cfg["lines"], len(lines)))
    return cfg, texts, lines


def units(cfg, lines):
    """Every question one AI is asked: (column, run, k, line), interleaved so that a stop leaves the columns even."""
    out = []
    for run in range(1, cfg["runs"] + 1):
        for k, ln in enumerate(lines):
            for col in COLUMNS:
                out.append((col, run, k, ln))
    return out


def cid(col, run, k):
    return "%s-r%d-%03d" % (CODE[col], run, k)


def plan_tagged():
    r = subprocess.run(["git", "-C", REPO, "rev-parse", "-q", "--verify", "refs/tags/" + PLAN_TAG],
                       capture_output=True, text=True)
    return r.returncode == 0


def approval_for(maker):
    if not os.path.exists(APPROVAL):
        raise SystemExit("no approval file: nothing is sent to any AI until G approves the cost")
    ok = json.load(open(APPROVAL, encoding="utf-8"))
    for key in ("approved_by", "date", "words", "cap_usd_makers", "makers"):
        if not ok.get(key):
            raise SystemExit("the approval file has no %r" % key)
    if maker not in ok["makers"]:
        raise SystemExit("the approval file does not approve %s" % maker)
    if sum(float(m["ceiling_usd"]) for m in ok["makers"].values()) > float(ok["cap_usd_makers"]) + 1e-9:
        raise SystemExit("the makers' ceilings add up to more than the approved cap")
    return ok, float(ok["makers"][maker]["ceiling_usd"])


# ---------------------------------------------------------------- what each maker is sent
def messages_with(system, messages, role="system"):
    return ([{"role": role, "content": system}] if system is not None else []) + list(messages)


def anthropic_params(model, system, col, messages):
    p = {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS, "messages": messages}
    if system is not None:
        p["system"] = ([{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}] if col == "floor"
                       else system)
    return p


def openai_body(model, system, messages):
    return {"model": model, "input": messages_with(system, messages)}


def google_request(system, messages, custom_id):
    r = {"contents": [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                      for m in messages], "metadata": {"custom_id": custom_id}}
    if system is not None:
        r["config"] = {"system_instruction": {"parts": [{"text": system}]}}
    return r


def chat_body(model, system, messages, with_model=True):
    b = {"messages": messages_with(system, messages)}
    if with_model:
        b["model"] = model
    return b


# ---------------------------------------------------------------- prices and estimates
def prices(cfg):
    return json.load(open(os.path.join(REPO, cfg["prices"]), encoding="utf-8"))


def price_of(cfg, maker, batch, today=None):
    p = dict(prices(cfg)[cfg["makers"][maker]["model"]])
    today = today or datetime.date.today().isoformat()
    for k in sorted(k for k in list(p) if k.startswith("from_")):
        if today >= k[5:]:
            p.update(p[k])
    m = p.get("batch", {}).get("multiplier", 1.0) if batch else 1.0
    return {"input": p["input"] * m, "output": p["output"] * m, "cached_input": p.get("cached_input", p["input"]) * m,
            "reasoning_separate": p.get("reasoning_separate", False)}


def cost(usage, price):
    """US dollars for one answer, at the price given. Reasoning is added to the output only where the maker reports it
    outside its output count (reasoning_separate). Cached input, where reported, at the cached price."""
    cached = usage.get("cached_input") or 0
    written = usage.get("cache_written") or 0           # Anthropic bills a cache write at 1.25 times the input price
    inp = (usage.get("input") or 0) - cached
    out = (usage.get("output") or 0) + ((usage.get("reasoning") or 0) if price.get("reasoning_separate") else 0)
    return (inp / 1e6 * price["input"] + written / 1e6 * price["input"] * 0.25 + cached / 1e6 * price["cached_input"]
            + out / 1e6 * price["output"])


def baseline_stats(cfg, maker):
    """The first batch's own tokens for this maker: per line, its mean input; overall, its mean answer, thinking
    included where the maker reports it apart."""
    base = cfg["makers"][maker].get("baseline")
    if not base:
        return None
    sep = prices(cfg)[cfg["makers"][maker]["model"]].get("reasoning_separate", False)
    per, outs = {}, []
    for p in sorted(glob.glob(os.path.join(REPO, base, "packet-%s-run*.jsonl" % maker))):
        for r in jl(p)[1:]:
            u = r.get("usage") or {}
            if r.get("answer") is None or not u:
                continue
            per.setdefault(r["id"], []).append(u.get("input") or 0)
            outs.append((u.get("output") or 0) + ((u.get("reasoning") or 0) if sep else 0))
    return {"input": {k: statistics.fmean(v) for k, v in per.items()}, "answer": statistics.fmean(outs)}


def estimate(cfg, texts, lines, maker, col, case):
    """The plan's section 9, as WC's cost report worked it out: central from the baseline's own counts; high with the
    first batch's answers twice as long, Google at its standard price, the floor at Anthropic's tokens per character,
    and the second batch at 9,000 tokens an answer at standard prices."""
    est = cfg["estimate"]
    st = baseline_stats(cfg, maker)
    first = st is not None
    batch = maker in BATCH and not (case == "high" and (maker == "google" or not first))
    price = price_of(cfg, maker, batch)
    add = 0
    if col == "short_instruction":
        add = est["short_instruction_tokens"]
    elif col == "floor":
        tpc = est["floor_tokens"]["anthropic"] if case == "high" else est["floor_tokens"].get(maker, est["floor_tokens"]["second_batch"])
        add = tpc
    tin = tout = 0.0
    for ln in lines:
        if first and ln["id"] in st["input"]:
            q_in = st["input"][ln["id"]]
        else:
            q_in = sum(len(m["content"]) for m in ln["messages"]) / est["chars_per_token_second_batch"]
        tin += (q_in + add) * cfg["runs"]
        if first:
            ans = st["answer"] * (2 if case == "high" else 1)
        else:
            ans = est["second_batch_answer_tokens"][case]
        tout += ans * cfg["runs"]
    usd = tin / 1e6 * price["input"] + tout / 1e6 * price["output"]
    return {"input_tokens": round(tin), "output_tokens": round(tout), "usd": round(usd, 4), "price": price,
            "batch_price": batch}


# ---------------------------------------------------------------- records
def record_path(d, maker, col):
    return os.path.join(d, "%s-%s.json" % (maker, col))


def packet_path(d, maker, col=None):
    return os.path.join(d, "packet-%s%s.jsonl" % (maker, "-" + col if col else ""))


def head_line(cfg, maker, route, col=None, extra=None):
    h = {"kind": "head", "run": "the floor given", "plan_tag": PLAN_TAG, "maker": maker,
         "model_requested": cfg["makers"][maker]["model"], "route": route, "runs": cfg["runs"],
         "columns": {c: {"file": cfg["columns"][c].get("file"), "sha256": cfg["columns"][c].get("sha256")} for c in COLUMNS},
         "suites": cfg["suites"], "tests": cfg["tests_tag"], "settings": cfg["makers"][maker]["settings"],
         "label": "the desks' own run"}
    if col:
        h["column"] = col
    h.update(extra or {})
    return h


def answer_line(r, col, run, k, ln, system):
    r.update(kind="answer", custom_id=cid(col, run, k), column=col,
             system_sha256=sha256_bytes(system.encode("utf-8")) if system is not None else None,
             id=ln["id"], item=ln["item"], test=ln["test"], text=ln["text"], wording=ln["wording"],
             held_out=ln.get("held_out", False), run=run, sent=ln["messages"])
    return r


def ledger(d, cfg):
    rows, by = [], {}
    for maker in BATCH:
        for col in COLUMNS:
            p = record_path(d, maker, col)
            if not os.path.exists(p):
                continue
            r = json.load(open(p, encoding="utf-8"))
            if r.get("dry"):
                continue
            real = (r.get("collected") or {}).get("cost_usd")
            by.setdefault(maker, {"spent": 0.0, "out_high": 0.0})
            if real is not None:
                by[maker]["spent"] += real
            else:
                by[maker]["out_high"] += r["estimate_high_usd"]
            rows.append((maker, col, r.get("status"), r["estimate_high_usd"], real))
    for maker in ONE_CALL:
        p = packet_path(d, maker)
        if os.path.exists(p):
            price = price_of(cfg, maker, False)
            spent = sum(cost(x["usage"], price) for x in jl(p)[1:] if x.get("usage"))
            by[maker] = {"spent": spent, "out_high": 0.0}
            rows.append((maker, "all", "one call each", None, spent))
    return by, rows


# ---------------------------------------------------------------- the batch makers
def mistral_call(method, path, body=None, files=None):
    key = os.environ["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai" + path
    if files:
        boundary = "----floorgiven%d" % random.randint(1, 1 << 30)
        parts = []
        for name, (fname, data, ctype) in files.items():
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                          % (boundary, name, fname, ctype)).encode() + data + b"\r\n")
        for name, val in (body or {}).items():
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode())
        data = b"".join(parts) + ("--%s--\r\n" % boundary).encode()
        headers = {"Authorization": "Bearer " + key, "Content-Type": "multipart/form-data; boundary=" + boundary}
    else:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=600) as r:
        raw = r.read()
        return json.loads(raw) if raw[:1] in (b"{", b"[") else raw


def batch_requests(cfg, texts, lines, maker, col):
    model = cfg["makers"][maker]["model"]
    sys_text = texts[col]
    out = []
    for run in range(1, cfg["runs"] + 1):
        for k, ln in enumerate(lines):
            c = cid(col, run, k)
            if maker == "anthropic":
                out.append({"custom_id": c, "params": anthropic_params(model, sys_text, col, ln["messages"])})
            elif maker == "openai":
                out.append({"custom_id": c, "method": "POST", "url": "/v1/responses",
                            "body": openai_body(model, sys_text, ln["messages"])})
            elif maker == "google":
                out.append(google_request(sys_text, ln["messages"], c))
            else:
                out.append({"custom_id": c, "body": chat_body(model, sys_text, ln["messages"], with_model=False)})
    return out


def send_batch(maker, model, reqs, d, name):
    if maker == "anthropic":
        import anthropic
        b = anthropic.Anthropic().messages.batches.create(requests=reqs)
        return {"batch_id": b.id, "status": b.processing_status}
    if maker == "openai":
        import openai
        client = openai.OpenAI()
        path = os.path.join(d, name + ".requests.jsonl")
        f = client.files.create(file=open(path, "rb"), purpose="batch")
        b = client.batches.create(input_file_id=f.id, endpoint="/v1/responses", completion_window="24h")
        return {"batch_id": b.id, "status": b.status, "input_file_id": f.id}
    if maker == "google":
        from google import genai
        b = genai.Client().batches.create(model=model, src=reqs, config={"display_name": name})
        return {"batch_id": b.name, "status": str(b.state)}
    path = os.path.join(d, name + ".requests.jsonl")
    up = mistral_call("POST", "/v1/files", body={"purpose": "batch"},
                      files={"file": (os.path.basename(path), open(path, "rb").read(), "application/jsonl")})
    job = mistral_call("POST", "/v1/batch/jobs", {"input_files": [up["id"]], "model": model,
                                                   "endpoint": "/v1/chat/completions",
                                                   "metadata": {"run": "the floor given", "batch": name}})
    return {"batch_id": job["id"], "status": job.get("status"), "input_file_id": up["id"]}


def write_requests(maker, reqs, d, name):
    if maker in ("openai", "mistral"):
        p = os.path.join(d, name + ".requests.jsonl")
        io.open(p, "w", encoding="utf-8", newline="\n").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs))
    else:
        p = os.path.join(d, name + ".requests.json")
        json.dump(reqs, io.open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return p


def cmd_dry(a):
    cfg, texts, lines = load_config()
    os.makedirs(a.dir, exist_ok=True)
    table = {}
    for maker in ([a.maker] if a.maker else list(cfg["makers"])):
        table[maker] = {}
        for col in COLUMNS:
            c = estimate(cfg, texts, lines, maker, col, "central")
            h = estimate(cfg, texts, lines, maker, col, "high")
            name = "%s-%s" % (maker, col)
            if maker in BATCH:
                reqs = batch_requests(cfg, texts, lines, maker, col)
            else:
                model = cfg["makers"][maker]["model"]
                reqs = [{"custom_id": cid(col, run, k), "body": chat_body(model, texts[col], ln["messages"])}
                        for run in range(1, cfg["runs"] + 1) for k, ln in enumerate(lines)]
            p = write_requests(maker, reqs, a.dir, name + ".dry")
            table[maker][col] = {"requests": len(reqs), "central_usd": c["usd"], "high_usd": h["usd"],
                                 "central_tokens": [c["input_tokens"], c["output_tokens"]],
                                 "high_tokens": [h["input_tokens"], h["output_tokens"]],
                                 "requests_file_sha256": sha256_file(p)}
    tot_c = sum(v["central_usd"] for m in table.values() for v in m.values())
    tot_h = sum(v["high_usd"] for m in table.values() for v in m.values())
    out = {"at": now(), "dry": True, "sent": "nothing", "table": table, "central_usd": round(tot_c, 2),
           "high_usd": round(tot_h, 2)}
    json.dump(out, io.open(os.path.join(a.dir, "dry.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for maker, cols in table.items():
        print("%-10s %s | three columns: central $%.2f, high $%.2f" % (
            maker, "  ".join("%s %d req $%.2f/$%.2f" % (c, v["requests"], v["central_usd"], v["high_usd"])
                             for c, v in cols.items()),
            sum(v["central_usd"] for v in cols.values()), sum(v["high_usd"] for v in cols.values())))
    print("all: central $%.2f, high $%.2f; nothing sent" % (tot_c, tot_h))


def cmd_submit(a):
    if a.maker not in BATCH:
        raise SystemExit("%s has no batch service in this run: use sync" % a.maker)
    if not plan_tagged():
        raise SystemExit("the plan is not tagged %s: nothing is sent before it is" % PLAN_TAG)
    cfg, texts, lines = load_config()
    ok, ceiling = approval_for(a.maker)
    os.makedirs(a.dir, exist_ok=True)
    rp = record_path(a.dir, a.maker, a.column)
    if os.path.exists(rp):
        raise SystemExit("%s was already sent" % os.path.basename(rp))
    hi = estimate(cfg, texts, lines, a.maker, a.column, "high")
    by, _ = ledger(a.dir, cfg)
    m = by.get(a.maker, {"spent": 0.0, "out_high": 0.0})
    total = m["spent"] + m["out_high"] + hi["usd"]
    if total > ceiling + 1e-9:
        raise SystemExit("not sent: %s spent $%.2f + out $%.2f + this batch's high $%.2f = $%.2f, over its ceiling $%.2f"
                         % (a.maker, m["spent"], m["out_high"], hi["usd"], total, ceiling))
    name = "%s-%s" % (a.maker, a.column)
    model = cfg["makers"][a.maker]["model"]
    reqs = batch_requests(cfg, texts, lines, a.maker, a.column)
    p = write_requests(a.maker, reqs, a.dir, name)
    ids = {cid(a.column, run, k): ln["id"] for run in range(1, cfg["runs"] + 1) for k, ln in enumerate(lines)}
    rec = {"maker": a.maker, "model": model, "column": a.column, "requests": len(reqs), "custom_ids": ids,
           "requests_file": os.path.basename(p), "requests_sha256": sha256_file(p),
           "system_sha256": cfg["columns"][a.column].get("sha256"), "estimate_high_usd": round(hi["usd"], 4),
           "price_per_million": hi["price"], "ceiling_usd": ceiling,
           "ledger_before": {"spent_usd": round(m["spent"], 4), "out_high_usd": round(m["out_high"], 4)},
           "approval": {k: ok[k] for k in ("approved_by", "date", "words")}, "route": "batch"}
    rec.update(send_batch(a.maker, model, reqs, a.dir, name))
    rec["sent_at"] = now()
    json.dump(rec, io.open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("sent %s: %d requests, high $%.2f; %s's ledger $%.2f of $%.2f; batch %s" % (
        name, len(reqs), hi["usd"], a.maker, total, ceiling, rec["batch_id"]))


def results(maker, rec):
    """(status, {custom_id: answer fields}) once a batch has ended; (status, None) before."""
    if maker == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        b = client.messages.batches.retrieve(rec["batch_id"])
        if b.processing_status != "ended":
            return b.processing_status, None
        out = {}
        for r in client.messages.batches.results(rec["batch_id"]):
            if r.result.type == "succeeded":
                msg = r.result.message
                u = msg.usage
                out[r.custom_id] = {"answer": "".join(x.text for x in msg.content if getattr(x, "type", "") == "text"),
                                    "model_returned": msg.model, "stop_reason": msg.stop_reason,
                                    "usage": {"input": (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0)
                                              + (getattr(u, "cache_creation_input_tokens", 0) or 0),
                                              "cached_input": getattr(u, "cache_read_input_tokens", 0) or 0,
                                              "cache_written": getattr(u, "cache_creation_input_tokens", 0) or 0,
                                              "output": u.output_tokens}}
            else:
                out[r.custom_id] = {"answer": None, "error": "%s: %s" % (r.result.type, getattr(r.result, "error", ""))}
        return "ended", out
    if maker == "openai":
        import openai
        client = openai.OpenAI()
        b = client.batches.retrieve(rec["batch_id"])
        if b.status not in ("completed", "failed", "expired", "cancelled"):
            return b.status, None
        out = {}
        for fid in (b.output_file_id, b.error_file_id):
            if not fid:
                continue
            for x in client.files.content(fid).text.splitlines():
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
                                       "usage": {"input": u.get("input_tokens"),
                                                 "cached_input": (u.get("input_tokens_details") or {}).get("cached_tokens"),
                                                 "output": u.get("output_tokens"),
                                                 "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens")}}
        return b.status, out
    if maker == "google":
        from google import genai
        b = genai.Client().batches.get(name=rec["batch_id"])
        state = b.state.name if hasattr(b.state, "name") else str(b.state)
        if state not in ("JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"):
            return state, None
        out = {}
        for r in b.dest.inlined_responses or []:
            c = (r.metadata or {}).get("custom_id")
            if r.error is not None or r.response is None:
                out[c] = {"answer": None, "error": str(r.error)[:500]}
                continue
            g = r.response
            u = g.usage_metadata
            out[c] = {"answer": g.text or "", "model_returned": getattr(g, "model_version", None) or rec["model"],
                      "stop_reason": str(g.candidates[0].finish_reason) if g.candidates else None,
                      "usage": {"input": u.prompt_token_count, "cached_input": getattr(u, "cached_content_token_count", None),
                                "output": u.candidates_token_count or 0,
                                "reasoning": getattr(u, "thoughts_token_count", None)}}
        return state, out
    job = mistral_call("GET", "/v1/batch/jobs/" + rec["batch_id"])
    st = job.get("status")
    if st not in ("SUCCESS", "FAILED", "TIMEOUT_EXCEEDED", "CANCELLED"):
        return st, None
    out = {}
    for fid in (job.get("output_file"), job.get("error_file")):
        if not fid:
            continue
        raw = mistral_call("GET", "/v1/files/%s/content" % fid)
        raw = raw.decode("utf-8") if isinstance(raw, bytes) else json.dumps(raw)
        for x in raw.splitlines():
            if not x.strip():
                continue
            r = json.loads(x)
            resp = r.get("response") or {}
            body = resp.get("body") or resp
            if r.get("error") or (resp.get("status_code") not in (None, 200)):
                out[r["custom_id"]] = {"answer": None, "error": json.dumps(r.get("error") or body)[:500]}
                continue
            out[r["custom_id"]] = chat_fields(body)
    return st, out


def chat_fields(body):
    """An OpenAI-shaped chat completion: the answer, the model, the stop reason, and the tokens, reasoning apart."""
    ch = (body.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):          # some hosts give the answer as parts; the reasoning parts are kept apart
        content = "".join(p.get("text", "") for p in content if p.get("type") in (None, "text"))
    u = body.get("usage") or {}
    return {"answer": content or "", "model_returned": body.get("model"), "stop_reason": ch.get("finish_reason"),
            "cut_short": ch.get("finish_reason") == "length",
            "reasoning_chars": len(msg.get("reasoning_content") or msg.get("reasoning") or ""),
            "usage": {"input": u.get("prompt_tokens"),
                      "cached_input": (u.get("prompt_tokens_details") or {}).get("cached_tokens"),
                      "output": u.get("completion_tokens"),
                      "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}}


def cmd_status(a):
    for p in sorted(glob.glob(os.path.join(a.dir, "*-*.json"))):
        if p.endswith(("dry.json", ".requests.json")) or ".dry." in p:
            continue
        r = json.load(open(p, encoding="utf-8"))
        if r.get("collected"):
            print(os.path.basename(p), "collected")
            continue
        st, _ = results(r["maker"], r)
        print(os.path.basename(p), st)


def cmd_collect(a):
    cfg, texts, lines = load_config()
    rp = record_path(a.dir, a.maker, a.column)
    rec = json.load(open(rp, encoding="utf-8"))
    st, res = results(a.maker, rec)
    if res is None:
        raise SystemExit("not finished yet: %s" % st)
    price = rec["price_per_million"]
    spent, errors = 0.0, 0
    out = packet_path(a.dir, a.maker, a.column)
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(head_line(cfg, a.maker, "batch", a.column, {"batch_id": rec["batch_id"],
                                                                          "sent_at": rec["sent_at"]}),
                           ensure_ascii=False) + "\n")
        for run in range(1, cfg["runs"] + 1):
            for k, ln in enumerate(lines):
                c = cid(a.column, run, k)
                x = res.get(c, {"answer": None, "error": "no result returned"})
                x = answer_line(x, a.column, run, k, ln, texts[a.column])
                x.update(seconds=None, at=rec["sent_at"])
                if x.get("usage"):
                    spent += cost(x["usage"], price)
                errors += x.get("answer") is None
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    rec["status"] = st
    rec["collected"] = {"at": now(), "packet": os.path.basename(out), "packet_sha256": sha256_file(out),
                        "answers": rec["requests"] - errors, "errors": errors, "cost_usd": round(spent, 4)}
    json.dump(rec, io.open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("collected %s-%s: %d answers, %d errors, $%.2f" % (a.maker, a.column, rec["requests"] - errors, errors, spent))


# ---------------------------------------------------------------- the one-call makers
ENDPOINT = {"meta": ("https://api.meta.ai/v1/chat/completions", "MODEL_API_KEY"),
            "deepinfra": ("https://api.deepinfra.com/v1/openai/chat/completions", "DEEPINFRA_API_KEY")}
RETRY = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524}


def one_call(maker, body):
    url, env = ENDPOINT[maker]
    attempts = []
    for n in range(6):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                         headers={"Authorization": "Bearer " + os.environ[env],
                                                  "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3600) as r:
                got = json.loads(r.read())
            attempts.append({"at": now(), "seconds": round(time.time() - t0, 2), "result": "answered"})
            out = chat_fields(got)
            out.update(seconds=round(time.time() - t0, 2), attempts=attempts)
            return out
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode("utf-8", "replace")
            attempts.append({"at": now(), "seconds": round(time.time() - t0, 2), "result": "HTTP %d: %s" % (e.code, msg)})
            if e.code not in RETRY:
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            attempts.append({"at": now(), "seconds": round(time.time() - t0, 2), "result": "%s: %s" % (type(e).__name__, e)})
        time.sleep(min(300, 10 * 2 ** n) * (0.5 + random.random()))
    return {"answer": None, "error": attempts[-1]["result"] if attempts else "not sent", "attempts": attempts}


def cmd_sync(a):
    if a.maker not in ONE_CALL:
        raise SystemExit("%s is sent through its batch service: use submit" % a.maker)
    if not plan_tagged():
        raise SystemExit("the plan is not tagged %s: nothing is sent before it is" % PLAN_TAG)
    cfg, texts, lines = load_config()
    ok, ceiling = approval_for(a.maker)
    os.makedirs(a.dir, exist_ok=True)
    price = price_of(cfg, a.maker, False)
    out = packet_path(a.dir, a.maker)
    done, spent = set(), 0.0
    for x in jl(out)[1:]:
        if x.get("answer") is not None:          # a question that got no answer is asked again on a restart
            done.add(x["custom_id"])
            spent += cost(x["usage"], price) if x.get("usage") else 0
    model = cfg["makers"][a.maker]["model"]
    todo = [u for u in units(cfg, lines) if cid(u[0], u[1], u[2]) not in done]
    per_call_high = estimate(cfg, texts, lines, a.maker, "floor", "high")["usd"] / (len(lines) * cfg["runs"])
    lock = threading.Lock()
    state = {"spent": spent, "in_flight": 0, "stopped": False, "n": 0}
    f = io.open(out, "a", encoding="utf-8", newline="\n")
    if not os.path.getsize(out):
        f.write(json.dumps(head_line(cfg, a.maker, "one call per answer, standard interface",
                                     extra={"concurrency": a.concurrency, "started": now()}), ensure_ascii=False) + "\n")
        f.flush()
    print("%s: %d to ask, %d already answered, spent $%.2f of $%.2f" % (a.maker, len(todo), len(done), spent, ceiling),
          flush=True)

    def work(u):
        col, run, k, ln = u
        with lock:
            if state["stopped"] or state["spent"] + (state["in_flight"] + 1) * per_call_high > ceiling:
                state["stopped"] = True
                return
            state["in_flight"] += 1
        body = chat_body(model, texts[col], ln["messages"])
        sent_at = now()
        r = one_call(a.maker, body)
        r["at"] = sent_at
        line = answer_line(r, col, run, k, ln, texts[col])
        with lock:
            state["in_flight"] -= 1
            if r.get("usage"):
                state["spent"] += cost(r["usage"], price)
            state["n"] += 1
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            f.flush()
            if state["n"] % 25 == 0:
                print("  %d answered; spent $%.2f of $%.2f" % (state["n"], state["spent"], ceiling), flush=True)

    with concurrent.futures.ThreadPoolExecutor(a.concurrency) as ex:
        list(ex.map(work, todo))
    f.close()
    print("%s: %s; spent $%.2f of $%.2f" % (a.maker, "stopped before its ceiling" if state["stopped"] else "every question asked",
                                           state["spent"], ceiling), flush=True)


def cmd_ledger(a):
    cfg, _, _ = load_config()
    ok = json.load(open(APPROVAL, encoding="utf-8")) if os.path.exists(APPROVAL) else {"makers": {}}
    by, rows = ledger(a.dir, cfg)
    for r in rows:
        print("%-10s %-18s %-22s high %s  real %s" % (r[0], r[1], r[2], "$%.2f" % r[3] if r[3] is not None else "-",
                                                     "$%.2f" % r[4] if r[4] is not None else "-"))
    for m, v in by.items():
        print("%-10s spent $%.2f, out (high) $%.2f, ceiling $%s" % (m, v["spent"], v["out_high"],
                                                                   ok["makers"].get(m, {}).get("ceiling_usd")))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("dry", "submit", "sync", "status", "collect", "ledger"):
        s = sub.add_parser(name)
        s.add_argument("--dir", required=True)
        if name in ("dry", "submit", "sync", "collect"):
            s.add_argument("--maker", required=name != "dry", choices=list(BATCH + ONE_CALL))
        if name in ("submit", "collect"):
            s.add_argument("--column", required=True, choices=COLUMNS)
        if name == "sync":
            s.add_argument("--concurrency", type=int, default=8)
    a = ap.parse_args()
    {"dry": cmd_dry, "submit": cmd_submit, "sync": cmd_sync, "status": cmd_status, "collect": cmd_collect,
     "ledger": cmd_ledger}[a.cmd](a)


if __name__ == "__main__":
    main()
