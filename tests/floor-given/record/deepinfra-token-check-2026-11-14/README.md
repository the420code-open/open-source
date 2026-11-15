# DeepInfra's token check · 14 November 2026

AG Opus, through G, 14 November 2026: "'Adds nothing', checked on the first question: a published item, its token
count from DeepInfra beside a local count with DeepSeek's own encoding script. If they differ, stop, and tell me
before any other question goes."

## What was sent

- **One published item, alone:** `T1.1/situation/original`, from `tests/generated/tests.jsonl` at tests-v1.1.
- **As the "as shipped" column sends it:** the situation only. No system message, no reasoning level, no answer
  length: DeepInfra's defaults.
- **To:** `deepseek-ai/DeepSeek-V4-Pro-0813` at https://api.deepinfra.com/v1/openai/chat/completions, its standard
  interface, never its batch service. The model returned: `deepseek-ai/DeepSeek-V4-Pro-0813`.
- **The whole reply** is in `deepinfra_response.json`, with the request body and the time it was sent.

## The local count

- **DeepSeek's own files,** from https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813 at commit
  72e1d3230f6c080a530b0a1d46f8eb4602340597: `encoding/encoding_dsv4.py` (29,001 bytes), `encoding/README.md`
  (9,168), `tokenizer.json` (6,367,146), `tokenizer_config.json` (801). Their SHA-256 are in `token_check.json`.
  The script was read before it was run; it imports nothing but Python's own typing, copy, json and re.
- **The encoding adds only its template:** the start token, the turn markers, the opening of the thinking block,
  and, in thinking mode, a fixed prefix for a "high" or "max" reasoning effort.

| The template, as | Local count | DeepInfra's |
|---|---|---|
| chat mode | 56 | **56** |
| thinking, effort "low" (no prefix) | 56 | **56** |
| thinking, effort "high" | 135 | 56 |
| thinking, effort "max" | 148 | 56 |

**DeepInfra's 56 prompt tokens are exactly DeepSeek's own template, with nothing added.** The check passes, and the
rest of DeepSeek's questions may go.

## One thing for the card

- **At its defaults, DeepInfra did not reason:** 0 reasoning tokens, and an empty reasoning text. 95 tokens of answer,
  ended by "stop".
- **DeepSeek's own service reasons by default,** at "high". At "high" the same question would have been 135 tokens.
- So, as AG Opus ruled ("send neither reasoning level nor answer length ... The card names the host, and says where
  its defaults may differ from DeepSeek's own service"), the card says: on this host, at its defaults, DeepSeek V4
  Pro answered without reasoning, where DeepSeek's own service reasons at "high". Every answer of the run records
  its reasoning tokens, so the card can say how many did.
