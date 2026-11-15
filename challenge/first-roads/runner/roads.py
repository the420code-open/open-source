"""The challenge's first roads: one call to one route, as the plan, draft 6, and settings.json set it.

Every route is a standard call to the maker's own interface, streamed, so that a long answer is never cut by a host's
idle limit; never batch, no caching, no system message, no temperature, and no length but where an interface requires
one (Anthropic's max_tokens, at the model's own maximum). The answer, the reasoning text where a maker returns it, the
model returned, the stop reason and the tokens are kept, with every attempt.

    from roads import call
    rec = call("anthropic", text)          # the run, the route checks, and the markers all use this one function

Zero-Clause BSD.
"""
import datetime
import json
import os
import random
import time

SETTINGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json"),
                          encoding="utf-8"))
M = SETTINGS["makers"]
PRICE = {  # $ per million tokens, in and out, as read on each maker's page on 14 November 2026 (the price of that night)
    "anthropic": (8.00, 40.00), "openai": (10.00, 50.00), "google": (2.00, 10.00), "xai": (2.00, 6.00),
    "meta": (4.00, 20.00), "mistral": (0.70, 2.10), "deepinfra": (1.30, 2.60), "kimi": (2.00, 10.00)}
LARGEST_CALL_USD = {k: (60000 * p[0] + 131072 * p[1]) / 1e6 for k, p in PRICE.items()}
COMPAT = {  # the makers whose interface takes an OpenAI-shaped chat call
    "xai": ("https://api.x.ai/v1", "XAI_API_KEY", "grok-4.7", {"reasoning_effort": "xhigh"}),
    "meta": ("https://api.meta.ai/v1", "MODEL_API_KEY", "muse-wonder-1.0", {"reasoning_effort": "max"}),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY", "mistral-large-4-0", {"reasoning_effort": "high"}),
    "deepinfra": ("https://api.deepinfra.com/v1/openai", "DEEPINFRA_API_KEY", "deepseek-ai/DeepSeek-V4-Pro-0813",
                  {"reasoning_effort": "max"}),
    "kimi": ("https://api.moonshot.ai/v1", "MOONSHOT_API_KEY", "kimi-k3.1-pro", {"reasoning_effort": "max"}),
}
for _k, (_u, _e, model, extra) in COMPAT.items():
    assert M[{"kimi": "moonshot"}.get(_k, _k)]["model"] == model, _k
    assert M[{"kimi": "moonshot"}.get(_k, _k)]["setting"] in ({"reasoning_effort": extra["reasoning_effort"]},
                                                             {"reasoning.effort": extra["reasoning_effort"]}), _k
assert M["anthropic"]["model"] == "claude-fable-5-2" and M["anthropic"]["setting"] == {"output_config.effort": "max"}
assert M["openai"]["model"] == "gpt-6-astra" and M["openai"]["setting"] == {"reasoning.effort": "max"}
assert M["google"]["model"] == "gemini-4-carbon" and M["google"]["setting"] == {"thinking_level": "high"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def cost(maker, usage):
    pin, pout = PRICE[maker]
    out = (usage.get("output") or 0)
    if maker in ("google", "xai") and usage.get("reasoning"):     # these two report thinking apart from the answer
        out += usage["reasoning"]
    return ((usage.get("input") or 0) * pin + out * pout) / 1e6


def _anthropic(text):
    import anthropic
    client = anthropic.Anthropic(timeout=3600.0, max_retries=0)
    with client.messages.stream(model="claude-fable-5-2", max_tokens=M["anthropic"]["max_tokens"],
                                messages=[{"role": "user", "content": text}],
                                output_config={"effort": "max"}) as s:
        m = s.get_final_message()
    answer = "".join(b.text for b in m.content if getattr(b, "type", "") == "text")
    thinking = "".join(getattr(b, "thinking", "") or "" for b in m.content if getattr(b, "type", "") == "thinking")
    u = m.usage
    return {"answer": answer, "reasoning_text": thinking, "model_returned": m.model, "stop_reason": m.stop_reason,
            "cut_short": m.stop_reason == "max_tokens",
            "refusal": m.stop_reason == "refusal",
            "stop_details": json.loads(m.stop_details.model_dump_json()) if getattr(m, "stop_details", None) else None,
            "usage": {"input": u.input_tokens, "cached_input": getattr(u, "cache_read_input_tokens", None),
                      "output": u.output_tokens, "reasoning": None}}


def _openai(text):
    from openai import OpenAI
    client = OpenAI(timeout=3600.0, max_retries=0)
    final = None
    stream = client.responses.create(model="gpt-6-astra", input=[{"role": "user", "content": text}],
                                     reasoning={"effort": "max"}, stream=True)
    for ev in stream:
        if ev.type in ("response.completed", "response.incomplete", "response.failed"):
            final = ev.response
    if final is None:
        raise ConnectionError("the stream ended with no final response")
    u = final.usage
    det = getattr(u, "output_tokens_details", None)
    cdet = getattr(u, "input_tokens_details", None)
    inc = getattr(final, "incomplete_details", None)
    return {"answer": final.output_text or "", "reasoning_text": "", "model_returned": final.model,
            "stop_reason": final.status + ((": " + inc.reason) if inc and getattr(inc, "reason", None) else ""),
            "cut_short": final.status == "incomplete",
            "refusal": any(getattr(c, "type", "") == "refusal" for o in (final.output or [])
                           for c in (getattr(o, "content", None) or [])),
            "error": json.loads(final.error.model_dump_json()) if getattr(final, "error", None) else None,
            "usage": {"input": u.input_tokens, "cached_input": getattr(cdet, "cached_tokens", None) if cdet else None,
                      "output": u.output_tokens, "reasoning": getattr(det, "reasoning_tokens", None) if det else None}}


def _google(text):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])       # held: an inline client closes before it sends
    cfg = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="high"))
    answer, thought, last, finish, model = [], [], None, None, None
    for ch in client.models.generate_content_stream(model="gemini-4-carbon", contents=text, config=cfg):
        last = ch
        model = getattr(ch, "model_version", None) or model
        for cand in (ch.candidates or []):
            if cand.finish_reason:
                finish = str(cand.finish_reason)
            for p in ((cand.content.parts if cand.content else None) or []):
                if getattr(p, "thought", False):
                    thought.append(p.text or "")
                elif p.text:
                    answer.append(p.text)
    um = getattr(last, "usage_metadata", None)
    return {"answer": "".join(answer), "reasoning_text": "".join(thought), "model_returned": model,
            "stop_reason": finish, "cut_short": bool(finish and "MAX_TOKENS" in finish),
            "refusal": bool(finish and ("SAFETY" in finish or "PROHIBITED" in finish)),
            "usage": {"input": getattr(um, "prompt_token_count", None),
                      "cached_input": getattr(um, "cached_content_token_count", None),
                      "output": getattr(um, "candidates_token_count", None),
                      "reasoning": getattr(um, "thoughts_token_count", None)}}


