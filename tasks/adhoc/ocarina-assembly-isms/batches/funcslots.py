#!/usr/bin/env python3
"""funcslots.py FILE:FUNC [FILE:FUNC ...] — for each function print its slot-named declarations and
up to N use lines per variable (assignments marked with '='), plus assignment count and whether the
variable is read after the last loop-closing brace that follows an assignment inside a loop."""
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from classify import SLOT_DECL, SRC, functions  # noqa: E402

MAXUSE = int(sys.argv[1]) if sys.argv[1].isdigit() else 5
specs = sys.argv[2:] if sys.argv[1].isdigit() else sys.argv[1:]

for spec in specs:
    path, fname = spec.split(":")
    lines = open(SRC + "/" + path, errors="replace").read().split("\n")
    for name, s, e in functions(lines):
        if name != fname:
            continue
        body = lines[s + 1 : e]
        sig = lines[s].strip()
        print("=" * 100)
        print("%s:%d %s   (%d lines)" % (path, s + 1, sig, e - s))
        seen = []
        for k, ln in enumerate(body):
            m = SLOT_DECL.match(ln)
            if m and m.group(1) not in seen:
                seen.append(m.group(1))
        for v in seen:
            pat = re.compile(r"\b%s\b" % v)
            uses = [(s + 2 + k, ln) for k, ln in enumerate(body) if pat.search(ln.split("//")[0])]
            assigns = sum(1 for _, ln in uses if re.search(r"\b%s\s*(\[[^\]]*\])?\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--)" % v, ln) or re.search(r"(\+\+|--)\s*%s\b" % v, ln))
            print("  -- %s: %d refs, %d assigns" % (v, len(uses), assigns))
            for lineno, ln in uses[:MAXUSE]:
                print("     %5d| %s" % (lineno, ln.strip()[:150]))
            if len(uses) > MAXUSE:
                print("     ... %d more" % (len(uses) - MAXUSE))
