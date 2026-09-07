#!/usr/bin/env python3
"""Close the traceability gap: put a short provenance comment at every header
DECLARATION site of a renamed symbol.

Why: the renaming convention puts a full provenance comment above each symbol's
DEFINITION, which leaves the DECLARATION bare -- and the declaration in
soh/include/functions.h is where a reader meets the name first, with no way to
tell a guessed name from an upstream one. See tasks/ocarina-split-rename-patch.md.

Form (maintainer's discretion, 2026-09-07): a SHORT inline tag, not a copy of
the definition-site prose, so two shared headers do not gain 66 long lines:

    void AudioMgr_StopAllSfx(void);            // was func_800C3C20 [oot]
    void Audio_RestorePrevBgm(void);           // was func_800F5B58 [LLM:HIGH]

It stays greppable by the same handle as the long form ("was func_"), and
"[oot]" vs "[LLM:...]" says at a glance whether the name is authoritative or a
guess. The full rationale + citation URL stays at the definition.

Commented-out placeholder declarations ("// ? Audio_ResetData(?);") are skipped:
they are not declarations, and appending a tag there reads badly.

EVERY tag is APPENDED to an existing line -- never inserted as a new line. That
is deliberate and load-bearing for the equivalence proof: no file changes its
line count, so __LINE__/__FILE__ and every debug print that uses them are
untouched, and the preprocessed translation units are provably identical to the
pre-split tree. The RumbleMgr typedef names itself on its closing brace, which
already carries "// size = 0x10E", so its tag is appended after that.

This script is IDEMPOTENT -- running it twice is a no-op -- so it is safe to
re-run after a pin bump adds new declarations.

Run from anywhere:
    python3 tasks/adhoc/ocarina-split-rename-patch/add_decl_comments.py [--dry-run]
"""
import csv
import os
import re
import sys

from _common import (CHECKOUT, is_comment_only, is_marker_line,
                     renamed_files)

HERE = os.path.dirname(os.path.abspath(__file__))

# Lines that already end in a comment: append after it rather than starting a
# second "//" run. (The RumbleMgr typedef names itself on "} RumbleMgr; //
# size = 0x10E".)
HAS_TRAILING_COMMENT = re.compile(r"//")


def tag_for(row):
    """The short bracket tag: authoritative upstream name, or our guess."""
    if row["provenance"] == "oot":
        return "oot"
    return f"LLM:{row['confidence']}"


def main(dry_run=False):
    with open(os.path.join(HERE, "rename_table.tsv")) as handle:
        table = {r["new"]: r for r in csv.DictReader(handle, delimiter="\t")}

    touched = renamed_files()
    word_re = re.compile("|".join(rf"\b{re.escape(n)}\b" for n in table))

    edits = 0
    for path in sorted(touched):
        if not path.endswith((".h", ".hpp")):
            continue
        full = os.path.join(CHECKOUT, path)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8") as handle:
            lines = handle.read().splitlines()

        out, changed = [], False
        for index, line in enumerate(lines):
            match = word_re.search(line)
            # Already traceable? (a marker within 3 lines above, or inline)
            already = ("was " in line
                       or any(is_marker_line(a) for a in lines[max(0, index - 3):index]))
            if not match or already or is_comment_only(line):
                out.append(line)
                continue
            row = table[match.group(0)]
            tag = f"was {row['old']} [{tag_for(row)}]"
            # Append to an existing trailing comment instead of opening a second
            # one, so the line stays valid and readable.
            joiner = ", " if HAS_TRAILING_COMMENT.search(line) else "  // "
            out.append(f"{line}{joiner}{tag}")
            changed, edits = True, edits + 1

        if changed:
            print(f"  {path}")
            if not dry_run:
                with open(full, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(out) + "\n")

    print(f"\ndeclaration sites annotated: {edits}"
          + ("  (dry run, nothing written)" if dry_run else ""))


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main(dry_run="--dry-run" in sys.argv)
