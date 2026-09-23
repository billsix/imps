#!/usr/bin/env bash
# asmdiff_tree.sh — the codegen gate over EVERY source file that differs between two git refs of a
# project's checkout: check out <ref-new>, list the .c files under the decomp sources that differ
# from <ref-old>, run tools/asmdiff.sh on each against <ref-old>, and summarise.
#
#   ASMDIFF_PROJECT=SuperMario64|OcarinaOfTime ASMDIFF_BUILD=<configured cmake tree> \
#     bash tools/asmdiff_tree.sh <ref-old> <ref-new> [<log file>]
#
# Two uses (tasks/reference/imps/standard-c-tooling.md):
#   the STREAM gate  — <pin> <stream-branch>: every rewrite in a standard-c stream, re-proven per file;
#   the RE-CUT gate  — <old-applied> <new-applied>: after a stream is re-cut under a new base, the
#                      final tree must compile identically to the old final tree.
# Files the build does not compile are SKIPped (they cannot be gated — leave them alone); files that
# exist only on one side are listed GONE/NEW. Renamed files: run asmdiff.sh by hand with
# ASMDIFF_CMD_FROM=<old path> (see tools/asmdiff.sh). Leaves the checkout on <ref-new>.
set -u
cd "$(dirname "$0")/.."                                   # repo root
case "${ASMDIFF_PROJECT:-SuperMario64}" in
    SuperMario64)  GS=n64/SuperMario64/Ghostship;   SRCROOT=src ;;
    OcarinaOfTime) GS=n64/OcarinaOfTime/Shipwright; SRCROOT=soh/src ;;
    *) echo "ASMDIFF_PROJECT must be SuperMario64 or OcarinaOfTime" >&2; exit 2 ;;
esac
old=${1:?usage: asmdiff_tree.sh <ref-old> <ref-new> [<log>]}; new=${2:?}; log=${3:-$(mktemp)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured cmake tree}"
git -C "$GS" checkout -q "$new" || exit 2
gsabs=$(cd "$GS" && pwd)
total=0; ident=0; diff=0; skip=0; : > "$log"
for f in $(git -C "$GS" diff --name-only "$old" "$new" -- "$SRCROOT" | grep '\.c$' | sort); do
    total=$((total+1))
    if ! [ -f "$GS/$f" ]; then skip=$((skip+1)); echo "GONE $f" >> "$log"; continue; fi
    if ! git -C "$GS" cat-file -e "$old:$f" 2>/dev/null; then skip=$((skip+1)); echo "NEW  $f (not at $old)" >> "$log"; continue; fi
    if ! grep -q "\"$gsabs/$f\"" "$ASMDIFF_BUILD/compile_commands.json"; then skip=$((skip+1)); echo "SKIP $f (not compiled)" >> "$log"; continue; fi
    r=$(bash tools/asmdiff.sh "$f" "$old" 2>&1 | head -1)
    case "$r" in IDENTICAL*) ident=$((ident+1));; *) diff=$((diff+1)); echo "DIFF $f: $r" | tee -a "$log";; esac
done
echo "tree gate $old..$new: $total files, $ident identical, $diff differ, $skip skipped (log: $log)"
[ "$diff" -eq 0 ]
