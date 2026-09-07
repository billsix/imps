#!/usr/bin/env python3
"""Adopt zeldaret/oot's verified names, one rename per commit.

Input: oracle.tsv rows with verdict ADOPT -- an upstream name whose body was
confirmed to match SoH's function at the same address (see oot_oracle.py).

Per rename, following tasks/reference/ocarina/decomp-renaming.md:
  * SCOPE the rename to the files holding the old name (so a file-local static
    cannot disturb a same-named static elsewhere);
  * COLLISION-CHECK the new name in that scope, and tree-wide for a non-static,
    skipping rather than clobbering;
  * add the provenance comment above the definition;
  * commit exactly one symbol.

The comment states the provenance and the verification, NOT an invented
description of what the function does: 292 fabricated behaviour summaries would
be worse than none, and the citation is the actual justification.

Run from the imps repo root:
    python3 tasks/adhoc/ocarina-decomp-rename-and-cleanup/apply_oot_names.py [--dry-run]
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
OOT_URL = "https://github.com/zeldaret/oot/blob/main/"


def soh_to_oot(path):
    """SoH source path -> its oot counterpart (mirrors oot_oracle.soh_to_oot)."""
    p = path[len("soh/"):] if path.startswith("soh/") else path
    return {
        "src/code/audio_thread.c": "src/audio/lib/thread.c",
        "src/code/audio_seq.c": "src/audio/game/sequence.c",
        "src/code/audio_sfx.c": "src/audio/game/sfx.c",
        "src/code/audio_general.c": "src/audio/game/general.c",
    }.get(p, p)


def git(*args, check=True):
    r = subprocess.run(("git", "-C", CHECKOUT) + args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def files_with(name):
    out = git("grep", "-lw", name, "--", *SCOPES, check=False)
    return [l for l in out.split() if l]


def main(dry_run=False):
    with open(os.path.join(HERE, "oracle.tsv")) as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r["verdict"] in ("ADOPT", "ADOPT_STRUCT")]
    print(f"ADOPT candidates: {len(rows)}")

    applied, skipped = 0, []
    for row in rows:
        old, new = row["soh_name"], row["oot_name"]
        scope = files_with(old)
        if not scope:
            skipped.append((old, new, "old name no longer present"))
            continue

        # Collision: the new name must not already exist. A static's collision
        # only matters inside its own file; a global's matters tree-wide.
        is_static = False
        defining = row["soh_file"]
        if defining in scope:
            text = open(os.path.join(CHECKOUT, defining), encoding="utf-8",
                        errors="replace").read()
            is_static = bool(re.search(rf"^static\s[^\n]*\b{re.escape(old)}\b",
                                       text, re.M))
        clash_scope = [defining] if is_static else None
        clash = git("grep", "-lw", new, "--", *(clash_scope or SCOPES), check=False)
        if clash.strip():
            skipped.append((old, new, f"name already exists in {clash.split()[0]}"))
            continue

        if dry_run:
            applied += 1
            continue

        # Rename inside the scope only.
        for path in scope:
            full = os.path.join(CHECKOUT, path)
            with open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            new_text = re.sub(rf"\b{re.escape(old)}\b", new, text)
            if new_text != text:
                open(full, "w", encoding="utf-8").write(new_text)

        # Provenance comment above the definition.
        full = os.path.join(CHECKOUT, defining)
        lines = open(full, encoding="utf-8", errors="replace").read().splitlines()
        oot_path = soh_to_oot(defining)
        how = ("body verified to match upstream at"
               if row["verdict"] == "ADOPT" else
               "structure verified to match upstream (identifiers and constants "
               "differ, upstream having since renamed them) at")
        comment = (f"// Name from zeldaret/oot (was {old}): adopted upstream's name for "
                   f"this address; {how} {float(row['body_match']):.2f}. "
                   f"[oot: {OOT_URL}{oot_path}]")
        # A function definition ends in "(", a data definition in "=" or ";".
        define_re = (rf"^[A-Za-z_].*\b{re.escape(new)}\s*\("
                     if row.get("kind", "func") == "func"
                     else rf"^(?:static\s+|extern\s+|const\s+)*[A-Za-z_].*"
                          rf"\b{re.escape(new)}\b\s*(?:\[|=|;)")
        for i, line in enumerate(lines):
            if re.match(define_re, line):
                if i and "was " in lines[i - 1]:
                    break
                lines.insert(i, comment)
                break
        open(full, "w", encoding="utf-8").write("\n".join(lines) + "\n")

        # Tag this symbol's header DECLARATIONS in the SAME commit -- a commit
        # must carry the whole rename, comments included (decomp-renaming.md).
        for path in files_with(new):
            if not path.endswith((".h", ".hpp")):
                continue
            full = os.path.join(CHECKOUT, path)
            with open(full, encoding="utf-8", errors="replace") as fh:
                hdr = fh.read().splitlines()
            changed = False
            for i, line in enumerate(hdr):
                if not re.search(rf"\b{re.escape(new)}\b", line):
                    continue
                if line.lstrip().startswith("//") or "was " in line:
                    continue           # not a declaration, or already tagged
                joiner = ", " if "//" in line else "  // "
                hdr[i] = f"{line}{joiner}was {old} [oot]"
                changed = True
            if changed:
                open(full, "w", encoding="utf-8").write("\n".join(hdr) + "\n")

        git("add", "-A", "soh")
        if not git("diff", "--cached", "--name-only").strip():
            skipped.append((old, new, "no change produced"))
            continue
        git("commit", "-q", "-m",
            f"soh: rename {old} -> {new}\n\n"
            f"Name source: zeldaret/oot (same decomp, same ROM address).\n"
            f"{'Body' if row['verdict'] == 'ADOPT' else 'Structure'} verified "
            f"against upstream at {float(row['body_match']):.2f}.\n"
            f"Defined in {defining}.")
        applied += 1

    print(f"applied : {applied}")
    print(f"skipped : {len(skipped)}")
    for old, new, why in skipped[:25]:
        print(f"  {old} -> {new}: {why}")
    if len(skipped) > 25:
        print(f"  ... and {len(skipped) - 25} more")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
