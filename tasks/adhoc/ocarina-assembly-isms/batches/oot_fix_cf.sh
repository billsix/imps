#!/usr/bin/env bash
# Commit the gate-identical parts of the three control-flow groups that failed as wholes; probe Dodongo.
set -u
. "$(dirname "$0")/oot_lib.sh"
A=soh/src/overlays/actors
git checkout -- soh/src/code/db_camera.c $A/ovl_En_Ma3/z_en_ma3.c $A/ovl_Boss_Dodongo/z_boss_dodongo.c
cat > "$W/m_oot_goto_return.txt" <<'MSG'
code: `return` instead of `goto` to a label whose body is a `return`

z_player_lib.c `goto return_neg` / `return_neg: return -1;` and
audio_heap.c two `goto fail` whose label lived inside an `if (0) {}`
only so it had a home: each jump lands on a single `return` of a
constant, so the jump is that return. Labels deleted with their last
reference. (db_camera.c has three `goto block_2` of the same shape, but
GCC then stops tail-merging the returns; that one is left for the
explained-diff list.)

Verified: both files compile to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m_oot_self_assign.txt" <<'MSG'
code, overlays/actors: delete the self-assignments and the lone `;` kept "to match"

`sp30 = sp30;`, `pos = pos;`, `spE8 = spE8;`, `normalVec = normalVec;`
(z_eff_blure.c, Bg_Hidan_Hamstep, Mir_Ray) and the empty statement after
Audio_SetSequenceMode in code_800EC960.c. Each existed only to shape the
ROM's stack frame or register allocation. (The pointer-spelled twin in
En_Ma3 is NOT a no-op in the generated code — the store back through
the pointer survives — so it is left for the explained-diff list.)

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
gate soh/src/code/z_player_lib.c soh/src/code/audio_heap.c && git add soh/src/code/z_player_lib.c soh/src/code/audio_heap.c && git commit -q -F "$W/m_oot_goto_return.txt" && git log --oneline -1
gate soh/src/code/code_800EC960.c soh/src/code/z_eff_blure.c $A/ovl_Bg_Hidan_Hamstep/z_bg_hidan_hamstep.c $A/ovl_Mir_Ray/z_mir_ray.c && git add soh/src/code/code_800EC960.c soh/src/code/z_eff_blure.c $A/ovl_Bg_Hidan_Hamstep/z_bg_hidan_hamstep.c $A/ovl_Mir_Ray/z_mir_ray.c && git commit -q -F "$W/m_oot_self_assign.txt" && git log --oneline -1
D=$A/ovl_Boss_Dodongo/z_boss_dodongo.c
echo "== dodongo probe: pad block only"
python3 - "$D" <<'EOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
old = "    { s32 pad; } // Required to match\n    return 1;\n}"; assert s.count(old) == 1
p.write_text(s.replace(old, "    return 1;\n}"))
EOF
gate "$D"; git checkout -- "$D"
echo "== dodongo probe: goto only"
python3 - "$D" <<'EOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
old = "    // required for matching\n    if ((limbIndex == 6) || (limbIndex == 7)) {\n        goto block_1;\n    }\nblock_1:\n    Matrix_TranslateRotateZYX(pos, rot);"
assert s.count(old) == 1
p.write_text(s.replace(old, "    Matrix_TranslateRotateZYX(pos, rot);"))
EOF
gate "$D"; git checkout -- "$D"
branch_summary 4
