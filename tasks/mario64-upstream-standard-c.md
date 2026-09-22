# SuperMario64: submit the `standard-c` stream to Ghostship upstream

**Status:** proposed — needs go-ahead (William Emerison Six <billsix@gmail.com> decides the
grouping and whether to submit at all; nothing here is to be started before that)
**Priority:** 5 · **Difficulty:** 4 (the patches exist and are proven; the work is the PR
conversation and re-cutting whatever upstream asks to regroup)
**Project key:** mario64
**Depends on:** `tasks/mario64-assembly-isms-to-standard-c.md` (the stream — its Phase B identical
set is done, 46 patches at 2026-09-22; Phase B.11's explained-diff items are NOT part of this)

## BLUF

Offer Ghostship (https://github.com/HarbourMasters/Ghostship) the 46 codegen-identical
assembly-ism rewrites in `n64/SuperMario64/patches/standard-c/` as small per-class PRs, each
quoting its gate result. Done = every patch either merged upstream (and then dropped from the
stream at the next pin bump, since the pin will contain it) or explicitly declined (recorded here
with the reason, patch kept as a personal carry).

## Context

- Read first: `n64/SuperMario64/CLAUDE.md` (Patches → `standard-c`), the task above (catalogue +
  progress log), and `tasks/reference/mario64/assembly-isms-in-the-decomp.md` ("Upstream
  posture" + "What the first cut found").
- What upstream is: a HarbourMasters PC port that already restructures the decomp (hooks→events,
  a port layer); its clang-format gate covers only `src/port/`, so the decomp files' hand style
  is what the patches match. Upstream's own commits have touched the same files (e.g. the renamed
  twin in `object_collision.c` that batch 9 copied), so "less MIPS, same code" has precedent.
- Every patch's message already carries the rule and the proof sentence ("compiles to
  byte-identical assembly before and after with the port's own flags"); the PR body can quote
  `tools/asmdiff.sh` as the reproduction.
- The pin is `49c5312a` (2026-09-01 `develop`); before submitting, check whether `develop` has
  moved and rebase the stream onto the tip (`git am --3way` on a scratch branch) — a PR against a
  stale base is the first thing a reviewer bounces.

## Plan

- [ ] Maintainer decides: submit? grouping? (open questions below)
- [ ] Rebase the stream onto current `develop` in a scratch clone; re-run the gate there
      (upstream may have changed flags or GCC).
- [ ] Open the PRs in the agreed grouping, uncontroversial first: `register` (3 patches),
      matching residue, `goto`→keyword, UNUSED/filler sweep, then the rest.
- [ ] Record each PR number + outcome here; at the next pin bump drop merged patches from the
      stream (`tools/check_patches_apply.sh SuperMario64` must stay green).

## Notes / decisions

- Not in scope: the explained-diff items (Phase B.11 of the source task) — those change codegen
  and need the maintainer's in-game oracle first; they would be a later, separate submission.
- The dangling-pointer fix (`tasks/mario64-surface-collision-dangling-pointer.md`) is a bug fix,
  not a cleanup — submit it on its own, first, regardless of this task's outcome.

## Open questions

1. One PR per class (e.g. "drop `register`") or per directory? Recommendation: per class, each
   PR = the 1–4 patches of that class, so a maintainer can merge the uncontroversial ones first.
2. Keep the `Co-Authored-By: Claude …` trailers on the upstream-bound commits? (Same question as
   `tasks/papermario-upstream-patches.md`.)
