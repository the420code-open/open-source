# The floor's checker (brief "phase 2, the floor, build" v2, Part Four). Zero-Clause BSD, Studio G.
#
#   python3 floor/checker/check.py                    check, print the result
#   python3 floor/checker/check.py --write            and write floor/checker/result.json (in a workflow: commit it)
#   python3 floor/checker/check.py --snapshot         take the snapshot of the version as its sources read now
#
# FLOOR_OVERRIDES, for tests only: a JSON file {"sources": {code: address}, "registry": address} that reads a
# source or the registry from a test address instead of its own.
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floorlib as F  # noqa: E402

SOURCE_CHANGED = "A source has changed since this version was read. A new version follows."
NOT_FOUND = "A line could not be found in its source."
# the third line (AG Opus, 12 November 2026): the floor's own files out of step with its source. The page never
# hides a failure, so every failure that is neither of the two above is shown with this line.
FORMS_MISMATCH = "This page’s files do not match the floor’s source. A new build follows."
PAGE_LINES = (SOURCE_CHANGED, NOT_FOUND, FORMS_MISMATCH)      # the order the page shows them in


TEST_OVERRIDES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-overrides.json")


def overrides():
    """Test addresses, for the simulated changes only: from FLOOR_OVERRIDES, or from test-overrides.json, a file
    that exists only on a test branch, never on main."""
    p = os.environ.get("FLOOR_OVERRIDES") or (TEST_OVERRIDES if os.path.exists(TEST_OVERRIDES) else None)
    if not p:
        return {"sources": {}}
    ov = json.load(open(p, encoding="utf-8"))
    ov.setdefault("sources", {})
    return ov


def snapshot_path(version):
    return os.path.join(F.FLOOR, "snapshots", "v" + str(version), "snapshot.json")


def take_snapshot(floor):
    ov = overrides()
    reg_url = ov.get("registry") or floor["registry"]["data"]
    data, by = F.registry(reg_url)
    keys = sorted({k for l in floor["lines"] for k in l.get("keys", [])})
    root = floor["sources"]["ROOT"]
    snap = {
        "version": str(floor["version"]),
        "taken": dt.date.today().isoformat(),
        "how": "read with poppler pdftotext on GitHub's ubuntu runner; normalised as floor/checker/floorlib.py says",
        "registry": {"version": data["registry"]["version"], "date": data["registry"]["date"],
                     "rows": {k: dict(zip(["id", "description", "status_raw", "home_ap"], F.row_cells(by[k]))) for k in keys}},
        "root": {"url": root["url"], "sha256": F.sha256_bytes(F.fetch(ov["sources"].get("ROOT") or root["url"]))},
        "sources": {},
    }
    for code, s in sorted(floor["sources"].items()):
        if s["kind"] != "registry":
            snap["sources"][code] = hashlib.sha256(F.source_text(s, ov["sources"].get(code)).encode("utf-8")).hexdigest()
    return snap


LATER = re.compile(r"^ ?(KS-[A-Z0-9.]+), dated addition, \d{1,2} [A-Z][a-z]+ \d{4} \(MKSR (v\d+\.\d+)\)\. ")


def later_addition(k, old, new, pinned):
    """The registry version of a dated addition the registry inserted into a row after the pinned version, or None.
    The row must keep every word it had, in order, with one block inserted, and that block must open as the registry
    opens a dated addition to this very switch, in a later version: "KS-BAR.9, dated addition, 13 November 2026
    (MKSR v5.40). ..."."""
    if len(new) <= len(old):
        return None
    i = next((j for j in range(len(old)) if old[j] != new[j]), len(old))
    block = new[i:len(new) - (len(old) - i)]
    if new[:i] + new[i + len(block):] != old:
        return None
    m = LATER.match(block)
    vers = lambda v: tuple(int(x) for x in v.lstrip("v").split("."))
    if not m or m.group(1) != k or not pinned or vers(m.group(2)) <= vers(pinned):
        return None
    return m.group(2)


