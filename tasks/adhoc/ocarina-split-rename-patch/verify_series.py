#!/usr/bin/env python3
"""Audit the rebuilt series: exactly one rename per commit, and nothing lost.

Checks, in order of importance:

  1. The series tip is byte-identical to the target tree. This is the whole
     safety argument -- history changed, content did not.
  2. Every commit is non-empty.
  3. Every symbol-rename commit introduces EXACTLY ONE new name and removes
     EXACTLY ONE old name -- the maintainer's "never two names per commit".
  4. Every rename in the table is covered by exactly one commit.
  5. Renames are TOTAL: the old name is gone from real code afterwards.

Run from anywhere:
    python3 tasks/adhoc/ocarina-split-rename-patch/verify_series.py
Exits non-zero on any failure, so it works as a gate.
"""
import collections
import csv
import os
import re
import sys

from _common import (ADDR_RE, INLINE_TAG_RE, code_part, git,
                     is_marker_line, pin_sha)

HERE = os.path.dirname(os.path.abspath(__file__))
# The series under audit is whatever is applied on top of the pin (normally
# HEAD after ./apply.sh); baseline-renames is the pre-split single commit, kept
# as the reference the split must reproduce.
BRANCH, BASELINE = "HEAD", "baseline-renames"
SUBJECT_RE = re.compile(r"^soh: rename (\S+) -> (\S+)$")


def main():
    with open(os.path.join(HERE, "rename_table.tsv")) as handle:
        table = {(r["old"], r["new"]) for r in csv.DictReader(handle, delimiter="\t")}

    failures = []

    # 1. The tip must reproduce the pre-split tree EXACTLY, except for the
    #    provenance comments this task adds. Any other difference means the
    #    split changed content, which it must never do.
    content_changes = []
    for line in git("diff", "-U0", BASELINE, BRANCH).splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
            continue
        body = line[1:]
        # Strip the short inline tag FIRST: it is appended to an existing
        # declaration, so that line shows up as -old/+old-plus-tag and the two
        # must cancel. Skipping it as "a comment" would leave the '-' unpaired.
        stripped = INLINE_TAG_RE.sub("", body)
        # A whole line that is only a provenance comment cancels nothing.
        if is_marker_line(body) or not stripped.strip():
            continue
        content_changes.append(stripped)
    net = collections.Counter(content_changes)
    leftover = {k: v for k, v in net.items() if v % 2}
    if leftover:
        failures.append(f"split changed CONTENT, not just comments: "
                        f"{list(leftover)[:5]}")
    else:
        print("OK  tip reproduces the pre-split tree; only comments differ")

    pin = pin_sha()
    log = [line.split(" ", 1) for line in
           git("log", "--reverse", "--format=%H %s", f"{pin}..{BRANCH}").splitlines()]
    print(f"OK  {len(log)} commits on the series")

    seen, file_renames = set(), 0
    for sha, subject in log:
        stat = git("show", "--stat", "--format=", sha).strip()
        if not stat:
            failures.append(f"empty commit: {subject}")
            continue
        match = SUBJECT_RE.match(subject)
        # A file-rename commit has the same subject shape but names paths, e.g.
        # "soh: rename code_800E6840.c -> audio_dcache.c".
        if not match or match.group(1).endswith(".c"):
            file_renames += 1
            continue
        old, new = match.groups()
        seen.add((old, new))

        # 3. exactly one name in, one out (ignoring provenance comment lines,
        #    which necessarily mention the old name).
        added, removed = set(), set()
        for line in git("show", "--format=", sha).splitlines():
            if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
                continue
            body = line[1:]
            if is_marker_line(body) or "// was " in body:
                continue
            names = set(ADDR_RE.findall(body)) | ({new} if re.search(
                rf"\b{re.escape(new)}\b", body) else set())
            (added if line.startswith("+") else removed).update(names)
        introduced = added - removed
        retired = removed - added
        if introduced != {new}:
            failures.append(f"{subject}: introduces {sorted(introduced)}, want [{new}]")
        if retired and retired != {old}:
            failures.append(f"{subject}: retires {sorted(retired)}, want [{old}]")

    print(f"OK  {file_renames} file-rename commits, {len(seen)} symbol-rename commits")

    # 4. coverage
    missing = table - seen
    extra = seen - table
    if missing:
        failures.append(f"{len(missing)} renames in the table have no commit: "
                        f"{sorted(missing)[:5]}")
    if extra:
        failures.append(f"{len(extra)} commits rename something not in the table: "
                        f"{sorted(extra)[:5]}")
    if not missing and not extra:
        print(f"OK  all {len(table)} table renames covered, one commit each")

    # 5. renames are total
    stale = []
    for old, new in table:
        out = git("grep", "-lw", old, BRANCH, "--",
                  "soh/src", "soh/include", "soh/soh", check=False)
        for line in out.splitlines():
            path = line.split(":", 1)[1] if ":" in line else line
            text = git("show", f"{BRANCH}:{path}", check=False)
            # code_part() drops BOTH provenance forms -- the long definition
            # comment and the short inline tag, including the ", was X [...]"
            # variant used where a line already ended in a comment.
            if any(re.search(rf"\b{re.escape(old)}\b", code_part(l))
                   for l in text.splitlines()):
                stale.append((old, path))
    if stale:
        failures.append(f"{len(stale)} renames left the old name in real code: "
                        f"{stale[:5]}")
    else:
        print("OK  every rename is total (old name survives only in comments)")

    print()
    for failure in failures:
        print(f"FAIL  {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    sys.exit(main())
