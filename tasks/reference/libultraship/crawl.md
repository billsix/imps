# The libultraship reference-doc crawl — protocol and iteration log

**What this is:** the standing protocol behind the 8-doc reference set
in this directory, plus the completed iteration log. The original task
(`tasks/archive/libultraship/2026/09/01/libultraship-reference-docs.md`)
ran 18 iterations on 2026-09-01 and is archived; **this doc is what a
future pin bump reopens.**

## The design (William Emerison Six <billsix@gmail.com>, 2026-09-01)

One evolving 8-doc set (`architecture-overview`, `build-system`,
`resource-system`, `fast3d-renderer`, `windowing-gui-input`,
`audio-and-libultra-shims`, `config-cvars-logging`, `bridge-api`),
updated **in place** — git history is the time axis. Each iteration:
checkout the next pin in `n64/libultraship/fetch.sh` (`PIN_SHA` and the doc
banners advance together), delta-read against the previous iteration's
doc state (small deltas verified directly; big ones via 3 parallel
subsystem readers demanding STILL-TRUE/CHANGED/NEW with `file:line`
anchors, every claim re-verified before it enters a doc), rewrite the
docs, tick the log, one path-scoped commit:
`n64/libultraship/fetch.sh tasks/reference/libultraship/ <this doc>`.

## The version topology (hard-won; do not re-derive)

- **13 release tags** 1.0.0 → 1.4.2 (newest tag is 2024-08). Always
  `git tag --sort=v:refname`.
- **The consumer line branches from 1.3.1** and bypasses 1.3.2–1.4.2:
  every game pin describes as `1.3.1-XXX` and is **newer in time than
  every release tag**. Describe-counts do NOT order commits — dates do
  (mm's 397 is later than old-Ghostship's 399).
- **Ghostship's current pin `c151cc91` (1.3.1-544) is a KiritoDv FORK
  branch** (`fix/scripting/v2+bass3l-fixes+postprocessing`): branch
  point `f30fe0ed` (1.3.1-463) + 81 fork commits; mainline 464–486 is
  absent from it (its "Merge branch 'main'" merged the fork's own
  main). Doc state for a fork pin must mark mainline features as
  REVERTED-TO-OLDER, not assume descent.

## Iteration log (all 2026-09-01; each = one imps commit)

1–13: the release-tag line, 1.0.0 → 1.4.2 (cold-authored at 1.0.0 via
4 parallel readers; per-tag deltas after; details in the archived task
and each commit message).
14: `e0c1b1fc` (1.3.1-399, old-Ghostship) — full rewrite onto the
consumer line (o2r default, Ship::/Fast::/LUS:: split, FetchContent,
injection-point Context, ucode tables, Prism archive shaders,
controller rework). Also fixed iteration 13's missed fetch.sh bump.
15: `7f2baa10` (1.3.1-397, MajorasMask) — tiny cousin delta
(+WASAPI mutex #1001, −LoadTextureFromResource tail).
16: `2917d0f4` (1.3.1-482, BanjoKazooie) — 85-commit descendant:
Context GetRawInstance rework, event system, scripting/keystore,
tests, opcode renumber ≥0x44, live custom shaders, Fast3dGui, O2r
handle pool, AudioDmaRegistry, OpenBSD.
17: `62e973ae` (1.3.1-486, OcarinaOfTime) — 4 commits (.meta archive
priority #1168, virtual ~AudioPlayer #1212, SETTIMG in-module #1176,
IsPyramidLike #1239).
18: `c151cc91` (1.3.1-544, Ghostship; FORK) — GPU T&L, Vulkan,
postprocessing/material shaders, mipmapping, async HD textures,
python-free build, portable TCC; mainline 464–486 reverted out.

## Reopening on a pin bump

When a game project bumps its LUS submodule: add the new pin to this
log as the next iteration, `git log --oneline <current-doc-pin>..<new>`
(and the reverse — check for fork topology with `git merge-base`
first), delta-read at the appropriate scale, advance `fetch.sh` +
banners, commit path-scoped. The doc state always describes exactly
one pin: whichever `fetch.sh` names.

## Known cross-check assets

- The maintainer's old fork doc set (authored at 1.3.1-399) lives at
  `/foo/opt/n64/libultraship/tasks/reference/` (machine-local, stale) —
  it was cross-checked during iteration 14 (~95% accurate, ~10 errors
  found and not carried) and is superseded by this set.
