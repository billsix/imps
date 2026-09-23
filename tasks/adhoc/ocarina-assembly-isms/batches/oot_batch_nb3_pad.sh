#!/usr/bin/env bash
# (1) Re-run the split numeric/boolean groups with the improved normaliser; (2) the pad-local sweep.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
A=soh/src/overlays/actors
gate_verbose() { local ok=1 f r; for f in "$@"; do case "$f" in *.h) continue;; esac; r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD 2>&1 | head -10); echo "$r" | sed 's/^/  /'; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
try() { local script=$1 grp=$2 msg=$3; shift 3; echo "== $grp"
    python3 "$S/$script" "$G" "$grp" 2>&1 | grep -v "^patched\|^done" ; git status --short | grep -q . || { echo "  (no change)"; return 1; }
    if gate_verbose "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! reverted"; git checkout -- "$@"; fi; }

sed -i 's/fault.c.s `<< 0x10 >>\n0x10` on a 5-bit field//' "$W/m_oot_masks.txt"
try patch_oot_bool2.py ternary_bool "$W/m_oot_ternary_bool.txt" $A/ovl_En_Fr/z_en_fr.c $A/ovl_En_Hy/z_en_hy.c $A/ovl_En_Ssh/z_en_ssh.c $A/ovl_En_St/z_en_st.c $A/ovl_En_Ko/z_en_ko.c
try patch_oot_bool2.py eq1_bitfield "$W/m_oot_eq1_bitfield.txt" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
try patch_oot_num.py masks     "$W/m_oot_masks.txt"     $A/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c $A/ovl_Door_Ana/z_door_ana.c $A/ovl_En_Elf/z_en_elf.c $A/ovl_player_actor/z_player.c $A/ovl_En_GeldB/z_en_geldb.c $A/ovl_En_Wf/z_en_wf.c $A/ovl_En_Zl2/z_en_zl2.c soh/src/code/z_room.c soh/src/code/z_kaleido_scope_call.c $A/ovl_Bg_Spot02_Objects/z_bg_spot02_objects.c $A/ovl_En_Ani/z_en_ani.c $A/ovl_En_In/z_en_in.c $A/ovl_En_Ru2/z_en_ru2.c soh/src/code/code_800EC960.c soh/src/code/z_scene_table.c
try patch_oot_num.py fault_sext "$W/m_oot_masks.txt" soh/src/code/fault.c
try patch_oot_num.py ub_shifts "$W/m_oot_ub_shifts.txt" $A/ovl_En_Wood02/z_en_wood02.c
try patch_oot_num.py ub_shift_seq "$W/m_oot_ub_shifts.txt" soh/src/code/audio_seqplayer.c
echo "== fold_return (per file)"
for f in soh/src/code/z_actor.c soh/src/code/sys_math3d.c $A/ovl_player_actor/z_player.c; do
    python3 "$OOTTOOL/fold_return_bool.py" "$f" | grep "^# .*folded"
    if gate_verbose "$f"; then git add "$f"; git commit -q -F "$W/m_oot_fold_return.txt"; git log --oneline -1; else echo "  !! reverted $f"; git checkout -- "$f"; fi
done

echo "==== pad-local sweep"
python3 "$OOTTOOL/drop_pad_locals.py" "$G" "$IMPS/tasks/adhoc/ocarina-assembly-isms/data/filler_function_local_unreferenced.txt" > "$W/oot_pad_log.txt" 2>&1
grep -c "deleted:" "$W/oot_pad_log.txt"; grep -c "REVIEW" "$W/oot_pad_log.txt"
CHANGED=$(git status --short | awk '{print $2}')
KEPT=(); DEFERRED=()
for f in $CHANGED; do
    if is_compiled "$f"; then r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); else r="not compiled"; fi
    case "$r" in IDENTICAL*) KEPT+=("$f");; *) echo "DEF $f: ${r%% —*}"; git checkout -- "$f"; DEFERRED+=("$f");; esac
done
echo "== kept: ${#KEPT[@]}  deferred: ${#DEFERRED[@]}"; printf '%s\n' "${DEFERRED[@]}" > "$W/oot_pad_deferred.txt"
commit_group() { local label=$1 pat=$2 files=() n
    for f in "${KEPT[@]}"; do case "$f" in $pat) files+=("$f");; esac; done
    [ ${#files[@]} -gt 0 ] || return 0
    git add "${files[@]}"; n=$(git diff --cached --numstat | awk '{s+=$2} END {print s}')
    git commit -q -F - <<MSG
$label: remove the function-local \`s32 pad;\` stack padding

These declarations exist to reproduce the ROM's stack-frame layout for
the matching build; none is referenced again in its function (checked
per function by the survey, then by the compiler). $n declaration(s) in
${#files[@]} file(s) under $label. Struct members are untouched — the
padding that fixes a layout (SaveContext, the audio structs, anything
memcpy'd or saved) lives in headers, which this patch does not visit.
Locals named \`pad\` that ARE used (z_camera.c, z_vr_box.c, …) are not on
the list.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1; }
commit_group "soh/src/boot"             'soh/src/boot/*'
commit_group "soh/src/code"             'soh/src/code/*'
commit_group "soh/src/overlays/actors"  'soh/src/overlays/actors/*'
commit_group "soh/src/overlays/effects" 'soh/src/overlays/effects/*'
commit_group "soh/src/overlays"         'soh/src/overlays/*'
branch_summary 12
echo "PAD BATCH DONE"
