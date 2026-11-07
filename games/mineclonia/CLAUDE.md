# mineclonia — Mineclonia on the Luanti engine, under imps

**Mineclonia** is a Minecraft-like survival sandbox game written in Lua for
**Luanti** (formerly Minetest), the open-source C++ voxel engine. Managed by imps as
a **pinned, reproducible build with no patch series** (decided 2026-11-07, William
Emerison Six <billsix@gmail.com>): the first unpatched project in `games/`. There is
no `apply.sh` and no `patches/`. A code or docs stream would be added as its own
task. All game assets ship in the upstream repo, so, unlike the N64 ports or GZDoom,
there is no game data for the maintainer to supply.

## Upstream + pins

- **Luanti** (engine, built) — https://github.com/luanti-org/luanti, tag **`5.18.0`**
  (`LUANTI_PIN_SHA=e8f12bf1b93245cfc479ea21787beb1ec472cce9`, latest stable,
  resolved 2026-11-07). LGPL-2.1+ code, CC BY-SA 3.0 media.
- **Mineclonia** (game, Lua + assets, not compiled) —
  https://codeberg.org/mineclonia/mineclonia, tag **`0.124.1`**
  (`MINECLONIA_PIN_SHA=7410cf18a231b4dd094bd90dc534951ef17b4275`, resolved
  2026-11-07). GPLv3 code, mostly CC BY-SA media. Its `game.conf` requires Luanti
  ≥ 5.10, and upstream supports **stable** Luanti releases only, so pin a final
  tag, never an `-rc`.

## Scripts

- `./installdependencies.sh` — Luanti's Fedora build deps on the **host** (`dnf`,
  root/`sudo`). Source: the "For Fedora users" list in the pinned tag's
  `doc/compiling/linux.md` (re-check it at each pin bump), plus git and ninja-build.
  The `Dockerfile` installs the same set plus the Xvfb/mesa smoke deps. Keep the two
  in sync.
- `./fetch.sh` — clone both repos into `checkout/{luanti,mineclonia}`, detach each
  at its pin. Idempotent.
- `./build.sh` — CMake/Ninja build of Luanti with **`RUN_IN_PLACE=TRUE`** into
  `bldInstall/<BUILD_TYPE>/`, then installs Mineclonia into its `games/` with
  `git archive` (a copy, without `.git`). RUN_IN_PLACE resolves data relative to the
  binary, so the install is relocatable: a container-built `bldInstall/` also runs on
  the host. `BUILD_ROOT` keeps the CMake caches apart (`build-cmake/` host,
  `build-container/` container), because a CMake cache records absolute paths.
- `./run.sh [luanti args…]` — launch with `--config runDir/luanti.conf
  --gameid mineclonia`. It points `<prefix>/worlds` at `runDir/worlds` with a symlink
  (never replacing a real directory), so worlds survive rebuilds and `make clean`.
  `--world NAME` resolves to `runDir/worlds/NAME`.

## Container (Makefile)

`make image`, `make build` (runs `./build.sh` in the container), `make version`,
`make smoke`, `make run` (X11/Wayland passthrough), `shell`/`shell-exec`,
`image-export`/`image-import`, `clean`/`distclean`. `PODMAN_RUN_FLAGS` is threaded
into every `run`.

- **`make smoke` is the gate:** it starts a dedicated server (`--server --gameid
  mineclonia`) in a throwaway world, waits for "listening on", and fails on any
  `ERROR[` line. Loading the server runs every Mineclonia Lua mod against the built
  engine, which is the compatibility check that matters at a pin bump. No display is
  needed. Verified 2026-11-07: Luanti 5.18.0 + Mineclonia 0.124.1, `SMOKE PASS`.
- Nested gotcha: inside a nested sandbox, `make image`'s `RUN dnf` can die with
  `pasta failed … Couldn't open network namespace`. Run that one build by hand with
  `podman build --network=host -t mineclonia-builder:latest -f Dockerfile .`
  (`~/.claude/reference/nested-run-and-gates.md`). Later `make build` cache-hits it.

## Pin bump

Bump either pin independently (the newest Mineclonia may need a newer Luanti; check
`min_minetest_version` in its `game.conf`), re-check the dependency list against the
new Luanti tag's `doc/compiling/linux.md`, then `make build && make smoke`.
