#!/usr/bin/env python3
"""Build the rename inventory that drives the patch split.

Every rename carries a provenance comment above its DEFINITION (completeness.py
proves this), so walk the post-commit tree, find each comment, and read the new
name off the declaration below it. Emits a TSV to stdout and to inventory.tsv:

    old <TAB> new <TAB> provenance <TAB> def_file <TAB> def_line

CAVEAT -- this is a starting point, not an oracle. It parses C declarations with
a regex, so it can mis-pick a type for a variable name. Hand-verify every row
before driving a rename off it. It also cannot resolve two rows by construction:

  * Struct_8016E320 -> SeqRequest  (a typedef; the name is on the CLOSING brace,
    not the line under the comment)
  * UnkRumbleStruct -> RumbleMgr   (a TYPE rename with no provenance comment at
    all, so there is nothing here to find -- see the task doc)

Run from the repo root:
    python3 tasks/adhoc/ocarina-split-rename-patch/inventory.py
"""
import collections
import csv
import os
import re
import sys

from _common import (CHECKOUT, CITED_RE, MARKERS, git, is_marker_line)

IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

# C keywords and the decomp's integer typedefs -- never the declared name.
NOT_A_NAME = {
    "static", "const", "void", "u8", "s8", "u16", "s16", "u32", "s32",
    "f32", "f64", "u64", "s64", "char", "int", "float", "double", "struct",
    "union", "enum", "unsigned", "signed", "extern", "typedef", "volatile",
    "register", "long", "short",
}


def declared_name(decl):
    """The identifier a C declaration introduces, or '' if unparseable."""
    # A '(' only means "function" if it comes before any '=' or '[' -- otherwise
    # it belongs to an initializer, e.g.
    #     char sSfxDistOverPrintMsg[] = VT_COL(RED, WHITE) "...";
    # where taking the ident before '(' would yield the macro VT_COL.
    def first(chars):
        found = [decl.index(c) for c in chars if c in decl]
        return min(found) if found else len(decl)

    if first("(") < first("=["):
        # A function: the name is the identifier immediately before '('.
        match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", decl)
        return match.group(1) if match else ""
    # Data: the name is the LAST identifier before the first '[', '=' or ';'.
    # Taking the first identifier would grab the TYPE (OSTime, Gfx, Vec3f...).
    head = re.split(r"[\[=;]", decl, maxsplit=1)[0]
    candidates = [token for token in IDENT_RE.findall(head)
                  if token not in NOT_A_NAME
                  and not re.match(r"^(func_|D_|Struct_)", token)]
    return candidates[-1] if candidates else ""


def main():
    # -l lists only the filenames that match; -e supplies each pattern.
    files = git("grep", "-l", "-e", MARKERS[0], "-e", MARKERS[1]).split()

    rows, unresolved = [], []
    for path in files:
        with open(os.path.join(CHECKOUT, path),
                  encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        for index, line in enumerate(lines):
            if not is_marker_line(line):
                continue
            cited = CITED_RE.search(line)
            if not cited:
                continue
            provenance = ("oot" if MARKERS[1] in line else "llm")
            # Walk past any continuation lines of a multi-line comment.
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].lstrip().startswith("//"):
                cursor += 1
            decl = lines[cursor] if cursor < len(lines) else ""
            new = declared_name(decl)
            if new:
                rows.append((cited.group(1), new, provenance, path, cursor + 1))
            else:
                unresolved.append((path, index + 1, cited.group(1),
                                   decl.strip()[:70]))

    rows.sort(key=lambda row: (row[3], row[4]))       # group by defining file
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "inventory.tsv")
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["old", "new", "provenance", "def_file", "def_line"])
        writer.writerows(rows)

    kinds = collections.Counter(row[2] for row in rows)
    reused = [name for name, count
              in collections.Counter(row[1] for row in rows).items() if count > 1]
    print(f"renames inventoried : {len(rows)}")
    print(f"  from zeldaret/oot : {kinds.get('oot', 0)}")
    print(f"  LLM-deduced       : {kinds.get('llm', 0)}")
    print(f"unresolved by parser: {len(unresolved)}")
    for item in unresolved:
        print(f"  {item[0]}:{item[1]}  {item[2]}  |  {item[3]}")
    print(f"new names reused for >1 old symbol: {reused or 'none'}")
    print(f"definition files    : {len(set(row[3] for row in rows))}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
