#!/usr/bin/env bash
# OoT batch — `== true` / `!= false` / `== false` / `!= true` on boolean-valued expressions.
# Per file: rewrite with drop_true_false_cmp.py (SKIP list carries the reader's look-alikes), gate;
# keep only files whose codegen is IDENTICAL; revert the rest (explained-diff task); commit per group.
set -u
. "$(dirname "$0")/oot_lib.sh"
FILES=$(grep -rlE '(==|!=) *(true|false|TRUE|FALSE)\b' soh/src/code soh/src/overlays soh/src/boot --include='*.c' | sort)
echo "files: $(echo $FILES | wc -w)"
KEPT=(); DEFERRED=(); : > "$W/oot_b_bool_log.txt"; : > "$W/oot_b_bool_review.txt"
for f in $FILES; do
    is_compiled "$f" || { echo "--  $f: not compiled, skipped"; continue; }
    out=$(python3 "$TOOL/standard-c/drop_true_false_cmp.py" "$f" 2>&1) || { echo "!! tool failed on $f"; git checkout -- "$f"; continue; }
    echo "$out" >> "$W/oot_b_bool_log.txt"; grep -E 'REVIEW|SKIP' <<<"$out" >> "$W/oot_b_bool_review.txt" || true
    n=$(grep -oE '^# .*: [0-9]+ rewritten' <<<"$out" | grep -oE '[0-9]+ rewritten' | grep -oE '^[0-9]+')
    [ "${n:-0}" -gt 0 ] || continue
    r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
    case "$r" in
        IDENTICAL*) echo "OK  $f ($n)"; KEPT+=("$f");;
        *) echo "DEF $f ($n): ${r%% —*}"; git checkout -- "$f"; DEFERRED+=("$f");;
    esac
done
echo "== kept: ${#KEPT[@]}  deferred: ${#DEFERRED[@]}"; printf '%s\n' "${DEFERRED[@]}" > "$W/oot_b_bool_deferred.txt"
echo "== review: $(wc -l < "$W/oot_b_bool_review.txt") lines"

commit_group() { # <label> <pattern>
    local label=$1 pat=$2 files=()
    for f in "${KEPT[@]}"; do case "$f" in $pat) files+=("$f");; esac; done
    [ ${#files[@]} -gt 0 ] || return 0
    git add "${files[@]}"
    git commit -q -F - <<MSG
$label: drop \`== true\` / \`!= false\` comparisons on boolean-valued expressions

Comparing a value that is already 0 or 1 against true/false is a MIPS-era
habit; C tests the value. This patch covers only the ${#files[@]} file(s) in
$label where every rewritten operand is a bitfield, a \`u8\`, a comparison
result or a local the compiler already knows to be 0/1 — which is why the
generated code is unchanged. Sites whose operand is a plain \`s32\` field or
an \`s32\` function result compared with 1 are deliberately left for a
separate patch: they are behaviour-preserving only by the (verified)
invariant that the value is only ever 0/1, and their codegen changes
(cmp \$1 -> test).

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1
}
commit_group "soh/src/code"           'soh/src/code/*'
commit_group "soh/src/boot"           'soh/src/boot/*'
commit_group "soh/src/overlays/actors" 'soh/src/overlays/actors/*'
commit_group "soh/src/overlays"       'soh/src/overlays/*'
branch_summary 6
