# OcarinaOfTime: the naming tail of `standard-c` — stack-slot locals, `argN`, per-actor `params` macros

**Status:** proposed — needs go-ahead (scaffolded 2026-09-23 when the first cut was archived)
**Priority:** 6 · **Difficulty:** 6 (three naming jobs; each rename is gate-identical by
construction, but the OoT rename stream sits ON TOP of `standard-c`, so every batch here must be
followed by a re-cut of `personal` — `tasks/reference/imps/recutting-a-stream-under-a-new-base.md`)
**Project key:** ocarina
**Depends on:** the archived `tasks/archive/ocarina/2026/09/23/ocarina-de-disassemble-ugly-c.md`;
`tasks/ocarina-review-recut-rename-patches.md` (the maintainer should accept the first re-cut before
a second one lands on top of it).

## BLUF

Three classes the survey sized but the first cut did not touch, all naming, all gate-identical:
(1) 1 988 stack-slot / `temp_` / `phi_` declarations in 748 functions (~85% nameable; 8 two-meaning
slots need a second variable, 5 loop-carried `phi_` groups are rename-only, 9 dead temps to delete);
(2) 172 `argN` parameter definitions in `code/` (~110 nameable, all tabled with a proposed name in
`tasks/adhoc/ocarina-assembly-isms/reports/naming-register-unused-filler.md`) + the 30 hottest in
overlays; (3) ~1 050 raw `params` masks in 190 actors → per-actor `ENXXX_GET_*(thisx)` macros over
`PARAMS_GET_U/S/NOMASK/NOSHIFT` (the `En_Holl` idiom), shape-to-shape only. Done = whichever
subset the maintainer picks is renamed, gated, exported to `standard-c`, and `personal` re-cut and
re-gated on top.

## Context

- Never rename `include/z64audio.h:706-735` `u8 arg0/1/2` (struct fields in an endianness
  union); rename call chains together (`Skin_*`, `func_800F3F84…`); `functions.h:452` names a
  param `arg4` its definition calls `exchangeItemId` — fix both. `-w` hides `-Wshadow`: compile
  touched files with `-Wshadow` besides the gate.
- `params` macros: map `(p >> s) & M` → `PARAMS_GET_U`, `(p & M) >> s` → `PARAMS_GET_S`
  (sign-extending — never normalise one into the other), `p & M` shifted → `NOSHIFT`; skip the 39
  `(u16)params` variants and every write.
- Tools: `tools/standard-c/rename_in_function.py`, `tools/asmdiff.sh`, then
  `tools/resolve_rename_conflicts.py` + `tools/asmdiff_tree.sh` for the re-cut; the runners from
  the first cut are under `tasks/adhoc/ocarina-assembly-isms/batches/`.

## Plan

- [ ] Maintainer picks the subset and the order (recommend `argN` in `code/` first: smallest,
      fully tabled).
- [ ] Batches on `imps-standard-c`, gate per file, export; re-cut `personal`; all gates; build.

## Open questions

1. Which of the three classes, and is the `params` macro job (190 headers) wanted at all?
