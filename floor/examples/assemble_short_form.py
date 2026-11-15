# Read floor.json and assemble the short form from it. Zero-Clause BSD, Studio G.
#
#   python3 assemble_short_form.py [path/to/floor.json] > floor.txt
#
# Every line in floor.json carries its own short form; this joins them, and adds the foot, as floor.txt has it.
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "floor/generated/floor.json"
doc = json.load(open(path, encoding="utf-8"))
head = doc["floor"]
reg = head["registry"]
body = "\n\n".join(line["short_form"] for line in doc["lines"])
foot = ("Version %s. Status: %s. Registry %s, %s.\nFingerprint (SHA-256 of the source, tag %s): %s\n%s"
        % (head["version"], head["status"], reg["version"], reg["date"], head["tag"], head["fingerprint"], head["page"]))
sys.stdout.reconfigure(encoding="utf-8", newline="\n")
sys.stdout.write(body + "\n\n" + foot + "\n")
