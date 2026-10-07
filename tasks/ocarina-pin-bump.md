# OcarinaOfTime — pin bump to current develop HEAD (the big one)

**Status:** proposed — todo (filed 2026-10-08 from the upstream sweep's findings).
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

- [ ] Fetch `ecd889c2`, branch at it, `git am --3way` the `standard-c` stream; **resolve conflicts**
      (starting at `z_kaleido_collect.c`), reading the new upstream for each.
- [ ] Re-run `tools/asmdiff.sh` per `standard-c` patch against the new compile flags; fix any that are no
      longer codegen-identical (a new flag/GCC may require re-doing a rewrite).
- [ ] **Re-cut `personal`** on the new standard-c tip (`tools/resolve_rename_conflicts.py`), then
      `tools/check_renames.py all` green.
- [ ] Re-verify the derived artifacts (above); update any that drifted (esp. build-target renames).
- [ ] Update `PIN_SHA` + pin comment in `fetch.sh`, regenerate both streams
      (`git format-patch --base=<tip> … -o patches/<stream>/`), refresh the per-project `CLAUDE.md`,
      **stage**.
- [ ] `tools/check_patches_apply.sh OcarinaOfTime` green (both lanes, stream order, pin guard).
- [ ] **Maintainer:** build + play-test; then archive.

## Open questions

None — the decision to tackle it is made. This is a large dedicated task; expect it to span a focused
session (standard-c conflicts + asmdiff, then the 488-patch re-cut).
