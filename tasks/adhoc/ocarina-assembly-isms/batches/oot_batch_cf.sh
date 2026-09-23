#!/usr/bin/env bash
# OoT batch — control flow + matching residue (hand-read sites). One group = one commit, only if IDENTICAL.
set -u
. "$(dirname "$0")/oot_lib.sh"
run_group() { local grp=$1 msg=$2; shift 2; echo "== $grp"
    python3 "$S/patch_oot_cf.py" "$G" "$grp" || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    commit_if_identical "$msg" "$@"; }
m() { cat > "$W/m_oot_$1.txt"; }

m goto_return <<'MSG'
code: `return` instead of `goto` to a label whose body is a `return`

z_player_lib.c `goto return_neg` / `return_neg: return -1;`, db_camera.c
three `goto block_2` / `block_2: return 1;`, and audio_heap.c two
`goto fail` whose label lived inside an `if (0) {}` only so it had a home:
each jump lands on a single return of a constant, so the jump is that
return. Labels deleted with their last reference.

Verified: all three files compile to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m goto_continue <<'MSG'
code: `continue` instead of `goto skip` in AudioPlayback_ProcessNotes

`skip:;` is the last statement of the loop body (the `if
(playbackState->priority != 0)` block that ends it), so the jump is a
`continue`. Label deleted.

Verified: audio_playback.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m goto_next <<'MSG'
overlays/actors: drop the `goto` to the next statement and the `{ s32 pad; }` in Boss_Dodongo

`if (limbIndex == 6 || limbIndex == 7) goto block_1; block_1:` jumps to
the statement that follows either way ("required for matching"); the
empty `{ s32 pad; }` block before `return 1` declared nothing that is
used. Both were stack-shape hacks for the ROM's compiler.

Verified: z_boss_dodongo.c, through its translation unit, compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m self_assign <<'MSG'
code, overlays/actors: delete the self-assignments and the lone `;` kept "to match"

`sp30 = sp30;`, `pos = pos;`, `spE8 = spE8;`, `normalVec = normalVec;`
(z_eff_blure.c, Bg_Hidan_Hamstep, Mir_Ray), the pointer-spelled twin in
En_Ma3 (`timerSecondsPtr = &gSaveContext.timerSeconds; …timerSeconds =
…timerSeconds; …timerSeconds = *timerSecondsPtr;` — a plain s16 written
with the value just read, both times) and the empty statement after
Audio_SetSequenceMode in code_800EC960.c. Each existed only to shape the
ROM's stack frame or register allocation.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m fake_temps <<'MSG'
code, overlays/actors: write the constant instead of a "needed to match" temporary

