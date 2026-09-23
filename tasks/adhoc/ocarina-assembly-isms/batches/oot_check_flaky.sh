#!/usr/bin/env bash
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
A=soh/src/overlays/actors
O="$W/oot_fix2.out"
echo "== stale_comments group-run hunks for z_player / z_kaleido_item"
grep -n -A7 "CODEGEN DIFFERS: soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_item.c" "$O" | head -9
grep -n -A7 "CODEGEN DIFFERS: soh/src/overlays/actors/ovl_player_actor/z_player.c" "$O" | tail -9
echo "== eq1 patch failure text"
grep -n -B2 -A6 "eq1_bitfield (per file)" "$O" | head -14
echo "== control: gate the two files now (tree clean)"
git status --short | grep -v '^??' || echo clean
gate $A/ovl_player_actor/z_player.c soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_item.c
echo "== control again (repeatability)"
gate $A/ovl_player_actor/z_player.c
echo "== eq1 sites still present?"
grep -n "enabled == 1\|isRelocated == 1\|isLoach == 1" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
echo "== yoda dry run on z_actor.c copy"
cp soh/src/code/z_actor.c "$S/za.c"; python3 "$OOTTOOL/flip_yoda.py" "$S/za.c" | tail -3
echo "== nested dry run on z_bgcheck.c copy"
cp soh/src/code/z_bgcheck.c "$S/zb.c"; python3 "$OOTTOOL/merge_nested_ifs.py" "$S/zb.c" | tail -3
grep -n -A3 "if (dynaRaycast->" "$S/zb.c" | grep -n -B1 -A2 "^[0-9]*-\s*if (" | head -12
