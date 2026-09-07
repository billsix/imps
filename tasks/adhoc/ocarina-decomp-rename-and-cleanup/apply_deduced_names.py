#!/usr/bin/env python3
"""Apply DEDUCED names -- ones no upstream decomp provides -- one per commit.

Unlike the oot adoptions, every name here is an inference, so it is marked more
heavily (William Emerison Six <billsix@gmail.com>, 2026-09-07): the marking
density tracks the uncertainty.

  definition   // LLM generated name (HIGH|GUESS), was <old>: <reason>
  declaration  ...;  // was <old> [LLM:HIGH]
  CALL SITES   ...;  // was <old> [LLM:HIGH]      <-- adopted names get none

A reader who meets the name anywhere therefore knows it is inferred and can go
read the reasoning at the definition. `git grep '\\[LLM:'` lists every place the
decomp leans on an inference.

Input: batch.tsv -- old, new, confidence(HIGH|GUESS), reason, def_file
Every row must come from having READ the function and its callers. A name
invented from a signature is the one outcome that damages a decomp; when the
body will not support a specific claim, leave the symbol out of the file.

Run from the imps repo root:
    python3 tasks/adhoc/ocarina-decomp-rename-and-cleanup/apply_deduced_names.py [--dry-run]
"""
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHECKOUT = os.path.join(ROOT, "n64", "OcarinaOfTime", "Shipwright")
SCOPES = ("soh/src", "soh/include", "soh/soh")


def git(*args, check=True):
    r = subprocess.run(("git", "-C", CHECKOUT) + args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def files_with(name):
    return [l for l in git("grep", "-lw", name, "--", *SCOPES, check=False).split() if l]


def main(dry_run=False):
    path = os.path.join(HERE, "batch.tsv")
    with open(path) as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r.get("old")]
    print(f"deduced names in this batch: {len(rows)}")

    applied, skipped = 0, []
    for row in rows:
        old, new = row["old"], row["new"]
        # Same shape as the adopted-name tag ("was <old> [oot]") so ONE
        # pattern matches both and check_renames.py sees them.
        tag = f"was {old} [LLM:{row['confidence']}]"
        scope = files_with(old)
        if not scope:
            skipped.append((old, new, "old name not present"))
            continue

        defining = row["def_file"]
        text = open(os.path.join(CHECKOUT, defining), encoding="utf-8",
                    errors="replace").read()
        is_static = bool(re.search(rf"^static\s[^\n]*\b{re.escape(old)}\b", text, re.M))
        # Collision check, ignoring COMMENTS: a provenance reason written
        # earlier in the same batch may mention the new name, and matching that
        # would block the rename against its own documentation.
        clash_files = []
        for p in git("grep", "-lw", new, "--",
                     *([defining] if is_static else SCOPES), check=False).split():
            with open(os.path.join(CHECKOUT, p), encoding="utf-8",
                      errors="replace") as fh:
                for l in fh:
                    code = l.split("//", 1)[0]
                    if re.search(rf"\b{re.escape(new)}\b", code):
                        clash_files.append(p)
                        break
        if clash_files:
            skipped.append((old, new, f"name already exists in {clash_files[0]}"))
            continue
        if dry_run:
            applied += 1
            continue

        for p in scope:
            full = os.path.join(CHECKOUT, p)
            with open(full, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
            out = []
            # A multi-line prototype's tag cannot go on the line carrying the
            # name -- that line ends in ',' and a "//" tag there would comment
            # out the rest of the parameter list. Defer it to the line that
            # closes the prototype with ';'.
            owed_tag = None
            for line in lines:
                if owed_tag is not None and line.rstrip().endswith(";"):
                    out.append(f"{line}  // {owed_tag}")
                    owed_tag = None
                    continue
                if not re.search(rf"\b{re.escape(old)}\b", line):
                    out.append(line)
                    continue
                renamed = re.sub(rf"\b{re.escape(old)}\b", new, line)
                # A DEFINITION and a header DECLARATION look alike at column 0;
                # the definition opens a body, the declaration ends in ';'.
                # Getting this wrong leaves declarations untagged.
                looks_top_level = re.match(
                    rf"^[A-Za-z_].*\b{re.escape(new)}\s*\(", renamed)
                # A header holds only prototypes, so a top-level match there is
                # always a declaration. Without this a MULTI-LINE prototype --
                # whose first line ends in ',' rather than ';' -- looks exactly
                # like a definition's opening line and is silently left untagged
                # (11 of them in functions.h, caught by the declarations gate).
                is_header = p.endswith(".h")
                is_def = (bool(looks_top_level) and not is_header and
                          not renamed.rstrip().endswith(";"))
                already = "was " in renamed
                # A macro continuation line ends in a backslash; appending a
                # "//" tag after it comments out the backslash and silently
                # breaks the macro (hit on z_en_insect.c's savestate field
                # list). Leave those lines untagged.
                continued = renamed.rstrip().endswith("\\")
                if is_header and not is_def and not already and not continued \
                        and not renamed.rstrip().endswith(";"):
                    # multi-line prototype: tag its closing line instead
                    out.append(renamed)
                    owed_tag = tag
                elif is_def or already or continued:
                    out.append(renamed)          # definition; comment added below
                else:
                    # A declaration or a call site -- both get the short tag, so
                    # the inference is visible wherever the name is used.
                    joiner = ", " if "//" in renamed else "  // "
                    out.append(f"{renamed}{joiner}{tag}")
            open(full, "w", encoding="utf-8").write("\n".join(out) + "\n")

        # The long reasoning goes above the definition.
        full = os.path.join(CHECKOUT, defining)
        lines = open(full, encoding="utf-8", errors="replace").read().splitlines()
        comment = (f"// LLM generated name ({row['confidence']}), was {old}: "
                   f"{row['reason']}")
        # A function definition ends in "(", a DATA definition in "[", "=" or
        # ";". Matching only the function shape silently skips data symbols,
        # leaving them renamed but uncited.
        define_re = (rf"^(?:static\s+|extern\s+|const\s+|volatile\s+)*"
                     rf"[A-Za-z_].*\b{re.escape(new)}\b\s*(?:\(|\[|=|;)")
        for i, line in enumerate(lines):
            if re.match(define_re, line):
                if i and "LLM generated name" in lines[i - 1]:
                    break
                lines.insert(i, comment)
                break
        open(full, "w", encoding="utf-8").write("\n".join(lines) + "\n")

        git("add", "-A", "soh")
        if not git("diff", "--cached", "--name-only").strip():
            skipped.append((old, new, "no change"))
            continue
        git("commit", "-q", "-m",
            f"soh: rename {old} -> {new}\n\n"
            f"Name source: DEDUCED from the code (confidence {row['confidence']}) "
            f"-- zeldaret/oot\nleaves this symbol address-named too, so there is no "
            f"upstream name to adopt.\nReason: {row['reason']}\n"
            f"Defined in {defining}.\n\n"
            f"Tagged [LLM:{row['confidence']}] at the definition, every "
            f"declaration and every call "
            f"site, so a\nreader meeting the name anywhere knows it is inferred.")
        applied += 1

    print(f"applied : {applied}")
    print(f"skipped : {len(skipped)}")
    for o, n, why in skipped:
        print(f"  {o} -> {n}: {why}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
