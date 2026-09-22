#!/usr/bin/env bash
# OoT batch — boolean shapes + numeric residue. One group = one commit, only if every file is IDENTICAL.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
run_group() { local script=$1 grp=$2 msg=$3; shift 3; echo "== $grp"
    python3 "$S/$script" "$G" "$grp" || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    commit_if_identical "$msg" "$@"; }
m() { cat > "$W/m_oot_$1.txt"; }
A=soh/src/overlays/actors

m bool_inc <<'MSG'
overlays/actors: set the En_Clear_Tag material flag instead of incrementing it

`u8 isMaterialApplied = false;` then `isMaterialApplied++` under
`if (!isMaterialApplied)` five times: the increment always goes 0 -> 1.

Verified: z_en_clear_tag.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m ternary_bool <<'MSG'
overlays/actors: drop `? true : false`, `!! == 0` and the result temporary around comparisons

`x = c ? true : false` on a u8 flag (En_Fr ×2), `return !c ? false : true`
(En_Hy), `if (!!(m) == 0)` (En_Ssh, En_St) and En_Ko's
`if (c) result = true; else result = false; return result;` — the
comparison already is the 0/1 value.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m eq1_bitfield <<'MSG'
code, overlays/actors: test the flag instead of comparing a 1-bit field / u8 flag with 1

`enabled == 1` on `u8 enabled : 1` bitfields (code_800EC960.c,
audio_effects.c), `isRelocated == 1` (`u32 isRelocated : 1`) and Fishing's
`u8 isLoach == 1`.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m fold_return <<'MSG'
code, overlays: `return c;` instead of `if (c) return true; return false;`

The condition is a comparison or a `&&`/`||` chain, so it already has the
value 0 or 1 that the two returns spell out; the s32 return type keeps
the same bits.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m ossan_dead <<'MSG'
overlays/actors: delete En_Ossan's unreachable parameter check

`params > OSSAN_TYPE_MASK && params < OSSAN_TYPE_KOKIRI` is `> 10 && < 0`
— empty (the decomp's own `//! @bug` note says the `&&` should have been
`||`). The block cannot run and GCC already omits it; making it `||`
would change behaviour, so this only removes what the ROM never did.

Verified: z_en_ossan.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m masks <<'MSG'
code, overlays/actors: drop `& 0xFFFF` where the store or the operand is already 16-bit

