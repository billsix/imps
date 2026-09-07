#!/usr/bin/env python3
"""Size the traceability gap this task exists to close.

The renaming convention (tasks/reference/ocarina/decomp-renaming.md) puts the
provenance comment above each symbol's DEFINITION. That leaves the DECLARATION
bare -- so a reader of soh/include/functions.h meets a renamed symbol with no
sign that the name is a guess rather than an upstream one.

This reports every HEADER site holding a renamed symbol with no provenance
comment within 3 lines above it. Once the task's step 3 lands, it must report 0.

Non-header sites are counted but not listed: those are ordinary call sites,
which the convention deliberately does NOT require to carry a comment.

Run from the repo root (needs inventory.tsv -- run inventory.py first):
    python3 tasks/adhoc/ocarina-split-rename-patch/header_gap.py
Exits non-zero while any header site is still uncommented, so it works as a gate.
"""
import collections
import csv
import os
import re
import sys

from _common import (CHECKOUT, INLINE_TAG_RE, is_comment_only,
                     is_marker_line, renamed_files)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    inventory = os.path.join(here, "inventory.tsv")
    if not os.path.exists(inventory):
        raise SystemExit("run inventory.py first (no inventory.tsv)")
    with open(inventory) as handle:
        new_names = {row["new"] for row in csv.DictReader(handle, delimiter="\t")}
    # The one type rename the inventory cannot derive (no comment to parse).
    new_names.add("RumbleMgr")

    touched = renamed_files()
    word_re = re.compile("|".join(rf"\b{re.escape(n)}\b" for n in new_names))

    header_sites = collections.defaultdict(list)
    other_total = other_bare = 0
    for path in touched:
        full = os.path.join(CHECKOUT, path)
        if not os.path.isfile(full):
            continue                       # deleted by the commit
        with open(full, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        for index, line in enumerate(lines):
            # A commented-out placeholder is not a declaration site.
            if not word_re.search(line) or is_comment_only(line):
                continue
            # Traceable either by the long definition-style marker above, or
            # by the short inline declaration tag this task introduced
            # ("// was func_800C3C20 [oot]").
            commented = (INLINE_TAG_RE.search(line) is not None
                         or any(is_marker_line(above)
                                for above in lines[max(0, index - 3):index]))
            # A typedef names itself on its CLOSING brace ("} RumbleMgr;"), so
            # its comment sits above the "typedef struct {" that opened it --
            # far outside a 3-line window. Walk back to find it.
            if not commented and line.lstrip().startswith("}"):
                for back in range(index - 1, max(-1, index - 400), -1):
                    if lines[back].strip().startswith("typedef struct"):
                        commented = back > 0 and is_marker_line(lines[back - 1])
                        break
            if path.endswith((".h", ".hpp")):
                header_sites[path].append((index + 1, commented))
            else:
                other_total += 1
                other_bare += not commented

    print("=== HEADER sites holding a renamed symbol ===")
    total = bare = 0
    for path, sites in sorted(header_sites.items()):
        uncommented = sum(1 for _, commented in sites if not commented)
        total += len(sites)
        bare += uncommented
        print(f"  {path:52s} {len(sites):4d} sites, "
              f"{uncommented:4d} with NO provenance")
    print(f"  {'TOTAL':52s} {total:4d} sites, {bare:4d} with NO provenance")
    print(f"\nnon-header sites: {other_total} ({other_bare} uncommented) "
          "-- call sites, comment not required by the convention")
    return 1 if bare else 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
