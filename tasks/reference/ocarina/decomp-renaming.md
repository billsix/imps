# Decomp renaming — method, findings, gotchas (reference)

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

Durable knowledge from the address-name→meaningful-name effort on the OoT decomp under `soh/src`.
Read this before doing more renaming. The live work record + progress log is
[`tasks/ocarina-decomp-rename-and-cleanup.md`](../../ocarina-decomp-rename-and-cleanup.md); this doc is the *how* and *why*
that outlives any one batch.

## The single biggest lever: zeldaret/oot is the oracle
SoH's decomp is the **zeldaret/oot** decomp at the **same ROM addresses**, so SoH's `func_800A9F30` **is**
oot's function at `0x800A9F30`. oot has named most of the game. Cross-reference online:
- Raw source: `https://raw.githubusercontent.com/zeldaret/oot/main/<path>` (blob form for citing in comments).
- **Match by body + address order**, not by guessing: oot lists functions in address order within a file, so
  align SoH's `func_<addr>` sequence to oot's named sequence and confirm the body matches.
- Path mapping: actors `src/overlays/actors/ovl_X/z_x.c`; core `src/code/*.c`; **audio moved** to
  `src/audio/game/*.c` (general/sfx/sequence), `src/audio/internal/*.c` (thread/playback). When a path 404s,
  web-search the oot function name.
- **BUT oot leaves a LOT of symbols address-named too.** When it does, an LLM/descriptive name is legitimate —
  just mark it as ours (see provenance convention). Roughly ~2/3 of what we hit had no oot name.

## Provenance-comment convention (the maintainer's request)
Every renamed symbol gets a **greppable** comment directly above its definition, in one of two forms:
- `// LLM generated name (HIGH|GUESS), was <addr>: <reason from the code>` — our deduction (oot has no name).
- `// Name from zeldaret/oot <file> (was <addr>): <reason>. [oot: <url>]` — authoritative upstream name.

Audit with `git grep 'LLM generated name' -- soh/src` / `git grep 'Name from zeldaret/oot' -- soh/src`; both
are trivially strippable before upstreaming. Never let both markers land on one line. When a rename is later
confirmed against oot, upgrade the LLM comment to the oot form (swap marker, append the URL).

## The safe-rename mechanic
A rename must be **total** (def + every reference) and behavior-preserving. Do NOT rely on a build (the maintainer (William Emerison Six <billsix@gmail.com>)
builds/runs separately; our renames are grep-complete, not build-verified).
- Global word-boundary replace scoped to **`soh/src` + `soh/soh` + `soh/include`** (the last is easy to
  forget — see gotcha). `sed 's/\bOLD\b/NEW/g'` on the files `git grep -lwI OLD` returns.
- **Collision check**: skip if `NEW` already exists as a token (tree-wide for externally-linked funcs).
- **Verify 0 residual** old refs after.
- **File renames**: `git mv`; the build globs `src/*` (`soh/CMakeLists.txt`), so no CMake edit — just verify
  nothing references the old filename (usually only stale cross-reference comments).
- **File-local `static` data**: scope the rename (and its collision check) to the ONE defining file. A generic
  static name (`sColChkInfoInit`, `sTentacleTextures`) legitimately exists in dozens of files with internal
  linkage — a tree-wide collision check false-trips, and a tree-wide rename would hit the wrong file.

## Gotchas that have bitten (check every time)
- **`soh/include/` headers.** `functions.h`/`variables.h` carry `func_/D_` prototypes+externs. If the rename
  scope omits `soh/include`, you leave dangling orphan protos (harmless to link, but an incomplete rename).
  Always include it. (48 symbols were left half-renamed this way until swept.)
- **Savestate `_copy` entanglement.** The C++ port layer's `savestates.cpp` snapshots specific `D_` globals
  into `<name>_copy` fields. `\b` word-boundary does NOT match `NAME_copy` (underscore is a word char), so a
  rename silently half-updates. Grep `savestates.cpp` for the symbol first; if entangled, either rename the
  `_copy` field too or skip + log (we skipped `D_801333F0`, `D_801755D0`).
