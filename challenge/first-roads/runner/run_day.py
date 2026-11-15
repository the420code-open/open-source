"""The challenge's first roads: the run day. The plan, draft 6 (challenge-plan-v3), at the settings of settings.json.

Each of the eight AIs is asked ten times with the paper with its dated notes, and three times more with the paper as
it stood on 13 November 2026, the known roads' arm, each in a fresh conversation, all on one day, Cape Town time.
Each AI gets the question and then the paper, as one message, with nothing before it (plan, section 4). The two
messages are built here from the committed files and checked against their fingerprints before anything is sent.

    python run_day.py messages <run_dir>        builds and fingerprints the two messages; sends nothing
    python run_day.py run      <run_dir>        sends every answer not yet answered; run again, it resumes

Every answer is kept whole, one file each, with its attempts, the model returned and its tokens. The run stops before
any call that could take the whole challenge past G's stop of $1,000 (approval.json). Every key comes from its
maker's own entry in makers_key.py, in this process only.

Zero-Clause BSD.
"""
import concurrent.futures as cf
import datetime
import glob
import hashlib
import io
import json
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import roads  # noqa: E402

CMD, RUN = sys.argv[1], sys.argv[2]
FILES = {
    "question": ("question_v2.txt", "7bc69b3de782f41fa2c297221bff3deb1b22340460d643498edca14ea65b75d3"),
    "paper": ("AP32_The_Correction_with_its_dated_notes_of_2026-11-14.txt",
              "8f55400408495b0b68558468526be1ccd3e670b6c64bf5093e190cfd3eff8344"),
    "question_known": ("question_for_the_known_road_v2.txt",
                       "88b5571a7bdc3147874a67fea0d0fdd64ae2459ab9219d74356e97aa92fb1d32"),
    "paper_known": ("AP32_The_Correction_as_it_stood_on_2026-11-13.txt",
                    "8f083031ac404a9a4647454ed9b9e79a5f0818e3e9a49ff1141702dee48c97c1"),
    "plan": ("plan_draft6.md", "00801978cdd98c82c8025da62c784800663f914606065b270d38f91bb411bfda"),
}
ARMS = {"with_its_dated_notes": ("question", "paper", 10), "as_it_stood_on_2026-11-13": ("question_known", "paper_known", 3)}
MAKERS = ["anthropic", "openai", "google", "xai", "meta", "mistral", "deepinfra", "kimi"]
SIDE_BY_SIDE = {"anthropic": 4, "openai": 6, "kimi": 3}   # rate limits at the top settings; every other maker: all at once
KEY = r"…\tools\open\makers_key.py"
ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "google": "GEMINI_API_KEY", "xai": "XAI_API_KEY",
       "meta": "MODEL_API_KEY", "mistral": "MISTRAL_API_KEY", "deepinfra": "DEEPINFRA_API_KEY", "kimi": "MOONSHOT_API_KEY"}
CAP = float(json.load(open(os.path.join(FR, "approval.json"), encoding="utf-8"))["challenge_stop_usd"])
CAPE_TOWN = datetime.timezone(datetime.timedelta(hours=2))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_checked(key):
    name, fp = FILES[key]
    b = open(os.path.join(FR, name), "rb").read()
    assert sha(b) == fp, "%s is not the committed file" % name
    return b.decode("utf-8")


def message(arm):
    q, p, _ = ARMS[arm]
    return read_checked(q).rstrip("\n") + "\n\n" + read_checked(p)


def log(line):
    s = "%s %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), line)
    print(s, flush=True)
    with io.open(os.path.join(RUN, "run.log"), "a", encoding="utf-8", newline="\n") as f:
        f.write(s + "\n")


