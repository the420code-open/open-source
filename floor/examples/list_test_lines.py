# List the floor's test lines with their keys. Zero-Clause BSD, Studio G.
#
#   python3 list_test_lines.py [path/to/floor.json]
#
# A test line is a line whose roles include "test-line". Each is printed with its id, its kill switches (the
# registry codes, with a link to each switch's row), its source, and its text.
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "floor/generated/floor.json"
doc = json.load(open(path, encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
for line in doc["lines"]:
    if "test-line" in (line.get("roles") or []):
        print(line["id"], ", ".join(line.get("keys", [])))
        for link in line.get("key_links", []):
            print("  ", link)
        print("   source:", line["source"]["title"], line["source"]["url"])
        print("  ", line["text"])
        print()
