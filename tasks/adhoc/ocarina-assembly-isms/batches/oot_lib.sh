#!/usr/bin/env bash
# Shared helpers for the OoT standard-c batches (sourced by batch scripts). Same shape as the SM64
# batch runners: gate every touched file, commit a group only when all are IDENTICAL, revert otherwise.
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
export ASMDIFF_PROJECT=OcarinaOfTime; : "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Shipwright build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/OcarinaOfTime/Shipwright"; TOOL="$IMPS/tools"
PIN=$(sed -n 's/^PIN_SHA=//p' "$IMPS/n64/OcarinaOfTime/fetch.sh")
cd "$G"
[ -n "${OOT_ANY_BRANCH:-}" ] || [ "$(git branch --show-current)" = imps-standard-c ] || { echo "Shipwright is not on imps-standard-c" >&2; exit 2; }

gate() { local ok=1 f r; for f in "$@"; do case "$f" in *.h) continue;; esac; r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
# commit_if_identical <msgfile> <files...>: gate the .c files, commit everything on success, revert on failure
commit_if_identical() { local msg=$1; shift
    if gate "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; return 0
    else echo "  !! codegen differs — reverted, listed for the explained-diff task: $*"; git checkout -- "$@"; return 3; fi; }
# is_compiled <path under checkout> -> 0 if the TU has a compile command
is_compiled() { grep -q "\"$G/$1\"" "$ASMDIFF_BUILD/compile_commands.json"; }
branch_summary() { echo "== uncommitted:"; git status --short | grep -v '^?? ' || echo "  none"; echo "== branch:"; git log --oneline "$PIN"..HEAD | head -"${1:-8}"; }
