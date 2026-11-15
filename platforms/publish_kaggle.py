"""A copy of the Embryo on Kaggle, made from a tagged version at home, never by hand (platforms brief, rule 2).

    KAGGLE_API_TOKEN=... python platforms/publish_kaggle.py --id OWNER/the-floor --title "The floor" \
        --subtitle "..." --tag floor-v1.0 --card platforms/huggingface/the-floor \
        --file floor/generated/floor.txt ...

It builds the copy from the tag (git show), with the licence file beside it and the card as the description;
creates the dataset private (it is made public only on launch day), or adds a new version if it exists; waits for
Kaggle to process it; then downloads it back and checks each file's SHA-256 against home. Kaggle's discussions cannot
be turned off: the weekly gathering lists them for reading by hand. The token comes from the environment.

Zero-Clause BSD.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--card", required=True, help="a folder with README.md (its body is the description) and LICENSE.md")
    ap.add_argument("--file", action="append", required=True)
    ap.add_argument("--keyword", action="append", default=[])
    a = ap.parse_args()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    tmp = tempfile.mkdtemp(prefix="kgcopy-")
    want = {}
    for f in a.file:
        data = subprocess.run(["git", "-C", root, "show", "%s:%s" % (a.tag, f)], capture_output=True, check=True).stdout
        name = os.path.basename(f)
        open(os.path.join(tmp, name), "wb").write(data)
        want[name] = hashlib.sha256(data).hexdigest()
    shutil.copy(os.path.join(root, a.card, "LICENSE.md"), os.path.join(tmp, "LICENSE.md"))
    card = open(os.path.join(root, a.card, "README.md"), encoding="utf-8").read()
    body = re.sub(r"^---\n.*?\n---\n", "", card, flags=re.S).strip()        # the card without Hugging Face's header
    meta = {"title": a.title, "subtitle": a.subtitle, "id": a.id, "description": body,
            "licenses": [{"name": "other"}], "keywords": a.keyword, "isPrivate": True}
    json.dump(meta, open(os.path.join(tmp, "dataset-metadata.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    owner, slug = a.id.split("/")
    exists = any(d.ref == a.id for d in (api.dataset_list(user=owner) or []))
    if exists:
        r = api.dataset_create_version(tmp, "from the home repository's tag %s" % a.tag, dir_mode="zip", quiet=True)
    else:
        r = api.dataset_create_new(tmp, public=False, dir_mode="zip", quiet=True)
    status = getattr(r, "status", None) or getattr(r, "error", None) or str(r)
    # wait for Kaggle to process it, then read it back
    back = os.path.join(tmp, "back")
    got = {}
    for _ in range(30):
        time.sleep(10)
        try:
            shutil.rmtree(back, ignore_errors=True)
            api.dataset_download_files(a.id, path=back, unzip=True, quiet=True)
            got = {n: hashlib.sha256(open(os.path.join(back, n), "rb").read()).hexdigest() == s
                   for n, s in want.items() if os.path.exists(os.path.join(back, n))}
            if len(got) == len(want):
                break
        except Exception as e:      # still processing
            status = "%s; waiting (%s)" % (status, type(e).__name__)
    print(json.dumps({"id": a.id, "created_as_new": not exists, "kaggle_said": str(status)[:300], "private": True,
                      "files_match_home": got, "address": "https://www.kaggle.com/datasets/%s" % a.id}, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    if len(got) != len(want) or not all(got.values()):
        sys.exit("not every file came back as it is at home")


if __name__ == "__main__":
    main()
