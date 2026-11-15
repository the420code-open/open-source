# The challenge's first roads · fixed before any AI is asked

Committed on 14 November 2026, at the plan's order, step 4: "This plan, the question, the paper in both its forms, and
the marking words are committed, with a fingerprint, before any AI is asked." No AI has been asked.

| File | What it is | SHA-256 |
|---|---|---|
| `plan.md` | The plan, draft 4, word for word (AG Opus, 14 November 2026) | 124029ab77a9d0f558ba8a2b301ec78f500f99e8e7d26f696eac8652989f118f |
| `question.txt` | The question, word for word, from the plan's section 4 | 39a880e3550f262c31f77e4e90f51599a67e34c02fb78bf0fada67d2d085ed82 |
| `question_for_the_known_road.txt` | The same, for the known road (section 7): its first paragraph names the paper "as it stood on 13 November 2026" in place of "with its dated note of 14 November 2026", and nothing else changes | 88b5571a7bdc3147874a67fea0d0fdd64ae2459ab9219d74356e97aa92fb1d32 |
| `AP32_The_Correction_with_its_dated_note_of_2026-11-14.txt` | The paper as published on the day, with its dated note, as plain text from its source of record | 99e7bd733a479013592df22e9f46820f24d550953e2496db01ecf17d0f173de6 |
| `AP32_The_Correction_as_it_stood_on_2026-11-13.txt` | The paper as it stood on 13 November 2026, before its note, as plain text from its source of record, for the known road | 8f083031ac404a9a4647454ed9b9e79a5f0818e3e9a49ff1141702dee48c97c1 |
| `marking_words.md` | The marking words: the plan's section 8, word for word | 39b21e5d4c868fb6a67d83df6ac49647b20732ae89f3f28042faa27f07063939 |
| `approval.json` | G's approval of 14 November 2026: the run capped at $60, the known road's arm at $20 | 621877f761195052267ed1653fdf9a319e033b16365523d94cb9e7255a1f66a8 |

## The paper, checked

- **With its dated note:** from `AP32_The_Correction_FINAL_dated_note_2026-11-14.docx` (SHA-256 61dc5280…), checked
  against the published PDF, `/AP32_The_Correction.pdf` (c12cab11…), by the test of record: every one of its 215
  paragraphs is in the PDF, and every sentence of the PDF is in the source, but for the two lines with the formula
  Threshold_eff = F × (R/R₀)^α, whose α and ₀ the PDF's text reader takes out of order. Checked by eye on the page: the
  formula reads as the text has it.
- **As it stood on 13 November 2026:** from `AP32_The_Correction_FINAL.docx` (232cec6d…), checked against the PDF
  published until 14 November 2026, `AP32_The_Correction_FINAL_published_to_2026-11-14.pdf` (489bec11…): OF RECORD
  both ways, 210 paragraphs. The formula checked by eye on the page.
- **Plain text:** every non-empty paragraph of the source, in order, one blank line between. The Contents page is
  included as the paper prints it.

## Not fixed here, and why

The run's settings, one per maker, are recorded with the run, not in the plan. Seven points the plan's words leave
open for them went to AG Opus with the price on 14 November 2026: DeepSeek's highest setting on DeepInfra;
Anthropic's required length cap; whether Google's calls are streamed; the markers' own settings; whether a refusal
gets the three marks; which of Google's models is its leading one; and batch and caching. Nothing in this folder
changes with their answers.
