# The floor's shared library: loading the source, normalising text, reading the sources, writing the three forms.
# Zero-Clause BSD, Studio G. Brief "phase 2, the floor, build" v2.
import hashlib
import html
import io
import json
import os
import re
import subprocess
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR = os.path.dirname(HERE)
SOURCE = os.path.join(FLOOR, "source", "floor.yaml")
GENERATED = os.path.join(FLOOR, "generated")
PAGE_URL = "https://aiethics.global/open-source/the-floor/"
REGISTRY_ROOM = "https://the420code.org/killswitches/"
UA = "the420code-open floor checker"


# ---------------------------------------------------------------- the source

def load(path=SOURCE):
    import yaml
    raw = open(path, "rb").read()
    return yaml.safe_load(raw.decode("utf-8"))["floor"], hashlib.sha256(raw).hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- normalising (brief Part Four)

QUOTES = {**{c: "'" for c in "‘’‚‛′`´"}, **{c: '"' for c in "“”„‟″"}}
DASHES = {c: "-" for c in "‐‑‒–—―−"}
SPACES = {c: " " for c in "       "}
TABLE = str.maketrans({**QUOTES, **DASHES, **SPACES})


def normalise(text):
    """Curly and straight quotation marks the same; hyphen, en dash and em dash the same; non-breaking spaces as
    spaces; every run of white space as one space."""
    text = (text or "").translate(TABLE).replace("​", "").replace("­", "")
    return re.sub(r"\s+", " ", text).strip()


def tidy_markup_spaces(text):
    """Spaces that markup leaves inside brackets, or before a full stop, a comma, a semicolon or a colon."""
    text = re.sub(r"([(\[]) +", r"\1", text)
    text = re.sub(r" +([)\]])", r"\1", text)
    return re.sub(r" +([.,;:])", r"\1", text)


def html_text(page):
    """HTML: scripts and styles dropped, tags stripped, entities read, then normalised."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return tidy_markup_spaces(normalise(html.unescape(page)))


def pdf_text(data):
    """PDF: text taken out with pdftotext. A hyphen at a line's end is kept, joining the two parts, only where the
    word is hyphenated elsewhere in the same paper; otherwise the break is removed and the parts join."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.pdf")
        open(p, "wb").write(data)
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", p, "-"], capture_output=True, check=True).stdout.decode("utf-8", "replace")
    out = out.replace("\r\n", "\n").replace("\f", "\n")
    # "elsewhere in the same paper" is read with every dash as one hyphen, as everywhere in the comparison
    flat = normalise(out)

    def join(m):
        a, b = m.group(1), m.group(2)
        hyphenated = re.search(r"(?<![\w-])" + re.escape(a) + "-" + re.escape(b) + r"(?![\w])", flat)
        return a + "-" + b if hyphenated else a + b
    out = re.sub(r"(\w+)[-‐‑­][ \t]*\n[ \t]*(\w+)", join, out)
    text = normalise(out)
    # pdftotext (poppler and xpdf both) already joins a word broken at a line's end and drops its hyphen, before
    # the rule above can see it. So the same rule, from the other side: a word that stands joined, where the same
    # paper writes it hyphenated elsewhere, takes its hyphen back. Today: social-credit (AP33), NON-NEGOTIABLE (AP38).
    for a, b in sorted(set(re.findall(r"(?<![\w-])([A-Za-z]{2,})-([A-Za-z]{2,})(?![\w-])", text))):
        text = re.sub(r"(?<![\w-])" + re.escape(a + b) + r"(?![\w-])", a + "-" + b, text)
    return text


def nearest(line_text, source_text, width=90):
    """Where a line's opening words stand in its source, for a note a desk can read."""
    words = line_text.split(" ")
    for n in (8, 5, 3):
        probe = " ".join(words[:n])
        i = source_text.find(probe)
        if i >= 0:
            return source_text[i:i + len(line_text) + 20][:width * 3]
    return None


def text_text(data):
    return normalise(data)


# ---------------------------------------------------------------- reading the sources

def fetch(url):
    if url.startswith("file:"):
        return open(url[5:], "rb").read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def source_text(src, url=None):
    """The normalised text of one source, from its address (or a test address)."""
    data = fetch(url or src["url"])
    if src["kind"] == "html":
        return html_text(data.decode("utf-8", "replace"))
    if src["kind"] == "pdf":
        return pdf_text(data)
    if src["kind"] == "text":
        return text_text(data.decode("utf-8", "replace"))
    raise ValueError("no text for kind " + src["kind"])