- **`__OTR__` asset-layer names** (display lists, textures declared in `soh/assets/.../*.h` and looked up by
  path string at runtime) can't be renamed without matching OTRExporter/`.o2r` pipeline edits. Leave
  address-named (e.g. the `z_demo_shd` Bongo-shadow DLs).
- **PC-port symbol clashes.** oot names some things after libc (`func_801067F0` = oot `fmodf` in
  `src/libc/fmodf.c`). Adopting that in a *PC port* clashes with the system libc. Keep the SoH-safe name
  (`Math_FMod`) and note the clash. Same class of caution for anything oot names identically to a platform symbol.
- **SoH-vs-oot naming-era differences.** oot has since renamed whole subsystems SoH predates. Keep SoH's
  in-tree convention rather than half-migrating (which clashes with the file's other names):
  `ElfMessage_*` (oot `QuestHint_*`), `TransitionUnk_*` (oot `TransitionTile_*`), `Opening_*` (oot
  `TitleSetup_*`); filenames `audioMgr.c` (oot `audio_thread_manager.c`), `debug_ctrlr2.c` (oot split into
  `sys_freeze.c` + `sys_debug_controller.c`).
- **Adopting an oot name that clashes with an existing SoH name.** e.g. oot's `Message_StartOcarina` needs
  SoH's *existing* `Message_StartOcarina` (= oot `Message_StartOcarinaImpl`) renamed first — a broad change to
  a widely-called symbol. Defer such multi-step realignments to the maintainer rather than doing them unverified.
  Same shape blocked `TransitionUnk_Start`→`TransitionUnk_Update` (the Update name was already taken).
- **Mirrored-name file pairs.** Two files whose functions map onto the same names can't both be non-static in
  C. The rumble pair resolved via oot: high-level `z_rumble.c` owns bare `Rumble_Update/Init/Destroy`;
  low-level `sys_rumble.c` owns `RumbleMgr_Update/Init/Destroy`.

## Cross-TU callers to remember (renames ripple here)
Actor funcs are referenced from SoH's C++ enhancement layer (`soh/soh/**.cpp`): the Anchor multiplayer
`HookHandlers.cpp`, randomizer `hook_handlers.cpp`, `BetterSaveMenu.cpp`, `AudioEditor.cpp`, TimeSavers skip
cutscene files, `z_scene_otr.cpp` (`extern "C"` + `OTRfunc_*` wrappers — leave the wrapper name intact). The
rename scope covering `soh/soh` catches these automatically; always keep it in scope.

## Method for a batch (repeatable)
1. Survey: per-file count of un-named `func_` defs; start with files that have the FEWEST (richest context,
   lowest risk). The "1–2 straggler" tier is done; the remaining **~175 files have 3+ un-named funcs each**.
2. Fan out read-only analysis agents (grouped by file) to propose names from body + callers + oot.
3. Apply centrally with the safe-rename mechanic (keeps consistency + the savestate/scope guards in one place).
4. Annotate with the provenance convention.
5. Log the batch + any held/deferred items + questions in the task doc.
6. Hand to the maintainer to build + run (the only real verification).

## Status at this stopping point (2026-07-31)
Done: **18/19 `code_<addr>.c` files renamed** (only `code_800FBCE0.c`, RCP, left — oot leaves its 2 funcs
address-named too); **~206 symbols renamed**, all cross-checked against oot (65 carry oot citations, 141 are
marked LLM because oot leaves them address-named). This covers the `code_` files + every file that had only
1–2 un-named funcs. **Remaining: ~3,988 un-named `func_` defs across ~175 denser files, plus the entire
de-obfuscation goal (goal 3), plus the open questions in the task doc.** Not archived — this is a live,
multi-session task; resume from the survey in the task doc.