def check(floor, fingerprint, snap):
    ov = overrides()
    checks, flags = [], {}

    def flag(line, *names):
        """A failure, with the page line it shows and the lines or switches it names."""
        flags.setdefault(line, []).extend(names)

    today = dt.date.today().isoformat()
    lines = floor["lines"]
    sources = floor["sources"]

    # 1. the source's own rules
    notes = []
    ids = [l["id"] for l in lines]
    notes += ["duplicate id %s" % i for i in sorted({i for i in ids if ids.count(i) > 1})]
    for l in lines:
        if l["kind"] == "work" and (not l.get("source") or l["source"].get("code") not in sources):
            notes.append("%s: a work line without a known source" % l["id"])
        if l["kind"] == "desk" and not l.get("approval"):
            notes.append("%s: a desk line without an approval" % l["id"])
    reg_url = ov.get("registry") or floor["registry"]["data"]
    reg, by = F.registry(reg_url)
    for l in lines:
        for k in l.get("keys", []):
            if k not in by:
                notes.append("%s: %s is not a code in the live registry" % (l["id"], k))
                # a switch the registry had when the version was read has gone: the source changed; a code it never
                # had cannot be found in its source
                flag(SOURCE_CHANGED if snap and k in snap["registry"]["rows"] else NOT_FOUND, k)
    pending = [l["id"] for l in lines if l["kind"] == "desk" and (l.get("approval") or {}).get("status") != "approved"]
    rules_ok = not notes
    checks.append({"check": "the source's own rules", "ok": rules_ok, "notes": notes,
                   "pending_desk_lines": pending})

    # 2. every extract, against its source
    notes, texts = [], {}
    for code, s in sources.items():
        if s["kind"] == "registry":
            continue
        try:
            texts[code] = F.source_text(s, ov["sources"].get(code))
        except Exception as e:
            notes.append("%s could not be read: %s" % (code, e))
    changed = {code for code, t in texts.items()
               if snap and hashlib.sha256(t.encode("utf-8")).hexdigest() != snap["sources"].get(code)}
    for l in lines:
        src = l.get("source")
        if l["kind"] != "work" or not src or sources[src["code"]]["kind"] == "registry":
            continue
        want = F.tidy_markup_spaces(F.normalise(l["text"]))
        if want not in texts.get(src["code"], ""):
            why = SOURCE_CHANGED if src["code"] in changed else NOT_FOUND
            near = F.nearest(want, texts.get(src["code"], ""))
            notes.append("%s: not found word for word in %s (%s)%s" % (l["id"], src["code"], why,
                                                                     "; the source reads: " + near if near else ""))
            flag(why, l["id"])
    checks.append({"check": "every extract, against its source", "ok": not notes, "notes": notes,
                   "sources_changed_since_snapshot": sorted(changed)})

    # 3. every key, against the registry version the floor was made from (its snapshot), pinned (AG Opus, through G,
    # 15 November 2026): a dated addition the registry made after that version, which keeps every word of the row as
    # it was and leaves its status as it was, is reported as later, never as a failure. The floor takes it in its
    # next version. Any other change to a keyed row, or to its status, still fails.
    notes, info, later = [], [], []
    pinned = (snap or {}).get("registry", {}).get("version")
    for k, row in sorted((snap or {}).get("registry", {}).get("rows", {}).items()):
        live = by.get(k)
        if not live:
            continue
        if live.get("description") == row["description"] and live.get("status_raw") == row["status_raw"]:
            continue
        added = later_addition(k, row["description"], live.get("description") or "", pinned)
        if added and live.get("status_raw") == row["status_raw"]:
            later.append({"switch": k, "added_in": added})
            info.append("%s: a dated addition in the registry's %s, later than %s, which this floor's rows are from. "
                        "The floor takes it in its next version." % (k, added, pinned))
        else:
            notes.append("%s: its row or status differs from the snapshot" % k)
            flag(SOURCE_CHANGED, k)
    if snap and reg["registry"]["version"] != pinned and not notes and not later:
        info.append("The registry's version has moved from %s to %s; no keyed switch's row or status changed. "
                    "The next version of the floor takes the new number." % (pinned, reg["registry"]["version"]))
    checks.append({"check": "every key, against the registry the floor was made from, " + str(pinned),
                   "ok": not notes, "notes": notes + info, "later_dated_additions": later})

    # 4. every registry row, cell by cell
    notes = []
    for l in lines:
        src = l.get("source")
        if src and sources[src["code"]]["kind"] == "registry":
            cells = l["text"].split(" · ")
            k = l["keys"][0]
            live = F.row_cells(by[k]) if k in by else None
            if live is None or cells != live:
                bad = [n for n, a, b in zip(["id", "description", "status_raw", "home_ap"], cells, live or [""] * 4) if a != b]
                notes.append("%s: the row for %s differs in %s" % (l["id"], k, ", ".join(bad) or "its cells"))
                flag(SOURCE_CHANGED, l["id"])
    checks.append({"check": "every registry row, cell by cell", "ok": not notes, "notes": notes})

    # 5. the root: this check never fails; a change opens a "floor-watch" issue
    root = sources["ROOT"]
    live_root = F.sha256_bytes(F.fetch(ov["sources"].get("ROOT") or root["url"]))
    root_changed = bool(snap) and live_root != snap["root"]["sha256"]
    checks.append({"check": "the root", "ok": True,
                   "notes": ["The root has changed since the snapshot: a floor-watch issue asks a desk to read it, "
                             "and the floor, again."] if root_changed else [],
                   "root_changed": root_changed, "live_sha256": live_root})

    # 6. the three forms, against the source
    notes = []
    with tempfile.TemporaryDirectory() as d:
        F.generate(out_dir=d)
        for name in ("floor.json", "floor.txt", "floor.schema.json", "page.html"):
            a = open(os.path.join(d, name), "rb").read()
            p = os.path.join(F.GENERATED, name)
            b = open(p, "rb").read() if os.path.exists(p) else b""
            if a != b:
                notes.append("%s differs from what the source generates" % name)
                flag(FORMS_MISMATCH)
    checks.append({"check": "the three forms, against the source", "ok": not notes, "notes": notes})

    passed = all(c["ok"] for c in checks)
    if floor["status"] == "final" and (pending or not passed):
        checks[0]["ok"] = False
        checks[0]["notes"].append("status is final, but %s" % ("desk lines wait for approval" if pending else "a check fails"))
        passed = False
    used = {k: v for k, v in ov.items() if v}
    result = {**({"test_addresses": used} if used.get("sources") or used.get("registry") else {}),
              "version": str(floor["version"]), "status": floor["status"], "fingerprint": fingerprint,
              "date": today, "passed": passed, "page_line": None, "page_lines": [], "named": [],
              "registry": {"floor_reads": floor["registry"]["version"], "live": reg["registry"]["version"]},
              "root_changed": root_changed, "checks": checks}
    return page_lines(result, flags)


