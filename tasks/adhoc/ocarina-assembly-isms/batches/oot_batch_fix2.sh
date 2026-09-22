#!/usr/bin/env bash
# Per-file retry of the two boolean groups whose whole-group gate failed on one file each, then cf2.
set -u
. "$(dirname "$0")/oot_lib.sh"
A=soh/src/overlays/actors
per_file() { local grp=$1 msg=$2; shift 2; echo "== $grp (per file)"
    python3 "$S/patch_oot_bool2.py" "$G" "$grp" >/dev/null 2>&1 || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    local f; for f in "$@"; do if gate "$f" >/dev/null; then git add "$f"; echo "  OK  $f"; else echo "  DEF $f"; git checkout -- "$f"; fi; done
    git diff --cached --quiet || { git commit -q -F "$msg"; git log --oneline -1; }; }
per_file ternary_bool "$W/m_oot_ternary_bool.txt" $A/ovl_En_Fr/z_en_fr.c $A/ovl_En_Hy/z_en_hy.c $A/ovl_En_Ssh/z_en_ssh.c $A/ovl_En_St/z_en_st.c $A/ovl_En_Ko/z_en_ko.c
per_file eq1_bitfield "$W/m_oot_eq1_bitfield.txt" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
bash "$S/oot_batch_cf2.sh"
