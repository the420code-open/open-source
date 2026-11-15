"""Every seed from 1,000,000 up that any packet on this computer has used, by engine. Read-only."""
import json, os, re, sys, collections
roots = [r"…"]
SEEDLINE = re.compile(r'"seed":\s*(\d+)')
used = collections.defaultdict(set)
files = 0
skipped = 0
for root in roots:
    for dp, dn, fn in os.walk(root):
        if ".git" in dp.split(os.sep):
            continue
        m = re.search(r"seeds-(\d+)-(\d+)", dp)
        if m and int(m.group(2)) < 1000000:
            skipped += 1
            continue
        for f in fn:
            if f != "packet.jsonl":
                continue
            p = os.path.join(dp, f)
            files += 1
            with open(p, encoding="utf-8", errors="replace") as fh:
                head = fh.readline()
                try:
                    h = json.loads(head)
                except ValueError:
                    continue
                eng = "second" if "browser" in json.dumps(h.get("engine", ""))  or "browser" in json.dumps(h)[:400] else "reference"
                for ln in fh:
                    mm = SEEDLINE.search(ln[:60])
                    if mm:
                        s = int(mm.group(1))
                        if s >= 1000000:
                            used[eng].add(s)
print("packets read:", files, "dirs skipped by name (seeds under 1,000,000):", skipped)
for eng, ss in used.items():
    ss = sorted(ss)
    # ranges
    rs, a = [], None
    for s in ss:
        if a is None: a = b = s
        elif s == b + 1: b = s
        else: rs.append((a, b)); a = b = s
    if a is not None: rs.append((a, b))
    print(eng, len(ss), rs[:40])
