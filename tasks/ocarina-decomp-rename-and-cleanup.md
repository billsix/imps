# Decomp: name the un-named functions & de-disassemble the ugly C

**Status:** proposed — ongoing/long-running; done in batches (one `code_*` file / cluster at a time).
**Workflow:** Claude edits; **the maintainer builds + runs** (needed to capture runtime logs *and* to verify
behavior is unchanged). Shipwright's build is heavy — batch small so each verify is worth it.
**Priority (William Emerison Six <billsix@gmail.com>, 2026-07-31): renaming files and functions is MORE important than de-obfuscating the
C.** Do the renames thoroughly and completely; treat the readability rewrites (goal 3) as secondary —
only when trivially safe and quick, otherwise skip them. A file/function with a good name and ugly
body is a win; don't hold up a rename batch on a risky readability rewrite.

## STOPPING POINT — resume here (2026-07-31, session end)
Stopped at a clean milestone (the maintainer's call); task stays **open** — the bulk of the renaming remains.
- **Done:** 18/19 `code_<addr>.c` files renamed (only `code_800FBCE0.c` left — RCP, oot leaves it
  address-named too); ~206 symbols renamed and cross-checked against zeldaret/oot (65 oot-cited, 141
  marked LLM because oot leaves them address-named). That's the `code_` files + every file that had only
  1–2 un-named funcs. All grep-complete, **NOT build-verified** — the maintainer's build is the gate.
- **Remaining:** **~3,988 un-named `func_` defs across ~175 denser files** (3+ un-named funcs each) +
  the whole **de-obfuscation goal (goal 3, untouched)** + the open questions below.
- **How to resume:** read **[`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)** first
  (the method, the oot cross-referencing oracle, the gotchas, the naming decisions), then re-run the
  survey (per-file un-named-func count, smallest first) and continue the batch loop.
- **Discretion-flags for the maintainer to eyeball** (in the review-pass log below): `Math_FMod` not renamed to
  oot's `fmodf` (libc clash); `TransitionUnk_Start` left (Update name taken); full `Message_StartOcarina`
  oot alignment deferred (touches a widely-called existing symbol).

## Goal
Three intertwined jobs across the un-reverse-engineered OoT decomp (`soh/src/`):
1. **Rename the address-named FILES.** Once you understand what a `code_<address>.c` file contains
   (from its functions), **rename the file to a meaningful name** (reflecting its subsystem — e.g. a
   file of `CollisionContext`/`bgId` functions → something like `bgcheck_dyna.c`) and **update the
   build system** to match (see the build-system note below).
2. **Name the meaningless functions/data.** Symbols still called `func_800xxxxx`, `D_80xxxxxx` —
   work out what each does, give it a good, meaningful name, and **update every caller/reference**.
3. **De-disassemble the ugly C.** Where a body reads like mechanically-lifted assembly (goto chains,
   raw pointer/offset arithmetic, throwaway temps, an `if/else` ladder that's really a `switch`),
   rewrite it into readable, idiomatic C **without changing behavior**.

## Where the work is (surveyed 2026-07-31)
Scale is large: **~10,781 `func_*` + ~4,546 `D_*`** un-named symbols across `soh/src`. This is a
multi-session effort — treat the survey below as a work-list, not a one-sitting job.
- **Start here (your stated entry point): the 19 `soh/src/code/code_<address>.c` files** — decomp
  segments named by ROM address, full of `func_<address>` functions. Good first targets because
  **their signatures are often already typed** (e.g. `code_800430A0.c:4`
  `func_800430A0(CollisionContext* colCtx, s32 bgId, Actor* actor)`), so many can be named from the
  signature + body + callers alone. Sizes range from ~30 to ~800 lines each.
- **Then the broader `func_/D_` hotspots** elsewhere in `soh/src/` (overlays, `code/`, etc.).

Orientation: `tasks/reference/ocarina/decomp-map.md` (where OoT gameplay systems live) and
`tasks/reference/ocarina/port-layer.md`.

## Method (per function)
1. **Static analysis first.** Read the function + all callers + the globals/struct fields it touches.
   OoT signatures are frequently already typed (`Actor*`, `PlayState*`, `CollisionContext*`, `bgId`),
   so a lot is inferrable from types + what it reads/writes. **Cross-reference known zeldaret/oot
   (and upstream SoH) naming where you're confident** — much of OoT has been named upstream — but
   verify against the actual body; don't blind-copy.
2. **Runtime logging when static analysis is inconclusive.** Add a *temporary* log at function entry
   (name, args, a call counter, caller) gated behind a debug toggle, then **ask the maintainer to run the game
   and exercise the relevant scene/actor** (these `code_` segments are gameplay code — collision,
   actors, etc.). Analyze the captured log (when/how often called, arg values, call sites) to infer
   purpose. *Confirm the exact log call on first use* — pick whatever SoH routes to its console/log
   (spdlog / `osSyncPrintf` shim); note it here once chosen.
3. **Name it** meaningfully (OoT house style: `verb_noun`, subsystem prefixes like `BgCheck_`,
   `Actor_`, `Collision_` matching the context the function operates on).
4. **Rename the definition and EVERY reference atomically.** `git grep` the exact symbol across
   `soh/src` (and headers/prototypes); update all in one change. A half-renamed symbol won't link.
5. **Readability pass** (optional per function, when it's disassembly-shaped): rewrite to idiomatic C,
   behavior-preserving.
6. **Remove the temporary logging** once named.
7. **Hand the batch to the maintainer to build + run** — confirms it links and that behavior is unchanged.

## Guardrails (important — OoT has more name-based indirection than SM64)
- **Behavior-preserving is the hard rule.** Renames must be total; readability rewrites must not
  change behavior. When unsure, leave it. Verify by the maintainer's build + in-game check.
- **Check for externally-fixed references before renaming.** OoT wires functions through tables and
  the DMA/overlay system: gamestate `init/destroy` pointers, actor overlay `ActorInit`/`ActorDB`
  entries, function-pointer tables, and possibly `spec`/dmadata/`.s` references. `git grep` the symbol
  across `.c/.h/.s/.inc/.spec` first; if it's referenced from a table or non-C file, update that too
  (or don't rename). Note: SoH replaced the actor overlay table with `ActorDB` (see
  `tasks/reference/ocarina/decomp-map.md`) — actor funcs are referenced from C there.
- **Temporary logging is scaffolding** — track what you add (here + a code comment) and remove it
  before the batch is done.
- **Batch small and reviewable** — one `code_*` file (or a related cluster) per batch. Shipwright's
  build is slow; make each the maintainer-verify count. Log progress below so a later session resumes cold.
- **This is stock SoH** (`bill` == upstream `develop`) — clean renames here are the kind of thing SoH
  upstream accepts, so keep changes tidy/upstreamable, and don't tangle a rename batch with unrelated
  edits.

## Build-system note (renaming a `code_*.c` file)
Shipwright compiles the decomp via a **`GLOB_RECURSE src/*.{c,h}`** (`soh/CMakeLists.txt:188`, see
`tasks/reference/ocarina/build-system.md`), so a source file has **no explicit entry in CMake** — a
`git mv soh/src/code/code_XXXX.c soh/src/code/<newname>.c` is picked up automatically **on the next
CMake re-configure** (the glob isn't `CONFIGURE_DEPENDS`, so a bare `--build` won't notice; the maintainer
re-runs cmake). "Update the build system appropriately" therefore means: **`git mv` the file, then
verify nothing references the old name** — `git grep code_XXXX` across `.c/.h/.spec/.inc/.txt` and
CMake (a matching header, an `#include`, a dmadata/spec/linker reference, a per-file property). If a
reference exists, update it in the same change. Most `code_*.c` are standalone TUs with no such
references, so it's usually just the `git mv` + a re-configure.

## Suggested order
Start with a **small, gameplay-observable `code_*` file with typed signatures** (e.g.
`code_800430A0.c` — collision-context functions, 105 lines) to establish the static-analysis +
runtime-logging round-trip with the maintainer, then work through the rest of `soh/src/code/code_*.c`, then the
broader hotspots.

## Tooling / method notes
- **Safe rename** = global word-boundary replace across `soh/src` (catches `.c/.h/.inc`) + a
  collision check (skip if the new name already exists) + verify 0 old refs remain. Renames are
  **grep-complete but NOT build-verified** (the maintainer asleep) — the maintainer should do a build pass to confirm.
- File renames are `git mv` (Shipwright globs `soh/src`, so the build picks them up on re-configure).

## Progress log
- **2026-07-31 batch 1 (7 smallest files).** All renames grep-verified complete (0 old refs).
  - HIGH confidence: `func_800C3C20`→`Audio_StopAllSfx` (`game.c` caller; stops sfx banks 0–6),
    `D_8012D200`→`sAllSfxBanks`; `func_801067F0`→`Math_FMod` (float remainder); `func_8006C510`→
    `Math_CubicHermiteSpline` (h00/h10/h01/h11 basis). Files w/ already-named funcs → renamed file
    only: `code_800E6840`→`audio_dcache.c` (Audio_Inval/WritebackDCache), `code_8006C3A0`→
    `flags_env.c` (Flags_*Env), `code_801068B0`→`memmove.c` (oot_memmove), `code_801067F0`→
    `math_fmod.c`.
  - MEDIUM / review: `func_8006C5A8`→`KeyFrame_Interpolate` (used by `z_fcurve_data_skelanime.c`;
    interpolates a TransformData value, step/linear/spline) → file `code_8006C510`→
    `curve_interpolation.c`; `func_800C3C20`'s file → `audio_stop_all_sfx.c`; controller-2 debug
    file `code_800D31A0`→`debug_ctrlr2.c` with `func_800D31A0`→`Debug_Freeze` (prints "Freeze!!",
    hangs — no callers found, possibly unused/ptr-referenced), `func_800D31F0`→
    `Debug_UpdateCtrlr2Valid`, `func_800D3210`→`Debug_ClearCtrlr2Valid` (both called per-frame from
    `graph.c`). — the maintainer: sanity-check these medium ones.

- **2026-07-31 batch 1b — `code_800F7260.c` → `audio_sfx.c`** (OoT SFX subsystem, ~95%
  already named). Grep-complete, 0 residual. HIGH: `func_800F8884`→`Audio_RemoveSoundBankEntriesByPos`,
  `func_800F8F88`→`Audio_UpdateActiveSounds` (sole caller `Audio_Update`); `D_801333D0`→
  `sBgmMutedChannels`, `D_801333F8`→`sSfxSwapTablesInitialized`, `D_80133340`→`sSfxDebugName`,
  `D_80133344`→`sSfxDistOverPrintMsg`. **HELD:** `D_801333F0` (savestate `_copy` entanglement,
  see Q3); `D_80133390`/`D_80133398` ("SEQ H"/"    L" seq-cmd debug labels — trivial, low-value
  names, left as-is).

- **2026-07-31 batch 2 — 8 more `code_*` files, 33 symbols.** All renames global word-boundary
  across `soh/src`+`soh/soh` (C++ port layer callers included, e.g. AudioEditor.cpp), collision-
  checked, 0 residual old refs. **Not build-verified (the maintainer asleep).**
  - **`code_800F9280.c` → `audio_seq.c`** (sequence-command layer). HIGH: `func_800F9474`→
    `Audio_StopSequence`, `func_800FA0B4`→`Audio_GetActiveSeqId`, `func_800FA11C`→
    `Audio_IsSeqCmdNotQueued`, `func_800FA174`→`Audio_ResetSequenceRequests`, `func_800FA3DC`→
    `Audio_UpdateActiveSequences`, `func_800FAEB4`→`Audio_ResetActiveSequencesAndVolume`,
    `Struct_8016E320`→`SeqRequest`, `D_8016E320`→`sSeqRequests`, `D_80133408`→`sStartSeqDisabled`.
    GUESS (review): `func_800FA18C`→`Audio_ClearSequenceSetupCommandsForOp`, `func_800FAD34`→
    `Audio_UpdateResetState`, `D_8013340C`→`sSeqCmdDebugPrintEnabled`, `D_80133410`→
    `sSoundModeList`, `D_80133418`→`sAudioResetState`. (OoT `AudioSeq_*` cross-refs noted by analyzer.)
  - **`code_800EC960.c` → `audio_general.c`** (game-side audio interface, ~80% pre-named; huge).
    Conservative — HIGH only: `func_800F4254`→`Audio_PlaySfxSwordCharge`, `func_800F6C34`→
    `Audio_ResetData` (strong), `func_800F5B58`→`Audio_RestorePrevBgm` (comment-confirmed). **~15
    GUESS SFX-helper names left un-applied** (`func_800F4010/436C/4524/4578/64E0/4C58/…`, various
    `D_8016B7*` scratch) — analyzer recommends pulling authoritative names from a zeldaret/oot
    `audio/general.c` checkout, which this repo lacks (see Q4). Full list in the agent report.
  - **`code_800E4FE0.c` → `audio_thread.c`** (audio-thread manager; modern OoT `AudioThread_`
    prefix, chosen because `Audio_Update` is already taken by general.c). HIGH: `func_800E4FE0`→
    `AudioThread_Update`, `func_800E5000`→`AudioThread_UpdateImpl`, `func_800E5584`→
    `AudioThread_ProcessGlobalCmd`, `func_800E6128`→`AudioThread_ProcessSeqPlayerCmd`,
    `func_800E6300`→`AudioThread_ProcessChannelCmd`, `func_800E5958`→`AudioThread_SetFadeOutTimer`,
    `func_800E59AC`→`AudioThread_SetFadeInTimer`, `func_800E5E20`→
    `AudioThread_GetExternalLoadQueueMsg`, `func_800E5E84`→`AudioThread_GetFontsForSequence`,
    `func_800E5EA4`→`AudioThread_GetSampleBankIdsOfFont`, `func_800E5EDC`→
    `AudioThread_ResetComplete`, `func_800E5F88`→`AudioThread_ResetAudioHeap`, `func_800E6070`→
    `AudioThread_GetChannelIO`. GUESS (review): `func_800E5F34`→`AudioThread_ClearResetQueue`,
    `func_800E60C4`→`AudioThread_GetSeqPlayerIO`, `func_800E66C0`→`AudioThread_CountAndReleaseNotes`,
    `func_800E6680`→`AudioThread_GetActiveNoteCount`, `func_800E66A0`→`AudioThread_ReleaseNonRamNotes`,
    `func_800E6590`→`AudioThread_GetLayerSamplesRemaining`, `D_801304E8`→`sMaxProcessCmdQueueDepth`.
    **HELD:** `func_800E64B0`/`64F8`/`651C` (ops `0xFA`/`0xFD` — no dispatch handler found, apparently
    dead, see Q5); `D_801755D0` (custom audio update hook — cross-file global with a savestate `_copy`
    field, same entanglement class as `D_801333F0`, see Q3). Prefix decision (a vs b) → Q6.
  - **`code_800430A0.c`** (DynaPoly carried-actor transforms) — **functions renamed, FILE name HELD**
    (Q7: these live inside `z_actor.c` upstream — merge back vs new file is a the maintainer call). HIGH
    behavior: `func_800430A0`→`DynaPoly_TransformCarriedActorPos`, `func_800432A0`→
    `DynaPoly_RotateCarriedActor`, `func_80043334`→`DynaPoly_SetStandingActorFlags`, `func_800433A4`→
    `DynaPoly_UpdateCarriedActor` (exact OoT spellings unverified — descriptive names).
  - **`code_800BB0A0.c` → `z_camera_spline.c`** (cutscene-camera cubic B-spline). HIGH:
    `func_800BB0A0`→`CutsceneCamera_CalcSpline`, `func_800BB2B4`→`CutsceneCamera_UpdateSpline`.
  - **File-rename-only (symbols already named):** `code_800FD970.c`→`rand.c`, `code_800FCE80.c`→
    `sys_math_float.c` (float-math lib `Math_F*`; `sys_math_atan.c` was already taken by the ATan2
    table file), `code_800FC620.c`→`system_heap.c` (live entry `SystemHeap_Init`; the C++-runtime
    thunks `func_800FC800..CB34` are upstream-anonymous — left as-is, Q8).
  - Also repointed 3 stale filename cross-reference comments (in `audio_general.c`, `audio_seq.c`,
    `audio_sfx.c`) to the new filenames.

- **4 `code_*` files deliberately HELD (need a the maintainer decision or an oot checkout):**
  `code_800430A0.c` (Q7 file name), `code_800A9F30.c` + `code_800D2E30.c` (**rumble collision** —
  the two files mirror each other's `Rumble_Update`/`Init`/`Destroy` names, which can't both be
  non-static in C; needs zeldaret/oot to assign, Q9), `code_800FBCE0.c` (**RCP status/halt** — new
  `Rcp_` prefix vs fold under `Sched_`/`Fault_`, Q10). Full per-file analyses are in the agent
  reports; nothing applied for these beyond code_800430A0's functions.

- **2026-07-31 batch 3 — "straggler" sweep: ~70 symbols across ~35 files** (files that had only
  1–2 un-named `func_`/`D_` symbols, found via a per-file def-count survey). All renames global
  word-boundary across `soh/src`+`soh/soh`, collision-checked (file-local statics scoped to their one
  file to avoid false trips), 0 residual. **Not build-verified (the maintainer asleep).** Method: OoT actor files
  have rigid `ActorInit` + action-func-table structure, so a lone straggler's role is deducible from
  named context + callers. Analyzers fanned out; applied centrally.
  - **Actor overlays (all file-local, HIGH unless noted):** `ArrowFire/Ice/Light_ApproachTrailPos`
    (3 identical siblings, GUESS), `ObjTimeblock_UpdateAltBehavior` (GUESS), `EnIshi_ApplyDrag`+
    `sRockYOffsets`/`sRockDragValues`, `EnBx_UpdateQuadCollider`+`sQuadVtx*`/`sTentacleTextures` (GUESS),
    `EnStream_CheckPlayerInRange` (comment-confirmed), `EnTk_DrawShovel`, `EnWf_TurnHead`,
    `EnZo_UpdateTalkState` (parallels named `EnTk_UpdateTalkState`), `Opening_DrawDebug` (empty stub),
    `BgHakaZou_SpawnDust`, `BgHidanKowarerukabe_WallBreak` (sibling of named `*_FloorBreak`/`*_LargeWallBreak`),
    `BgSpot17Bakudankabe_SpawnFragments` (**also updated `soh/soh/Network/Anchor/HookHandlers.cpp`** —
    Anchor multiplayer hook), `DoorShutter_DrawJabuDoor`+`sStyleIndexByDoorType`/`sBossDoorInfo`/
    `sBossDoorTextures`, `DemoKankyo_InitRainDrop`+`sRainSpeed`/`sWarpCsFrameThreshold`/`sWarpSparklePos`/
    `sSparklePos` (+6 comment-marked-unused warp/sparkle statics named `s*Unused*`),
    `BgBomGuard_UpdateWallHeight` (GUESS), `BgGjyoBridge_DoNothing`, `BgHakaHuta_Rest`+`sLidRest*`,
    `BgInGate_SwingOpen`, `BgJyaBombchuiwa_GrowLightRay`+`sLightRayPos`/`sLightRayRot`,
    `BgMizuUzu_UpdateWhirlpool`.
  - **Core `code/` files (cross-TU — callers updated tree-wide):** `AudioMgr_NotifyTaskDone`,
    `Audio_NoteStealAndTakeOwnership`, `DynaPolyActor_IsPushPathClear` (4 files: +3 external actor
    callers; GUESS — semantic Q11), `Math_GetControlStickPolar` (HIGH; z_player stores into
    `sControlStickMagnitude`/`Angle`), `PreNMI_Halt`, `Skin_ApplyLimbMatrices`,
    `SkinMatrix_SetRotateFromQuaternion` (unused, applied anyway), the speed-meter audio-thread timing
    trio `gAudioThreadUpdateTimeStart`/`Acc`/`gAudioThreadUpdateTime` (HIGH, cross-TU speed_meter.c/
    audioMgr.c/graph.c), `Interface_Destroy`/`Interface_Init` (HIGH, z_play callers),
    `ElfMessage_CheckConditionsAnd`/`CheckConditionsRandom` (GUESS), `TransitionUnk_Start`/`IsDone` +
    `sTransUnk*DList`, `Message_StartOcarinaAction` (**17 files** — high-fanout public API) /
    `Message_StartOcarinaActionSong` (GUESS pair — `unk_E40E` 0 vs 1; semantic Q11),
    `Object_LoadAll` (**+`BetterSaveMenu.cpp`**) / `Object_LoadEntry` (**+`z_scene_otr.cpp` extern "C"
    decl**; the `OTRfunc_800982FC` wrapper name is intentionally left intact), plus 3 cosmetic
    function-scope statics in z_message_PAL.
  - **Left un-named on purpose (no naming basis / dead + no upstream convention), logged not applied:**
    `func_800FCB70` (padutils — empty, uncalled stub), `func_80001F48`/`func_80001F8C` (z_locale —
    dead region/ctrlr3 predicates, anonymous upstream too), `D_8014B30C`/`D_80153D7C` (z_message_PAL
    file-padding globals). See Q12.

- **2026-07-31 batch 4 — second straggler wave: ~57 symbols across 21 more files** (the remaining
  1–2-unnamed-func actor overlays + game.c/pfschecker.c/z_fishing.c). Same safe-rename method; 0 residual.
  Highlights: BgMjin/BgSpot01Fusya/BgSpot01Idosoko/BgSpot11Bakudankabe, EnBa/EnButte/EnEg/EnFdFire/
  EnFr/EnGanonOrgan/EnGirlA/EnHorse/EnJsjutan/EnRu2/EnYabusameMark/EnZl4/ItemBHeart/ObjMakekinsuta
  actions + their file-local static data; `GameState_UpdateDebugRegisters`/`GameState_DrawEnd` +
  `sGameStateSpeedMeter` (game.c); `PfsChecker_CorruptedInit`/`PfsChecker_Corrupted` (libultra pak-fs
  checker internals — confirmed NOT externally-fixed OS names, so safe; used a `PfsChecker_` prefix
  rather than the bare `corrupted`/`corrupted_init` originals to avoid a token clash); `Fishing_CheckFishBite`
  + 14 fishing rod/reel/lure static timers. Cross-TU renames (EnZl4_*, ItemBHeart_Bob) updated their
  `.h` prototypes and the SoH C++ enhancement files that call them.
  - **HELD (wave 4):** `z_demo_shd`'s 3 display lists `D_809932D0/90/B8` — these are `__OTR__` asset-layer
    names declared in the assets header and looked up at runtime by path string; renaming needs synchronized
    asset-pipeline edits (Q13). And `is_debug.c` `func_80002384` — byte-identical to libc `__assert` but
    SoH already declares `__assert`, so renaming risks a clash; it's dead/uncalled (Q14).

- **2026-07-31 name-provenance annotations (at the request of William Emerison Six <billsix@gmail.com>).** Every symbol I renamed gets an inline
  greppable comment at its DEFINITION recording that the name is machine-generated and WHY it was chosen:
  `// LLM generated name (HIGH|GUESS), was <old_addr>: <reason from the code>`. The literal marker
  **`LLM generated name`** makes them trivial to audit (`git grep 'LLM generated name'`) or strip before
  upstreaming (`sed`). Placed on HIGH and GUESS alike (the maintainer's choice), so the whole rename surface is
  reviewable. Manifest of all 191 renames + def-files lives in the session scratchpad; the annotation
  was applied by a fan-out over the definition files.

- **2026-07-31 oot-sourced resolutions (William Emerison Six <billsix@gmail.com>: look online, cite sources).** With no local oot checkout,
  resolved held/GUESS names from the public **zeldaret/oot** decomp online (same game, same ROM
  addresses). These carry a distinct comment marker **`Name from zeldaret/oot ... Source: <url>`** (not
  the `LLM generated name` tag) because they're authoritative upstream names, not guesses. 18+4 such
  citations added.
  - **Rumble cluster RESOLVED (Q9).** Collision broken by oot: high-level `code_800A9F30.c` → **`z_rumble.c`**
    (owns `Rumble_Update`/`Rumble_Override`/`Rumble_Init`/`Rumble_Destroy`/`Rumble_Controller1HasRumblePak`/
    `Rumble_Reset`/`Rumble_SetUpdateEnabled`, `sRumbleMgr`); low-level `code_800D2E30.c` → **`sys_rumble.c`**
    (owns `RumbleMgr_Update`/`Init`/`Destroy`, `sWasEnabled`). Type `UnkRumbleStruct`→`RumbleMgr`. All
    grep-clean, 0 residual. Source: github.com/zeldaret/oot `src/code/z_rumble.c` + `src/code/sys_rumble.c`.
  - **DynaPoly file RESOLVED (Q7) — my earlier premise was WRONG.** oot does NOT keep these inside
    `z_actor.c`; it has a dedicated standalone **`src/code/z_bg_collect.c`** (126 lines, exactly these 4
    funcs). So `code_800430A0.c` → **`z_bg_collect.c`** (1:1 upstream precedent, no code moved, no build
    edit). Funcs → oot names `DynaPolyActor_UpdateCarriedActorPos`/`UpdateCarriedActorRotY`/
    `TransformCarriedActor`; the 4th (`func_80043334`) oot leaves address-named, so it keeps our
    descriptive `DynaPolyActor_SetStandingActorFlags` (marked LLM, prefix aligned to siblings).
  - **audio_general GUESS pile RESOLVED (Q4) — oot leaves ~28 of them address-named too**, vindicating not
    guessing. Applied only the **5** oot actually names (`Audio_PlayCutsceneEffectsSequence`,
    `Audio_SetMainBgmVolume`, `Audio_SetGanonsTowerBgmVolumeLevel`, `Audio_LowerMainBgmVolume`,
    `Audio_UpdateRiverSoundVolumes`) + corrected `Audio_PlaySfxSwordCharge`→**`Audio_PlaySwordChargeSfx`**
    (oot word order). Everything else in that file stays address-named because oot does too. Source:
    github.com/zeldaret/oot `src/audio/game/general.c`.
  - **RCP file `code_800FBCE0.c` LEFT AS-IS (Q10, the maintainer: use discretion).** `func_800FBCE0`/`func_800FBFD8` are address-named in
    oot as well — no canonical name to pull.

- **2026-07-31 full oot review pass (William Emerison Six <billsix@gmail.com>: check all work vs zeldaret/oot, fix/enrich, use discretion).**
  Fanned 8 agents over all ~206 renamed symbols, each cross-checking against zeldaret/oot online. Result:
  **65 renames now carry `Name from zeldaret/oot ... [oot: <url>]` citations** (was 21) — 16 symbols renamed
  to oot's canonical spelling + 28 comments upgraded (my name already matched oot) + earlier oot-sourced ones.
  The other 141 stay `LLM generated name` because **oot itself leaves those symbols address-named** (verified),
  so my names are honest, behavior-checked guesses with no upstream counterpart. 0 residual, 0 double-markers.
  - **Renamed to oot canonical (examples):** `Math_GetControlStickPolar`→`Lib_GetControlStickData`,
    `Audio_StopAllSfx`→`AudioMgr_StopAllSfx` (+`sSfxBankIds`), `Debug_Freeze`→`Freeze_CurrentThread`,
    `Math_CubicHermiteSpline`→`Curve_CubicHermiteSpline`, `KeyFrame_Interpolate`→`Curve_Interpolate`,
    `sStartSeqDisabled`→`gStartSeqDisabled` + `sSeqCmdDebugPrintEnabled`→`gAudioDebugPrintSeqCmd` (oot
    globals, s→g linkage fix), `sMessageDebugMsgNo`→`sMessageDebuggerTextboxCount`,
    `DoorShutter_DrawJabuDoor`→`DoorShutter_DrawJabuJabuDoor`, `Audio_RemoveSoundBankEntriesByPos`→
    `Audio_RemoveSfxFromBankByPos`, `AudioThread_GetSampleBankIdsOfFont`→`Audio_GetSampleBankIdsOfFont`,
    `gAudioThreadUpdateTime`→`gAudioThreadUpdateTimeTotalPerGfxTask`, `sStyleIndexByDoorType`→`sTypeStyles`,
    `Audio_ClearSequenceSetupCommandsForOp`→`Audio_ReplaceSeqCmdSetupOpVolRestore`.
  - **2 files renamed to match oot:** `z_camera_spline.c`→**`z_cutscene_spline.c`**,
    `curve_interpolation.c`→**`z_fcurve_data.c`**.
  - **Semantic FIX (my name was wrong):** my `Message_StartOcarinaActionSong` implied "a song variant" — the
    flag is actually oot's `disableSunsSong`. Fixed the pair to `Message_StartOcarinaSunsSongDisabled` (oot,
    cited) / `Message_StartOcarinaSunsSongEnabled` (func_8010BD58). Also `sTransUnkTestDList`→
    `sTransUnkBackgroundDL` (oot: it's the background DL, not a "test" list).
  - **DECISIONS / flags for the maintainer (discretion used — you may want to review):**
    1. **`Math_FMod` kept, NOT renamed to oot's `fmodf`** — oot names it `fmodf` (src/libc/fmodf.c), but in a
       PC port that would **clash with the system libc `fmodf`**. Left `Math_FMod`, comment notes the clash.
    2. **`TransitionUnk_Start` (func_800B23E8) left as-is** — oot says this empty stub fills the *Update* slot,
       but SoH already has a `TransitionUnk_Update`, so renaming would collide. Needs you to confirm the
       vtable-slot assignment; I didn't force a colliding rename.
    3. **Full `Message_StartOcarina` oot alignment DEFERRED** — oot's canonical names want SoH's *existing*
       `Message_StartOcarina` renamed to `Message_StartOcarinaImpl` (then func_8010BD58 → `Message_StartOcarina`).
       That touches a widely-called pre-existing symbol; too broad to do unverified while you're away. Recommend
       you run it if you want the exact oot names.
    4. **Kept SoH-convention prefixes where oot renamed whole subsystems** (to avoid churn/clashes, per your
       "minimal / upstream-friendly"): `ElfMessage_*` (oot `QuestHint_*`), `TransitionUnk_*` (oot
       `TransitionTile_*`), `Opening_*` (oot `TitleSetup_*`); and kept the SoH filenames `audioMgr.c`
       (oot `audio_thread_manager.c`) and `debug_ctrlr2.c` (oot split into `sys_freeze.c` +
       `sys_debug_controller.c`). Bodies verified equivalent; only the SoH-vs-oot naming era differs.

## Open questions
1. **How aggressive on the readability rewrites** — light-touch (rename + only the worst disassembly
   patterns) or a fuller de-disassembly per file? Light-touch is safer for a decomp; recommend that
   first.
2. **Upstreaming:** since this is stock SoH, do you want the renames kept clean specifically to submit
   upstream (like the accepted cheat branches), or just local readability? (Affects naming rigor.)
3. **Savestate-entangled `D_` symbols** — `D_801333F0` (3 refs in `savestates.cpp`) and `D_801755D0`
   (the custom audio-update hook; has a `D_801755D0_copy` field in the savestate struct). My
   word-boundary rename does **not** touch the `_copy` suffixed fields, so renaming these would leave
   a half-renamed pair. HELD both. Want me to (a) rename the symbol **and** its `_copy` field together
   (mechanical, I can do it), or (b) leave these at their address names?
4. **[RESOLVED — oot leaves them address-named; applied the 5 oot names]** **`audio_general.c` GUESS SFX-helper pile (~15 symbols).** The analyzer could name them confidently
   only from a zeldaret/oot `src/audio/general.c` checkout, which isn't in this repo. Do you have an
   oot checkout I can point an agent at to lock the exact house names (upgrades ~15 GUESSes to HIGH), or
   should I apply my behavior-derived guesses now?
5. **Dead audio-thread ops `0xFA`/`0xFD`** (`func_800E64B0`/`64F8`/`651C`) — no dispatch handler or
   caller found; apparently dead debug code. Leave at address names (my choice), or do you know they're
   live in some build/config?
6. **`audio_thread.c` prefix consistency** — I named only the `func_*` symbols `AudioThread_*` and left
   the file's pre-existing older `Audio_*` names (e.g. `Audio_QueueCmd`) untouched (less churn). Want me
   to also migrate those existing `Audio_*` names in this file to `AudioThread_*` for a uniform file
   (more churn, cleaner)? Recommend leaving as-is unless upstreaming.
7. **[RESOLVED — oot has standalone `z_bg_collect.c`; renamed to that]** ~~Its 4 DynaPoly funcs live inside z_actor.c~~ (WRONG premise — oot extracted them to `z_bg_collect.c`)
   upstream, not a standalone file. Options: **(a)** give it a new subsystem file name (my lean:
   `z_dyna_poly_actor.c`), or **(b)** merge these 4 functions back into `z_actor.c`. Which? (Functions
   are already renamed either way.)
8. **`system_heap.c` C++-runtime thunks** (`func_800FC800..CB34`, ~7) are anonymous in upstream oot
   too (the "possibly some kind of new()" comments are inherited). Apply speculative C++-semantic names
   (`SystemHeap_New`/`Array_New`/…), or leave `func_*` until runtime confirms? Recommend leaving.
9. **[RESOLVED — z_rumble.c/sys_rumble.c from oot]** **Rumble collision** (`code_800A9F30.c` + `code_800D2E30.c`). Both files' functions map onto the
   same trio `Rumble_Update`/`Rumble_Init`/`Rumble_Destroy` — one file is the high-level retrace-
   callback API (calls `gPadMgr`, installed from `game.c`), the other the low-level `RumbleMgr`-struct
   manager. Two non-static functions can't share a name, and I can't confidently say which file owns the
   bare `Rumble_*` names vs a qualified variant without a zeldaret/oot checkout. HELD both files (names
   and functions). A `git grep` in an oot tree resolves this instantly — do you have one?
10. **[HELD — oot also leaves these address-named]** **`code_800FBCE0.c` (RCP status/halt).** Two functions (`func_800FBCE0` = log RSP/RDP status,
    `func_800FBFD8` = force-halt the RCP, reached only from the scheduler hang-handler + shutdown). No
    prefix exists yet and they're anonymous upstream. Introduce a new `Rcp_` prefix
    (`Rcp_LogStatus`/`Rcp_Halt`), or fold under `Sched_`/`Fault_`? And is `func_800FBFD8` "halt/stop"
    (my read — it never restarts the RCP) rather than "reset"?
11. **A few GUESS names encode a semantic guess I couldn't verify statically** — flag if any read wrong:
    `Message_StartOcarinaAction`/`...Song` (the only difference is `unk_E40E` = 0 vs 1, an undocumented
    "ocarina related" flag; both are thin wrappers on `Message_StartOcarina`), and
    `DynaPolyActor_IsPushPathClear` (two line-tests in front of a pushable dyna actor; callers treat
    `true` as "clear to move"). Both applied (reversible) — happy to rename if you know the real intent.
12. **Genuinely-dead / conventionless symbols left un-named** (see batch-3 log): the two `z_locale`
    predicates, the `padutils` empty stub, and two `z_message_PAL` padding globals. Rename them for
    de-addressing consistency (e.g. `Locale_IsRegionForcedNoCtrlr3`), or leave as `func_/D_`? I left
    them (no caller context / anonymous upstream). Recommend leaving.
13. **`z_demo_shd` display lists** (`D_809932D0`/`D_80993390`/`D_809934B8`, the Bongo-shadow body/hand
    DLs) are `__OTR__` asset-layer names looked up by path string at runtime. Renaming them cleanly needs
    matching edits in the assets header + the OTRExporter/`.o2r` extraction keys. Want me to do the
    synchronized asset-rename (bigger, touches the pipeline), or leave asset symbols address-named?
14. **`is_debug.c` `func_80002384`** is byte-for-byte OoT `__assert` but SoH already declares a libc
    `__assert` (and this copy is uncalled/dead). Rename to `__assert` (risks clashing with the decl),
    give it a distinct name like `Fault_AssertHang`, or leave it? I left it.
