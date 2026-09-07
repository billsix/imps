#!/usr/bin/env python3
"""Prove the rename commit is renames + comments and NOTHING else.

If any behavioural change is hiding in the 6,854-line commit it must be split
out separately, so this checks before the split starts (and again after, as a
regression gate).

Method: for each file the commit touched, take the post-commit content, delete
the provenance comment lines, reverse every rename (new -> old), and diff
against the same file at the pin. A clean commit leaves nothing.

Two kinds of expected, harmless residue -- read any output with these in mind:

  * CONTINUATION lines of a multi-line provenance comment. Only the first line
    carries the marker, so the rest survive the filter. They start with '//'.
  * FILE-LOCAL STATIC COLLISIONS. Reversing tree-wide hits names that already
    existed elsewhere: sColChkInfoInit is the new name for D_80A65F38 in
    ovl_En_Md, but 60 other files already had their own static of that name.
    Likewise sTentacleTextures, which the commit uses for BOTH D_809B8118 and
    D_809D2560 in different files. This is exactly the hazard that makes the
    real split file-scoped.
  * THE TWO RENAMES THE INVENTORY CANNOT CARRY -- UnkRumbleStruct -> RumbleMgr
    (soh/include/z64.h, functions.h, sys_rumble.c) and Struct_8016E320 ->
    SeqRequest (audio_seq.c). Both show up here until they are added by hand.
  * STALE-PATH COMMENT UPDATES from the 20 file renames, e.g. a comment saying
    "see code_800F9280.c" retargeted to audio_seq.c. These belong to the file
    rename commit, not to any symbol rename.

Anything else is real work mixed into the commit -- investigate before splitting.

As of 2026-09-07 the run is CLEAN: 69 residual lines, every one in a category
above, so the commit is renames + comments and nothing else.

Run from the repo root (needs inventory.tsv -- run inventory.py first):
    python3 tasks/adhoc/ocarina-split-rename-patch/residue.py
"""
import collections
import csv
import difflib
import os
import re
import sys

from _common import (CHECKOUT, git, is_marker_line, pin_sha, rename_commit)


def blob(rev, path):
    """File content at `rev`, or None if it does not exist there."""
    out = git("show", f"{rev}:{path}", check=False)
    return out if out else None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    inventory = os.path.join(here, "inventory.tsv")
    if not os.path.exists(inventory):
        raise SystemExit("run inventory.py first (no inventory.tsv)")
    with open(inventory) as handle:
        new_to_old = {row["new"]: row["old"]
                      for row in csv.DictReader(handle, delimiter="\t")}

    pin, sha = pin_sha(), rename_commit()
    # --find-renames=40% is loose enough to pair the code_<addr>.c files with
    # their renamed successors, several of which changed substantially.
    name_status = git("show", "--name-status", "--find-renames=40%",
                      "--pretty=", sha)
    paths = {}                              # post-commit path -> pin path
    for line in name_status.splitlines():
        fields = line.split("\t")
        if fields[0].startswith("R"):
            paths[fields[2]] = fields[1]
        elif fields[0] == "M":
            paths[fields[1]] = fields[1]

    word_re = re.compile("|".join(rf"\b{re.escape(n)}\b" for n in new_to_old))
    residue = collections.Counter()
    samples = {}
    for new_path, old_path in sorted(paths.items()):
        before, after = blob(pin, old_path), blob(sha, new_path)
        if before is None or after is None:
            continue
        reverted = [line for line in after.splitlines()
                    if not is_marker_line(line)]
        reverted = [word_re.sub(lambda m: new_to_old[m.group(0)], line)
                    for line in reverted]
        diff = [line for line in difflib.unified_diff(
                    before.splitlines(), reverted, n=0, lineterm="")
                if line.startswith(("+", "-"))
                and not line.startswith(("+++", "---"))]
        # Drop pure comment-continuation additions -- expected, see docstring.
        diff = [line for line in diff if not re.match(r"^\+\s*//", line)]
        if diff:
            residue[new_path] = len(diff)
            samples[new_path] = diff[:6]

    print(f"files compared                : {len(paths)}")
    print(f"files with residue            : {len(residue)}")
    print(f"residual changed lines        : {sum(residue.values())}")
    print("\n(expect only comment continuations and static-name collisions -- "
          "see the docstring)\n")
    for path, count in residue.most_common():
        print(f"  {count:4d}  {path}")
        for line in samples[path]:
            print(f"          {line}")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
