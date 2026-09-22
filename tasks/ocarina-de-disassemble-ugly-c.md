# OcarinaOfTime: rewrite the decomp's assembly-isms into standard C — the `standard-c` stream, UNDER the rename stream

**Status:** first cut COMPLETE 2026-09-22 — awaiting the maintainer's review and host play.
Result: **36 codegen-identical patches** in `patches/standard-c/`, `ORDER` = `standard-c`,
`personal`; the 488-patch rename stream **re-cut on top** (87 conflicts resolved mechanically, zero
hand edits), every rename gate and the old-vs-new tree gate green (496/496 identical),
`tools/check_patches_apply.sh OcarinaOfTime` 524 clean; full sandbox build: last Progress-log
entry. Left for the maintainer: (a) review the 120 rename patches whose content changed (87
resolved + 33 context moves), (b) the explained-diff list (`tasks/ocarina-standard-c-explained-diffs.md`),
(c) the naming classes (stack-slot locals, `argN`, per-actor `params` macros — not attempted), (d)
the bugs task. Started 2026-09-22 (William Emerison Six <billsix@gmail.com>: "do the
same thing for Ocarina Of Time. make a task first, stage it, and then start implementing"),
unattended, with authorisation to commit in the `Shipwright` checkout and export patches, and to
**re-cut the 488-patch `personal` rename stream** where it stops applying on top ("sure … I
version control all of these patches, so I will lose nothing"). Decisions taken at start (the
maintainer's answers, 2026-09-22): codegen-identical-only first cut (as SM64); rewrites that
change codegen go to an explained-diff task; the rewrites apply FIRST, the renames on top.
**Priority:** 4 · **Difficulty:** 8 (the rewrites are the same job as SM64's; the 488 rename
patches sitting on top are what makes this hard) · **Project key:** ocarina
**Started:** 2026-09-08 as a `proposed` stub (goal 3 of the rename effort); rewritten 2026-09-22
into the working task, modelled on `tasks/mario64-assembly-isms-to-standard-c.md`.

## BLUF

Find every construct in Ship of Harkinian's OoT decomp (`Shipwright/soh/src/{code,overlays,boot,…}`)
that reads like mechanically-lifted MIPS rather than C and rewrite the ones that are **clearly and
explainably** behaviour-preserving into standard C, as a patch stream `patches/standard-c/` that
applies **first** — before the personal 488-patch rename stream — with every patch proved by the
SM64 assembly-diff gate (identical generated code, or it does not go in). "Done" = the safe
classes are rewritten and exported; the `personal` rename stream still applies on top (re-cut
where it no longer does, same final tree); `tools/check_patches_apply.sh OcarinaOfTime` and a full
build are green; the docs are current; the explained-diff list is filed as its own task.

## Context (cold-start)

Read first, in order:

1. **`tasks/reference/mario64/assembly-isms-in-the-decomp.md`** — the patterns and the semantic
   rules; SM64 and OoT come from the same decomp lineage (zeldaret / sm64 decomp, same
   `//! @bug` conventions, same `sp24`/`temp_v0`/`phi_s3` naming, same padding fillers), so
   the 20 patterns and "What the first cut found" apply almost verbatim. OoT differences are
   listed below.
2. `tasks/mario64-assembly-isms-to-standard-c.md` — the method that worked: batches per class ×
   directory, the gate, per-file revert of anything not IDENTICAL, per-directory commits.
3. `tasks/reference/ocarina/decomp-renaming.md` — the rename effort's **Guardrails** (OoT has more
   name-based indirection: `ActorDB`, gamestate tables, function-pointer tables) and the file-rename
   mechanics (`GLOB_RECURSE`, so a `git mv` needs a re-configure). `tasks/reference/ocarina/decomp-map.md`
   for where subsystems live.
4. `n64/OcarinaOfTime/CLAUDE.md` + `patches/ORDER` — today's single stream `personal` (488
   patches: 3,781 symbol renames + 18 file renames, written against the bare pin). The stream is
   re-created by `git am` from `patches/personal/`, so the checkout normally sits at pin + 488.