irqmgr.c `u64 temp = STATUS_PRENMI; gIrqMgrResetStatus = temp;` (and the
NMI twin), z_kaleido_setup.c `u64 temp = 0` used as a 0 twice, En_Nb and
En_Ru2 `s32 one; one = 1; D = one;`, and Boss_Tw's `s32 zero = 0; if
(zero) { accel.x *= 2.0; }` ("tricks the compiler into allocating more
stack"). The stores are the same width and value without the detour.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m dead_locals <<'MSG'
code, overlays/actors: remove dead locals and dead stores kept "to match"

`waterBoxList` (z_bgcheck.c), `unused` (En_Trap), `thisx` (En_Zl3
func_80B59AD0) are never read; `z16 = 0` (Bg_Ice_Objects) is overwritten
before every read; `xz = sinZ` / `xy = sinY` (z_skin_matrix.c) are
locals re-assigned before their next read — the `mf->` stores beside
them are fields and stay.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m aliases <<'MSG'
code, overlays/actors: drop the redundant aliases, `(*p).f`, `((void)0, x)` and `& 0xFFFFFFFF`

`EnRu1* thisx = this` (one use), `csCmdNPCAction2` copied into
`csCmdNPCAction`, `ac = (ActorContext*)play` overwritten before use
(Obj_Mure), `unk2C7` copy of `this->unk_2C7` (En_Elf), the
`((void)0, expr)` comma tricks (En_GeldB, En_Horse), `(*msgCtx).x` and
`(*newPoly).x` for `->` (En_Fr, z_bgcheck.c), and `& 0xFFFFFFFF` on an
s32 (game.c) — each a register-allocation nudge for the ROM's compiler,
each a no-op in C.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m always_true_guard <<'MSG'
overlays/actors: unwrap the always-true `if (sp150)` inside `for (i1 = 0; i1 < sp150; i1++)` in Boss_Fd

Inside the loop `i1 < sp150` with `i1 >= 0` already means `sp150 != 0`.

Verified: z_boss_fd.c, through its translation unit, compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m if1_unwrap <<'MSG'
boot, code, overlays/actors: unwrap the `if (1) {` blocks

A constant-true `if` was the decomp's way to open a scope the ROM's
compiler needed (z_std_dma.c, code_800EC960.c, z_actor.c, Bg_Hidan_Hrock,
Demo_Go — bodies hoisted; z_player_lib.c — with its dead `s32 pad[2]`).
Where the block declares locals (Boss_Fd, Boss_Ganon2) it becomes a bare
`{ … }` scope so the declarations keep their extent.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m empty_arms <<'MSG'
code, overlays/actors: delete the empty if/else arms kept "to match"

audio_synthesis.c's three-arm `if … {} else if … {} else {}` ("no-op ifs
required for matching"), Bg_Treemouth's empty `else`, a commented-out
`if (!x) {}` in z_camera.c, and ucode_disas.c's `if (x == 0) {} else {
print }` written as `if (x != 0) { print }` (dropping the clang-format
fence that protected only that one-liner; the twin below already reads
`if (this->enableLog)`).

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m unreachable <<'MSG'
overlays/actors: delete `break` after `return` and a stray `;`

Obj_Oshihiki's three `return …; break;` case arms and the `;` before the
closing brace of ObjBean_UpdateLeaves.

Verified: both files, through their translation units, compile to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m parameter_tails <<'MSG'
code: `else` instead of a redundant `else if (X == 0)` after `if (X != 0)` in Interface_Update

Seven `restrictions.*` chains test a field and then its exact complement;
nothing between the two tests writes `interfaceCtx->restrictions` (the
arms write only `gSaveContext.buttonStatus[]` and a local), so the second
test is `else`.

Verified: z_parameter.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

A=soh/src/overlays/actors
run_group goto_return      "$W/m_oot_goto_return.txt"      soh/src/code/z_player_lib.c soh/src/code/db_camera.c soh/src/code/audio_heap.c
run_group goto_continue    "$W/m_oot_goto_continue.txt"    soh/src/code/audio_playback.c
run_group goto_next        "$W/m_oot_goto_next.txt"        $A/ovl_Boss_Dodongo/z_boss_dodongo.c
run_group self_assign      "$W/m_oot_self_assign.txt"      soh/src/code/code_800EC960.c soh/src/code/z_eff_blure.c $A/ovl_Bg_Hidan_Hamstep/z_bg_hidan_hamstep.c $A/ovl_Mir_Ray/z_mir_ray.c $A/ovl_En_Ma3/z_en_ma3.c
run_group fake_temps       "$W/m_oot_fake_temps.txt"       soh/src/code/irqmgr.c soh/src/code/z_kaleido_setup.c $A/ovl_En_Nb/z_en_nb.c $A/ovl_En_Ru2/z_en_ru2.c $A/ovl_Boss_Tw/z_boss_tw.c
run_group dead_locals      "$W/m_oot_dead_locals.txt"      soh/src/code/z_bgcheck.c $A/ovl_En_Trap/z_en_trap.c $A/ovl_En_Zl3/z_en_zl3.c $A/ovl_Bg_Ice_Objects/z_bg_ice_objects.c soh/src/code/z_skin_matrix.c
run_group aliases          "$W/m_oot_aliases.txt"          $A/ovl_En_Ru1/z_en_ru1.c $A/ovl_Obj_Mure/z_obj_mure.c $A/ovl_En_Elf/z_en_elf.c $A/ovl_En_GeldB/z_en_geldb.c $A/ovl_En_Horse/z_en_horse.c $A/ovl_En_Fr/z_en_fr.c soh/src/code/z_bgcheck.c soh/src/code/game.c
run_group always_true_guard "$W/m_oot_always_true_guard.txt" $A/ovl_Boss_Fd/z_boss_fd.c
run_group if1_unwrap       "$W/m_oot_if1_unwrap.txt"       soh/src/boot/z_std_dma.c soh/src/code/code_800EC960.c soh/src/code/z_actor.c soh/src/code/z_player_lib.c $A/ovl_Bg_Hidan_Hrock/z_bg_hidan_hrock.c $A/ovl_Boss_Fd/z_boss_fd.c $A/ovl_Boss_Ganon2/z_boss_ganon2.c $A/ovl_Demo_Go/z_demo_go.c
run_group empty_arms       "$W/m_oot_empty_arms.txt"       soh/src/code/audio_synthesis.c $A/ovl_Bg_Treemouth/z_bg_treemouth.c soh/src/code/z_camera.c soh/src/code/ucode_disas.c
run_group unreachable      "$W/m_oot_unreachable.txt"      $A/ovl_Obj_Oshihiki/z_obj_oshihiki.c $A/ovl_Obj_Bean/z_obj_bean.c
run_group parameter_tails  "$W/m_oot_parameter_tails.txt"  soh/src/code/z_parameter.c
branch_summary 14
