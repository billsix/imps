# gzdoom — GZDoom (Doom-engine source port), under imps

**GZDoom** is the widely-used open-source Doom-engine source port (ZDoom family):
it runs the original id games and the huge ecosystem of PWADs/mods, with a modern
renderer (OpenGL/Vulkan) and the ZScript scripting language. Managed by imps as a
**code-patch carrier**: `checkout/gzdoom/` is a pristine clone pinned by
`fetch.sh`, with the maintainer's `patches/` series applied by `apply.sh`. Not a
fork — the patch series is the whole delta.

## Upstream + pins

- **GZDoom** — https://github.com/ZDoom/gzdoom, pinned at tag **`g4.14.2`**
  (`GZDOOM_PIN_SHA=99aa489d09015a95bb78df2b30ede29f328cc874`, resolved 2026-09-20).
- **ZMusic** — https://github.com/ZDoom/ZMusic, pinned at tag **`1.3.0`**
  (`ZMUSIC_PIN_SHA=95efd37ca0832855a9afd8af48c74c389d614ae5`, resolved 2026-09-20).
  GZDoom links ZMusic for music playback; it is **built first** and installed into
  the same prefix so GZDoom's `cmake/FindZMusic.cmake` finds it via
  `CMAKE_PREFIX_PATH`. ZMusic is a build dependency only — **never patched**
  (single lane: `patches/` apply to `checkout/gzdoom/` alone).

## Scripts

The four host-runnable scripts (the imps native-build baseline — see the master
`CLAUDE.md`), plus `apply.sh`:

- `./installdependencies.sh` — install GZDoom's + ZMusic's Fedora build deps on
  the **host** (`dnf`, root/`sudo`; guarded on `dnf`; package list inlined so it
  runs before the first fetch). The same set as the `Dockerfile`, minus the
  container-only Xvfb smoke deps. Keep the two lists in sync.
- `./fetch.sh` — clone GZDoom @ `g4.14.2` and ZMusic @ `1.3.0` into `checkout/`,
  detach each at its pin, init submodules, set `commit.gpgsign false`. Idempotent.
- `./apply.sh` — `git am --3way` the `patches/` streams onto `checkout/gzdoom/`
  (refuses unless HEAD is at the GZDoom pin). Today it applies the `book/`
  stream (the comment-only doc-region markers below).
- `./build.sh` — native CMake/Ninja build (ZMusic then GZDoom) into
  `bldInstall/<BUILD_TYPE>/` beside the script; `-DSYSTEMINSTALL=ON` (finds its
  own `gzdoom.pk3`). Calls `fetch.sh` if the checkout is missing. Release default;
  `BUILD_TYPE=Debug ./build.sh` for debug.
- `./run.sh <base.wad> [args…]` — launch the built `gzdoom` with a CLI WAD
  (`-iwad`), from a gitignored `runDir/` as cwd. Needs a real display + audio.

## Build — native (baseline) and podman (optional)

**Native (the baseline):** `./installdependencies.sh` (once) → `./build.sh` →
`./run.sh <wad>`, all on the host, no container. Installs into
`bldInstall/<BUILD_TYPE>/`, builds under `build-cmake/<BUILD_TYPE>/` — both
gitignored.

**Podman (Fedora-44, optional):** `Dockerfile` + `Makefile` are native imps
files. The image carries the toolchain + GZDoom's Linux build deps; the source is
**bind-mounted** at `/work` (never baked), so host edits/patches propagate without
an image rebuild.

```sh
make image          # build the Fedora-44 builder image
make build          # ZMusic then GZDoom -> install/Release/  (Release default)
make build BUILD_TYPE=Debug   # a debug build, into build/Debug + install/Debug
make version        # print the built gzdoom's version (headless; proves it links)
```

