#!/usr/bin/env bash
# Recovery + redo: drop the ungated sweep edits left by the broken tool_sweep, then rerun the Yoda and
# nested-if sweeps with a correct per-file count, and the eq1 group per file.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
A=soh/src/overlays/actors
echo "== dropping $(git status --short | grep -c '^ M') ungated modified files"; git checkout -- soh; git status --short | grep -v '^??' || echo "clean"
tool_sweep() { local tool=$1 msg=$2; shift 2; local kept=() f n r
    for f in "$@"; do is_compiled "$f" || continue
        n=$(python3 "$OOTTOOL/$tool" "$f" | grep -oE '^# total: [0-9]+' | grep -oE '[0-9]+$'); [ "${n:-0}" -gt 0 ] || { git checkout -- "$f"; continue; }
        r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
        case "$r" in IDENTICAL*) echo "OK  $f ($n)"; kept+=("$f");; *) echo "DEF $f ($n): ${r%% —*}"; git checkout -- "$f";; esac
    done
    [ ${#kept[@]} -gt 0 ] || { echo "  nothing kept"; return 0; }
    git add "${kept[@]}"; git commit -q -F "$msg"; git log --oneline -1; }
per_file() { local grp=$1 msg=$2; shift 2; echo "== $grp (per file)"
    python3 "$S/patch_oot_bool2.py" "$G" "$grp" 2>&1 | grep -v "^patched\|^done"; git status --short | grep -q . || { echo "  (no change)"; return 1; }
    local f; for f in "$@"; do git diff --quiet -- "$f" && continue; if gate "$f" >/dev/null; then git add "$f"; echo "  OK  $f"; else echo "  DEF $f"; git checkout -- "$f"; fi; done
    git diff --cached --quiet || { git commit -q -F "$msg"; git log --oneline -1; }; }
per_file eq1_bitfield "$W/m_oot_eq1_bitfield.txt" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
echo "== yoda sweep"
tool_sweep flip_yoda.py "$W/m_oot_yoda.txt" $(find soh/src/code soh/src/overlays soh/src/boot -name '*.c' | sort)
echo "== nested-if sweep"
tool_sweep merge_nested_ifs.py "$W/m_oot_nested.txt" $(find soh/src/code soh/src/overlays soh/src/boot -name '*.c' | sort)
git status --short | grep -v '^??' || echo "clean"
branch_summary 5
echo "SWEEPS DONE"