5. The survey kit: `tasks/adhoc/ocarina-assembly-isms/discover.sh` (the census; `data/*.txt` +
   `SUMMARY.txt`, `reports/*.md`, and the one-shot batch runners under `batches/`) and the
   promoted tools in `tools/` (`asmdiff.sh` takes the project via `ASMDIFF_PROJECT`; the per-class
   rewrite tools in `tools/standard-c/`; map: `tasks/reference/imps/standard-c-tooling.md`).

Facts that shape everything (verified 2026-09-22 against pin `acdbc651d`):

- **The `personal` stream must apply on top of `standard-c`.** `patches/ORDER` becomes
  `standard-c`, `personal`. A rename patch touches the same lines a rewrite touches (renames are
  whole-file symbol substitutions), so `git am --3way` WILL conflict in the files both streams
  touch. Resolution policy (maintainer, 2026-09-22): fix the conflicting rename patches; where
  that becomes impractical, **re-cut** the rename stream — regenerate it from its end result so
  the *final tree* (pin + standard-c + renames) is the pin + old-renames tree with the same
  rewrites applied, proven by re-running the standard-c rewrites' gate on the renamed tree AND by
  `tools/check_renames.py` (the rename effort's own totality check). Every changed rename patch is
  logged in the Progress log.
- **The gate runs on the BARE PIN tree** (branch `imps-standard-c` in `Shipwright`), because the
  rename stream renames 18 files and thousands of symbols — the stream is written against what
  upstream has. Configured tree: the scratch `soh-build` (`cmake -S Shipwright -B <dir> -GNinja
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`; needs `opus-devel`,
  `opusfile-devel`, `libogg-devel`, `libvorbis-devel` in the sandbox — installed 2026-09-22,
  candidates for the sandbox base list like `libshaderc-devel` was).
- The decomp is compiled as **C (C23, `-O2`)** by GCC (`soh/CMakeLists.txt`: `CMAKE_C_STANDARD 23`;
  the Linux flags block mirrors the CafeOS one: `-O2`, `-Werror-implicit-function-declaration`,
  the `-Wno-*` set). 804 `.c` files under `soh/src`, no `.cpp` there. `-O2` means the memset/
  memcpy-loop class MAY gate identical here (unlike SM64 at `-O1`) — try it.
- **Port-layer code lives in `soh/soh/` (C++)** — excluded. `soh/src/` is the decomp; SoH has
  edited it heavily (enhancements interleaved with decomp code, `CVarGetInteger(...)` guards,
  `GameInteractor` hooks), so "upstream" for a rewrite is SoH, not zeldaret; keep SoH's edits
  intact and match the surrounding hand style. SoH's clang-format covers `soh/soh/` only? —
  verify before any formatting; never reformat a decomp file.
- OoT-specific idioms to expect (zeldaret conventions): `if (1) {}` / `if (0) {}` matching
  blocks, `PAD`/`padding`/`unk_XX` struct fillers (layout-fixed — leave), `s32 pad;` locals,
  `temp_*`/`phi_*`/`sp*` names, `UNK_TYPE`, `BINANG`/`DEG_TO_BINANG` angle macros (the analogue
  of `DEGREES()`), `!` block comments `//!`, `FAKE`/`fake match` notes, `do {} while (0)` in
  macros (leave: those are macro hygiene, not matching residue).

## The gate

Same tool, parametrised: `ASMDIFF_PROJECT=OcarinaOfTime ASMDIFF_BUILD=<soh-build> bash
tools/asmdiff.sh soh/src/code/z_actor.c [<ref>=HEAD]`. Rule as SM64:
**IDENTICAL for every touched file, or the change is reverted and listed for the explained-diff
task.** `-D__LINE__=0` pinning stays (SoH macros bake `__LINE__` too).

## Ground rules

The SM64 task's rules 1–8 apply unchanged (behaviour-preserving is the hard rule; never script a
class blind — tool + SKIP list + per-file gate; one class × one directory per patch; delete the
matching comment with the construct; header prototypes move with renames; leave uncompiled
regions; keep `//!` notes; upstream-shaped commit messages with the rule + gate result). Plus:

9. **Never touch a SoH enhancement line** in a decomp file (anything under a `CVarGet*` guard or
   a `GameInteractor` call) unless the rewrite is inside pure decomp code around it.
10. **Every rename-stream patch that has to change is logged** (which, why, how: hand-fix vs
    re-cut), because the maintainer version-controls those patches and will diff them.

