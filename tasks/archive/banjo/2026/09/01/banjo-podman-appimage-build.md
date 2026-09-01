# BanjoKazooie: podman AppImage build like MajorasMask's

**Status:** done — verified 2026-09-01 (nested image/build/appimage in
the sandbox; the maintainer confirmed `make run` works on the host,
closing the "runnable" gate). Archived same day.
**Priority:** 4
**Difficulty:** 4

## BLUF

Give `BanjoKazooie/` a `Dockerfile` + `Makefile` podman build producing an
AppImage, the way `MajorasMask/` has one — derived from Lighthouse's own
CI workflow, **on the same OS version CI uses**. Done when `make appimage`
in `BanjoKazooie/` produces a runnable `out/lighthouse.appimage` from the
patched checkout.

## Context

Read first:

- **The template:** `MajorasMask/Dockerfile` + `MajorasMask/Makefile` (see
  the ocarina sibling task `ocarina-podman-appimage-build.md` — same
  pattern, and whichever lands first informs the other).
- **The CI files to derive from:** `Lighthouse/.github/workflows/linux.yml`
  — its job runs on **ubuntu-latest**, which is a moving target: resolve
  what `ubuntu-latest` meant at the pin date (2026) and pin the Dockerfile
  to that concrete version, recording the resolution in a comment. Check
  `main.yml` too (it may be the release/AppImage workflow while linux.yml
  is only a build check).
- `BanjoKazooie/CLAUDE.md` "Version notes" — two configure-time network
  fetches matter inside a container build: `sse2neon.h` is downloaded from
  an **unpinned master** (unreproducible; consider pre-placing or pinning
  it in the Dockerfile) and `dr_libs` comes via FetchContent (pinned).
  Also `-DUSE_NETWORKING=OFF` exists for SDL2_net-less environments.
- Build gotchas doc: `tasks/reference/banjo/build-system.md`.

## Steps

1. Read `linux.yml` + `main.yml` at the pin: base OS, apt packages,
   from-source libs, AppImage/packaging step.
2. Write `BanjoKazooie/Dockerfile` (FROM the resolved CI ubuntu version) +
   `Makefile` adapted from MajorasMask's (SRC = `Lighthouse/`, image
   context = the checkout).
3. Decide the AppImage step from what CI/upstream provides (Lighthouse
   1.0.0 ships Linux artifacts — mirror however CI packages them).
4. Verify: `make appimage` from the patched checkout; run on the host from
   `runDir/`. Remember the game binary is not installed by
   `cmake --install` — package from the build tree.
5. Update `BanjoKazooie/README.md`/`CLAUDE.md` and the master docs.

## Outcome (2026-09-01)

Implemented on the MM template: `BanjoKazooie/Dockerfile` (ubuntu:24.04
— resolved from CI's `ubuntu-latest` — apt list inlined from
`main.yml`'s build-linux job, SDL 2.30.3 / tinyxml2 10.0.0 /
libzip 1.10.1 from source) + `Makefile` (GeneratePortO2R in-container
instead of CI's separate Torch job). New convention discovered and
applied to MM too: `USERNS_FLAG` drops `--userns=keep-id` under
`NESTED_PODMAN=1` (no subordinate IDs in the sandbox; host behavior
unchanged). Verified nested: `make image` (1.08 GB), `make build`
(patched tree, 17 MB binary), `make appimage`
(`out/lighthouse.appimage`, 12.5 MB). Remaining: run the AppImage on
the maintainer's host.

## Open questions

1. None yet — CI-mirror variant only, like the ocarina task; a modern-OS
   variant can come later.
