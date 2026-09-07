#!/usr/bin/env bash
#
# Repair the declaration tags that apply_deduced_names.py left off MULTI-LINE
# prototypes in soh/include/functions.h.
#
# The tagger appends "// was <old> [LLM:HIGH]" to the header line carrying a
# renamed name.  When a prototype is split across two lines the name sits on
# the FIRST line, which ends in ',' -- so that line looked like a definition's
# opening line, was treated as a definition, and the declaration went untagged.
# The build is unaffected; the check_renames.py "declarations" gate is not.
#
# The series must stay one-rename-per-commit, so the tag has to go into the
# commit that performed the rename, not into a follow-up commit.  This script
# rewrites exactly those commits in place.
#
# Two mechanics worth knowing:
#
#   * There is no editor in the container, so the todo list is edited by
#     GIT_SEQUENCE_EDITOR (a sed one-liner) rather than interactively.
#
#   * Amending a commit changes the context lines that LATER commits' diffs
#     expect, so replaying them conflicts in this header.  Every such conflict
#     resolves the same way: take the incoming commit's version of the header
#     (which carries the original, untagged text) and re-run the tagger over
#     it.  The tagger only tags a prototype whose NEW name is already present,
#     so it restores exactly the tags whose rename commits have replayed --
#     no more -- and is idempotent.
#
# Run from the imps repo root.  Reads "<sha> <old> <new>" rows on stdin,
# oldest commit first.
set -u
CHECKOUT=n64/OcarinaOfTime/Shipwright
HDR=soh/include/functions.h

mapfile -t ROWS
[ "${#ROWS[@]}" -gt 0 ] || { echo "nothing to do"; exit 0; }
BASE=$(cut -d' ' -f1 <<< "${ROWS[0]}")

cd "$CHECKOUT" || exit 1
printf '%s\n' "${ROWS[@]}" | awk '{print $2, $3}' > /tmp/decl_pairs.txt

# The undo: `git reset --hard backup-decltags`.
git branch -f backup-decltags HEAD

tag_header() {
    HDR="$HDR" python3 - <<'PY'
import os, re
hdr = os.environ["HDR"]
pairs = [l.split() for l in open("/tmp/decl_pairs.txt") if l.strip()]
lines = open(hdr, encoding="utf-8").read().splitlines()
changed = False
for old, new in pairs:
    for i, line in enumerate(lines):
        if not re.match(rf"^[A-Za-z_].*\b{re.escape(new)}\s*\(", line):
            continue
        # walk forward to the line that closes the prototype
        j = i
        while j < len(lines) and not lines[j].rstrip().endswith(";"):
            j += 1
        if j < len(lines) and "// was " not in lines[j] and "// was " not in line:
            lines[j] += f"  // was {old} [LLM:HIGH]"
            changed = True
        break
if changed:
    open(hdr, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
}

SHAS=$(printf '%s\n' "${ROWS[@]}" | cut -d' ' -f1 | cut -c1-9 | paste -sd'|')
GIT_SEQUENCE_EDITOR="sed -i -E 's/^pick ($SHAS)/edit \\1/'" \
    git rebase -i "$BASE^" >/dev/null 2>&1

while [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; do
    conflicts=$(git diff --name-only --diff-filter=U)
    if [ -n "$conflicts" ]; then
        if [ "$conflicts" != "$HDR" ]; then
            echo "UNEXPECTED CONFLICT in: $conflicts"; exit 1
        fi
        git checkout --theirs -- "$HDR"
        tag_header
        git add "$HDR"
        git -c core.editor=true rebase --continue >/dev/null 2>&1
    else
        tag_header
        git add "$HDR"
        git commit -q --amend --no-edit
        git -c core.editor=true rebase --continue >/dev/null 2>&1
    fi
done
echo "rebase finished at: $(git log --oneline -1)"