def _compat(maker, text):
    from openai import OpenAI
    base, env, model, extra = COMPAT[maker]
    client = OpenAI(api_key=os.environ[env], base_url=base, timeout=3600.0, max_retries=0)
    stream = client.chat.completions.create(model=model, messages=[{"role": "user", "content": text}], stream=True,
                                            stream_options={"include_usage": True}, extra_body=extra)
    answer, reasoning, finish, usage, got_model = [], [], None, None, None
    for ch in stream:
        got_model = ch.model or got_model
        if getattr(ch, "usage", None):
            usage = ch.usage
        for c in (ch.choices or []):
            if c.finish_reason:
                finish = c.finish_reason
            d = c.delta
            if d is None:
                continue
            ex = d.model_extra or {}
            r = ex.get("reasoning_content") or ex.get("reasoning")
            if isinstance(r, str):
                reasoning.append(r)
            if isinstance(d.content, str):
                answer.append(d.content)
            elif isinstance(d.content, list):              # Mistral gives parts: its thinking parts are kept apart
                for p in d.content:
                    p = p if isinstance(p, dict) else getattr(p, "model_dump", lambda: {})()
                    if p.get("type") in (None, "text"):
                        answer.append(p.get("text", ""))
                    elif p.get("type") == "thinking":
                        reasoning.append(json.dumps(p.get("thinking"), ensure_ascii=False)
                                         if not isinstance(p.get("thinking"), str) else p["thinking"])
            u = (c.model_extra or {}).get("usage")
            if u and not usage:
                usage = u
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    usage = usage or {}
    det = usage.get("completion_tokens_details") or {}
    pdet = usage.get("prompt_tokens_details") or {}
    return {"answer": "".join(answer), "reasoning_text": "".join(reasoning), "model_returned": got_model,
            "stop_reason": finish, "cut_short": finish == "length",
            "refusal": finish == "content_filter",
            "usage": {"input": usage.get("prompt_tokens"), "cached_input": pdet.get("cached_tokens"),
                      "output": usage.get("completion_tokens"), "reasoning": det.get("reasoning_tokens"),
                      "as_reported": usage}}


ROUTE = {"anthropic": _anthropic, "openai": _openai, "google": _google}


def call(maker, text, tries=6):
    """One answer from one route. A call that fails before its answer is complete is sent again, from the start, in a
    fresh conversation, and every attempt is kept: only a whole answer, or the maker's own refusal, is an answer."""
    attempts = []
    for n in range(tries):
        t0 = time.time()
        try:
            out = ROUTE[maker](text) if maker in ROUTE else _compat(maker, text)
            out["usd"] = round(cost(maker, out["usage"]), 6)
            attempts.append({"at": now(), "seconds": round(time.time() - t0, 2), "result": "answered"})
            out.update(maker=maker, seconds=round(time.time() - t0, 2), attempts=attempts, at=now())
            return out
        except Exception as e:   # noqa: BLE001 - kept whole in the record; a 4xx that is not a rate limit is final
            status = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
            body = getattr(e, "body", None) or getattr(e, "message", None) or str(e)
            attempts.append({"at": now(), "seconds": round(time.time() - t0, 2), "status": status,
                             "result": "%s: %s" % (type(e).__name__, str(body)[:1500])})
            if status is not None and 400 <= int(status) < 500 and int(status) not in (408, 409, 425, 429):
                break
        time.sleep(min(300, 15 * 2 ** n) * (0.5 + random.random()))
    return {"maker": maker, "answer": None, "error": attempts[-1]["result"] if attempts else "not sent",
            "attempts": attempts, "at": now(), "usd": 0.0}