## Plan

- [x] **Phase A — survey.** (Done 2026-09-22: census, four parallel reader reports, catalogue, gate
      proven both ways.) Census (`discover.sh`, done 2026-09-22 — see Progress log), parallel
      verified reads per directory group (`code/`, `overlays/actors`, `overlays/{effects,gamestates,misc}`,
      `boot`+`libultra`), the catalogue below, the gate proven both ways on SoH (untouched file →
      IDENTICAL; one flipped operator → diff).
- [x] **Phase B — batches, safest first** (first cut done 2026-09-22 — the Progress log entry lists
      every group; the explained-diff list is `tasks/ocarina-standard-c-explained-diffs.md`; the
      naming classes — stack-slot locals, `argN`, per-actor `params` macros — are NOT in the first
      cut) (same order as SM64): `register`; matching residue
      (`if (1) {}`, lone `;`, `do{}while(0)` around one call, one-line-to-match); `goto`→keyword;
      redundant `else if`; `== TRUE`/`!= FALSE` on boolean-valued operands; 16-bit residue;
      `UNUSED`/`pad` locals (function-local only); raw indices → names; argN/register-named params;
      regex-missed constructs. Each: commit on `imps-standard-c`, gate, export
      `patches/standard-c/`, replay.
- [x] **Phase C — the rename stream on top.** (Done 2026-09-22 — Progress log: 87 patches resolved mechanically, all gates green.) `patches/ORDER` = `standard-c`, `personal`;
      `./fetch.sh && ./apply.sh`; for each rename patch that fails: hand-fix (re-export that
      patch) or, if the failures pile up, re-cut the stream; prove the final tree (renames total
      via `tools/check_renames.py`; the rewrites' gate re-run on the renamed tree);
      `tools/check_patches_apply.sh OcarinaOfTime`; full build.
- [x] **Phase D — docs + follow-ups.** (Done 2026-09-22; `tasks/ocarina-upstream-standard-c.md`,
      `tasks/ocarina-standard-c-explained-diffs.md`, `tasks/ocarina-decomp-bugs-found-by-survey.md`
      filed `proposed`.) `n64/OcarinaOfTime/CLAUDE.md` patch list + ORDER note;
      `n64/CLAUDE.md` index + stream list; drift table; `tasks/reference/imps/patch-streams-design.md`
      (ORDER case); reference doc: an OoT section in `assembly-isms-in-the-decomp.md` (or its own
      doc if the differences warrant); file `tasks/ocarina-standard-c-explained-diffs.md` and
      `tasks/ocarina-upstream-standard-c.md` (proposed).
- [ ] **Maintainer:** host build + play with the full series; review the changed rename patches.

## The catalogue

Census counts are `data/SUMMARY.txt` (2026-09-22, pin tree); "real" = what the readers verified by
reading (`tasks/adhoc/ocarina-assembly-isms/reports/*.md` — the per-site tables, look-alike lists
and grep commands live there; this is the index). Verdicts: **DO** = mechanical, gate-provable;
**CARE** = per site with an argument, usually an explained diff; **LEAVE** = not this task.
Anchors are `Shipwright/soh/src/…` as of the pin (line numbers rot as batches land — locate by text).

### A. Control flow and matching residue (`reports/control-flow-and-matching.md`)

| class | hits → real | verdict | what / where |
|---|---|---|---|
| `goto` | 63 → 63 (41 labels) | **DO** 4 shapes / CARE 3 / LEAVE rest | goto-as-return: `z_player_lib.c` `return_neg`, `audio_heap.c` `fail` (+ its `if (0) {}` home) — done; `db_camera.c` `block_2` ×3 gates DIFF (tail-merge) → explained. goto-as-continue `audio_playback.c skip:;` — done. goto-to-next-statement `z_boss_dodongo.c block_1` gates DIFF (418 lines, block layout) → explained. CARE: `z_skin.c close_disps`, `audio_load.c again:` (backward = do/while), `code_800E4FE0.c block_11`. LEAVE: 9 SoH-authored, 3 in `#if 0`, jumps into another `case` (`z_camera.c` ×4, bosses), labelled breaks, cleanup tails. |
| infinite loops | 71 → 70 | **DO** 11 test-first / LEAVE rest | rewrite to `while (test)`: `audio_load.c` ×2, `z_jpeg.c`, `z_map_mark.c`, `z_lmap_mark.c`, `pfsfilestate.c` (uncompiled), `z_file_choose.c` ×2, `z_bg_spot16_bombstone.c`, `code_800EC960.c`, `z_eff_blure.c`. LEAVE: event loops, interpreters, 15 `z_bgcheck.c` list walks (exit after the first statement), `z_bgcheck.c:1698` (float/NaN). Not yet batched. |
| `if (x) {}` / `if (1)` / `if (0)` | 75 + 9 + 11 | **DO** (done: 72 empty ifs, 8 `if (1) {` unwraps, 2 empty-arm chains, the ucode_disas inversion) / LEAVE `if (0) { rodata strings }` | tool `tools/standard-c/drop_empty_if.py`; 1 file deferred (`z_view.c`, `data/batch_emptyif_deferred.txt`). |
| `else if (x == k)` ladders | 397 | **DO** 7 (done: `z_parameter.c` tails) / CARE 12 switch candidates / LEAVE side-effecting | switch candidates (`z_camera.c:5978`, `z_vimode.c:81`, `z_fbdemo_triforce.c`, `z_kankyo.c`, limb ladders in bosses) = jump tables → explained-diff. |
| matching comments | 91 → 72 excusing a construct | **DO** ~30 (done: lone `;`, `{ s32 pad; }`, self-assignments ×4, `u64 temp` ×3, `s32 one` ×2, dead locals ×5, dead stores ×2, aliases ×4, `((void)0, x)` ×2, `(*p).f` ×3, `& 0xFFFFFFFF`, always-true guard, `if (zero)`) / CARE / LEAVE | En_Ma3 pointer self-store gates DIFF (the store survives) → explained; 11 stale comment-only fixes pending; LEAVE `* 0.2` double, `//! @bug` notes, `boss_fd.c:492`. |
| `volatile` / `OOT_DEBUG` | 15 / 14 | LEAVE (live cross-thread) / DO 1 (`D_8016A578` zero refs) | |
| extras | — | **DO** 5 unreachable `break` (done ×3 compiled; 2 in uncompiled libultra), stray `;` (done); 21 nested-if `&&` chains (pending, gate each) | `do{}while(0)` in bodies: 0. |

### B. Naming residue (`reports/naming-register-unused-filler.md`)

| class | hits → real | verdict | what / where |
|---|---|---|---|
| `register` | 56 → 48 decls | **LEAVE** | all in `libultra/io`, `libultra/os` — excluded from the build (`soh/CMakeLists.txt:191-193`); ungateable. |
| function-local `s32 pad;` | census wrong both ways → **1 717** never-referenced locals (`data/filler_function_local_unreferenced.txt`) + 20 nested-scope duplicates | **DO** (tool `drop_pad_locals.py`, per function + text, gate per file) | 14 locals named `pad` are real variables (`z_camera.c`, `z_vr_box.c`, `audio_seqplayer.c`, `z_boss_va.c`, `z_boss_mo.c`, `z_boss_sst.c`, `z_en_torch2.c`) — not on the list; header/struct fillers (1 242 lines) LEAVE (memcpy'd: `SaveManager.cpp`, `savestates.cpp`). |
| stack-slot / `temp_` / `phi_` names | 10 087 → 1 988 decls in 748 functions | CARE per function (~85% nameable) | 8 two-meaning slots need a second variable (`db_camera.c new_var2`, `Camera_CalcUpFromPitchYawRoll sp54`, …); 5 loop-carried `phi_` groups rename-only; 9 dead temps → delete. Tool: `rename_in_function.py`; `-w` hides `-Wshadow` — compile touched files with it. Not batched in the first cut. |
| `argN` params | 1 767 → 172 defs in `code/` (~110 nameable), 30 hottest in overlays tabled | CARE (naming) | never rename `z64audio.h:706-735` `u8 arg0/1/2` (struct fields); rename call chains together (`Skin_*`, `func_800F3F84…`). `functions.h:452` names a param `arg4` the definition calls `exchangeItemId`. Not batched. |
| `UNUSED` | 1 → 0 | — | OoT uses `s32 pad;` and `(void)x;`; no side-effecting dead locals found (two scans). |

### C. Booleans and annotations (`reports/booleans-comments-whole-functions.md`)

| class | hits → real | verdict | what / where |
|---|---|---|---|
| `== true/false` | 136 → 133 decomp + 3 SoH | **DO** ~58 (done: 14 files gate-identical) / CARE 74 (s32 fields/results) | tool `drop_true_false_cmp.py` with the SoH + value-test SKIPs; 18 files deferred (`oot_b_bool_deferred.txt`) → explained. Look-alikes: `lightDecay`, `noStop` (values, not booleans), `audio_heap.c` `(apply != false) && (apply == true)`. |
| other boolean shapes | — | **DO** (done: `isMaterialApplied++` ×5; pending gate: `? true : false` ×3, `!!(m) == 0` ×2, `== 1` on bitfields ×6, `if (c) return true; return false;` folds) / CARE 8 `switch (bool)`, `isDead++`, `stopRotate++` | Yoda `literal < x` ×40 decomp sites → DO (not yet batched); `!!x` returns LEAVE. |
| `//!` annotations | 213 → 121 notes | LEAVE (C1) / DO 1 C2 (done: En_Ossan dead block) / 6 C3 comment-only (pending) | |
| whole-function shapes (12 files read) | 17 constructs | mixed | comma-in-`if` (`z_camera.c` ×3), post-increment split (`z_collision_check.c` ×3), parameter-as-scratch (`z_actor.c`, `z_player.c` ×4), 4-wide byte copy → memcpy (`z_message_PAL.c:1954`, may gate at -O2), mirror blocks (explained). |
| **bugs found (not this stream)** | — | file separately | uninitialised `getItemId` (`z_en_ge1.c`) and `fairyType` (`z_shot_sun.c`) — switches without `default`; OOB `sOwEntranceFlag[20]` read (`z_map_exp.c`, `z_map_data.c`); 64-bit sentinel truncation `z_en_horse.c` `0xABABABAB`. |

### D. Raw memory and numeric (`reports/raw-memory-and-numeric.md`)

| class | hits → real | verdict | what / where |
|---|---|---|---|
| `& 0xFFFF` / `<<16>>16` | 87 → 22 droppable | **DO** (batched) / CARE 3 / LEAVE 61 | `fault.c` sign-extension idiom gates DIFF (`cmpw`→`cmpl`) → explained; `z_en_ex_item.c` mask is load-bearing (`(u16)` spelling instead); `z_en_cow.c` DIFF; audio/RSP/S2DEX words LEAVE. |
| signed `<<` | 680 → 5 UB | **DO** (done: En_Wood02 ×4) | `audio_seqplayer.c` `s8 value << 1` → `* 2` gates a 2-line operand-order DIFF → explained. `>>` on signed: never `/`. |
| named indices | — | **DO** (done: `fwork[GDF_FWORK_1]` ×5, horse-race `GET/SET_EVENTINF_HORSES_*` ×15, `(u8*)` textboxSegment ×4, memset cast) / CARE `eventChkInf[11] &= ~bit` ×7 (a call → DIFF) | no `rawData` union in OoT; `unk_XX[]` are typed arrays (rename task, not this). |
| casts | `(s32)` 442 → 7, `(f32)` 370 → 32 | **DO** (done) / LEAVE `(s16)` (0 removable), float truncations | `(s16)frameCount` ×22 numerically a no-op but DIFF → explained. |
| `params` unpacking | 1 051 raw sites, 190 actors | CARE (naming: per-actor `ENXXX_GET_*` via `PARAMS_GET_U/S/NOSHIFT`, shape-to-shape only) | identical by construction; a ~190-header naming job — scope decision for the maintainer. |
| angle constants | 13 730 | **LEAVE** | no integer `DEG_TO_BINANG`; `DEGF_TO_BINANG(180.0f)` is UB (out-of-range float→s16); `BINANG_ROT180` is off by one from `+ 0x8000`. |
| double literals, `/ const` | 361, 995 | **LEAVE** | five result-changing doubles listed in the report (`z_actor.c:2477` `// required to match`); pow2 divisors already strength-reduced. |

## Progress log

- 2026-09-22 — **Phase A started.** Checkout branch `imps-standard-c` created at the pin
  (`acdbc651d`; the maintainer's applied-series checkout was clean, the 488-patch tree is
  reproducible from `patches/personal/`). Scratch configure of `Shipwright` with
  `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` → 1374 TUs under `soh/src` (`code` 151, `overlays` 512,
  `boot` 10, `libultra` 11, `buffers` 3); needed `opus-devel` + `opusfile-devel` in the sandbox
  (installed; added to both sandboxes' `01-install-base.sh`, staged there). **Gate proven both ways
  on SoH** (`ASMDIFF_PROJECT=OcarinaOfTime`): untouched `z_actor.c` → IDENTICAL; one `&`→`|` flip
  → 199 differing asm lines. Flags that matter: `-O2 -fno-fast-math -ffp-contract=off`, C, GCC
  (so, unlike SM64 at `-O1`, byte-loop → `memset`/`memcpy` MAY gate identical here).
  **Census** (`discover.sh`, 32 classes, `data/SUMMARY.txt`): goto 63, `if (1)` 9, empty then 75,
  `else if (x == k)` 397, matching comments 91, `register` 56, stack/temp/phi names 10087, argN
  1767, pad/unk fillers 11789, `== TRUE`-family 136, `& 0xFFFF`/`<<16>>16` 87, `<<`/`>>` small
  shifts 680, `(s16)` 1051, double literals 361, BINANG macros 212. **117 of 804 `.c` files are
  not compiled by SoH** (114 `libultra`, `dmadata`, `elf_message` — `data/uncompiled.txt`): not
  gateable, LEAVE. Consequence already found: **the `register` class is empty in compiled code** —
  all 52 real `register` declarations are in uncompiled `libultra/`; the 4 hits in compiled TUs are
  the word in comments. Four parallel readers (naming / control-flow / raw-numeric / booleans) are
  producing `reports/*.md`; the catalogue is written from them.

- 2026-09-22 — **Phase B (batches), first cut.** All on `imps-standard-c`, every commit gate-identical
  per touched file, one class × directory group per commit (revert-on-diff policy as SM64):
  booleans on 0/1 operands (2 commits, 14 files; 18 files deferred — plain s32 fields); empty
  `if (x) {}` (3 commits, 46 files, `drop_empty_if.py`); goto→return/continue, self-assignments,
  fake temps, dead locals/stores, aliases/`(*p).f`/`((void)0,x)`/`& 0xFFFFFFFF`, always-true guard,
  `if (1) {` unwraps, empty arms + the ucode_disas inversion, unreachable `break`/stray `;`, the
  seven `z_parameter.c` `else if` tails (11 commits); `isMaterialApplied++`, `? true : false`/
  `!! == 0`/`return result` folds, `== 1` on bitfields, En_Ossan's dead block (4 commits);
  `& 0xFFFF` drops (15 files), En_Wood02 UB shifts, `(f32)Animation_GetLastFrame` ×32, `(s32)`
  promotion no-ops ×7, `fwork[GDF_FWORK_1]` + horse-race `GET/SET_EVENTINF_HORSES_*`,
  `(u8*)textboxSegment` + memset cast (6 commits); **the `s32 pad;` sweep: 1 710 declarations in
  461 files, 0 deferred** (`drop_pad_locals.py`, per function + text, 5 commits); test-first loops
  ×9 + z_eff_blure (2 commits); stale matching/`//!` notes (1 commit); Yoda flips and nested-if
  `&&` merges (`flip_yoda.py`, `merge_nested_ifs.py` — 63 files kept between them; 6 + 13 files deferred).
  **Gate incidents:** (a) the normaliser now renumbers `.LFB/.LFE/.LC` labels too (a fold moved
  function numbering; control re-proven both ways on SoH and SM64 afterwards); (b) the first
  `tool_sweep` mis-parsed the tool's count and left ~100 files edited but ungated — caught by the
  next group's gate showing impossible diffs for comment-only edits; the tree was reset and the
  sweeps redone with the fixed parser — nothing ungated was ever committed (every commit re-gated
  its own files after a clean checkout). **Explained-diff list** (reverted, filed in
  `tasks/ocarina-standard-c-explained-diffs.md`): db_camera `goto block_2` ×3, Boss_Dodongo goto-to-
  next, En_Ma3 pointer self-store (the store survives), fault.c sext idiom (`cmpw`→`cmpl`),
  `audio_seqplayer.c` `value << 1` (one `cmpq` operand order), `if (c) return true` folds (z_actor.c,
  sys_math3d.c, z_player.c), En_Ko result temp, code_800EC960 `.enabled == 1`, z_file_choose digit
  loops (58 lines), z_kaleido_equipment empty-if-with-note, the 18 `== true` files, `switch (bool)`
  ×8, 12 switch-shaped ladders, `Flags_UnsetEventChkInf` ×7, `(s16)frameCount` ×22.

- 2026-09-22 — **Phase C (the rename stream on top) + gates.** Stream exported: **36 patches** in
  `patches/standard-c/`; `patches/ORDER` = `standard-c`, `personal` (rationale inline).
  **Stream gate:** every one of the 486 files the branch changed compiles identically at the branch
  and at the pin (486/486). **Replay:** `git -c merge.conflictStyle=diff3 am --3way` of the old 488
  rename patches onto `imps-standard-c` (branch `imps-applied`): 401 applied untouched, **87
  conflicted and were resolved mechanically** by `resolve_rename_conflicts.py` (our side of each
  block + that patch's `old -> new` renames + its added provenance lines; the inline `// was …`
  tag appended to a rewritten line is carried over by prefix match) — one shape needed the tool
  extended mid-run (`z_bg_spot01_objects2.c`: rename + appended tag on a line whose cast the
  rewrites had dropped). Zero patches needed a human edit. **Rename gates on the new tree:**
  `tools/check_renames.py series` (487 symbol commits, 3 781 renames claimed, all total),
  `traceable`, `declarations` — ALL PASSED. **Final tree gate:** every file that differs between
  the old applied tree (`imps-personal-old` = pin + old renames) and the new one (pin + standard-c
  + re-cut renames) compiles identically — 478 by path, plus the 18 renamed files gated with their
  old path's compile command (`ASMDIFF_CMD_FROM`) — 496/496, 0 differ. So the re-cut changed no
  code: the new tree is the old tree with the rewrites applied, and the rewrites are invisible to
  the compiler. `personal` re-exported: 488 patches, `--base` = the standard-c tip; 120 of 488
  differ in content from the old series (87 resolved + 33 whose context lines moved), all 488 in
  SHAs. `tools/check_patches_apply.sh OcarinaOfTime`: 524 patches applied cleanly from the bare pin.
  Full build of the applied tree: see the next entry.

- 2026-09-22 — **Full sandbox build of the applied tree** (`imps-applied` = pin + 36 standard-c +
  488 re-cut renames; scratch `soh-build` reconfigured for the 18 renamed files): 1731/1731,
  `soh.elf` linked (52.9 MB), 0 errors. **Phase D docs:** `n64/OcarinaOfTime/CLAUDE.md` (stream
  entry, re-cut note, ORDER), `n64/CLAUDE.md` (stream list, index line, ORDER cases),
  `tasks/reference/imps/patch-streams-design.md` (the standard-c-under-personal case + the re-cut
  method), `tasks/reference/imps/derived-artifact-drift.md` (`personal` is keyed to the standard-c
  tip; bump order), `tasks/reference/mario64/assembly-isms-in-the-decomp.md` (what the OoT twin
  added). Filed `proposed`: `tasks/ocarina-standard-c-explained-diffs.md` (18 items),
  `tasks/ocarina-upstream-standard-c.md`, `tasks/ocarina-decomp-bugs-found-by-survey.md`.
  Checkout left on `imps-applied`; branches `imps-standard-c` (the stream) and `imps-personal-old`
  (the pre-re-cut reference tree, keep until the maintainer has reviewed the re-cut). Everything
  staged in imps; nothing committed there.

## Notes / decisions

- Stream name `standard-c` (not the stub's `readability`), FIRST in ORDER (not after `personal`
  as the stub proposed) — the maintainer's ruling 2026-09-22: "we need to do these code changes
  first, before the renaming".
- Carried over from the rename effort, still unresolved and still not blocking: the
  savestate-entangled `D_` symbols with `_copy` fields; the `system_heap.c` C++-runtime thunks.

## Open questions

1. Upstream grouping and trailers: same answers as SM64 (per class; keep the trailers; store here
   for now) — assumed, say if not.
