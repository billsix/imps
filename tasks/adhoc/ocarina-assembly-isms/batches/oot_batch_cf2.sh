#!/usr/bin/env bash
# OoT batch — test-first loops, Yoda flips (tool), nested-if merges (tool), stale comments.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
A=soh/src/overlays/actors
gate_verbose() { local ok=1 f r; for f in "$@"; do case "$f" in *.h) continue;; esac; r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD 2>&1 | head -8); echo "$r" | sed 's/^/  /'; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
try() { local grp=$1 msg=$2; shift 2; echo "== $grp"
    python3 "$S/patch_oot_cf2.py" "$G" "$grp" 2>&1 | grep -v "^patched\|^done"; git status --short | grep -q . || { echo "  (no change)"; return 1; }
    if gate_verbose "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! reverted (per-file retry)"; git checkout -- "$@"
        python3 "$S/patch_oot_cf2.py" "$G" "$grp" >/dev/null 2>&1; local f; for f in "$@"; do if gate "$f" >/dev/null; then git add "$f"; else echo "  DEF $f"; git checkout -- "$f"; fi; done
        git diff --cached --quiet || { git commit -q -F "$msg"; git log --oneline -1; }; fi; }
# tool_sweep <tool> <msg> <files...>: run the tool per file, gate, keep IDENTICAL, one commit
tool_sweep() { local tool=$1 msg=$2; shift 2; local kept=() f n r
    for f in "$@"; do is_compiled "$f" || continue
        n=$(python3 "$OOTTOOL/$tool" "$f" | grep -oE '^# .*: [0-9]+' | grep -oE '[0-9]+$'); [ "${n:-0}" -gt 0 ] || continue
        r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
        case "$r" in IDENTICAL*) echo "OK  $f ($n)"; kept+=("$f");; *) echo "DEF $f ($n): ${r%% —*}"; git checkout -- "$f";; esac
    done
    [ ${#kept[@]} -gt 0 ] || { echo "  nothing kept"; return 0; }
    git add "${kept[@]}"; git commit -q -F "$msg"; git log --oneline -1; }
m() { cat > "$W/m_oot_$1.txt"; }
m loops <<'MSG'
code, overlays: write the search loops with their exit test in the header

`while (true) { if (!c) break; … }` where the test is the first statement
is `while (c) { … }`: audio_load.c's DMA chunk loop (`size >= 0x400`),
z_jpeg.c (`!exit`), the two map-mark walks (`markType != NONE`), the two
digit loops in z_file_choose.c (`*ones >= 100` / `>= 10` — an s16
promoted to int, so `(*ones - 100) < 0` is exactly `*ones < 100`),
Bg_Spot16_Bombstone's table walk (De Morgan on integer tests, bounds
check still first), and code_800EC960.c's `while (f()) {}`. z_eff_blure.c's
`if (c) { … } else { break; }` is the same inversion.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m yoda <<'MSG'
code, overlays: write comparisons with the variable first

`15 < x`, `950.0f < projectedW`, `0 <= index` — the constant-first order
is the MIPS `slti` operand order, not the reader's. Mirrored operator,
same value.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m nested <<'MSG'
code, overlays: one `&&` condition instead of three or more nested single-statement ifs

`if (A) { if (B) { if (C) { body } } }` with no `else` on any arm is
`if (A && B && C) { body }`; `&&` evaluates the tests left to right and
stops at the first false one, exactly as the nesting did, so calls with
side effects keep their order and their guards.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m stale_comments <<'MSG'
code, overlays: retire the matching notes whose construct is gone, and three stale `//!` bug notes

"required to match" comments on constructs that no longer need to match
(Bg_Gnd_Soulmeiro, Bg_Ydan_Maruta, Demo_Ik, En_Zl4, z_actor.c,
z_en_item00.c, z_kaleido_item.c ×2, z_lights.c, z_player.c's BAD_RETURN
note — the macro is `void` in the port), and `//! @bug` notes describing
what the port already fixed: audio_heap.c has its explicit `return ret;`,
En_Po_Sisters zeroes `spE7`, En_Tana's table has its third entry, and
z_kaleido_equipment.c's note guarded a commented-out call (the empty
`if` goes with it).

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

try loops "$W/m_oot_loops.txt" soh/src/code/audio_load.c soh/src/code/z_jpeg.c soh/src/code/z_map_mark.c soh/src/overlays/misc/ovl_kaleido_scope/z_lmap_mark.c soh/src/overlays/gamestates/ovl_file_choose/z_file_choose.c $A/ovl_Bg_Spot16_Bombstone/z_bg_spot16_bombstone.c soh/src/code/code_800EC960.c
try eff_blure_loop "$W/m_oot_loops.txt" soh/src/code/z_eff_blure.c
echo "== yoda sweep"
tool_sweep flip_yoda.py "$W/m_oot_yoda.txt" $(grep -rlE "(^|[^A-Za-z_0-9.])-?[0-9]+(\.[0-9]*f?)? *(<=|>=|<|>) *[A-Za-z_]" soh/src/code soh/src/overlays soh/src/boot --include='*.c' | sort)
echo "== nested-if sweep"
tool_sweep merge_nested_ifs.py "$W/m_oot_nested.txt" $(find soh/src/code soh/src/overlays soh/src/boot -name '*.c' | sort)
try stale_comments "$W/m_oot_stale_comments.txt" $A/ovl_Bg_Gnd_Soulmeiro/z_bg_gnd_soulmeiro.c $A/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c $A/ovl_Demo_Ik/z_demo_ik.c $A/ovl_En_Zl4/z_en_zl4.c soh/src/code/z_actor.c soh/src/code/z_en_item00.c soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_item.c soh/src/code/z_lights.c $A/ovl_player_actor/z_player.c soh/src/code/audio_heap.c $A/ovl_En_Po_Sisters/z_en_po_sisters.c soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_equipment.c $A/ovl_En_Tana/z_en_tana.c
branch_summary 8
echo "CF2 DONE"
