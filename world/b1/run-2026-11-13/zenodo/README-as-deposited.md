# B1 · The defector does not last · the full run, 13 to 14 November 2026

Every file the run of the frozen hypothesis hyp-B1-v1 wrote, the world's code as the run used it, and every cell's
judgement. The frozen hypothesis is its own record: DOI 10.5281/zenodo.24207719. This record is its supplement.

B1 was frozen and deposited on 13 November 2026, and run that night, as frozen: from 23:08 on 13 November to 00:18 on
14 November, Cape Town time.

## What the run is

In the frozen text's own terms: in this world a record is exact, so every careful giver cuts a defector within the
record's window, and a defector cut off falls. So every cell that could fire held, as its frozen text said it would
before any run. In each of those 104 cells the judgement reads "B1 holds in this cell, and the switches hold". That is
the premises at work. It is not a test the switches could have failed, and it is not counted as support.

- **The 104 controls:** "a defector lasts" in 56, "no defector lasts" in 48. A control fires nothing (B1, section 10).
- **The second engine** ran 32 of the cells beside the reference engine, on its own seeds, and agreed in all 32, by
  the rule set before the run (B1, section 9): their averages lie within three standard errors of each other.

## The files

| File | What it holds | Files inside |
|---|---|---|
| `b1-run-1-reference-packets-summaries-console.tar.gz` | The reference engine, seeds 1 to 100: every cell's packet (one line per seed), its summary, and its console output | 624 |
| `b1-run-2-second-engine.tar.gz` | The second engine, seeds 100,001 to 100,100: the same, for its 32 cells | 96 |
| `b1-run-3-reference-event-logs-part01-of-11.tar` to `-part11-of-11.tar` | The reference engine's event logs, one per cell, each gzipped already: every event of every seed, and the round lines of the first five seeds. In eleven plain tar parts of about 280 MB, so each could be uploaded on its own; together they hold the 208 logs | 208 |
| `b1-run-4-world-code.tar.gz` | The world's code as the run used it: from the tag `world-ref-v1.0` (commit 6782c5f), the reference engine, the second engine, the specification's version 1.0, the test values and the engines' comparison; and B1's 208 cells, their index, and the runner, as committed at 23:08:10 on 13 November 2026, before the first cell began | 232 |
| `b1-run-5-judgement.tar.gz` | Every cell's judgement, `judgement.json` and `judgement.md`; the script that wrote it from the packets, `judge.py`; and the run's log, `run.log`; as committed at 00:22:17 on 14 November 2026 | 4 |
| `manifest.sha256` | The SHA-256 of each of the run's 928 files, in archives 1 to 3, as committed with the judgement | |
| `manifest-code-and-judgement.sha256` | The SHA-256 of each of the 236 files in archives 4 and 5 | |

Every file inside an archive keeps the path its manifest gives it, and is as it was committed.

Line 220 of judge.py is a guard. It checks that the judgement never contains certain words, and so it holds those
words itself.

## To check every file

Unpack all five archives, the eleven parts of archive 3 among them, into one empty folder, put the two manifests beside them, and run:

```
sha256sum -c manifest.sha256
sha256sum -c manifest-code-and-judgement.sha256
```

The first checks 928 files, the second 236. Each archive's own SHA-256 is in this record's description.

## What is not here

- **Nothing of the run is left out.** Every file it wrote is in archives 1 to 3.
- **From the tag `world-ref-v1.0`,** only the code the run used is in archive 4. The tag also holds the drafts of the
  hypotheses and of the specification; they are not code, and are left out. The frozen hypothesis is its own record,
  and the specification's version 1.0 is in archive 4.
- **Nothing of the tests** is in this record. The run's files are the world's.

## Terms

CC0 1.0 Universal. Everything built for the open-source work on The 420 Code is given away with no restriction.
Creator: G, Studio G, Strand, Cape Town.
