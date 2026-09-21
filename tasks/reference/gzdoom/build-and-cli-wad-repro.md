# GZDoom carrier — build notes + the CLI-WAD failure reproduction

Durable notes for `games/gzdoom/`: how it builds, and the reproduced evidence
behind the Phase-C CLI-WAD-loading fix (see `tasks/gzdoom-port-and-cli-wad-patch.md`).
Pinned to GZDoom `g4.14.2` (`99aa489d0`) + ZMusic `1.3.0` (`95efd37`); re-verify
against the source if the pin moves.

## Build (what works)

Two build paths share this dependency set: the **native host scripts**
(`installdependencies.sh` → `build.sh`, the primary path) and the **Fedora-44
container** (`games/gzdoom/Dockerfile` + `make build`). Build deps that were
actually needed to configure + compile GZDoom 4.14.2 + ZMusic 1.3.0 (all
installed cleanly, no CMake "not found" iterations after this set):

- toolchain: `gcc-c++ cmake make git ninja-build pkgconf-pkg-config`
- core: `SDL2-devel zlib-devel libjpeg-turbo-devel bzip2-devel`
- audio: `openal-soft-devel fluidsynth-devel` (ZMusic backends)
- video: `libvpx-devel` (GZDoom 4.14 `cmake/FindVPX.cmake`, cutscene playback)
- render: `mesa-libGL-devel vulkan-loader-devel vulkan-headers`
- GTK IWAD picker: `gtk3-devel`
- headless smoke-run: `xorg-x11-server-Xvfb mesa-dri-drivers` (llvmpipe swVulkan/GL)

Order: **ZMusic first**, installed into the shared prefix; then GZDoom, which
finds ZMusic through `CMAKE_PREFIX_PATH=<prefix>` (its `cmake/FindZMusic.cmake`
uses `find_path`/`find_library`, so the installed `<prefix>/{include,lib64}`
resolves — no explicit `-DZMUSIC_*` needed). Both `-DCMAKE_BUILD_TYPE=Release`
by default. GZDoom links llvmpipe software Vulkan fine under Xvfb; a headless
run reaches the game console. `gzdoom --version` prints
`GZDoom g4.14.2 - 2025-01-29 ... SDL version`.

### The `-DSYSTEMINSTALL=ON` requirement (resource-path gotcha)

GZDoom installs its resource `.pk3`s to `<prefix>/share/games/doom/` but the
binary to `<prefix>/bin/`. Built with `SYSTEMINSTALL=OFF` (the default), GZDoom
looks for `gzdoom.pk3` only **next to the binary** (progdir) and in fixed system
paths (`/usr/share/games/doom`, `$HOME/.local/share/games/doom`) — none of which
is an out-of-tree prefix like the carrier's `/work/install/Release`. Result:
`Cannot find gzdoom.pk3`. `src/CMakeLists.txt` gates the fix on the
`SYSTEMINSTALL` option: with it ON it bakes
`-DPROGDIR="${CMAKE_INSTALL_PREFIX}/${INSTALL_PK3_PATH}"` (= `<prefix>/share/games/doom`),
so the installed binary finds its own resources. **Both** build paths pass
`-DSYSTEMINSTALL=ON`: the container Makefile (baking `/work/install/<type>/share/games/doom`)
and the native `build.sh` (baking `<repo>/bldInstall/<type>/share/games/doom`).
Because that path is baked **absolute**, a container-built binary and a
host-built binary are not interchangeable — each finds its `.pk3` only from the
prefix it was built for — which is why the two use separate prefixes (`install/`
vs `bldInstall/`).

## The CLI-WAD failure — reproduced (Phase-C evidence)

Test IWAD: a real DOOM2.WAD (the maintainer's own game data, bind-mounted
read-only; location not recorded). All runs headless under Xvfb +
`SDL_AUDIODRIVER=dummy`, a valid llvmpipe software-Vulkan display present.

There are **two independent failure halves**. The carrier's build fixes the
first; the second is the Phase-C patch target.

### Half 1 (build): resources unfindable — fixed by `-DSYSTEMINSTALL=ON`

Before `SYSTEMINSTALL=ON`, `gzdoom.pk3` (the base resource carrying `IWADINFO`,
the IWAD identification data) was off the search path for the non-standard
`/work/install/Release` prefix, so even `-iwad <valid path>` could not identify
the IWAD:

| invocation (pre-SYSTEMINSTALL binary) | outcome |
|---|---|
| `-iwad /wads/DOOM2.WAD`, **no** display | fatal `Cannot find gzdoom.pk3`, exit 255 |
| `-iwad /wads/DOOM2.WAD`, **with** display | **hangs** (exit 124) — pk3 missing → drops into the GTK picker |
| `-config <ini: FileSearch→share/games/doom> -iwad /wads/DOOM2.WAD` | **loads** ("adding …DOOM2.WAD, 2919 lumps"), reaches console, `+quit` exit 0 |

With `-DSYSTEMINSTALL=ON` (PROGDIR baked to the install's `share/games/doom`) the
plain `-iwad <valid path>` now **loads with no config and no picker** (exit 0,
`GZDOOM_SMOKE_CONSOLE_REACHED`). This is what `make smoke WAD=…` exercises.

### Half 2 (Phase-C target): the GTK IWAD picker blocks whenever `-iwad` is absent

Same working `SYSTEMINSTALL=ON` binary, WAD present but **not** named by an
explicit `-iwad`:

| invocation | outcome |
|---|---|
| no `-iwad`, WAD in a search dir (`~/.config/gzdoom/`) | **hangs** (exit 124) — GTK IWAD picker |
| `-file /wads/DOOM2.WAD` (WAD as PWAD), no `-iwad` | **hangs** (exit 124) — GTK IWAD picker |
| no `-iwad`, WAD in a search dir, **`queryiwad=false`** in config | **loads** (exit 0) — picker skipped, IWAD auto-selected |

The last row is the proof: setting the `queryiwad` cvar false makes the exact
same no-`-iwad` case load cleanly, so the hang IS the picker (`I_PickIWad`, GTK
path on Linux; triggered from `d_iwad.cpp`). This matches the maintainer's report
— passing a WAD via the flags "failed" (picker), and dropping a WAD into a `~/`
dot-folder "worked" because `$HOME/.local/share/games/doom` / `$HOME/.config/gzdoom`
are default IWAD-search dirs (so the picker at least found it — but still asked).

**Phase-C fix direction (not yet written):** a clean CLI path that makes a
CLI-passed WAD play without the picker even when no explicit `-iwad` is given —
e.g. auto-classify a single positional/`-file` WAD as the IWAD, or a flag that
implies `queryiwad=false` and honours the CLI-provided WAD. The code lives in
`src/d_iwad.cpp` (`FIWadManager::IdentifyVersion` / `I_PickIWad`). Carry it as an
`upstream-candidates` stream in `patches/`.

## Reproduce it

```sh
# Native (primary) — on a host, or a bare fedora:44 standing in for one:
cd games/gzdoom && ./installdependencies.sh && ./build.sh && ./run.sh /path/to/DOOM2.WAD
# Container:
cd games/gzdoom && ./fetch.sh && make image && make build
make version                                   # prints the version banner
make smoke WAD=/path/to/DOOM2.WAD              # headless Xvfb CLI-WAD launch
```
