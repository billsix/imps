# OcarinaOfTime — pin bump to current develop HEAD (the big one)

**Status:** in progress — both streams replayed, all gates green (incl. the asmdiff re-gate, run
nested 2026-10-08), staged; awaiting only the maintainer's build + play-test, then archive.
**Priority:** 5
**Difficulty:** 9 (524 patches across two streams; the 488-patch rename stream must be re-cut — the
maintainer's "most problems" project)
**Created:** 2026-10-08 (William Emerison Six <billsix@gmail.com>: "yes, write it as a todo").
**Part of:** `tasks/imps-check-upstreams-and-rebase-patches.md` (the 2026-10-07 upstream sweep).

## BLUF

Bump `n64/OcarinaOfTime`'s pin from `acdbc651…` to Shipwright's current develop HEAD
`ecd889c2019b87e78b0a3d942a6a3fe98b7efaed`, replaying its **524-patch** series (36 `standard-c` + 488
`personal` rename, applied standard-c-first). The sweep's probe found the **`standard-c` stream conflicts
~20 patches in, at `soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_collect.c`**; and even once standard-c
is clean, the **488-patch `personal` rename stream must be re-cut** on the new standard-c tip. Done = both
streams rebased (standard-c conflict-resolved + codegen-identity re-proven; personal re-cut), derived
artifacts re-verified, pin + patches + docs updated and staged, and the maintainer has built + play-tested.

## Context

- **Why this is hard** (the maintainer flagged it): the biggest series in imps, Shipwright's develop moves
  fast and has had structural refactors (e.g. the earlier ZAPDTR→torch restructure), and the `personal`
  stream is a **pure-rename stream keyed to the `standard-c` TIP** (its `base-commit` footer), not the pin.
- **Two invariants beyond "applies"** (`tasks/reference/imps/derived-artifact-drift.md`):
  1. `standard-c` (36) must stay **codegen-identical** — after rebasing, re-run `tools/asmdiff.sh` per
     patch against the new upstream's own compile flags (a new flag/GCC can turn an identical rewrite into
     a differing one). Method: `tasks/reference/imps/standard-c-tooling.md`.
  2. `personal` (488, renames) must be **re-cut on the new standard-c tip** with
     `tools/resolve_rename_conflicts.py`, then verified with `tools/check_renames.py all`. Method:
     `tasks/reference/imps/recutting-a-stream-under-a-new-base.md`.
- **Order:** bump + stabilize `standard-c` FIRST (it's the base the personal stream sits on), then re-cut
  `personal`.
- **Probe state (2026-10-07):** `git am` of `standard-c` onto `ecd889c2` applied ~20 patches then
  conflicted at `z_kaleido_collect.c` (a file-choose/nameset patch; upstream kaleido changed). Checkout was
  restored to the old applied HEAD (`ffa8e2752`); pin unchanged.
- **Derived artifacts** to re-verify at the bump: `Dockerfile` (Shipwright `generate-builds.yml` Linux job
  + `linux-build-deps/apt.txt`), `installdependencies.sh` (`linux-build-deps/dnf.txt`), `build.sh`/Makefile
  targets (`GenerateSohOtr`, watch for target renames like the ZAPDTR→torch era), `run.sh` OpenGL seed +
  ROM handling.

## Plan

- [x] Fetch `ecd889c2`, branch at it, `git am --3way` the `standard-c` stream; **resolve conflicts**.
      Two 3-way conflicts hand-resolved (`soh/src/code/audio_playback.c`, `ovl_Door_Ana/z_door_ana.c`) —
      each kept upstream's new wrapper/refactor and applied our rewrite; `z_kaleido_collect.c` (the probe's
      ~20-patch conflict) resolved too. standard-c tip = `e6647b4d`.
