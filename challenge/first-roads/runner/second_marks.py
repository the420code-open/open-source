"""The challenge's first roads: the second marks, by fresh sessions of AG Opus that G opens. The markers' message,
version 1, word for word, with Part Three's batch line after "Use nothing but this message". AG Opus, through G,
15 November 2026, midday: "Build their batches as you built scorer two's, by size, with the batch line of Part Three.
Send them to G with the exact first message for each chat. They mark every answer of the eight AIs, and not the work's
own roads."

As scorer two's were: shuffled, with no AI named, each answer under a number of its own; the key that names each
answer's AI is kept apart and never put in a batch. Each answer comes with its own question and paper, as the batch
line says.

    python second_marks.py <run_dir>

Zero-Clause BSD.
"""
import glob
import hashlib
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import marks  # noqa: E402  (its message builder; sys.argv is set below so its command runs nothing)

RUN = sys.argv[1]
WHO = sys.argv[2] if len(sys.argv) > 2 else "second"    # "second": the fresh sessions; "first": AG Opus's own
OUT = os.path.join(RUN, "%s-marks" % WHO)
SEED = {"second": 20261115, "first": 20261116}[WHO]   # each its own shuffle
PREFIX = {"second": "R", "first": "M"}[WHO]
SIZE = 560000                     # bytes in a batch, about as scorer two's were
BATCH_LINE = ("Below are several answers, each with its own question and paper. Mark each one alone, in turn, as if it "
              "were the only one. Give a result for each, in the form below, headed by its number.")
FIRST = ("1:1 + 1×ε @ AS [+α | −α]\n\n"
         "You are one of the markers of the challenge's first roads, for the Open Source work on The 420 Code. The "
         "attached batch file is your whole message: read it and mark as it says, every answer in it, each alone.\n\n"
         "- Use the attached file and nothing else. Do not read any memory file, do not search past chats, do not use "
         "the web, and do not open any other file.\n"
         "- You are not told which AI wrote any answer, and you do not try to find out. You have seen no other mark.\n"
         "- Nothing from this job is saved to memory.\n"
         "- The file is long. Read it in parts, in order, and write each result into a marks file as you go, headed by "
         "its number (R001 and so on), in the form the file gives. Name the file \"Second marks - \" followed by the batch "
         "file's own name. If you cannot write files, give the results in the chat instead, in parts, in order.\n"
         "- When you are done, check that every number in the batch has exactly one result.\n\n"
         "What to send me: the marks file, and in the chat only that you are done and how many answers you marked.")


def frame():
    """Part One up to its slots, with the batch line after the first paragraph."""
    t = marks.part_one()
    first, rest = t.split("\n\n", 1)
    assert first.startswith("**Use nothing but this message.**")
    head = rest.split("**The question the AI was given:**", 1)[0].rstrip("\n")
    return first + "\n\n" + BATCH_LINE + "\n\n" + head


def item(n, arm, answer):
    q, p = marks.ARMS[arm]
    return ("---\n\n## Answer %s\n\n**The question the AI was given:**\n\n%s\n\n**The paper, as the AI was given it:**\n\n"
            "%s\n\n**The AI's answer:**\n\n%s" % (n, marks.read(q).rstrip("\n"), marks.read(p).rstrip("\n"),
                                                answer.rstrip("\n") if answer.strip() else "(The answer is empty.)"))


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(RUN, "answers", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        if r.get("answer") is not None:
            rows.append((os.path.basename(f)[:-5], r))
    assert len(rows) == 104, "not every answer is in: %d" % len(rows)
    random.Random(SEED).shuffle(rows)
    key, items = {}, []
    for i, (name, r) in enumerate(rows, 1):
        n = "%s%03d" % (PREFIX, i)
        key[n] = {"answer": name, "maker": r["maker"], "arm": r["arm"], "k": r["k"]}
        items.append((n, item(n, r["arm"], r["answer"])))
    fr = frame()
    batches, cur, size = [], [], len(fr.encode("utf-8"))
    for n, t in items:
        b = len(t.encode("utf-8"))
        if cur and size + b > SIZE:
            batches.append(cur)
            cur, size = [], len(fr.encode("utf-8"))
        cur.append((n, t))
        size += b
    if cur:
        batches.append(cur)
    os.makedirs(OUT, exist_ok=True)
    made = []
    for j, bt in enumerate(batches, 1):
        name = "%s marks batch %d of %d.md" % (WHO.capitalize(), j, len(batches))
        body = fr + "\n\n" + "\n\n".join(t for _, t in bt) + "\n"
        io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(body)
        made.append({"file": name, "answers": [n for n, _ in bt], "bytes": len(body.encode("utf-8")),
                     "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()})
    if WHO == "second":
        io.open(os.path.join(OUT, "the first message for each chat.txt"), "w", encoding="utf-8",
                newline="\n").write(FIRST + "\n")
    else:
        io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write(
            "# AG Opus's own marks · the challenge's first roads · %d batches\n\n"
            "AG Opus, through G, 15 November 2026: \"Built the same way as the fresh sessions' batches: by size, numbered "
            "only, maker and model hidden, in a shuffle of their own. You keep the key.\"\n\n"
            "- Every answer of the eight AIs, 104, each under its own number, M001 and so on, with its own question and "
            "paper, in the markers' message, version 1, word for word, with Part Three's batch line.\n"
            "- One answer is empty: Google's, cut short at Google's own ceiling. It is shown as \"(The answer is "
            "empty.)\".\n"
            "- Each batch's marks come back in one file, in Part One's result form, headed by number.\n"
            "- No other mark is sent to AG Opus until all of these are back.\n" % len(made))
    json.dump({"seed": SEED, "key": key}, open(os.path.join(RUN, "%s-marks-key.json" % WHO), "w", encoding="utf-8"),
              indent=1)
    json.dump(made, open(os.path.join(OUT, "batches.json"), "w", encoding="utf-8"), indent=1)
    for m in made:
        print(m["file"], len(m["answers"]), m["bytes"])


main()
