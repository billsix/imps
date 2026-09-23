#!/usr/bin/env bash
# Re-run the groups of oot_batch_nb.sh that did not commit, showing the gate's first hunk on a diff.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
A=soh/src/overlays/actors
sed -i 's/(st, macro, 3),/(st, macro, 4),/; s/MESSAGE_STATIC_TEX_SIZE,", 2),/MESSAGE_STATIC_TEX_SIZE,", 4),/' "$S/patch_oot_num.py"
gate_verbose() { local ok=1 f r; for f in "$@"; do case "$f" in *.h) continue;; esac; r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD 2>&1 | head -12); echo "$r" | sed 's/^/  /'; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
try() { local script=$1 grp=$2 msg=$3; shift 3; echo "== $grp"
    python3 "$S/$script" "$G" "$grp" 2>&1 | grep -v "^patched\|^done" ; git status --short | grep -q . || { echo "  (no change)"; return 1; }
    if gate_verbose "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! reverted"; git checkout -- "$@"; fi; }
try patch_oot_bool2.py ternary_bool "$W/m_oot_ternary_bool.txt" $A/ovl_En_Fr/z_en_fr.c $A/ovl_En_Hy/z_en_hy.c $A/ovl_En_Ssh/z_en_ssh.c $A/ovl_En_St/z_en_st.c $A/ovl_En_Ko/z_en_ko.c
try patch_oot_bool2.py eq1_bitfield "$W/m_oot_eq1_bitfield.txt" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
echo "== fold_return"
FR="soh/src/code/z_actor.c soh/src/code/sys_math3d.c $A/ovl_player_actor/z_player.c soh/src/overlays/effects/ovl_Effect_Ss_Kakera/z_eff_ss_kakera.c"
python3 "$OOTTOOL/fold_return_bool.py" $FR | grep "^#"
if gate_verbose $FR; then git add $FR; git commit -q -F "$W/m_oot_fold_return.txt"; git log --oneline -1; else echo "  !! reverted (per-file retry below)"; git checkout -- $FR
    for f in $FR; do python3 "$OOTTOOL/fold_return_bool.py" "$f" | grep "^# .*folded"; if gate "$f"; then git add "$f"; git commit -q -F "$W/m_oot_fold_return.txt"; git log --oneline -1; else git checkout -- "$f"; fi; done
fi
try patch_oot_num.py masks     "$W/m_oot_masks.txt"     $A/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c $A/ovl_Door_Ana/z_door_ana.c $A/ovl_En_Elf/z_en_elf.c $A/ovl_player_actor/z_player.c $A/ovl_En_GeldB/z_en_geldb.c $A/ovl_En_Wf/z_en_wf.c $A/ovl_En_Zl2/z_en_zl2.c soh/src/code/z_room.c soh/src/code/z_kaleido_scope_call.c $A/ovl_Bg_Spot02_Objects/z_bg_spot02_objects.c $A/ovl_En_Ani/z_en_ani.c $A/ovl_En_In/z_en_in.c $A/ovl_En_Ru2/z_en_ru2.c soh/src/code/code_800EC960.c soh/src/code/z_scene_table.c soh/src/code/fault.c
try patch_oot_num.py ub_shifts "$W/m_oot_ub_shifts.txt" $A/ovl_En_Wood02/z_en_wood02.c soh/src/code/audio_seqplayer.c
try patch_oot_num.py names     "$W/m_oot_names.txt"     $A/ovl_Boss_Ganon/z_boss_ganon.c soh/src/code/z_horse.c soh/src/code/z_message_PAL.c soh/src/code/z_parameter.c $A/ovl_Bg_Ingate/z_bg_ingate.c $A/ovl_En_Horse/z_en_horse.c $A/ovl_Oceff_Spot/z_oceff_spot.c $A/ovl_En_In/z_en_in.c
try patch_oot_num.py pointers  "$W/m_oot_pointers.txt"  $A/ovl_Boss_Va/z_boss_va.c soh/src/code/z_message_PAL.c
branch_summary 10