Build layout (all gitignored): native uses `build-cmake/<BUILD_TYPE>/{zmusic,gzdoom}`
+ `bldInstall/<BUILD_TYPE>/`; the container uses `build/<BUILD_TYPE>/{zmusic,gzdoom}`
+ `install/<BUILD_TYPE>/` (each a shared prefix; `bin/gzdoom`, `lib64/libzmusic.so*`,
and GZDoom's bundled `.pk3` resources). The two prefixes are kept separate because
`-DSYSTEMINSTALL=ON` bakes an **absolute** resource path, so a container-built
binary (`/work/...`) will not run on the host, and vice versa.

**Build deps** (Fedora package names, in the `Dockerfile`): `gcc-c++ cmake make
git ninja-build pkgconf-pkg-config`; `SDL2-devel zlib-devel libjpeg-turbo-devel
bzip2-devel`; audio `openal-soft-devel fluidsynth-devel`; video (4.14 cutscenes,
`FindVPX.cmake`) `libvpx-devel`; render `mesa-libGL-devel vulkan-loader-devel
vulkan-headers`; the startup IWAD-picker GUI `gtk3-devel`; headless smoke-run
`xorg-x11-server-Xvfb mesa-dri-drivers` (llvmpipe software GL under Xvfb).

## Run — and the CLI-WAD goal (Phase C, not yet fixed)

The maintainer wants to launch his WADs from the **command line** and skip
GZDoom's Linux **startup GUI** (a GTK IWAD-selection dialog). Two independent
halves were reproduced (full evidence: `tasks/reference/gzdoom/build-and-cli-wad-repro.md`):

- **Resource half — fixed by the build.** The install is built with
  `-DSYSTEMINSTALL=ON` so the binary finds its own `gzdoom.pk3`; an explicit
  `-iwad <valid path>` now loads with no config and **no picker** (this is what
  `make smoke` and `make run` do).
- **Picker half — the Phase-C target, NOT yet fixed.** Whenever no explicit
  `-iwad` is given (a WAD sitting in a search dir, or passed via `-file`), the
  **GTK IWAD picker** pops and blocks. Proven by `queryiwad=false` making the same
  case load. A `patches/` change (an `upstream-candidates` stream) is planned to
  make a CLI-passed WAD just play with no GUI — the picker lives in
  `src/d_iwad.cpp` (`I_PickIWad`).

```sh
# Real display (maintainer's normal use): X11/Wayland passthrough + audio.
make run WAD=/path/to/DOOM2.WAD [ARGS='-file some_pwad.wad']
# Headless (no display) reproduction/verification under Xvfb:
make smoke WAD=/path/to/DOOM2.WAD [ARGS=...] [TIMEOUT=25]
```

`run`/`smoke` mount the WAD read-only at `/wads/<name>` and pass it via `-iwad`;
`LD_LIBRARY_PATH` is set to the install's lib dir so `libzmusic.so.1` resolves.
WADs are the maintainer's own game data — **never committed**, location never
recorded here.

## Patches

- `patches/book/` — the **comment-only** `// doc-region-begin/end <name>`
  marker stream, so the Sphinx book (`book/`, below) `literalinclude`s source
  spans by NAME, not line numbers. Adding a marker must never change the program
  — **proven comment-only** by `tools/prove_comment_only.sh --allow-line-shift
  checkout/gzdoom <pin> HEAD` (every touched file identical once gcc strips
  comments). `patches/LANG` = `c` (GZDoom is C++, but its `//` + `/* */` comment
  syntax is identical to C, so the shared C prover — which globs `*.cpp` —
  handles it; the dispatcher only knows c/rust/kotlin, so `cpp` is not a valid
  value). Two patches, one per book stage:
  - `0001-book-...Sphinx-teaching-book` — the first two chapters. Six regions:
    `doom_loop`, `startup_to_loop`, `game_main_entry` (`src/d_main.cpp`);
    `scan_iwad`, `iwad_picker_decision` (`src/d_iwad.cpp`); `init_multiple_files`
    (`src/common/filesystem/source/filesystem.cpp`).
  - `0002-book-...OpenGL-renderer` — the OpenGL-renderer chapter. Nine regions
    across five files: `renderstate_draw_api`
    (`src/common/rendering/hwrenderer/data/hw_renderstate.h`);
    `render_one_viewpoint` (`src/rendering/hwrenderer/hw_entrypoint.cpp`);
    `process_scene`, `draw_scene`, `create_scene`, `render_scene`
    (`src/rendering/hwrenderer/scene/hw_drawinfo.cpp`); `gl_apply`, `gl_draw`
    (`src/common/rendering/gl/gl_renderstate.cpp`); `gl_frame_update`
    (`src/common/rendering/gl/gl_framebuffer.cpp`).
  > Caveat: the shared `tools/check_comment_only_streams.sh` cannot yet
  > *discover* this project — its shapes expect a direct-child checkout, a
  > `checkout/.git`, or a `repos` manifest, none of which match the `games/`
  > family's `checkout/<name>/` layout — so it currently skips gzdoom. Prove
  > with `prove_comment_only.sh` directly until the gate learns a games-family
  > shape.
- The Phase-C CLI-WAD-loading fix will be a later stream
  (`patches/upstream-candidates/`), shaped for upstream submission
  (nice-to-have, maintained here regardless). `patches/ORDER` lists `book`
  (streams commute — disjoint files — so the order is not load-bearing today).

## The book (student-facing docs)

`book/` is the Sphinx teaching book *How a Doom Engine Works* (HTML/EPUB/PDF via
its own Dockerfile+Makefile), reading this source to show how a game engine
starts up, finds its data, and runs. The **beginning** ships three chapters —
*From launch to the main loop* (`src/d_main.cpp`), *IWADs, PWADs, and the lump
filesystem* (`src/d_iwad.cpp` + the filesystem), and *The OpenGL renderer* (one
3D frame from the shared HW renderer down to `glDrawArrays`) — each
`literalinclude`ing the checkout by doc-region marker (the `patches/book/`
stream above; the book does not build against a bare checkout — `apply.sh`
first). Its `Makefile`
mounts the parent `games/gzdoom/` at `/work` so `../../checkout/gzdoom/src/...`
resolves. Build: `cd book && make html`. Details: `book/README.md`.

## Reference docs / task

Deep dives go in `tasks/reference/gzdoom/` (the IWAD/PWAD model, the startup
picker `d_iwad.cpp`, the CLI flags, the build/dependency graph). Port + patch
plan: `tasks/gzdoom-port-and-cli-wad-patch.md`.