def registry(url):
    data = json.loads(fetch(url).decode("utf-8"))
    by = {}
    for s in data["switches"]:
        for label in s.get("labels") or [s["id"]]:
            by.setdefault(label, s)
    return data, by


def row_cells(s):
    """A registry row is its four cells: id, description, status_raw, home_ap."""
    return [s.get("id") or "", s.get("description") or "", s.get("status_raw") or "", s.get("home_ap") or ""]


# ---------------------------------------------------------------- the three forms

def short_title(src):
    t = src["title"]
    return ", ".join(t.split(", ")[:2]) if t.startswith("The Interior,") else t


def anchor(key):
    return REGISTRY_ROOM + "#" + re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


def is_heading(line):
    return "heading" in (line.get("roles") or [])


def short_line(line, sources):
    """One line of the short form (brief Part Two, 3)."""
    src = line.get("source")
    bracket = None
    if src:
        bracket = short_title(sources[src["code"]])
        if line.get("keys"):
            bracket += "; " + ", ".join(line["keys"])
    if is_heading(line):
        return "## " + line["text"] + (" [" + bracket + "]" if bracket else "")
    if line["kind"] == "work":
        return "> " + line["text"] + " [" + bracket + "]"
    return line["text"] + " [desk]"


def full_lines(floor):
    sources = floor["sources"]
    out = []
    for line in floor["lines"]:
        e = dict(line)
        if line.get("source"):
            s = dict(sources[line["source"]["code"]])
            e["source"] = {**line["source"], **{"title": s["title"], "url": s["url"], "version": s["version"],
                                                 "kind": s["kind"], **({"data": s["data"]} if "data" in s else {})}}
        if line.get("keys"):
            e["key_links"] = [anchor(k) for k in line["keys"]]
        e["short_form"] = short_line(line, sources)
        out.append(e)
    return out


def floor_txt(floor, fingerprint):
    body = "\n\n".join(short_line(l, floor["sources"]) for l in floor["lines"])
    reg = floor["registry"]
    foot = ("Version %s. Status: %s. Registry %s, %s.\nFingerprint (SHA-256 of the source, tag floor-v%s): %s\n%s"
            % (floor["version"], floor["status"], reg["version"], reg["date"], floor["version"], fingerprint, PAGE_URL))
    return body + "\n\n" + foot + "\n"


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": PAGE_URL + "floor.schema.json",
    "title": "The floor",
    "type": "object",
    "required": ["floor", "sources", "lines"],
    "properties": {
        "floor": {"type": "object",
                  "required": ["version", "status", "date", "registry", "note", "fingerprint", "tag", "page"],
                  "properties": {"version": {"type": "string"}, "status": {"enum": ["draft", "final"]},
                                 "date": {"type": "string"}, "note": {"type": "string"},
                                 "fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                 "tag": {"type": "string"}, "page": {"type": "string"},
                                 "registry": {"type": "object", "required": ["version", "date", "data"]}}},
        "sources": {"type": "object", "additionalProperties": {
            "type": "object", "required": ["title", "url", "version", "kind"],
            "properties": {"kind": {"enum": ["html", "pdf", "text", "registry"]}}}},
        "lines": {"type": "array", "items": {
            "type": "object", "required": ["id", "part", "kind", "text", "short_form"],
            "properties": {
                "id": {"type": "string", "pattern": "^F(-H|[0-8])\\.[0-9]+[a-z]?$"},
                "part": {"type": "string"},
                "kind": {"enum": ["work", "desk"]},
                "text": {"type": "string", "minLength": 1},
                "source": {"type": "object", "required": ["code", "title", "url", "version", "kind"]},
                "keys": {"type": "array", "items": {"type": "string", "pattern": "^KS-"}},
                "key_links": {"type": "array", "items": {"type": "string"}},
                "roles": {"type": "array", "items": {"enum": ["heading", "test-line"]}},
                "joins": {"type": "array", "items": {"type": "string"}},
                "approval": {"type": "object", "required": ["status", "by"],
                             "properties": {"status": {"enum": ["pending", "approved"]}}},
                "short_form": {"type": "string"}},
            "allOf": [
                {"if": {"properties": {"kind": {"const": "work"}}}, "then": {"required": ["source"]}},
                {"if": {"properties": {"kind": {"const": "desk"}}}, "then": {"required": ["approval"]}}]}}},
}


