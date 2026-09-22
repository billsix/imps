#!/usr/bin/env bash
# Phase C for OoT: export standard-c, put it FIRST in ORDER, replay the 488-patch personal stream on
# top with 3-way merges, resolve rename conflicts mechanically, re-export personal, and keep a
# reference branch of the OLD applied tree for the final tree-wide gate.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
P="$IMPS/n64/OcarinaOfTime"
LOG="$W/oot_phase_c.log"; : > "$LOG"
git status --short | grep -v '^??' | grep -q . && { echo "checkout dirty; abort" >&2; exit 2; }

echo "== 1. export standard-c ($(git rev-list --count "$PIN"..imps-standard-c) commits)"
mkdir -p "$P/patches/standard-c"; rm -f "$P/patches/standard-c"/*.patch
git format-patch --no-cover-letter --base="$PIN" "$PIN"..imps-standard-c -o "$P/patches/standard-c/" >/dev/null; ls "$P/patches/standard-c" | wc -l
cat > "$P/patches/ORDER" <<'EOF'
# Stream apply order for this project, most-dependent-first.
#
# `standard-c` FIRST (2026-09-22): the upstream-bound rewrites of the decomp's
# assembly-isms into standard C. They are meant to be merged upstream, so they
# must be the BASE the personal stream sits on: the renames then apply to the
# code as upstream would see it after merging, and a conflict surfaces here,
# on our side, rather than in a rebase we cannot do. The two streams touch the
# same files (477 rewritten, 509 renamed), so this order is load-bearing; the
# `personal` patches were re-cut against the rewritten tree when standard-c
# landed (tasks/ocarina-de-disassemble-ugly-c.md, Phase C).
#
# `personal` = the 488-patch decomp rename (3,781 symbols + 18 file renames);
# every later stream must be written against the renamed tree.
#
# One stream per line; listed streams apply first, in this order. Comments and
# blank lines are ignored.
standard-c
personal
EOF

echo "== 2. reference branch: the OLD applied tree (pin + old personal)"
git branch -f imps-personal-old "$PIN"; git checkout -q imps-personal-old
git am -q --3way "$P/patches/personal"/*.patch >>"$LOG" 2>&1 || { echo "old personal series does not apply on the bare pin?!" >&2; git am --abort; exit 2; }
echo "  old applied tree: $(git rev-list --count "$PIN"..HEAD) commits"

echo "== 3. replay personal on top of standard-c (3-way, diff3 markers, mechanical resolution)"
git branch -f imps-applied imps-standard-c; git checkout -q imps-applied
RESOLVED=(); UNRESOLVED=()
for p in "$P/patches/personal"/*.patch; do
    if git -c merge.conflictStyle=diff3 am -q --3way "$p" >>"$LOG" 2>&1; then continue; fi
    conflicted=$(git diff --name-only --diff-filter=U)
    if [ -z "$conflicted" ]; then echo "  !! $(basename "$p") failed without conflicts"; git am --abort; UNRESOLVED+=("$(basename "$p")"); break; fi
    if python3 "$IMPS/tools/resolve_rename_conflicts.py" "$G" "$p" $conflicted >>"$LOG" 2>&1; then
        git add $conflicted; GIT_EDITOR=true git am --continue -q >>"$LOG" 2>&1 || { echo "  !! continue failed on $(basename "$p")"; UNRESOLVED+=("$(basename "$p")"); break; }
        RESOLVED+=("$(basename "$p"): $(echo "$conflicted" | tr '\n' ' ')")
    else
        echo "  !! unresolved conflict in $(basename "$p"): $conflicted"; UNRESOLVED+=("$(basename "$p")"); break
    fi
done
echo "  applied: $(git rev-list --count imps-standard-c..HEAD) of 488; mechanically resolved: ${#RESOLVED[@]}; unresolved: ${#UNRESOLVED[@]}"
printf '%s\n' "${RESOLVED[@]}" > "$W/oot_phase_c_resolved.txt"
[ ${#UNRESOLVED[@]} -eq 0 ] || { printf '%s\n' "${UNRESOLVED[@]}"; echo "STOPPED (git am in progress on imps-applied)"; exit 3; }

echo "== 4. rename totality gates"
(cd "$P" && python3 tools/check_renames.py series 2>&1 | tail -4)
(cd "$P" && python3 tools/check_renames.py traceable 2>&1 | tail -3)

echo "== 5. re-export personal against the standard-c tip"
rm -f "$P/patches/personal"/*.patch
git format-patch --no-cover-letter --base=imps-standard-c imps-standard-c..imps-applied -o "$P/patches/personal/" >/dev/null; ls "$P/patches/personal" | wc -l
echo "PHASE C DONE (checkout on imps-applied)"
