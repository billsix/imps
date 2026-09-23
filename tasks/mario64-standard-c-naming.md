# SuperMario64: name the remaining stack-slot locals (`sp24`, `temp_v0`, `argN`) — the naming tail of `standard-c`

**Status:** proposed — needs go-ahead (scaffolded 2026-09-23 when the first cut was archived, so
the recommendation is not stranded)
**Priority:** 6 · **Difficulty:** 4 (renames are compiler-checked and gate-identical by construction;
the work is reading each function to pick the name)
**Project key:** mario64
**Depends on:** the archived `tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`
(batch 9 did the oracle-backed subset); stream `n64/SuperMario64/patches/standard-c/`.

## BLUF

Rename the ~470 remaining stack-slot / register-named locals in `src/game` and `src/engine` (the
census: `tasks/adhoc/mario64-assembly-isms/data/stack_named_locals.txt`; the reader's per-file
triage: `tasks/adhoc/mario64-assembly-isms/reports/naming-register-unused-filler.md`) to names
derived from their use, one file or function cluster per commit, gated IDENTICAL, appended to the
`standard-c` stream (the personal streams replay on top as in the first cut). Done = `game/` and
`engine/` have no `spNN`/`temp_`/`phi_` locals outside goddard and copt; goddard is CARE (keep its
`// sp24` trailing-comment convention) and copt is LEAVE.

## Context

- Tool: `tools/standard-c/rename_in_function.py <file> <func> old=new …` (whole-word, function-
  scoped, fails loudly); gate: `tools/asmdiff.sh` per file; method and lessons:
  `tasks/reference/imps/standard-c-tooling.md`. Header prototypes move with parameter renames.
- Oracle where one exists: upstream already renamed a twin in the same file (`object_collision.c`,
  `object_helpers.c`, `chuckya.inc.c` — see the report); otherwise name from the body.
- Rules from the first cut: never rename a table-dispatched parameter; `argN` in `audio/` is
  mostly dead code — skip; the `-w`-free build here does warn on shadowing, so keep the build
  warning-clean.

## Plan

- [ ] `engine/` first (47 → done in batch 9? no — `math_util.c` etc. still have `sp` locals),
      then `game/object_helpers.c` (31), then behaviours by hit count.
- [ ] Export, replay (`patches/ORDER` unchanged), `tools/check_patches_apply.sh SuperMario64`.

## Open questions

1. Start with `engine/` as the upstream taste-test (recommended), or with the hottest `game/` file?