def floor_json(floor, fingerprint):
    head = {k: floor[k] for k in ("version", "status", "date", "registry", "note")}
    head = {**head, "version": str(head["version"]), "date": str(head["date"]),
            "fingerprint": fingerprint, "tag": "floor-v%s" % floor["version"], "page": PAGE_URL}
    lines = full_lines(floor)
    for l in lines:
        l["part"] = str(l["part"])
    doc = {"floor": head, "sources": floor["sources"], "lines": lines}
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def esc(s):
    return html.escape(s or "", quote=True)


def page_html(floor, fingerprint, json_sha, txt_sha):
    """The page's body, for aiethics.global's own shell (brief Part Two, 1). Plain text only: every line escaped."""
    sources = floor["sources"]
    out = []
    head = [l for l in floor["lines"] if l["part"] == "H"]
    rest = [l for l in floor["lines"] if l["part"] != "H"]
    out.append('<div class="fl-head">')
    for l in head:
        out.append("<p>%s</p>" % esc(l["text"]))
    if floor["status"] == "final":
        out.append('<p class="fl-status">Approved, %s.</p>' % esc(str(floor["date"])))
    else:
        out.append('<p class="fl-status">Draft. Not yet approved.</p>')
    out.append('<p class="fl-small">Lines with a source are the work’s own. Every other line, headings included, is the desk’s.</p>')
    out.append("</div>")
    for l in rest:
        src = l.get("source")
        lid = esc(l["id"])
        if is_heading(l):
            tag = "h2" if l["id"].endswith(".0") else "h3"
            out.append('<%s id="%s">%s</%s>' % (tag, lid.lower(), esc(l["text"]), tag))
            if src:
                out.append('<p class="fl-small fl-src">%s</p>' % source_note(l, sources))
            continue
        if l["kind"] == "work":
            out.append('<blockquote class="fl-work" id="%s"><p>%s</p></blockquote>' % (lid.lower(), esc(l["text"])))
            out.append('<p class="fl-small fl-src"><span class="fl-id">%s</span> %s</p>' % (lid, source_note(l, sources)))
        else:
            out.append('<p class="fl-desk" id="%s">%s</p>' % (lid.lower(), esc(l["text"])))
            pend = "" if (l.get("approval") or {}).get("status") == "approved" else " Waiting for approval."
            out.append('<p class="fl-small fl-src"><span class="fl-id">%s</span> Desk wording.%s</p>' % (lid, pend))
    reg = floor["registry"]
    out.append('<div class="fl-foot">')
    out.append("<p>Version %s. Registry %s, %s.</p>" % (esc(str(floor["version"])), esc(reg["version"]), esc(str(reg["date"]))))
    out.append('<p>Fingerprint, the SHA-256 of the source as tagged floor-v%s: <code class="fl-hash">%s</code></p>'
               % (esc(str(floor["version"])), fingerprint))
    out.append('<p>The structured file, <a href="floor.json">floor.json</a>: <code class="fl-hash">%s</code></p>' % json_sha)
    out.append('<p>The short form, ready to paste, <a href="floor.txt">floor.txt</a>: <code class="fl-hash">%s</code></p>' % txt_sha)
    out.append("<!--checker-->")
    out.append("</div>")
    return "\n".join(out) + "\n"


def source_note(l, sources):
    src = l["source"]
    s = sources[src["code"]]
    bits = [esc(s["title"])]
    if src.get("place"):
        bits.append(esc(src["place"]))
    note = ", ".join(bits) + '. <a href="%s">%s</a>' % (esc(s["url"]), esc(s["url"].replace("https://", "")))
    if "test-line" in (l.get("roles") or []):
        note += ' <span class="fl-test">Test line</span>'
    if l.get("keys"):
        note += " " + " ".join('<a class="fl-key" href="%s">%s</a>' % (esc(anchor(k)), esc(k)) for k in l["keys"])
    return note


def generate(out_dir=GENERATED, source=SOURCE):
    """All three forms, from the source alone, in one run."""
    floor, fingerprint = load(source)
    os.makedirs(out_dir, exist_ok=True)
    fj = floor_json(floor, fingerprint).encode("utf-8")
    ft = floor_txt(floor, fingerprint).encode("utf-8")
    sj = (json.dumps(SCHEMA, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    ph = page_html(floor, fingerprint, sha256_bytes(fj), sha256_bytes(ft)).encode("utf-8")
    files = {"floor.json": fj, "floor.txt": ft, "floor.schema.json": sj, "page.html": ph}
    for name, data in files.items():
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
    return fingerprint, files
