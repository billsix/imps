#!/usr/bin/env bash
# Batch 5 — `== TRUE` / `!= FALSE` / `== FALSE` / `!= TRUE` on boolean-valued expressions.
# Per file: rewrite with drop_true_false_cmp.py, gate; keep the file only if its codegen is
# IDENTICAL (the operand was a bitfield / comparison result / value the compiler already knew
# to be 0/1); otherwise revert it and list it for the explained-diff phase. Then one commit per
# directory for the kept files.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
FILES=$(grep -rl -E '(!= FALSE|== TRUE|== FALSE|!= TRUE)' src/game src/engine src/goddard src/menu src/audio --include='*.c' --include='*.h' | grep -v 'load_sh\|port_sh\|port_eu\|synthesis_sh\|copt' | sort)
echo "files: $(echo $FILES | wc -w)"
KEPT=(); DEFERRED=(); REVIEW="$W/b5_review.txt"; : > "$REVIEW"
for f in $FILES; do
    out=$(python3 "$TOOL/standard-c/drop_true_false_cmp.py" "$f" 2>&1) || { echo "!! tool failed on $f"; tail -3 <<<"$out"; git checkout -- "$f"; continue; }
    echo "$out" >> "$W/b5_tool_log.txt"
    grep -E 'REVIEW|SKIP' <<<"$out" >> "$REVIEW" || true
    n=$(grep -E '^# .*rewritten' <<<"$out" | grep -oE '[0-9]+ rewritten' | grep -oE '^[0-9]+')
    [ "${n:-0}" -gt 0 ] || { echo "-- $f: nothing rewritable"; continue; }
    r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
    case "$r" in
        IDENTICAL*) echo "OK  $f ($n sites)"; KEPT+=("$f");;
        *) echo "DEF $f ($n sites): ${r%% —*}"; git checkout -- "$f"; DEFERRED+=("$f");;
    esac
done
echo "== kept: ${#KEPT[@]}  deferred: ${#DEFERRED[@]}"
printf '%s\n' "${DEFERRED[@]}" > "$W/b5_deferred.txt"
echo "== review lines: $(wc -l < "$REVIEW")"; head -20 "$REVIEW"

commit_dir() { # <dir-label> <pattern>
    local label=$1 pat=$2 files=()
    for f in "${KEPT[@]}"; do case "$f" in $pat) files+=("$f");; esac; done
    [ ${#files[@]} -gt 0 ] || return 0
    git add "${files[@]}"
    git commit -q -F - <<MSG
$label: drop \`== TRUE\` / \`!= FALSE\` comparisons on boolean-valued expressions

Comparing a value that is already 0 or 1 against TRUE/FALSE is a MIPS-era
habit; standard C tests the value. This patch covers only the ${#files[@]} file(s)
in $label/ where every rewritten operand is a bitfield, a comparison result
or a value the compiler already knows to be 0/1 — which is why the generated
code is unchanged. Sites whose operand is a plain s32 field compared with 1
are deliberately left for a separate patch: they are behaviour-preserving
only by the (verified) invariant that the field is only ever assigned
TRUE/FALSE, and their codegen changes (cmp \$1 -> test).

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1
}
commit_dir game    'src/game/*'
commit_dir engine  'src/engine/*'
commit_dir goddard 'src/goddard/*'
commit_dir menu    'src/menu/*'
commit_dir audio   'src/audio/*'
echo "== uncommitted:"; git status --short | grep -v '^?? \| libultraship' || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -6
