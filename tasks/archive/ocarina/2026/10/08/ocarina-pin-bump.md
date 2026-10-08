# OcarinaOfTime — pin bump to develop 9.3.0 (the big one)

**Status:** DONE 2026-10-08 — both streams replayed onto the `9.3.0` pin (`ecd889c2`), all gates green,
maintainer built and play-tested on the host ("builds and plays"), archived.
**Priority:** 5 · **Difficulty:** 9 (the largest series in imps; the rename stream had to be re-cut).
**Created:** 2026-10-08 (William Emerison Six <billsix@gmail.com>: "yes, write it as a todo").
**Part of:** `tasks/imps-check-upstreams-and-rebase-patches.md` (the 2026-10-07 upstream sweep).

## BLUF

Bumped `n64/OcarinaOfTime` from `acdbc651d` (9.2.3-421) to Shipwright's develop head
`ecd889c2019b87e78b0a3d942a6a3fe98b7efaed`, which upstream had tagged **9.3.0**. Both patch lanes were
replayed onto it: the 36-patch `standard-c` stream (two 3-way conflicts hand-resolved) and the rename
`personal` stream re-cut on the new standard-c tip, finishing at **525 applied patches** (36 `standard-c`
+ 489 `personal`, the personal stream having grown by one tail patch). All gates passed, the maintainer
built and played it, and the task was archived.

## What was hard (the going-in situation)

- The biggest series in imps, on an upstream (`develop`) that moves fast and has had structural refactors;
  the `personal` stream is a **pure-rename stream keyed to the `standard-c` TIP** (its `base-commit`
  footer), not the pin, so a bump re-cuts it.
- Two invariants beyond "applies" (`tasks/reference/imps/derived-artifact-drift.md`): `standard-c` must stay
  codegen-identical (re-proven with `tools/asmdiff.sh`), and `personal` must be re-cut on the new standard-c
  tip (`tools/resolve_rename_conflicts.py`, verified with `tools/check_renames.py all`).
- The 2026-10-07 sweep probe had applied ~20 `standard-c` patches onto `ecd889c2` before conflicting at
  `z_kaleido_collect.c`, then restored the checkout and left the pin unchanged — so the conflict was known
  going in.

## What was done

1. **`standard-c` replayed onto `ecd889c2`** (tip `e6647b4d`). Three 3-way conflicts resolved by hand,
   each keeping upstream's new wrapper/refactor and re-applying our rewrite: `z_kaleido_collect.c` (the
   probe's conflict), `soh/src/code/audio_playback.c`, and `ovl_Door_Ana/z_door_ana.c`.
2. **`personal` re-cut** on the new standard-c tip with `tools/resolve_rename_conflicts.py` (driven by a
   resume-mode replay; the resolver handled the rename-conflict blocks, and a few "upstream changed a call
   signature next to a renamed symbol" conflicts were resolved by hand). `tools/check_renames.py all` came
   back green (3,778 renames, all traceable/tagged/total), and `tools/remaining_address_names.py` showed
   only the 4 declared-exclusion symbols — i.e. the bump introduced no new unnamed address symbols.
3. **New-at-pin reconciliation (tail patch `personal/0489`).** The 9.3.0 pin added references to renamed
   symbols in call sites the per-definition-file commits could not have seen:
   `SkipCutscene/QuickBossDeaths.cpp` calls `func_800C08AC` (`Play_ReturnToMainCam`) and `func_80064534`
   (`Cutscene_StopManual`); `CutsceneTime.cpp` names `func_80064824` (`CutsceneCmd_Misc`) and `func_80065134`
   (`Cutscene_Command_SetTime`) in comments. All four are oot-adopted names, so no call-site tag. The same
   patch repositioned one `audio_thread.c` provenance comment the 3-way replay had dropped inside a function
   body (it had mis-paired `AudioLoad_GetFontsForSequence`). It was kept as a dedicated tail patch so the 488
   re-cut patches stayed byte-stable for review (the sandbox blocks `rebase -i`, so folding it into the
   defining commits was not possible).
4. **asmdiff stream re-gate, run nested** (full SoH build in `soh-builder`, gcc-11; tree configured at the
   standard-c tip with `CMAKE_EXPORT_COMPILE_COMMANDS=ON`; `asmdiff_tree.sh ecd889c2 <standard-c tip>`).
   Result: **486 files, 478 byte-identical, 8 differ** — `audio_heap.c` (1212 asm lines), `z_message_PAL.c`
   (2878), `audio_synthesis.c` (32), `z_bgcheck.c` (20), `z_en_owl.c` (36), `z_en_torch2.c` (6),
   `z_en_trap.c` (15), `z_en_wood02.c` (4). Each file's *source* diff was exactly the intended cleanup,
   cleanly applied (no reverted upstream code); the codegen differed only because cleanups that were
   byte-identical on the old pin's versions (removing an unused `s32 pad;`, `goto`→`return`, `<<`→`*`,
   `== false`→`!`, `(uintptr_t)`→`(u8*)`, the eventInf macro) now shift the frame on 9.3.0's rewritten
   functions, so GCC re-allocates registers/slots — a behavior-equivalent reschedule. The maintainer's call
   (2026-10-08) was to **accept the 8 in-stream and document them**, relaxing the OoT `standard-c` invariant
   at 9.3.0 to "byte-identical OR a behavior-equivalent diff explained in
   `tasks/ocarina-standard-c-explained-diffs.md`" ("Accepted IN the stream" section, with per-file mechanism,
   asm hunks, and the re-gate command). The nested build recipe this gate needed was harvested into
   `tasks/reference/imps/standard-c-tooling.md`.
5. **Derived artifacts re-verified.** `generate-builds.yml`'s Linux job changed only cosmetically (a
   readme-artifact move) between pins; `linux-build-deps/apt.txt` and the from-source dep versions were
   unchanged, so the `Dockerfile` was accurate (only its pin-SHA comment updated). The libultraship submodule
   was unchanged (`62e973ae`, 1.3.1-486), torch `2ab12fe9`.
6. **Pin + patches + docs updated.** `fetch.sh` `PIN_SHA` → `ecd889c2` with the `9.3.0` describe comment;
   the `personal` stream regenerated (`--base=e6647b4d`, 489 patches); `n64/OcarinaOfTime/CLAUDE.md`,
   `n64/CLAUDE.md`, and the `Dockerfile` refreshed. (The `standard-c` patches had already been regenerated at
   `ecd889c2` in a prior session.)
7. **Gates green.** `tools/check_patches_apply.sh OcarinaOfTime` applied all 525 patches cleanly from the pin
   (stream order + pin guard); `tools/check_renames.py all` passed.
8. **Maintainer built + play-tested** on the host 2026-10-08 ("builds and plays"), then this task was
   archived.

## Open questions

None (resolved 2026-10-08, William Emerison Six <billsix@gmail.com>): the 8 behavior-equivalent codegen
diffs were accepted in-stream and documented (see step 4).

Optional follow-up (not required for a correct bump, not done): re-run `tools/oot_oracle.py` against
zeldaret/oot at 9.3.0 to upgrade `[LLM:HIGH]` guesses to `[oot]`-adopted names where upstream has since
named them — a provenance-comment enhancement that needs network + review.
