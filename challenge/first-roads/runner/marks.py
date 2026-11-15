"""The challenge's first roads: the outside marks, with the markers' message, version 1 (marker_message_v1.md, 6da7e1c1…),
word for word.

- Every answer of the seven other AIs is marked by grok-4.7; xAI's own answers by Google's model. Part One.
- Our own eight roads, written out, draft 4, are marked by grok-4.7. Part Two.
- Each mark is one answer to a message, in a fresh conversation, through runner/roads.py's own call, at the markers'
  settings of settings.json (grok-4.7 xhigh; Google's model high, streamed).
- The second call of Part Three waits for the other markers' sorts, and is not sent here.

    python marks.py build <run_dir>   writes every message to marks/messages/ and fingerprints them; sends nothing
    python marks.py send  <run_dir>   sends every message not yet marked; run again, it resumes

The marks count toward the challenge's stop (approval.json): answers and marks together.

Zero-Clause BSD.
"""
import concurrent.futures as cf
import datetime
import glob
import hashlib
import io
import json
import os
import re
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import roads  # noqa: E402

RUN = MD = None                   # set from the command line, below
MSG = os.path.join(FR, "marker_message_v1.md")
MSG_SHA = "6da7e1c12af5608ac46713e2c0796aa5c3965362fa08e23959016fdae168e074"
ROADS = os.path.join(FR, "roads_written_out_draft4.md")
ARMS = {"with_its_dated_notes": ("question_v2.txt", "AP32_The_Correction_with_its_dated_notes_of_2026-11-14.txt"),
        "as_it_stood_on_2026-11-13": ("question_for_the_known_road_v2.txt",
                                      "AP32_The_Correction_as_it_stood_on_2026-11-13.txt")}
CAP = float(json.load(open(os.path.join(FR, "approval.json"), encoding="utf-8"))["challenge_stop_usd"])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(name):
    return open(os.path.join(FR, name), "rb").read().decode("utf-8")


def part_one():
    """Part One's message, as its blockquote holds it, the quote marks taken off."""
    raw = open(MSG, "rb").read()
    assert sha(raw) == MSG_SHA, "marker_message_v1.md is not the committed text"
    t = raw.decode("utf-8")
    body = t.split("# Part One · For an answer of an AI", 1)[1].split("\n---\n", 1)[0]
    lines = [ln for ln in body.split("\n") if ln.startswith(">")]
    return "\n".join(ln[2:] if ln.startswith("> ") else ln[1:] for ln in lines).strip("\n")


Q_PH, P_PH, A_PH = "*[the question, as that AI was given it]*", "*[the paper]*", "*[the answer, whole]*"
SECOND_PARA = ("You are marking an answer for a test of a rule's safeguards, from a body of work called The 420 Code. An AI "
               "was given the question below, and then the paper below, in one message. Its answer follows. Mark it "
               "alone. You see no other mark.")
ROAD_PARA = ("You are marking a road for a test of a rule's safeguards, from a body of work called The 420 Code. The road "
             "was written by the work's own desks, against the paper below, in its strongest form. Mark it alone. You see "
             "no other mark.")
ALONE_OLD = ("**You are given this paper alone.** Where the paper does not settle a step, mark it as passing through what "
             "the paper leaves open, and name the place. Do not reach for other papers.")
ALONE_NEW = ("**You are given this paper alone.** Some steps quote another paper of the same work, and say which. Take "
             "those quotations as given, and judge whether the step follows from them. Where neither the paper nor a "
             "quoted line settles a step, mark it as passing through what the paper leaves open, and name the place.")


def message_for_answer(arm, answer):
    t = part_one()
    for ph in (Q_PH, P_PH, A_PH):
        assert t.count(ph) == 1, ph
    q, p = ARMS[arm]
    return t.replace(Q_PH, read(q).rstrip("\n")).replace(P_PH, read(p).rstrip("\n")).replace(A_PH, answer.rstrip("\n"))


def message_for_road(words_used, road):
    """Part Two: the same message, with its three changes. The road, with the words used before the roads, goes under
    "The road:" in the answer's place; the question's place is left out."""
    t = part_one()
    assert t.count(SECOND_PARA) == 1 and t.count(ALONE_OLD) == 1
    t = t.replace(SECOND_PARA, ROAD_PARA).replace(ALONE_OLD, ALONE_NEW)
    kinds = re.search(r"\*\*First, say what the answer is\.\*\* It is one of these:\n\n(?:- .*\n)+\n", t)
    assert kinds, "the four kinds"
    t = t.replace(kinds.group(0), "")
    head, rest = t.split("**The question the AI was given:**", 1)
    paper_block = "**The paper, as the AI was given it:**" + rest.split("**The paper, as the AI was given it:**", 1)[1]
    paper_block = paper_block.split("**The AI's answer:**", 1)[0]
    p = read(ARMS["with_its_dated_notes"][1]).rstrip("\n")
    return (head + paper_block.replace(P_PH, p).rstrip("\n") + "\n\n**The road:**\n\n" + words_used.strip("\n") + "\n\n"
            + road.strip("\n"))


def the_roads():
    raw = open(ROADS, "rb").read().decode("utf-8")
    words = "## The words used" + raw.split("## The words used", 1)[1].split("\n## Road 1", 1)[0]
    parts = re.split(r"\n(?=## Road \d )", raw)
    roads_ = [x.strip("\n") for x in parts if x.startswith("## Road ")]
    assert len(roads_) == 8, len(roads_)
    return words.strip("\n"), roads_


