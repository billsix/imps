# Add Mineclonia (a Luanti game) to the `games/` family

**Status:** proposed — scope decided 2026-11-07; implementation awaits go-ahead (William Emerison Six <billsix@gmail.com>, 2026-11-07)
**Priority:** 6
**Difficulty:** 5

## BLUF

Add **Mineclonia** (https://codeberg.org/mineclonia/mineclonia), a Minecraft-like survival game
written in Lua for the **Luanti** engine (formerly Minetest, https://github.com/luanti-org/luanti, C++),
as `games/mineclonia/`. Mineclonia itself is pure Lua plus assets and is not compiled. The
buildable part is the Luanti engine, so the project fetches **two** pinned repos side by side, the
way gzdoom fetches gzdoom + ZMusic: `checkout/luanti/` (built) and `checkout/mineclonia/` (installed
into Luanti's `games/` dir). Done = the four host scripts (`fetch.sh`, `installdependencies.sh`,
`build.sh`, `run.sh`) launch Luanti with Mineclonia selected, natively and in the optional
container, plus a headless smoke run, the tier-3 `games/mineclonia/CLAUDE.md`, and a line in
`games/CLAUDE.md`.

## Context

- Read first: `CLAUDE.md` (master: per-project folder contract, native-host-build baseline),
  `games/CLAUDE.md` (family contract: `*_PIN_SHA` per repo, `checkout/<name>/`, Dockerfile/Makefile
  targets), and `games/gzdoom/` as the worked two-repo example. Headless GUI testing:
  `tasks/reference/imps/headless-gui-port-testing.md`.
- Research (2026-11-07, `git ls-remote` + upstream README/`game.conf`):
  - Mineclonia latest tag **`0.124.1`** (README "Version: 0.124.1"). Its `game.conf` declares
    `min_minetest_version = 5.10`, and the README says only **stable** Luanti releases are supported.
  - Luanti latest stable tag **`5.18.0`** (a `5.18.0-rc1` also exists; pin the final tag).
  - Licences: Mineclonia code **GPLv3** (`LICENSE.txt`), media under various CC licences (mostly
    CC BY-SA). Luanti is LGPL-2.1+ (code) / CC BY-SA 3.0 (media). Unlike the N64 ports and GZDoom,
    **all game data ships in the upstream repo**, so there is no "maintainer supplies the data"
    step. (Re-verify both licences at pin time.)
  - Luanti builds with CMake. Typical Fedora deps: `cmake gcc-c++ freetype-devel libpng-devel
    libjpeg-turbo-devel libX11-devel mesa-libGL-devel sqlite-devel libcurl-devel zlib-devel
    gmp-devel jsoncpp-devel luajit-devel openal-soft-devel libvorbis-devel libogg-devel
    zstd-devel SDL2-devel` (Luanti 5.x moved to SDL2). **Verify against the pinned tag's
    `doc/compiling/linux.md`**. Do not trust this list.
  - Luanti's `RUN_IN_PLACE=TRUE` build keeps `games/`, `worlds/`, and config next to the binary,
    which fits imps' "install into a prefix beside the script, run from `runDir/`" contract.

## Plan

1. `fetch.sh`: clone luanti at `5.18.0` and mineclonia at `0.124.1` (full SHAs + tag/date
   comments, `commit.gpgsign false`, idempotent).
2. `installdependencies.sh`: the dnf list, verified against the pinned tag's docs.
3. `build.sh`: CMake build of Luanti (Release, `RUN_IN_PLACE`) into `bldInstall/`, then copy or
   symlink `checkout/mineclonia` → `<install>/games/mineclonia`.
4. `run.sh`: launch with `--gameid mineclonia` (and `--world`) using `runDir/` as the user dir.
5. Optional container `Dockerfile` + `Makefile` per the family contract; a headless smoke
   (`--go`, Xvfb, hard-kill + `ps` audit) like gzdoom's.
6. Docs: `games/mineclonia/CLAUDE.md` + `README.md`, a `games/CLAUDE.md` index line, master
   `CLAUDE.md` family blurb, and a `tasks/reference/mineclonia/` dir only if something non-obvious
   comes up.

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-07)

**A pinned, reproducible build only:** no `patches/`, no `apply.sh`, no documentation stream.
This makes it the first unpatched project in `games/`, so `games/CLAUDE.md`'s index line should
say "pinned build, no patch series". A code or docs stream can be added later as its own task.
