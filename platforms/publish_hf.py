"""A copy of the Embryo on Hugging Face, made from a tagged version at home, never by hand (platforms brief, rule 2).

    HF_TOKEN=... python platforms/publish_hf.py --repo Studio-G-Open-Source/the-floor --type dataset \
        --tag floor-v1.0 --card platforms/huggingface/the-floor \
        --file floor/generated/floor.txt --file floor/generated/floor.json ...

It builds the copy from the tag (git show), with the card and the licence file beside it; creates the repository
private (it is made public only on launch day); uploads; turns discussions off (rule 8: not another inbox); and then
reads the files back and checks each one's SHA-256 against home. The token comes from the environment, never a file.

Zero-Clause BSD.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--type", default="dataset", choices=["dataset", "space", "model"])
    ap.add_argument("--tag", required=True)
    ap.add_argument("--card", required=True, help="a folder with README.md and LICENSE.md")
    ap.add_argument("--file", action="append", required=True)
    ap.add_argument("--space-sdk", default="static")
    a = ap.parse_args()
    from huggingface_hub import HfApi
    api = HfApi(token=os.environ["HF_TOKEN"])
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    tmp = tempfile.mkdtemp(prefix="hfcopy-")
    want = {}
    for f in a.file:
        data = subprocess.run(["git", "-C", root, "show", "%s:%s" % (a.tag, f)], capture_output=True, check=True).stdout
        name = os.path.basename(f)
        open(os.path.join(tmp, name), "wb").write(data)
        want[name] = hashlib.sha256(data).hexdigest()
    for name in ("README.md", "LICENSE.md"):
        shutil.copy(os.path.join(root, a.card, name), os.path.join(tmp, name))
    kw = {"space_sdk": a.space_sdk} if a.type == "space" else {}
    api.create_repo(a.repo, repo_type=a.type, private=True, exist_ok=True, **kw)
    info = api.repo_info(a.repo, repo_type=a.type)
    if not info.private:
        sys.exit("the repository is public already: nothing uploaded. It is made public only on launch day.")
    commit = api.upload_folder(folder_path=tmp, repo_id=a.repo, repo_type=a.type,
                               commit_message="%s, from the home repository's tag %s" % (a.repo.split("/")[-1], a.tag))
    # discussions and pull requests off (platforms brief, rule 8)
    req = urllib.request.Request("https://huggingface.co/api/%ss/%s/settings" % (a.type, a.repo), method="PUT",
                                 data=json.dumps({"discussionsDisabled": True}).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["HF_TOKEN"],
                                          "Content-Type": "application/json", "User-Agent": "studiog-copier"})
    try:
        urllib.request.urlopen(req, timeout=60)
        discussions = "off"
    except urllib.error.HTTPError as e:
        discussions = "not turned off (%s): turn off in the repository's settings" % e.code
    # read back, and check each file against home
    got = {}
    for name, sha in want.items():
        path = api.hf_hub_download(a.repo, name, repo_type=a.type, revision=commit.oid, local_dir=os.path.join(tmp, "back"))
        got[name] = hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
    info = api.repo_info(a.repo, repo_type=a.type)
    print(json.dumps({"repo": a.repo, "type": a.type, "private": info.private, "commit": commit.oid, "tag": a.tag,
                      "discussions": discussions, "files_match_home": got,
                      "address": "https://huggingface.co/%s%s" % ("" if a.type == "model" else a.type + "s/", a.repo)},
                     indent=1))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
