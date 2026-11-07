# Added Mineclonia (a Luanti game) to the `games/` family

**Done 2026-11-07** (authorized batch; William Emerison Six <billsix@gmail.com> set the scope).

`games/mineclonia/` builds the **Luanti** engine (https://github.com/luanti-org/luanti, tag
`5.18.0`, `e8f12bf1b932…`) and installs the **Mineclonia** game
(https://codeberg.org/mineclonia/mineclonia, tag `0.124.1`, `7410cf18a231…`) into it. The project
facts, pins, scripts, and the gotchas below live in `games/mineclonia/CLAUDE.md`. This record
keeps the decisions and how the work was verified.

## Decisions

- **A pinned, reproducible build only** (maintainer, 2026-11-07), chosen over a code patch stream
  or a documentation carrier. So there is no `apply.sh` and no `patches/`, which makes it the first
  unpatched `games/` project. The imps gates already skip such a project:
  `check_patches_apply.sh` skips anything without `apply.sh`, and the comment-only gate only sees
  projects with doc streams.
- **Two repos, like gzdoom + ZMusic:** Mineclonia is Lua + assets, so only Luanti is compiled.
  `build.sh` copies the game into the engine's `games/` with `git archive` (a self-contained
  install, not a symlink into `checkout/`).
- **`RUN_IN_PLACE=TRUE`**: Luanti resolves its data relative to the binary, so `bldInstall/` is
  relocatable. That lets the container `make build` run the same `./build.sh` as the host (one
  build recipe), with a separate `BUILD_ROOT` per environment because CMake caches record
  absolute paths.
- **Player state in `runDir/`:** `run.sh` passes `--config runDir/luanti.conf` and symlinks
  `<prefix>/worlds` → `runDir/worlds`. It replaces only a symlink or nothing, never a real
  directory, which keeps the master "runDir is sacred" contract.
- **Smoke = a headless dedicated server**, not an Xvfb client. Loading a server runs every Lua mod
  against the built engine, which is the compatibility check a pin bump needs, and it needs no
  GL.
- The dependency list is Luanti 5.18.0's own `doc/compiling/linux.md` Fedora list minus
  `kernel-devel`/`automake`, plus `git`/`ninja-build`.

## Verification (2026-11-07, nested podman)

- `./fetch.sh` cloned both pins; a re-run left both at the pinned SHAs (idempotent).
- `make image` failed nested with `pasta failed … Couldn't open network namespace` (the known
  nested `podman build` gotcha); the image was built by hand with `--network=host`, after which
  `make build` cache-hit it.
- `make build` → `Luanti 5.18.0 (Linux)` (`make version`); `make smoke` → `Server for
  gameid="mineclonia" listening`, no `ERROR[` lines, `SMOKE PASS`.
- Not exercised here (needs a display): `./run.sh` / `make run` interactive play. That is a
  maintainer check.
