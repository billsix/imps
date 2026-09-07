#!/usr/bin/env python3
"""Build the COMPLETE rename table -- the input to the whole split.

inventory.py derives 205 rows by parsing the declaration under each provenance
comment. This adds the two it structurally cannot, and computes the two extra
columns the split needs:

  * scope      -- the files a rename may touch, defined as the files that
                  contained the OLD name at the pin. This is exact, and it is
                  what makes file-local statics safe: D_80A65F38 lives in one
                  file, so renaming it to sColChkInfoInit cannot disturb the 60
                  other files that already have their own static of that name.
  * confidence -- HIGH / GUESS / oot, for the short declaration-site comment.

Writes rename_table.tsv next to this script. Run from anywhere:
    python3 tasks/adhoc/ocarina-split-rename-patch/build_rename_table.py
"""
import csv
import os
import re
import subprocess
import sys

from _common import SOURCE_PATHS, git, pin_sha

HERE = os.path.dirname(os.path.abspath(__file__))

# The two renames inventory.py cannot derive, with their definition sites.
#   Struct_8016E320 -- a typedef; the name is on the CLOSING brace, so there is
#     no declaration on the line below the comment to parse.
#   UnkRumbleStruct -- a TYPE rename carrying no provenance comment at all, and
#     not address-named, so the git-grep audit never sees it either.
EXTRA = [
    ("Struct_8016E320", "SeqRequest", "oot",
     "soh/src/code/audio_seq.c", 0),
    ("UnkRumbleStruct", "RumbleMgr", "llm",
     "soh/include/z64.h", 0),
]


def files_containing(rev, name):
    """Files at `rev` holding `name` as a whole word. -l lists names only;
    -w matches whole words so D_8016E32 never matches D_8016E320."""
    out = git("grep", "-lw", name, rev, "--", *SOURCE_PATHS, check=False)
    # `git grep <rev>` prefixes each path with "<rev>:"; strip it back off.
    return sorted(line.split(":", 1)[1] for line in out.split() if ":" in line)


def confidence_of(old, provenance):
    """Read HIGH/GUESS out of the definition-site comment, for the short
    declaration comment. oot-sourced names are simply tagged 'oot'."""
    if provenance == "oot":
        return "oot"
    out = git("grep", "-h", f"was {old}", check=False)
    match = re.search(r"LLM generated name \((HIGH|GUESS)\)", out)
    return match.group(1) if match else "HIGH"


def main():
    rows = []
    with open(os.path.join(HERE, "inventory.tsv")) as handle:
        rows = [(r["old"], r["new"], r["provenance"], r["def_file"],
                 int(r["def_line"])) for r in csv.DictReader(handle, delimiter="\t")]
    have = {r[0] for r in rows}
    rows += [e for e in EXTRA if e[0] not in have]

    pin = pin_sha()
    out_path = os.path.join(HERE, "rename_table.tsv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["old", "new", "provenance", "confidence",
                         "def_file", "def_line", "scope"])
        for old, new, provenance, def_file, def_line in sorted(
                rows, key=lambda r: (r[3], r[4], r[0])):
            scope = files_containing(pin, old)
            if not scope:
                print(f"  WARNING: {old} not found at the pin", file=sys.stderr)
            writer.writerow([old, new, provenance, confidence_of(old, provenance),
                             def_file, def_line, ",".join(scope)])
            rows_written = True

    with open(out_path) as handle:
        n = sum(1 for _ in handle) - 1
    print(f"rename table rows : {n}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
