#!/usr/bin/env python3
"""Tag every header DECLARATION of a renamed symbol with its provenance.

WHEN TO RUN IT
    After a batch of decomp renames, before regenerating the patches. Run it
    until `check_renames.py declarations` reports no untagged sites.

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
re-run after a pin bump or a new rename batch adds declarations.

USAGE
    n64/OcarinaOfTime/tools/tag_declarations.py [--dry-run]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from renames_common import (CHECKOUT, INLINE_TAG_RE, git, is_comment_only,
                            is_marker_line, rename_range, renamed_symbols)

# Lines that already end in a comment: append after it rather than starting a
# second "//" run. (The RumbleMgr typedef names itself on "} RumbleMgr; //
# size = 0x10E".)
HAS_TRAILING_COMMENT = re.compile(r"//")


def _confidence(old):
    """HIGH/GUESS, read from the long definition-site comment."""
    out = git("grep", "-h", f"was {old}", check=False)
    match = re.search(r"LLM generated name \((HIGH|GUESS)\)", out)
    return match.group(1) if match else "HIGH"


def tag_for(row):
    """The short bracket tag: authoritative upstream name, or our guess."""
    if row["provenance"] == "oot":
        return "oot"
    return f"LLM:{row['confidence']}"


def main(dry_run=False):
    # {new: (old, provenance)} straight from the tree's provenance comments --
    # no external table to keep in sync.
    table = {new: {"old": old, "provenance": prov, "confidence": ""}
             for new, (old, prov) in renamed_symbols().items()}
    for new, row in table.items():
        row["confidence"] = _confidence(row["old"]) if row["provenance"] == "llm" else "oot"

    touched = [p for p in git("diff", "--name-only", rename_range()).split() if p]
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
    main(dry_run="--dry-run" in sys.argv)
