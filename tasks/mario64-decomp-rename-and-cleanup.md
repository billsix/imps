# Decomp: name the un-named functions & de-disassemble the ugly C

**Status:** proposed — ongoing/long-running; do it in batches (one file or subsystem at a time).
**Not a cheat** — this is decomp cleanup, so it does **not** use the EventSystem/CVar recipe. The
usual Ghostship workflow still applies: Claude edits, **Bill builds + runs** (needed both to capture
runtime logs *and* to verify behavior is unchanged).

## Goal
Two intertwined jobs across the un-reverse-engineered parts of the decomp:
1. **Name the meaningless functions/data.** Symbols still called `func_80xxxxxx`, `D_80xxxxxx`,
   `sub_…` — work out what each does, give it a good, meaningful name, and **update every caller**.
2. **De-disassemble the ugly C.** Where a body reads like mechanically-lifted assembly (goto
   chains, raw pointer/offset arithmetic, throwaway temp vars, an `if/else` ladder that's really a
   `switch`, redundant casts), rewrite it into readable, idiomatic C **without changing behavior**.

## Where the work actually is (surveyed 2026-07-31)
There are **no `code_*` files** (the remembered name doesn't match this tree). The un-named symbols
(~379 `func_*` + ~431 `D_*`) are concentrated here — **confirm with Bill if he had specific files in
mind** (open question 1):
- **`src/goddard/` — the primary target** (the GD / Mario-head intro engine; the most
  disassembly-shaped code): `renderer.c` (155 symbols), `joints.c` (92), `skin.c` (62),
  `shape_helper.c` (62), `objects.c` (62), `particles.c` (38), `debug_utils.c` (21),
  `draw_objects.c` (12), `skin_movement.c` (7). Exercised at runtime on the **title / file-select
  draggable Mario head** → runtime logging works here.
- **`src/audio/`**: `external.c` (92), `port_eu.c` (14), `port_sh.c` (13).
- **Scattered `src/game/`**: `mario_actions_cutscene.c` (25), `area.c` (15), `level_update.c` (8),
  a few `behaviors/*.inc.c`.

Orientation: `tasks/reference/mario64/decomp-map.md` (goddard = the GD dynamic-object engine; its own
display-list interpreter + face skinning).

## Method (per function)
1. **Static analysis first.** Read the function + all its callers + the globals/struct fields it
   touches. Many can be named from reading alone (small helpers; math on obvious fields; a getter/
   setter shape). Where you're confident it matches a known SM64-decomp name, use that — but verify
   against the actual body, don't assume.
2. **Runtime logging when static analysis is inconclusive.** Add a *temporary* log at function entry
   (its name, args, a call counter, maybe the caller) — gate it behind a debug CVar so it's
   toggleable — then **ask Bill to run the game and exercise the relevant scene** (the file-select
   Mario head for goddard; a specific cutscene for `mario_actions_cutscene.c`; audio playback for
   `src/audio/`). Analyze the captured log (when/how often it's called, arg values, call sites) to
   infer purpose. *Confirm the exact log call to use on first run* — pick whatever Ghostship routes
   to its console/stdout (e.g. an spdlog/printf shim); note it here once chosen.
3. **Name it** meaningfully (match decomp/house naming: `verb_noun`, the GD/`gd_` prefix style in
   goddard, field-derived names).
4. **Rename the definition and EVERY reference atomically.** `git grep` the exact symbol; update the
   definition, all callers, any forward decls/headers, in one change. A half-renamed symbol won't
   link.
5. **Readability pass** (optional per function, when it's disassembly-shaped): rewrite to idiomatic C,
   behavior-preserving.
6. **Remove the temporary logging** once named.
7. **Hand the batch to Bill to build + run** — confirms it links, and that behavior is unchanged
   (this is a decomp; a "cleanup" that changes behavior is a bug).

## Guardrails (important)
- **Behavior-preserving is the hard rule.** Renames must be total (def + all refs). Readability
  rewrites must not change what the code does — prefer small, obviously-equivalent transforms;
  when unsure, leave it. Verify by Bill's build + in-game check, not just "it looks right."
- **Check for externally-fixed references before renaming.** If a symbol is referenced by name from
  a data table, a name-based lookup, ASM/`.s`/`.inc`, a linker script, or the GD dynlist/segment
  system, renaming it there too (or not at all) is required — don't rename one side. (Most ASM is
  gone in a port, but goddard/audio have data tables — grep the symbol across `.c/.h/.inc/.s` first.)
- **Temporary logging is scaffolding** — track what you added (here + a code comment) and remove it
  before the batch is done, per the "temporary additions" convention.
- **Batch small and reviewable.** One file (or a cluster of related functions) per batch, so Bill can
  build/verify and the diff is readable. Log progress below so a later session resumes cold.
- Keep each rename/rewrite as its own logical change; don't mix a rename batch with unrelated edits.

## Suggested order
Start where analysis is easiest and runtime-observable: a small goddard file first
(`skin_movement.c` or `debug_utils.c`) to establish the logging mechanism + verify the round-trip
with Bill, then the big ones (`renderer.c`, `joints.c`, `objects.c`), then `src/audio/`, then the
scattered `src/game/` functions.

## Progress log
- (empty — append one line per completed file/batch: what was renamed, any readability rewrites,
  build/run verified by Bill.)

## Open questions
1. **Target scope:** you described "files named like `code_ something`" — none exist in this tree. Is
   the real target the un-named-function hotspots above (goddard / audio / scattered game), or did you
   have a specific set of files in mind? (This sets the batching.)
2. **How aggressive on the readability rewrites** — light touch (rename + only the worst disassembly
   patterns), or a fuller de-disassembly pass per file? The latter is much slower and riskier for
   behavior; recommend light-touch first.