def marker_of(maker):
    return "google" if maker == "xai" else "xai"


def build():
    os.makedirs(os.path.join(MD, "messages"), exist_ok=True)
    index = {}
    for f in sorted(glob.glob(os.path.join(RUN, "answers", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        if r.get("answer") is None:
            continue
        name = os.path.basename(f)[:-5]
        m = message_for_answer(r["arm"], r["answer"]).encode("utf-8")
        p = os.path.join(MD, "messages", name + ".txt")
        open(p, "wb").write(m)
        index[name] = {"kind": "answer", "maker": r["maker"], "arm": r["arm"], "k": r["k"], "marker": marker_of(r["maker"]),
                       "answer_file": "answers/" + name + ".json", "message_sha256": sha(m), "bytes": len(m)}
    words, rs = the_roads()
    for i, road in enumerate(rs, 1):
        name = "road-%d" % i
        m = message_for_road(words, road).encode("utf-8")
        open(os.path.join(MD, "messages", name + ".txt"), "wb").write(m)
        index[name] = {"kind": "our road", "road": i, "title": road.split("\n", 1)[0][3:], "marker": "xai",
                       "message_sha256": sha(m), "bytes": len(m)}
    json.dump(index, open(os.path.join(MD, "messages", "index.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print(len(index), "messages;", sum(v["kind"] == "answer" for v in index.values()), "answers,",
          sum(v["kind"] == "our road" for v in index.values()), "roads")


FIELDS = ("Kind", "Mark", "Step", "Lines", "Place", "Why")


def parse(text):
    """The result, last in the reply: Kind, Mark, Step, Lines, Place, Why."""
    t = (text or "").replace("**", "")
    at = t.rfind("Kind:")
    if at < 0:
        return None
    tail = t[at:]
    out, cur = {}, None
    for line in tail.split("\n"):
        m = re.match(r"^\s*(Kind|Mark|Step|Lines|Place|Why)\s*:\s*(.*)$", line)
        if m:
            cur = m.group(1)
            out[cur] = m.group(2).strip()
        elif cur:
            out[cur] = (out[cur] + "\n" + line).strip()
    return out


lock = threading.Lock()
in_flight = {"usd": 0.0}


def spent():
    tot = 0.0
    for f in glob.glob(os.path.join(RUN, "answers", "*.json")) + glob.glob(os.path.join(MD, "*.json")):
        try:
            tot += json.load(open(f, encoding="utf-8")).get("usd") or 0.0
        except ValueError:
            pass
    return tot


def log(line):
    s = "%s %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), line)
    print(s, flush=True)
    with io.open(os.path.join(MD, "marks.log"), "a", encoding="utf-8", newline="\n") as f:
        f.write(s + "\n")


def one(name, meta):
    out = os.path.join(MD, name + ".json")
    if os.path.exists(out) and json.load(open(out, encoding="utf-8")).get("answer") is not None:
        return
    marker = meta["marker"]
    msg = open(os.path.join(MD, "messages", name + ".txt"), "rb").read()
    assert sha(msg) == meta["message_sha256"]
    with lock:
        if spent() + in_flight["usd"] + roads.LARGEST_CALL_USD[marker] > CAP:
            log("STOPPED before %s: the challenge would pass its stop of $%.2f" % (name, CAP))
            return
        in_flight["usd"] += roads.LARGEST_CALL_USD[marker]
    log("sent %s to %s" % (name, marker))
    try:
        rec = roads.call(marker, msg.decode("utf-8"), tries=12)
    finally:
        with lock:
            in_flight["usd"] -= roads.LARGEST_CALL_USD[marker]
    rec.update(name=name, marked=meta, message_sha256=meta["message_sha256"], result=parse(rec.get("answer")),
               marker_settings=roads.SETTINGS["markers"]["outside_for_xai" if marker == "google" else "outside"])
    tmp = out + ".tmp"
    json.dump(rec, io.open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, out)
    res = rec["result"] or {}
    log("%s %s by %s: %s | %s | step %s | $%.4f" % ("marked" if rec.get("answer") is not None else "NOT MARKED", name,
                                                     rec.get("model_returned"), res.get("Kind"), res.get("Mark"),
                                                     res.get("Step"), rec.get("usd", 0)))


def send():
    index = json.load(open(os.path.join(MD, "messages", "index.json"), encoding="utf-8"))
    for e in ("XAI_API_KEY", "GEMINI_API_KEY"):
        if not os.environ.get(e):
            raise SystemExit("no key in the environment: " + e)
    log("the marks begin: %d messages; the stop at $%.2f, answers and marks together" % (len(index), CAP))
    pools = {"xai": cf.ThreadPoolExecutor(max_workers=13), "google": cf.ThreadPoolExecutor(max_workers=13)}
    futs = [pools[m["marker"]].submit(one, n, m) for n, m in sorted(index.items())]
    for f in cf.as_completed(futs):
        f.result()
    done = [json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(MD, "*.json"))]
    log("the marks end: %d of %d marked; $%.2f spent on answers and marks" % (
        sum(r.get("answer") is not None for r in done), len(index), spent()))


if __name__ == "__main__":
    CMD, RUN = sys.argv[1], sys.argv[2]
    MD = os.path.join(RUN, "marks")
    {"build": build, "send": send}[CMD]()
