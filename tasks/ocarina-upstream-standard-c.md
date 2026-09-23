# OcarinaOfTime: submit the `standard-c` stream to Ship of Harkinian upstream

**Status:** proposed — needs go-ahead (William Emerison Six <billsix@gmail.com>, 2026-09-22: "I
just want to store them in this repo for now, with eventually looking to upstream them")
**Priority:** 6 · **Difficulty:** 4
**Project key:** ocarina
**Depends on:** `tasks/archive/ocarina/2026/09/23/ocarina-de-disassemble-ugly-c.md` (the stream: 36 codegen-identical patches
at 2026-09-22). Sister: `tasks/mario64-upstream-standard-c.md` (same decisions: per-class PRs,
`Co-Authored-By` trailers kept).

## BLUF

Offer HarbourMasters/Shipwright the 36 assembly-ism rewrites in
`n64/OcarinaOfTime/patches/standard-c/` as small per-class PRs, each quoting its gate result. Done =
each patch merged (then dropped from the stream at the next pin bump) or declined here with the
reason. Not before the maintainer says so.

## Context

- Read first: `n64/OcarinaOfTime/CLAUDE.md` (Patches → `standard-c`), the source task (catalogue +
  progress log), `tasks/reference/mario64/assembly-isms-in-the-decomp.md` ("Upstream posture").
- SoH is further from zeldaret than Ghostship is from sm64: its decomp files carry interleaved
  enhancement code, and its own contributors have already deleted matching hacks in places. The
  strongest openers: the `s32 pad;` sweep (1 710 declarations, pure noise to a port), the 72 empty
  `if (x) {}`, the UB left shifts in En_Wood02, the `(uintptr_t)`→`(u8*)` fix that only compiles
  under `-Wno-int-conversion`.
- Rebase onto current `develop` in a scratch clone and re-run the gate there before opening
  anything; the pin (`acdbc651d`, 2026-09-01) will be stale.
- The `personal` rename stream is NOT part of this; if a `standard-c` patch is merged upstream,
  the next pin bump drops it and re-cuts `personal` on the new base (`derived-artifact-drift.md`).

## Plan

- [ ] Maintainer decides: submit? which classes first?
- [ ] Scratch rebase onto `develop`; re-gate.
- [ ] PRs per class; record numbers/outcomes here; drop merged patches at the next bump.

## Open questions

1. Which class opens the conversation? Recommendation: the `s32 pad;` sweep (largest, least
   arguable) — or the UB shifts if a small first PR is preferred.
