# Reorganize patch streams around upstreamable units

**Status:** done 2026-10-27 (staged; the maintainer committed the work, then squashes). Core work
complete and gated; the Tier-2 doc sweep was split into its own task
(`tasks/imps-tier2-stream-rename-doc-sweep.md`).
**Priority:** 2
**Difficulty:** 5

## BLUF

Every upstream-bound unit of work is now its own `patches/upstreamable-<slug>/` stream — one PR's worth
per folder — so a unit can be worked on, built, and submitted **in isolation on pristine upstream**,
never entangled with personal patches. The established upstream-bound streams were renamed under the
convention (`standard-c` → `upstreamable-standard-c`; OoT's `personal` rename →
`upstreamable-rename-decomp`), the coarse `upstream-candidates/` grab-bag was split into one
`upstreamable-<slug>/` per PR, two tools (`tools/apply_unit.sh`, `tools/check_upstreamable_applies.sh`)
and a per-unit `DEPENDS` mechanism were added, and the invariant was codified: **an upstreamable unit
depends only on pristine upstream and other upstreamable units — never on `personal`/`cheats`/`book`.**
The durable rationale lives in `tasks/reference/imps/patch-streams-design.md`; this doc is the work record.

## Context

The currency of upstreaming is a **unit of work** (one PR), not a patch file — and a unit can be many
patches on purpose (OoT's decomp rename is 490, sliced into bite-sized reviewable commits). Before this
change the streams were too coarse in one place: `upstream-candidates/` was a grab-bag holding several
distinct PRs (e.g. MM's 64-bit audio fix and its CI patch in one folder), and there was no way to apply or
test one unit in isolation — `apply.sh`/`check_patches_apply.sh` always applied the whole personal stack.
The existing `standard-c` stream was already the target shape (one upstreamable unit, its own named folder,
many proven patches); this generalized that shape to every upstream-bound unit.

Related: master `CLAUDE.md` ("Patch philosophy"), `n64/CLAUDE.md` (the stream contract + `ORDER`),
`tasks/reference/imps/patch-streams-design.md` (the durable "why"), and
`tasks/n64-upstreamable-appimage-make-target.md` (the CI-AppImage work whose patch became each port's
`upstreamable-ci-appimage` unit).

## Decisions (maintainer, William Emerison Six <billsix@gmail.com>, 2026-10-27)

1. The `upstreamable-` prefix marks every upstream-bound unit, including renaming `standard-c` to
   `upstreamable-standard-c`, so `ls upstreamable-*` answers "what would I upstream?".
2. Alt 2 — the folder split plus an isolate helper, a gate, and the invariant; the `README.md`s were
   updated too, not just the CLAUDE.md files.
3. OoT's decomp rename is a genuine upstreamable unit — reclassified `personal/` →
   `upstreamable-rename-decomp`, declaring it depends on `upstreamable-standard-c` (low priority to submit,
   but a unit).
4. PR groupings confirmed: Banjo's four JeodC-reviewed patches are one `upstreamable-fixonfedora` unit;
   PaperMario's two extractor patches are one `upstreamable-rom-cli-import` unit ("go, both groupings are
   right").

## The invariant

An `upstreamable-<slug>` unit depends only on **pristine upstream** and **other upstreamable units** —
never on a `personal`/`cheats`/`book` patch (a candidate that needs the cheats to apply is not
upstreamable; that dependency is the bug). Cross-unit prerequisites are declared in
`patches/<slug>/DEPENDS` (one upstreamable stream per line; absent = stands on the bare pin).
`tools/check_upstreamable_applies.sh` enforces it. Full rationale, and the DEPENDS-vs-ORDER split:
`tasks/reference/imps/patch-streams-design.md`.

## What was done

Final stream layout — 12 upstreamable units across the five ports, with `cheats`/`book` unchanged:

| Port | upstreamable units (one PR each) | renamed/split from |
|---|---|---|
| **SuperMario64** | `upstreamable-standard-c` (46) · `upstreamable-ci-appimage` (1) · `upstreamable-fedora-shaderc-deps` (1) | `standard-c`; `upstream-candidates/0001-ci`; `…/0002-…libshaderc` |
| **MajorasMask** | `upstreamable-ci-appimage` (1) · `upstreamable-audio-64bit` (1) | `upstream-candidates/0001-ci`; `…/0002-Fix-silent-SFX…` |
| **BanjoKazooie** | `upstreamable-ci-appimage` (1) · `upstreamable-fixonfedora` (4) | `upstream-candidates/0001-ci`; `…/0002..0005` |
| **OcarinaOfTime** | `upstreamable-standard-c` (36) · `upstreamable-rename-decomp` (490, `DEPENDS` standard-c) · `upstreamable-ci-appimage` (1) | `standard-c`; `personal`; `upstream-candidates/0001-ci` |
| **PaperMario** | `upstreamable-ci-appimage` (1) · `upstreamable-rom-cli-import` (2) | `upstream-candidates/0001-ci`; `…/0002-rompath` + `…/0003-refuse` |

- **Mechanics** (`tasks/adhoc/upstreamable-stream-reorg/reorg.sh`, re-runnable): folders renamed with
  `git mv`; grab-bag patches moved into per-unit folders, each renumbered from `0001` with its
  `[PATCH n/m]` subject fixed to match; the tracked `.keep` files `git rm`'d from the emptied
  `upstream-candidates/` dirs. `patches/ORDER` updated for SuperMario64 and OcarinaOfTime (data lines +
  prose); `upstreamable-rename-decomp/DEPENDS` created.
- **Tools added:** `tools/apply_unit.sh <Project> <slug>` (reset to pin, apply only the unit's DEPENDS
  closure, leave branch `imps-<slug>` to build/PR) and `tools/check_upstreamable_applies.sh` (gate:
  every unit applies in isolation and the invariant holds; `--build` also runs the container AppImage).
- **Docs:** master `CLAUDE.md` (the convention + invariant + tools), `n64/CLAUDE.md` (stream list,
  `ORDER` discussion, projects index), all five per-project `CLAUDE.md` patch lists, all five `apply.sh`
  header comments, the root `README.md` (new "Upstreamable units" section + isolate recipe) and
  PaperMario `README.md`, `tasks/reference/imps/patch-streams-design.md` (durable rationale), and
  `tasks/n64-upstreamable-appimage-make-target.md` (repointed to `upstreamable-ci-appimage`).

## Proofs

- **Applied tree byte-identical** before vs after, all five checkouts — the reorg changed no built code
  (pure rename/renumber of disjoint streams; only the `[PATCH n/m]` commit subjects moved, not tree
  content).
- `tools/check_patches_apply.sh` — all five full series apply cleanly; checkouts left on the full series.
- `tools/check_upstreamable_applies.sh` — all **12 units** apply in isolation on pristine upstream and the
  invariant holds; OoT's `upstreamable-rename-decomp` correctly pulls `upstreamable-standard-c` first
  (526 patches).
- No tool hardcoded a renamed path (`apply.sh`/`check_patches_apply.sh` are stream-generic; `book`/`cheats`
  kept their names).

## Remaining

- **Tier-2 doc sweep** — split out to `tasks/imps-tier2-stream-rename-doc-sweep.md` (proposed): historical
  mario64/ocarina task docs and several reference docs still name streams `standard-c`/`personal`/
  `upstream-candidates`. Non-blocking; a separate pass.
- **Archive this task** after the maintainer's work commit (its own commit, per the three-commit
  lifecycle), harvesting nothing further (the durable rationale is already in `patch-streams-design.md`).
