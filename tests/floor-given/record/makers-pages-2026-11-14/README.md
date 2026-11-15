# The makers' pages, as they stood on 14 November 2026

Dated copies, for the record of the floor-given run. Each was fetched by WC from the maker's own site, signed out,
and is kept as it came, with a plain-text reading beside the HTML. `SHA256SUMS` has every file's fingerprint.

## Mistral · fetched 2026-11-14 15:47:56 UTC (the model page) and 15:48 UTC (the terms)

- `mistral/model-mistral-large-4-0.md` and `.html`: https://docs.mistral.ai/models/mistral-large-4-0
  - "API names: `mistral-large-4`, `mistral-large-4-0`, `mistral-large-latest`"
  - "Status: GA"
  - "Release date: 2026-11-05"
- `mistral/commercial-terms-of-service.html` and `.txt`: https://legal.mistral.ai/terms/commercial-terms-of-service/
  (Effective: September 25, 2026)
  - **4.2, Training:** Mistral AI will not use Customer Data or Outputs to train its models except on an opt-in, an
    opt-out not taken, Feedback, an Order Form, or "(d) when Customer uses Labs or Preview Models".
  - **4.3, Labs or Preview Models:** "experimental, preview or pre-release models identified as such, including those
    identifiable by the prefix "labs" in AI Studio". Large 4 is not identified so on its page.
- **So, as AG Opus ruled through G on 14 November 2026:** the held-out items may go to `mistral-large-4-0`, the fixed
  name, never "latest".

## Meta · fetched 2026-11-14 15:49:14 UTC

- `meta/muse-wonder.md`: https://dev.meta.ai/docs/muse-wonder.md
  - "Muse Wonder is in preview."
- `meta/terms-of-service.html` and `.txt`: https://dev.meta.ai/legal/terms-of-service (Last updated: October 9, 2026)
  - Meta "will not use Content submitted in a request to the Standard Services to train Meta Models."
  - Contributor Services, section 6: Meta may use Content to train its models.
  - **The terms have no word on preview models:** "preview", "beta", "pre-release" and "experimental" do not occur.
- `meta/model-designation-and-geographic-use-policy.html` and `.txt`: https://dev.meta.ai/legal/geographic-use-policy
  (Last updated: November 9, 2026)
  - "Standard Models (use constitutes use of "Standard Services"): Muse Image, Muse Spark 1.1, Muse Spark 1.2,
    Muse Spark 1.3, Muse Voice Transcribe, SAM 3.1, Muse Wonder, Muse Wonder Full, Muse Ember"
  - "Contributor Models (use constitutes use of "Contributor Services"): Muse Spark 1.2 Contributor, Muse Spark 1.3
    Contributor"
  - A Coding Harness Subscription counts as Contributor Services by default. The run uses an API key, not a
    subscription.
  - "Meta may update these designations": the run day reads this page again before the first question.
- `meta/commitments.html` and `.txt`: https://dev.meta.ai/legal/commitments
  - "Standard Services: Meta does not use your Content from Standard Services to train Meta Models."
- **So:** Muse Wonder, though in preview, is designated a Standard Model, and Meta does not train on what is sent to
  it. By AG Opus's rule ("If they allow training, Meta gets the published items only"), Meta gets every item, the
  held-out ones included.