def page_lines(result, flags):
    """The plain lines the page shows for a failing run, each with what it names, in the page's order. A failure
    that gives no line of its own (the floor's own rules broken, its snapshot missing) shows the third line, so the
    page never hides a failure."""
    if result["passed"]:
        flags = {}
    elif not flags:
        flags = {FORMS_MISMATCH: []}
    result["page_lines"] = [{"line": l, "named": sorted(set(flags[l]))} for l in PAGE_LINES if l in flags]
    result["page_line"] = result["page_lines"][0]["line"] if result["page_lines"] else None
    result["named"] = sorted({n for l in result["page_lines"] for n in l["named"]})
    return result


# ---------------------------------------------------------------- GitHub: the result, the snapshot, the watch

def gh(path, method="GET", body=None):
    req = urllib.request.Request("https://api.github.com" + path, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "User-Agent": F.UA,
                                          "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, (json.loads(raw) if raw else None)


def commit(path, text, message):
    import base64
    repo, branch = os.environ["GITHUB_REPOSITORY"], os.environ.get("GITHUB_REF_NAME", "main")
    rel = os.path.relpath(path, os.path.dirname(F.FLOOR)).replace(os.sep, "/")
    st, cur = gh("/repos/%s/contents/%s?ref=%s" % (repo, rel, branch))
    if st == 200 and base64.b64decode(cur["content"]).decode("utf-8") == text:
        print("unchanged:", rel)
        return
    body = {"message": message, "branch": branch, "content": base64.b64encode(text.encode("utf-8")).decode()}
    if st == 200:
        body["sha"] = cur["sha"]
    st, res = gh("/repos/%s/contents/%s" % (repo, rel), "PUT", body)
    print("committed:" if st in (200, 201) else "NOT committed (%s):" % st, rel)


def watch(result, snap):
    repo = os.environ["GITHUB_REPOSITORY"]
    gh("/repos/%s/labels" % repo, "POST", {"name": "floor-watch", "color": "8B6914",
                                          "description": "The root has changed: read it, and the floor, again"})
    st, open_ = gh("/repos/%s/issues?state=open&labels=floor-watch" % repo)
    if st == 200 and open_:
        print("a floor-watch issue is already open: #%d" % open_[0]["number"])
        return
    body = ("The root for AI has changed since floor version %s was read.\n\nRead the root, and the floor, again.\n\n"
            "Snapshot: %s\nNow: %s\nNoticed by the floor's checker on %s."
            % (result["version"], snap["root"]["sha256"], result["checks"][4]["live_sha256"], result["date"]))
    st, made = gh("/repos/%s/issues" % repo, "POST", {"title": "Floor watch: the root has changed", "body": body,
                                                     "labels": ["floor-watch"]})
    print("floor-watch issue opened: #%s" % (made or {}).get("number") if st == 201 else "floor-watch issue NOT opened (%s)" % st)


def main():
    floor, fingerprint = F.load()
    in_workflow = bool(os.environ.get("GITHUB_ACTIONS"))
    if "--snapshot" in sys.argv:
        snap = take_snapshot(floor)
        text = json.dumps(snap, ensure_ascii=False, indent=1) + "\n"
        p = snapshot_path(floor["version"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="\n").write(text)
        print(text)
        if in_workflow:
            commit(p, text, "floor: the snapshot of version %s, as its sources read now" % floor["version"])
        return
    p = snapshot_path(floor["version"])
    snap = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    result = check(floor, fingerprint, snap)
    if snap is None:
        result["checks"].append({"check": "the snapshot", "ok": False, "notes": ["no snapshot for this version yet"]})
        result["passed"] = False
        result = page_lines(result, {**{l["line"]: l["named"] for l in result["page_lines"]}, FORMS_MISMATCH: []})
    out = os.path.join(F.FLOOR, "checker", "result.json")
    before = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
    # the page shows the date of the last pass; a failing run carries the last pass forward
    result["last_passed"] = result["date"] if result["passed"] else before.get("last_passed")
    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    print(text)
    if "--write" in sys.argv:
        open(out, "w", encoding="utf-8", newline="\n").write(text)
        if in_workflow:
            commit(out, text, "floor: the checker's result, %s" % result["date"])
    if in_workflow and result["root_changed"]:
        watch(result, snap)


if __name__ == "__main__":
    main()
