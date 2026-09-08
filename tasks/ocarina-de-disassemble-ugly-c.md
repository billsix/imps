# Ocarina: de-disassemble the ugly C in the OoT decomp

**Status:** proposed — needs go-ahead
**Priority:** 7
**Difficulty:** 8
**Started:** 2026-09-08

## BLUF

Goal 3 of the finished decomp-rename effort, split out to stand on its own: where
a body in `soh/src/` reads like mechanically-lifted assembly — `goto` chains, raw
pointer/offset arithmetic, throwaway temps, an `if/else` ladder that is really a
`switch` — rewrite it into idiomatic C **without changing behaviour**. Goals 1
and 2 of the parent (rename the address-named files, name the address-named
symbols) are **done**; this is the remainder, and it is deliberately a different
kind of work with a different risk profile. "Done" is not "every file"; done is
whatever the maintainer calls it, with every change behaviour-verified.

## Context

### Read first

- **[`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)**
  — the governing conventions from the rename effort. **The Guardrails section
  applies here unchanged**, and matters more: a rename is checked by the
  compiler, a rewrite is not.
- **[`tasks/ocarina-decomp-rename-and-cleanup.md`](ocarina-decomp-rename-and-cleanup.md)**
  — the parent task this was split out of, including its per-file survey of
  where the ugly code is.
- **[`tasks/reference/ocarina/decomp-map.md`](reference/ocarina/decomp-map.md)**
  — where OoT subsystems live.

### Why this is separate, and why it is riskier than the renames

The renames had a total oracle: the compiler and linker prove identifier
consistency, so a mistake could not reach a build. **A behaviour-preserving
rewrite has no such oracle.** `gcc -fpreprocessed` comparisons and
`tools/prove_comment_only.sh` — the proofs that carried the rename work — say
nothing about a rewritten loop. The only checks available are the test the
maintainer runs in-game, and reading.

That difference is the whole reason this is its own task. It also sets the
default: **when unsure, leave it.** A file with good names and an ugly body is
already a win (the maintainer's ruling, 2026-07-31: renames matter more than
de-obfuscation).

### Current state

The tree is at pin `acdbc651d4b11e29518442d6875a3ec181414cfc`, with
`n64/OcarinaOfTime/patches/personal/` carrying 488 patches — 3,781 symbol
renames plus 18 file renames. Every address-named symbol outside the declared
exclusions now has a name, so the code is readable enough that the ugly bodies
are actually identifiable, which was not true before.

`n64/OcarinaOfTime/tools/remaining_address_names.py` reports the naming work as
complete (6 rows, 4 distinct names, all excluded by decision).

## Goal

Turn mechanically-lifted assembly into idiomatic C, one small reviewable batch
at a time, changing no behaviour.

## Plan

- [ ] Survey what is actually ugly now that everything has a name — the parent's
      survey predates the renames and is worth re-taking.
- [ ] Agree the aggressiveness (see Open questions 1).
- [ ] Pick the first batch: one file, or a tight cluster, small enough that the
      maintainer's build-and-play verify is worth its cost.
- [ ] Rewrite, keeping each change independently revertible.
- [ ] Verify: container build green, then the maintainer plays the affected area.
- [ ] Regenerate the stream and re-run `tools/check_patches_apply.sh OcarinaOfTime`.

## Notes / decisions

- **A new stream, not the `personal` one.** These are not renames, and the
  `personal` stream is now a coherent 488-patch unit that reviews as one idea.
  Recommend `patches/readability/`, added to `patches/ORDER` after `personal`
  (it must be written against the renamed tree).
- Carried over from the parent, still unresolved: the savestate-entangled `D_`
  symbols with `_copy` fields, and the `system_heap.c` C++-runtime thunks. Both
  were HELD rather than decided; neither blocks starting.

## Open questions

1. **How aggressive?** Light-touch (only the worst disassembly patterns: `goto`
   chains, ladders that are really switches) or a fuller de-disassembly per file?
   Recommend light-touch — it is the safer default for a decomp with no
   behavioural oracle, and it can always be deepened later.
2. **Is this for upstream, or local readability?** The renames were shaped for
   upstream; a readability rewrite is a much harder sell to a decomp project,
   which generally wants to stay close to the original. Recommend treating it as
   local-only, which also relaxes the naming-rigor bar.
