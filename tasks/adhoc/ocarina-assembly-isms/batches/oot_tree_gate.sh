#!/usr/bin/env bash
# Tree-wide gates for OoT:
#   stream : every file the standard-c branch changed, compiled at the branch vs at the PIN -> IDENTICAL
#   final  : every file that differs between the OLD applied tree (imps-personal-old) and the NEW applied
#            tree (imps-applied), compiled on both -> IDENTICAL (renames + rewrites change no code)
# usage: oot_tree_gate.sh stream|final
set -u
. "$(dirname "$0")/oot_lib.sh"
mode=${1:?stream|final}
case "$mode" in
    stream) branch=imps-standard-c; ref=$PIN ;;
    final)  branch=imps-applied;    ref=imps-personal-old ;;
esac
git checkout -q "$branch"
files=$(git diff --name-only "$ref" "$branch" -- soh/src | grep '\.c$' | sort)
total=0; ident=0; diff=0; skip=0; : > "$W/oot_tree_gate_$mode.txt"
for f in $files; do
    total=$((total+1))
    [ -f "$f" ] || { skip=$((skip+1)); echo "GONE $f" >> "$W/oot_tree_gate_$mode.txt"; continue; }
    is_compiled "$f" || { skip=$((skip+1)); echo "SKIP $f (not compiled)" >> "$W/oot_tree_gate_$mode.txt"; continue; }
    git cat-file -e "$ref:$f" 2>/dev/null || { skip=$((skip+1)); echo "NEW  $f (not at $ref)" >> "$W/oot_tree_gate_$mode.txt"; continue; }
    r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" "$ref" 2>&1 | head -1)
    case "$r" in IDENTICAL*) ident=$((ident+1));; *) diff=$((diff+1)); echo "DIFF $f: $r" | tee -a "$W/oot_tree_gate_$mode.txt";; esac
done
echo "$mode gate: $total files, $ident identical, $diff differ, $skip skipped (see oot_tree_gate_$mode.txt)"