Stores into u8/s8/s16/Vec3s fields (Bg_Ydan_Maruta, Door_Ana, En_Elf,
z_player.c ×2, En_GeldB, En_Wf, En_Zl2, z_room.c's triple mask), masks on
u16 operands (z_kaleido_scope_call.c, Bg_Spot02_Objects, En_Ani, En_In,
En_Ru2's u16 argument, code_800EC960.c's non-negative s8), masks on the
u16 argument of coss() (z_scene_table.c ×4), and fault.c's `<< 0x10 >>
0x10` on a 5-bit field. Each mask was the MIPS `andi` before a half-word
store or of a value the type system already bounds.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m ub_shifts <<'MSG'
code, overlays/actors: multiply instead of left-shifting values that can be negative

En_Wood02's `unk_14C` is an s16 set to -1 and -0x15 on reachable paths;
`unk_14C << 4` (and `home.rot.z << 8`, an s16 from scene data) is
undefined behaviour in C when the value is negative. `* 16` / `* 256`
are defined and produce the same bits on every target; the two guarded
sites are rewritten the same way for consistency. audio_seqplayer.c's
`s8 value << 1` likewise becomes `* 2`.

Verified: both files compile to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m casts_f32 <<'MSG'
overlays/actors: drop the `(f32)` on Animation_GetLastFrame() calls

The function returns an s16; the 32 casts feed an f32 parameter or an
f32/s16 variable, and the conversion the assignment performs is the
same one the cast spelled out (an s16 round-trips through f32 exactly).

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m casts_s32 <<'MSG'
code, overlays/actors: drop `(s32)` casts that only restate integer promotion

An s16 or u8 operand of `>>`, `+`, `<` or an array index is promoted to
int anyway; the seven casts (Bg_Hidan_Kousi, Bg_Spot01_Objects2 ×2,
En_Wallmas — the outer `(s16)` wrap stays — Obj_Bean, En_Fr,
z_skin_awb.c) change nothing.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m names <<'MSG'
code, overlays/actors: use the existing names for Ganon's fwork[1] and the horse-race save bits

`this->fwork[1]` -> `fwork[GDF_FWORK_1]` (the file's own enum, used by
87 other sites); `gSaveContext.eventInf[0] & 0xF` and the `& 0x10) >> 4`
horse-type read -> `GET_EVENTINF_HORSES_STATE()` /
`GET_EVENTINF_HORSES_HORSETYPE()`, and En_In's read-modify-write of the
type bit -> `SET_EVENTINF_HORSES_HORSETYPE()` — the pure macros
z64save.h already defines for exactly these expressions.

Verified: every file compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
m pointers <<'MSG'
code, overlays/actors: byte-pointer arithmetic as `(u8*)`, and no cast into memset's void*

z_message_PAL.c adds an offset to `(uintptr_t)msgCtx->textboxSegment` and
passes the integer to memcpy — a constraint violation that compiles only
under `-Wno-int-conversion`; `(u8*)segment + offset` is the same address
as a pointer. Boss_Va's `(u8*)` on memset's `void*` argument is dropped.

Verified: both files compile to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group patch_oot_bool2.py bool_inc     "$W/m_oot_bool_inc.txt"     $A/ovl_En_Clear_Tag/z_en_clear_tag.c
run_group patch_oot_bool2.py ternary_bool "$W/m_oot_ternary_bool.txt" $A/ovl_En_Fr/z_en_fr.c $A/ovl_En_Hy/z_en_hy.c $A/ovl_En_Ssh/z_en_ssh.c $A/ovl_En_St/z_en_st.c $A/ovl_En_Ko/z_en_ko.c
run_group patch_oot_bool2.py eq1_bitfield "$W/m_oot_eq1_bitfield.txt" soh/src/code/code_800EC960.c soh/src/code/audio_effects.c soh/src/code/audio_load.c $A/ovl_Fishing/z_fishing.c
echo "== fold_return"
FR="soh/src/code/z_actor.c soh/src/code/sys_math3d.c $A/ovl_player_actor/z_player.c soh/src/overlays/effects/ovl_Effect_Ss_Kakera/z_eff_ss_kakera.c"
python3 "$OOTTOOL/fold_return_bool.py" $FR | grep -v "^  folded" ; commit_if_identical "$W/m_oot_fold_return.txt" $FR
run_group patch_oot_bool2.py ossan_dead   "$W/m_oot_ossan_dead.txt"   $A/ovl_En_Ossan/z_en_ossan.c
run_group patch_oot_num.py masks     "$W/m_oot_masks.txt"     $A/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c $A/ovl_Door_Ana/z_door_ana.c $A/ovl_En_Elf/z_en_elf.c $A/ovl_player_actor/z_player.c $A/ovl_En_GeldB/z_en_geldb.c $A/ovl_En_Wf/z_en_wf.c $A/ovl_En_Zl2/z_en_zl2.c soh/src/code/z_room.c soh/src/code/z_kaleido_scope_call.c $A/ovl_Bg_Spot02_Objects/z_bg_spot02_objects.c $A/ovl_En_Ani/z_en_ani.c $A/ovl_En_In/z_en_in.c $A/ovl_En_Ru2/z_en_ru2.c soh/src/code/code_800EC960.c soh/src/code/z_scene_table.c soh/src/code/fault.c
run_group patch_oot_num.py ub_shifts "$W/m_oot_ub_shifts.txt" $A/ovl_En_Wood02/z_en_wood02.c soh/src/code/audio_seqplayer.c
echo "== casts_f32"
python3 "$S/patch_oot_num.py" "$G" casts_f32 > "$W/oot_casts_f32.log" && CF=$(git status --short | awk '{print $2}') && commit_if_identical "$W/m_oot_casts_f32.txt" $CF
run_group patch_oot_num.py casts_s32 "$W/m_oot_casts_s32.txt" $A/ovl_Bg_Hidan_Kousi/z_bg_hidan_kousi.c $A/ovl_Bg_Spot01_Objects2/z_bg_spot01_objects2.c $A/ovl_En_Wallmas/z_en_wallmas.c $A/ovl_Obj_Bean/z_obj_bean.c $A/ovl_En_Fr/z_en_fr.c soh/src/code/z_skin_awb.c
run_group patch_oot_num.py names     "$W/m_oot_names.txt"     $A/ovl_Boss_Ganon/z_boss_ganon.c soh/src/code/z_horse.c soh/src/code/z_message_PAL.c soh/src/code/z_parameter.c $A/ovl_Bg_Ingate/z_bg_ingate.c $A/ovl_En_Horse/z_en_horse.c $A/ovl_Oceff_Spot/z_oceff_spot.c $A/ovl_En_In/z_en_in.c
run_group patch_oot_num.py pointers  "$W/m_oot_pointers.txt"  $A/ovl_Boss_Va/z_boss_va.c soh/src/code/z_message_PAL.c
branch_summary 12
