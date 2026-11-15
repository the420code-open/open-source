# skills

**the-420-code-floor** is a skill in the open Agent Skills format. It is our own instructions and a small script, and it holds none of the work's words.

The script fetches the floor's short form from its home, aiethics.global. It checks the copy's SHA-256 fingerprint against the one written in the skill. It hands the text to the agent only if they match. If they do not, it stops and says why.

Terms: Zero-Clause BSD (LICENSE-0BSD). Where a platform publishes skills under MIT-0, as ClawHub does, it is offered there under MIT-0. The skill carries no item's text and no line of the work, so that is ours to give.

## Tested on 13 November 2026

- **The script alone.**
  - The live copy passes, with exit code 0.
  - A copy with one letter changed ("AI" to "Al") is stopped, with exit code 2.
  - The repository's own copy passes.
- **Agents.** Two separate agents were each given only the skill folder and told to follow `SKILL.md`.
  - **Against the real home:** the agent got the floor, with its check line.
  - **Against the altered copy, served locally:** the agent got "STOPPED", told the person it could not apply the floor, and used no other copy.

Still to test: in OpenClaw, and in Claude Code's own skill loader.
