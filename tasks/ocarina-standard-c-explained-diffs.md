# OcarinaOfTime: the assembly-ism rewrites deliberately left OUT of `standard-c` (codegen changes)

**Status:** proposed — needs go-ahead (per item or group, after the identical set has been reviewed
and played; William Emerison Six <billsix@gmail.com> asked for the deliberate omissions to be their
own task, 2026-09-22 — the SM64 twin is `tasks/mario64-standard-c-explained-diffs.md`)
**Priority:** 5 · **Difficulty:** 5 (each item is small; none can be proven by the gate, so every
one needs the maintainer's in-game oracle)
**Project key:** ocarina
**Depends on:** `tasks/ocarina-de-disassemble-ugly-c.md` (the stream; this is its explained-diff list).

## BLUF

Everything from the OoT assembly-isms catalogue that is behaviour-preserving **by argument** but
changes the generated code, so the `standard-c` rule ("byte-identical assembly or it does not go
in") excluded it — each reverted by the gate during the first cut. Done = each item lands as its own
commit in a separate stream `patches/standard-c-explained/` (listed in `ORDER` after `standard-c`,
before `personal`) with the quoted asm hunks and the argument in the message, verified in-game, or
is declined here with a reason.

## Context

- Why the split exists and what "explained" means: `tasks/reference/mario64/assembly-isms-in-the-decomp.md`
  ("What the first cut found"); the gate: `ASMDIFF_PROJECT=OcarinaOfTime ASMDIFF_BUILD=<soh-build>
  bash tools/asmdiff.sh <file> HEAD` prints the differing hunks.
- Keep this a separate stream: the identical set is upstream-shaped as-is; these are a harder sell
  and must be droppable independently. Any stream added here sits UNDER `personal` (the rename
  stream), so its patches are written against the pin tree + `standard-c`.

## The list (all reverted during the first cut, 2026-09-22; the deferred-file lists are under `tasks/adhoc/ocarina-assembly-isms/data/` — `batch_bool_deferred.txt`, `batch_emptyif_deferred.txt`)

| # | site | rewrite | why codegen differs | risk |
|---|---|---|---|---|
| 1 | `soh/src/code/db_camera.c` three `goto block_2` → `block_2: return 1;` | `return 1;` at each site | GCC stops tail-merging the three returns (72 asm lines) | none; equivalent by inspection |
| 2 | `ovl_Boss_Dodongo/z_boss_dodongo.c` `if (limbIndex == 6 \|\| 7) goto block_1; block_1:` (jump to the next statement) | delete the block | the empty conditional jump anchors a basic block; removing it re-lays out the whole TU (418 lines) | none |
| 3 | `ovl_En_Ma3/z_en_ma3.c` `s16* timerSecondsPtr = &gSaveContext.timerSeconds; …timerSeconds = …timerSeconds; …timerSeconds = *timerSecondsPtr;` | delete the pointer and both self-stores | the store through the pointer after the `HIGH_SCORE` write survives at -O2 (`movw %dx, gSaveContext+5100`): 6 lines | none in a single-threaded game (stores back the value just read); the comment said "weirdness necessary to match" |
| 4 | `soh/src/code/fault.c` ×2 `(s32)((((u32)cause >> 2) & 0x1F) << 0x10) >> 0x10` | `(s32)(((u32)cause >> 2) & 0x1F)` | the 16-bit round-trip made GCC compare in `w` registers; the plain form compares in `l` (18 lines) | none; value is a 5-bit field |
| 5 | `soh/src/code/audio_seqplayer.c` `s8 value << 1` | `value * 2` | operand order of one `cmpq` (2 lines) | none; **removes UB** for negative `value` (guarded only against -1) |
| 6 | `if (c) return true; return false;` folds: `z_actor.c` ×7 (8 lines), `sys_math3d.c` ×8 (482 lines), `z_player.c` ×4 (13 925 lines — layout) | `return c;` | GCC emits `setcc`/`movzx` vs the branch pair, and in `z_player.c` the function layout moves | none; `c` is a comparison chain (0/1 already) |
| 7 | `ovl_En_Ko/z_en_ko.c` `if (c) result = true; else result = false; return result;` | `return yawDiffAbs < 0x3FFC;` | 1242 lines (layout) | none |
| 8 | `soh/src/code/code_800EC960.c` `bitField0.enabled == 1` | `.enabled` | 4 lines (`cmp $1` vs `test` on the bitfield extract) | none for a `:1` bitfield |
| 9 | 18 files of `== true/false` on plain `s32`/`s16` fields and `s32` function results (`oot_b_bool_deferred.txt`: `z_bgcheck.c` 14, `z_en_horse.c` 27, `z_collision_check.c` 7, `z_effect.c` 7, `audio_seqplayer.c` 5, …) | `x` / `!x` | `cmp $1` → `test` | each writer verified to store only 0/1 by the survey (report class A CARE tables); a value of 2 would flip `== true` |
| 10 | 8 `switch (bool)` sites (`Bg_Mori_Elevator`, `Boss_Mo`, `En_Fr`, `audio_load.c` ×4, `En_Heishi1`) | `if/else` | block layout | gains behaviour for values ≠ 0/1 (none written today) |
| 11 | `isDead++` (Boss_Va ×3, one unguarded), `stopRotate++` (En_Ex_Item ×2) | `= true` | `add` vs `mov` | reads are truthiness-only; unguarded `isDead++` would wrap at 256 today — the rewrite is strictly safer |
| 12 | 12 `else if (x == k)` ladders that are a `switch` (`z_camera.c:5978`, `z_vimode.c:81`, `z_fbdemo_triforce.c`, `z_kankyo.c`, `z_message_PAL.c:2308`, limb ladders in Boss_Ganon2/Boss_Dodongo/Fishing/En_Dha/En_Po_Field, `Bg_Jya_Bigmirror`, `Bg_Hidan_Hrock`, `En_Po_Relay`) | `switch` | jump tables | none; discriminant not written in any arm (verified) |
| 13 | `eventChkInf[11] &= ~0x800…0x8000` ×6 (`z_demo.c`), `&= 0xFFDF` (`Bg_Spot01_Fusya`) | `Flags_UnsetEventChkInf(EVENTCHKINF_…)` | a cross-TU call replaces an `andw` | none; or add a pure `CLEAR_EVENTCHKINF` macro first and it gates identical |
| 14 | `z_en_cow.c` `((u32)Rand_ZeroFloat(1000.0f) & 0xFFFF) + 40.0f` | drop the mask | `movzwl`+`cvtsi2ssl` vs `cvtsi2ssq` | none (value < 1000) |
| 15 | `(s16)frameCount` ×22 on an f32 holding an integer (e.g. `z_en_diving_game.c`) | drop | `cvttss2si`+`cvtsi2ss` | none numerically |
| 16 | `z_skin.c` `goto close_disps` → `CLOSE_DISPS; return;`; `audio_load.c` `again:` backward goto → `do/while`; `code_800E4FE0.c` `block_11` shared case tail | keyword forms | likely small diffs | read each |
| 17 | mirror-image duplicated blocks (`z_boss_ganon.c:3810-3827`, `z_en_horse.c:3209-3227`, the horse anim ladder, `z_en_zl3.c` lerp twins), `z_message_PAL.c:1954` 4-wide byte copy → `memcpy` | fold | may gate identical at -O2 — try first | — |
| 18 | "missing return" `//!` notes (`z_camera.c` ×4, `z_demo_gj.c`, `z_en_st.c`, `audio_load.c:631`) | add `return` | changes the epilogue | legal C today because every caller ignores the value — cosmetic |

## Plan

- [ ] Maintainer picks the first group (recommend #1, #2, #4, #5, #6–#8: no invariant needed —
      pure layout/instruction-selection diffs, plus one UB removal).
- [ ] Per item: commit on `imps-standard-c-explained` at the tip of the applied `standard-c`
      stream; message = rule + quoted hunks + argument; export to `patches/standard-c-explained/`;
      `ORDER` = `standard-c`, `standard-c-explained`, `personal`; `tools/check_patches_apply.sh
      OcarinaOfTime` (the rename stream must still apply on top).
- [ ] Maintainer host build + play of the affected area per group; record the verdict here.

## Open questions

1. Start with the no-invariant group (#1, #2, #4–#8)? Recommendation: yes.
