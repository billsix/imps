# libultraship: per-tag reference documentation crawl

**Status:** proposed — needs go-ahead
**Priority:** 3
**Difficulty:** 8

## BLUF

Produce very detailed, trustworthy reference documentation for
libultraship — the shared engine under all four game ports — by walking
**every release tag oldest→newest**: at each tag, do a full sweep of the
source and create/update the reference docs in
`tasks/reference/libultraship/`, then STOP and tell the maintainer, who
commits that tag's doc state; then advance to the next newer tag and
repeat (maintainer's iterative-checkpoint design, 2026-09-01). This task
is also how the maintainer's old libultraship `bill` branch gets ported:
that branch is docs-only, and this crawl supersedes its doc set.

## Facts established in-session (2026-09-01)

- **Upstream:** `https://github.com/Kenix3/libultraship` (the URL every
  port's `.gitmodules` uses).
- **13 tags** (version-sorted): 1.0.0, 1.0.1, 1.1.0, 1.2.0, 1.2.1, 1.2.2,
  1.3.0, 1.3.1, 1.3.2, 1.3.3, 1.4.0, 1.4.1, 1.4.2. Always list/compare
  with `git tag --sort=v:refname`, never lexically.
- **Tag-line vs consumer-line split:** every game-port pin describes as
  `1.3.1-XXX` — mm `7f2baa10` (397), old-Ghostship `e0c1b1fc` (399),
  ocarina `62e973ae` (486), banjo `2917d0f4` (482) — i.e. the consumers'
  commits descend from **1.3.1**, NOT through the 1.3.2+ tags. The
  1.3.2–1.4.2 tags live on a line the ports don't build. The tag walk
  documents the release line; see open question 1 for the consumer line.
- **The maintainer's study clone** at `/foo/opt/n64/libultraship`
  (machine-local) is **stale** — it lacks ocarina's `62e973ae` pin — and
  its `bill` branch carries: the 8-doc reference set + CLAUDE.md pinned at
  `1.3.1-399` (the old Ghostship pin), plus 3 upstream commits by KiritoDv
  from an unmerged PR (not the maintainer's work; not to port). Work from
  a fresh clone, not this one.

## Structure in imps

- `libultraship/` project dir with a `fetch.sh` per the folder contract —
  no patches, no build scripts (it's a library the ports vendor as a
  submodule; imps documents it). **`PIN_SHA` advances to each tag as the
  crawl proceeds**, so every checkpoint commit records which tag its doc
  state describes.
- Docs at `tasks/reference/libultraship/`, shared by all projects (the
  consumers' own docs should cite these pinned docs rather than embedding
  drifting LUS line numbers — the versioned-dependency convention).

## Method — one iteration per tag

1. `fetch.sh` checkout of the tag (`git -C libultraship checkout <tag>`).
2. **Full sweep.** First iteration (1.0.0) uses the cold-authoring method
   from the global conventions ("Authoring a reference set for a codebase
   you don't know"): fan out one reader per subsystem in parallel,
   `file:line`-anchored structured reports, verify every claim
   independently before it enters a doc (two readers disagreeing = check
   yourself; "grep found nothing" is not proof of absence), distinguish
   live from dead code explicitly.
3. **Every later iteration uses the delta method** ("Reference docs for a
   versioned dependency"): hand each reader the previous tag's doc as
   baseline and demand STILL-TRUE (re-anchored) / CHANGED (old→new) /
   NEW-ABSENT. A version bump can be a structural refactor, not line
   drift — re-verify, don't re-anchor blindly.
4. **Doc set shape:** an `architecture-overview.md` anchor + one doc per
   subsystem, cross-linked. The old `bill`-branch set is a good skeleton
   (architecture-overview, resource-system, fast3d-renderer,
   windowing-gui-input, audio-and-libultra-shims, config-cvars-logging,
   build-system, bridge-api) but the set must follow what actually exists
   at each tag — name docs by what's present at the pinned version, add
   or retire docs as subsystems appear and vanish across versions.
5. **Banner every doc** with the tag + full SHA it describes and a
   one-line re-sync check (compare against `PIN_SHA` in
   `libultraship/fetch.sh`).
6. Update this task's progress log (below), **stage everything, stop, and
   tell the maintainer** — he commits. Only then advance to the next tag.

Around 1.3.1 the old `bill`-branch doc set (at 1.3.1-399) becomes a useful
extra cross-check baseline; it is otherwise retired by this crawl.

## Scale note

13+ full sweeps will span many sessions. Each iteration must be
cold-executable: the progress log says which tag is done and which is
next, and the docs themselves carry their tag banners, so any future
session can resume without this conversation.

## Progress checklist — one checkbox per iteration, in order

Check each off when its sweep is done AND the maintainer has committed
that tag's doc state. Add a one-line note per completed item (date, doc
set changes, anything surprising).

- [x] 1.0.0 — DONE 2026-09-01 (sweep + the maintainer's checkpoint
      commit). Four parallel readers, claims verified; 8-doc set in
      `tasks/reference/libultraship/` (same names as the old
      `bill`-branch set for 1.3.1 comparability). Highlights: D3D12 and
      GLX backends exist but are compiled out (`ENABLE_DX12`/
      `X11_SUPPORTED` never defined); Metal already present; the Wii U
      (`CafeOS`) build cannot compile at this tag (includes a
      nonexistent `menu/ImGuiImpl.h`); `ResourceClearCache` declared
      but never defined; no thread or rumble shims; archives are
      MPQ/StormLib; no version constant exists in code.
- [x] 1.0.1 — DONE 2026-09-01 (delta, 7 commits/12 files; per-tag
      commits authorized for this work session). Two 1.0.0 documented
      defects fixed upstream: the SaveSettings double-increment and the
      Wii U `menu/ImGuiImpl.h` compile-breaker. Also: fullscreen default
      F9→F11 (handler + seed), ZAPDUtils PRIVATE→PUBLIC (closes the
      FileHelper include leak), DisplayList XML gains
      Grayscale/SetGrayscaleColor, `G_BG_COPY` honors horizontal flip,
      DXGI vsync rework. Doc titles made version-less (banner carries
      the pin).
- [x] 1.1.0 — DONE 2026-09-01 (delta, only 2 commits): config
      migrations arrive (`ConfigVersionUpdater` +
      `RunVersionUpdates`/`ConfigVersion` key) and
      `Context::CreateDefaultSettings` bulk seeding is REMOVED (killing
      the documented seeded-keys mismatch); new GBI extension
      `G_EXTRAGEOMETRYMODE` (0x3A) with `G_EX_INVERT_CULLING`.
- [x] 1.2.0 — DONE 2026-09-01 (delta, 12 commits): **GLX and the X11
      dependency deleted** (dead since forever); app-directory model
      reworked (`SHIP_BIN_DIR` removed → `/proc/self/exe`; new
      `NON_PORTABLE` define routes the data dir to
      `SDL_GetPrefPath`; `LocateFileAcrossAppDirs` helper);
      `RomToBigEndian` added to ZAPDUtils BitConverter; better SDL
      frame-pacing timer, display handling, Input Editor joystick
      preview, misc fixes.
- [x] 1.2.1 — DONE 2026-09-01 (delta, 2 commits): SDL fullscreen made
      multi-monitor aware; `Gui::LoadGuiTexture` routes through the
      resource system so GUI icons honor HD/alt texture packs.
- [x] 1.2.2 — DONE 2026-09-01 (delta, 4 commits): Advanced Resolution
      Mode GUI controls; clearMtx hack list 4→6 addresses (PAL GC MQ +
      PAL1.0); reversed romSize check fixed in ZAPDUtils BitConverter.
- [x] 1.3.0 — DONE 2026-09-01 (delta, 9 commits):
      `Context::CreateUninitializedInstance` (games can drive subsystem
      init themselves); Archive version-check refinement (empty
      validHashes skips the check, version tracking decoupled); Color24
      CVar save/load fix; more Advanced Resolution; keyboard-resize,
      Windows frame-pacing, and SDL button-release fixes.
- [x] 1.3.1 — DONE 2026-09-01 (delta, 2 commits: Input Editor overflow
      fix, >100% DPI cropping fix). The planned cross-check against the
      old `bill`-branch doc set is deferred to the consumer-pin
      iterations — that set was authored at 1.3.1-**399**, i.e. deep
      into the consumer line, not at this tag.
- [x] 1.3.2 — DONE 2026-09-01 (one commit: partial revert of the 1.3.0
      keyboard-resize change in the DXGI backend).
- [x] 1.3.3 — DONE 2026-09-01 (one commit: missing switch `break` in
      gfx_dxgi that caused input lag).
- [x] 1.4.0 — DONE 2026-09-01 (4 commits): console gains a
      binding-clear command; Stats window uses ImGui delta time; Switch
      audio reinit after suspend; CI builds all branches.
- [ ] 1.4.1 — delta (2023-12)
- [ ] 1.4.2 — delta (2024-08; newest tag)

Then the consumer line — the games' submodule pins are full iterations
too (decided with the maintainer, 2026-09-01), and they are **newer than
every release tag** (all 2026), so they come last, in commit-date order.
Topology note: they branch from **1.3.1**, bypassing 1.3.2–1.4.2, and are
cousins of each other (none is an ancestor of the next) — so baseline the
FIRST pin's delta on the **1.3.1 checkpoint** (retrieve it from imps git
history; the maintainer commits every iteration), then each later pin on
the previous pin's checkpoint (close cousins, ~90 commits apart at most).
(Ocarina's old fork once pinned `f30fe0ed` / 1.3.1-463 — rolled back, used
by nothing; deliberately not an iteration.)

- [ ] `e0c1b1fc` (1.3.1-399, 2026-02-20) — Ghostship's pin (old fork;
      when the SuperMario64 project lands at its new GitHub-develop pin,
      append that pin's LUS submodule SHA as a further iteration)
- [ ] `7f2baa10` (1.3.1-397, 2026-02-27) — MajorasMask's pin (later date
      despite the smaller describe-count; dates, not counts, order these)
- [ ] `2917d0f4` (1.3.1-482, 2026-07-29) — BanjoKazooie's pin
- [ ] `62e973ae` (1.3.1-486, ~2026-08) — OcarinaOfTime's pin

## Open questions

None. (The consumer-pin question was decided 2026-09-01: the four ports'
submodule pins are full iterations in the checklist, ordered after 1.3.1
and before the 1.3.2+ release tags.)