- [x] **Ran the asmdiff stream gate nested** (full SoH build in `soh-builder`, gcc-11; configured at the
      standard-c tip with `CMAKE_EXPORT_COMPILE_COMMANDS=ON`; `asmdiff_tree.sh ecd889c2 89273b1f`).
      Result: **486 files, 478 identical, 8 DIFFER** — `audio_heap.c` (1212 asm lines), `z_message_PAL.c`
      (2878), `audio_synthesis.c` (32), `z_bgcheck.c` (20), `z_en_owl.c` (36), `z_en_torch2.c` (6),
      `z_en_trap.c` (15), `z_en_wood02.c` (4). **Each file's *source* diff is exactly the intended cleanup,
      cleanly applied — no reverted upstream code.** The codegen differs because the cleanups
      (`s32 pad;` removal, `goto`→`return`, `<<`→`*`, `== false`→`!`, `(uintptr_t)`→`(u8*)`, the eventInf
      macro) were byte-identical on the *old* pin's versions of these functions but not on 9.3.0's: removing
      an unused `pad` shrinks the frame and GCC re-allocates slots/registers across the whole function, a
      behavior-equivalent reschedule (verified: the C expressions are unchanged; e.g. `z_en_wood02` is only
      `movswl`→`movzbl/movzwl`, a narrower load of the same small non-negative value). The build tree
      persists at `Shipwright/build-cmake` (gitignored) for a re-gate after the decision below.
- [x] **Re-cut `personal`** on the new standard-c tip with `tools/resolve_rename_conflicts.py` (driver:
      `scratchpad/oot_recut_resume.sh` — a resume-mode replay; the resolver handled the rename-conflict
      blocks, a few "upstream changed a call signature next to a renamed symbol" conflicts were
      hand-resolved). `tools/check_renames.py all` → **green** (3778 renames, all traceable/tagged/total).
      `tools/remaining_address_names.py` → only the 4 declared-exclusion symbols, i.e. **no new unnamed
      address symbols from the bump**.
- [x] Re-verify derived artifacts: `generate-builds.yml` Linux job changed only cosmetically
      (readme-artifact move) between pins, `linux-build-deps/apt.txt` unchanged, from-source dep versions
      unchanged → `Dockerfile` accurate (only its pin-SHA comment updated). LUS submodule unchanged
      (`62e973ae`, 1.3.1-486), torch `2ab12fe9`.
- [x] Update `PIN_SHA` + comment in `fetch.sh` (`ecd889c2`, git describe `9.3.0`), regenerate the
      `personal` stream (`--base=e6647b4d`, now **489** patches incl. the tail reconciliation 0489), refresh
      `n64/OcarinaOfTime/CLAUDE.md` + `n64/CLAUDE.md` + `Dockerfile`, **staged**. (standard-c patches were
      already regenerated/committed at `ecd889c2` in a prior session.)
- [x] `tools/check_patches_apply.sh OcarinaOfTime` → **green** (525 patches, stream order + pin guard).
- [ ] **Maintainer:** build + play-test (and the asmdiff re-gate above); then archive.

## New-at-pin reconciliation (patch personal/0489)

The 9.3.0 pin added references to symbols the rename series renames, in call sites the per-definition-file
commits could not have seen: `SkipCutscene/QuickBossDeaths.cpp` calls `func_800C08AC`
(`Play_ReturnToMainCam`) + `func_80064534` (`Cutscene_StopManual`); `CutsceneTime.cpp` names `func_80064824`
(`CutsceneCmd_Misc`) + `func_80065134` (`Cutscene_Command_SetTime`) in comments. All four are oot-adopted
names (no call-site tag). Patch 0489 also repositions one `audio_thread.c` provenance comment the 3-way
replay dropped inside a function body (it mis-paired `AudioLoad_GetFontsForSequence`). Kept as a dedicated
tail patch so the 488 re-cut patches stay byte-stable for review; interactive rebase to fold it into the
defining commits was unavailable (sandbox blocks `rebase -i`).

## Open questions

None remaining. (Resolved 2026-10-08, William Emerison Six <billsix@gmail.com>: the 8 behavior-equivalent
codegen diffs are **accepted in-stream and documented** in `tasks/ocarina-standard-c-explained-diffs.md`
— "Accepted IN the stream" section, with per-file mechanism, asm hunks, and the re-gate command. The OoT
`standard-c` invariant at 9.3.0 is now "byte-identical OR a behavior-equivalent diff explained there".)

Optional follow-up (not required for a correct bump): re-run `tools/oot_oracle.py` against
zeldaret/oot at 9.3.0 to upgrade `[LLM:HIGH]` guesses to `[oot]`-adopted names where upstream has since
named them — a provenance-comment enhancement, needs network + review, filed here as a note rather than done.
