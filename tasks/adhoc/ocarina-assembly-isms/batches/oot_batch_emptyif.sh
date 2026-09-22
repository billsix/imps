#!/usr/bin/env bash
# OoT batch — empty `if (<pure read>) {}` matching artefacts. drop_empty_if.py per compiled file, gate,
# keep IDENTICAL files, revert the rest, commit per group.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
FILES=$(grep -rlE '^\s*if \(.*\) \{\s*\}\s*$|^\s*if \(.*\) \{\s*$' soh/src/code soh/src/overlays soh/src/boot --include='*.c' | sort)
echo "candidate files: $(echo $FILES | wc -w)"
KEPT=(); DEFERRED=(); : > "$W/oot_b_emptyif_log.txt"
for f in $FILES; do
    is_compiled "$f" || continue
    out=$(python3 "$OOTTOOL/drop_empty_if.py" "$f" 2>&1) || { echo "!! tool failed on $f"; git checkout -- "$f"; continue; }
    n=$(grep -oE '^# .*: [0-9]+ deleted' <<<"$out" | grep -oE '[0-9]+ deleted' | grep -oE '^[0-9]+')
    [ "${n:-0}" -gt 0 ] || continue
    echo "$out" >> "$W/oot_b_emptyif_log.txt"
    r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
    case "$r" in
        IDENTICAL*) echo "OK  $f ($n)"; KEPT+=("$f");;
        *) echo "DEF $f ($n): ${r%% —*}"; git checkout -- "$f"; DEFERRED+=("$f");;
    esac
done
echo "== kept: ${#KEPT[@]}  deferred: ${#DEFERRED[@]}"; printf '%s\n' "${DEFERRED[@]}" > "$W/oot_b_emptyif_deferred.txt"

commit_group() { # <label> <pattern>
    local label=$1 pat=$2 files=() n
    for f in "${KEPT[@]}"; do case "$f" in $pat) files+=("$f");; esac; done
    [ ${#files[@]} -gt 0 ] || return 0
    git add "${files[@]}"
    n=$(git diff --cached --numstat | awk '{s+=$2} END {print s}')
    git commit -q -F - <<MSG
$label: delete the empty \`if (x) {}\` statements kept "to match"

An \`if\` with an empty body and a side-effect-free condition does nothing;
the decomp kept them because the original compiler needed the read to
reproduce the ROM's register allocation ("Needed to match", "fixes
regalloc, may be fake", "Very fake, but needed to get the s registers
right"). GCC at -O2 already drops the dead load, so the generated code is
unchanged. $n line(s) in ${#files[@]} file(s) under $label; the comment that
excused each one goes with it.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1
}
commit_group "soh/src/code"            'soh/src/code/*'
commit_group "soh/src/boot"            'soh/src/boot/*'
commit_group "soh/src/overlays/actors" 'soh/src/overlays/actors/*'
commit_group "soh/src/overlays"        'soh/src/overlays/*'
branch_summary 6
