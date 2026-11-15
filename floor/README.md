# floor

The floor, in its three forms, generated from one source, with a checker. Draft until every desk line is approved
and the checker passes.

- source/floor.yaml: the one source. Everything else is generated from it, never edited by hand.
- generated/: floor.json (with floor.schema.json), floor.txt (the short form, ready to paste), and page.html (the page's
  body, built into aiethics.global/open-source/the-floor/).
- checker/: floorlib.py (normalising, reading the sources, writing the forms), check.py (the checker), result.json.
- snapshots/: for each version, the keyed registry rows, the root's fingerprint, and each source's normalised text's SHA-256.
- examples/: two short examples that read floor.json.

The fingerprint of a version is the SHA-256 of source/floor.yaml as committed under its tag, such as floor-v0.3.

Terms: the text and the data under CC0 1.0 Universal, the code under Zero-Clause BSD. The floor's extracts stay the
work's, under the work's own terms: share them, never alter them.
