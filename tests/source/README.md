# tests/source

`tests.yaml` is the tests' only source. Everything the suite uses is generated from it.

It was built from the tests, draft 3, and the final paraphrases that AG Opus approved on 12 November 2026. In T6.3, every "01:00" became "01:30", in the originals and both paraphrases, as AG Opus ruled on 13 November 2026; nothing else in a paraphrase changed. For every item it holds:

- its ID, its test, and whether it uses the work's words;
- the floor lines its rubric scores against, by ID, in the floor's version 1.0;
- its texts: the situation, the twin, twins A and B, or forms A and B;
- for each text, the original, paraphrases 1 and 2, and the rubric.

A conversation is stored as turns, each with who speaks and what they say. Where an item's figures change in a paraphrase, as in T3.1, that paraphrase carries its own figures in its rubric. A rubric line that defines a word rather than giving a mark, as T7.3's "What a lecture is", is kept under `defines`; the rubric's full text, as the scorer reads it, is always in `text`.

AG Opus checks this file against the tests, draft 3, and the final paraphrases, by script, before anything is generated from it.

The held-out items have the same shape, but are kept elsewhere. They never enter this folder.

Terms: CC0 1.0 Universal.
