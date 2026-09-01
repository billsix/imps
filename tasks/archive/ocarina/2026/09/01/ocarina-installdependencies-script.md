# OcarinaOfTime: installdependencies.sh — Fedora 44 dnf install script

**Status:** done — verified 2026-09-01: a fresh fedora:44 container ran
installdependencies.sh then a full out-of-tree configure + GenerateSohOtr
+ complete build, all green. The open question resolved as recommended:
the package list is INLINED (works before first fetch), citing
linux-build-deps/dnf.txt + BUILDING.md at the pin; python3 added on top
for the asset extractor. Archived same day.
**Priority:** 3
**Difficulty:** 2

## BLUF

Study Ship of Harkinian's build documentation and add
`OcarinaOfTime/installdependencies.sh`: a Fedora 44 `dnf install` script that
installs everything the build needs, so `installdependencies.sh` →
`build.sh` → `run.sh` works on a fresh Fedora 44 box. Done when a machine
(or container) without the deps can run all three in order successfully.

## Context

Read first:

- `Shipwright/docs/BUILDING.md` (in the pinned checkout) — the Fedora
  section (lines ~117-123) is:
  `dnf install gcc gcc-c++ $(cat linux-build-deps/dnf.txt)` (or `clang`
  instead of the gcc pair).
- `Shipwright/linux-build-deps/dnf.txt` — the upstream-maintained package
  list: git cmake ninja-build lsb_release SDL2-devel SDL2_net-devel
  libpng-devel libzip-devel libzip-tools nlohmann-json-devel tinyxml2-devel
  spdlog-devel opusfile-devel libvorbis-devel. Sibling files: `apt.txt`,
  `pacman.txt`, `zypper.txt`, `flake.nix`, `minimum-gcc-version.txt`,
  `minimum-clang-version.txt`.
- `OcarinaOfTime/build.sh` / `fetch.sh` — the scripts the deps must serve.

Decisions already made:

- Script name/place: `OcarinaOfTime/installdependencies.sh`, following the
  same conventions as the other per-project scripts
  (`cd "$(dirname "$0")"` not needed here — it's a plain dnf run — but
  keep the shebang/`set -e`/comment style).
- Target: Fedora 44, gcc toolchain (matches how the maintainer builds).

## Steps

1. Read `docs/BUILDING.md` fully — check for deps mentioned in prose that
   `dnf.txt` omits (Python for any scripts, boost, etc.), and the minimum
   gcc/cmake versions against what Fedora 44 ships.
2. Write `installdependencies.sh`: `dnf install -y gcc gcc-c++` + the
   `dnf.txt` list. Caveat: read the list from
   `Shipwright/linux-build-deps/dnf.txt` at run time only if the checkout
   is guaranteed present — simpler and more robust is to inline the list
   with a comment citing its source file and the pinned SHA it was copied
   from, since deps may be wanted before the first fetch.
3. Guard `command -v dnf` and fail loudly on a non-dnf host (the
   cross-project "host-agnostic setup" convention).
4. Verify: best done in a fresh `fedora:44` container — run
   `installdependencies.sh`, then `fetch.sh` + `build.sh`, and confirm the
   build completes. (This doubles as the first step toward the planned
   podman build support.)

## Open questions

None — the inline choice was adopted (see Status).