def cmd_messages():
    os.makedirs(os.path.join(RUN, "messages"), exist_ok=True)
    read_checked("plan")
    out = {}
    for arm in ARMS:
        m = message(arm).encode("utf-8")
        p = os.path.join(RUN, "messages", "message_%s.txt" % arm)
        open(p, "wb").write(m)
        out[arm] = {"file": "messages/message_%s.txt" % arm, "sha256": sha(m), "bytes": len(m)}
    json.dump(out, open(os.path.join(RUN, "messages", "messages.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


def keys():
    """Each maker's key is put in this process's environment by makers_key.py run, one inside the other, and never
    written anywhere. Here it is only checked that each is there."""
    missing = [mk for mk in MAKERS if not os.environ.get(ENV[mk])]
    if missing:
        raise SystemExit("no key in the environment for: " + ", ".join(missing))


lock = threading.Lock()


def spent():
    tot = 0.0
    for f in glob.glob(os.path.join(RUN, "answers", "*.json")):
        try:
            tot += json.load(open(f, encoding="utf-8")).get("usd") or 0.0
        except ValueError:
            pass
    return tot


in_flight = {"usd": 0.0}


def one(mk, arm, k):
    p = os.path.join(RUN, "answers", "%s-%s-%02d.json" % (mk, arm, k))
    if os.path.exists(p) and json.load(open(p, encoding="utf-8")).get("answer") is not None:
        return
    with lock:
        if spent() + in_flight["usd"] + roads.LARGEST_CALL_USD[mk] > CAP:
            log("STOPPED before %s %s %d: the whole challenge would pass the stop of $%.0f" % (mk, arm, k, CAP))
            return
        in_flight["usd"] += roads.LARGEST_CALL_USD[mk]
    day = datetime.datetime.now(CAPE_TOWN).date().isoformat()
    log("sent %s %s %d (Cape Town %s)" % (mk, arm, k, day))
    try:
        rec = roads.call(mk, message(arm), tries=12)      # up to about an hour of trying again, for a rate limit
    finally:
        with lock:
            in_flight["usd"] -= roads.LARGEST_CALL_USD[mk]
    rec.update(arm=arm, k=k, message_sha256=sha(message(arm).encode("utf-8")), cape_town_day_sent=day,
               settings=roads.M[{"kimi": "moonshot"}.get(mk, mk)])
    tmp = p + ".tmp"
    json.dump(rec, io.open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    log("%s %s %s %d: %s, %s, %s tokens out, $%.4f, %ss" % (
        "answered" if rec.get("answer") is not None else "NOT ANSWERED", mk, arm, k, rec.get("model_returned"),
        rec.get("stop_reason"), (rec.get("usage") or {}).get("output"), rec.get("usd", 0), rec.get("seconds")))


def cmd_run():
    os.makedirs(os.path.join(RUN, "answers"), exist_ok=True)
    keys()
    log("the run begins: %d AIs, %s; the stop at $%.0f" % (len(MAKERS), ", ".join(
        "%d %s" % (n, a) for a, (_, _, n) in ARMS.items()), CAP))
    pools = {mk: cf.ThreadPoolExecutor(max_workers=SIDE_BY_SIDE.get(mk, 13)) for mk in MAKERS}
    futs = [pools[mk].submit(one, mk, arm, k) for arm, (_, _, n) in ARMS.items() for k in range(1, n + 1)
            for mk in MAKERS]
    for f in cf.as_completed(futs):
        f.result()
    done = [json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(RUN, "answers", "*.json"))]
    log("the run ends: %d of %d answered; $%.2f spent" % (sum(r.get("answer") is not None for r in done),
                                                          sum(n for _, _, n in ARMS.values()) * len(MAKERS), spent()))


ROUTES = MAKERS + ["marker-xai", "marker-google"]


def cmd_ready():
    """AG Opus, 15 November 2026: "If any route fails, mend it and test it again; the run waits for that, not for a
    date." Every route's latest check, across route-check/*/, must have passed, or the run does not start."""
    latest = {}
    for f in sorted(glob.glob(os.path.join(FR, "route-check", "*", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        if r.get("route") in ROUTES and (r["route"] not in latest or r["at"] >= latest[r["route"]]["at"]):
            latest[r["route"]] = dict(r, file=f)
    failing = [x for x in ROUTES if not (latest.get(x) or {}).get("passed")]
    if failing:
        log("the run waits: these routes have not passed their check: " + ", ".join(failing))
        raise SystemExit(4)
    log("every route has passed its check: " + ", ".join("%s (%s)" % (x, latest[x]["at"]) for x in ROUTES))


{"messages": cmd_messages, "run": cmd_run, "ready": cmd_ready}[CMD]()
