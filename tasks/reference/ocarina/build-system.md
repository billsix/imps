# Reference: The build system

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.
> **Largely stale at the current pin:** this doc describes the ZAPDTR/OTRExporter asset
> pipeline, which upstream has replaced with the `torch` submodule (`soh-torch` extractor +
> `soh-o2r-packer`). Treat as historical until re-verified.

*Standing reference. How SoH is configured, compiled, and how assets get extracted. Read before
changing CMake or adding a dependency. Companions: [asset-pipeline.md](asset-pipeline.md),
[architecture-overview.md](architecture-overview.md). Human-facing steps: `docs/BUILDING.md`.*

Project version **9.2.3** ("Ackbar Golf"). CMake-driven; the tree uses **`.o2r`** archives (the
task/older-docs "OTR" naming is a generation behind — see [asset-pipeline.md](asset-pipeline.md)).

## The executable

- **Target `soh`** (`soh/CMakeLists.txt:231`, `add_executable(${PROJECT_NAME} ${ALL_FILES})`). Output
  per platform: `soh.elf` (Linux), `soh-macos`→`soh` (macOS), `soh.nro` (Switch), `soh.rpx`/`.wuhb`
  (Wii U).
- **Sources** (`ALL_FILES`, `soh/CMakeLists.txt:220-226`) are three globs:
  - `soh__` — the **port layer** `GLOB_RECURSE soh/*.{c,cpp,h,hpp}` (`:135`) = `soh/soh/`.
  - `src__` — the **decomp** `GLOB_RECURSE src/*.{c,h}` (`:188`), with N64-only subtrees **filtered
    out** (`src/dmadata/`, `src/elf_message/`, **`src/libultra/{io,libc,os,rmon}/`**, several `gu/`
    files replaced by port versions) — `:192-207`. (Reading `src/libultra/io/contreaddata.c` to trace
    input is reading excluded dead code — the live impls are LUS.)
  - `soh__Extractor` — `soh/Extractor/*`.
- **Standards**: C++20 / C23 (root `CMakeLists.txt:4-5`); ZAPD/OTRExporter use C11.
- **Strict IEEE-754 to match N64 MIPS**: `-fno-fast-math -ffp-contract=off` (GNU/Clang) / `/fp:precise`
  (MSVC) — the R4300/RSP have no FMA (root `:141-147`). `SUPPRESS_WARNINGS=ON` → `-w` on the decomp
  (`:17-27`). Default `CMAKE_BUILD_TYPE=Debug` (`:149`).
- **`build.c`/`properties.h`** are `configure_file`-generated into the source tree (stamp git
  branch/commit/tag/version) — they show as untracked after configuring.

## Submodules & dependencies

Three git submodules (`.gitmodules`):
- **libultraship** — `github.com/kenix3/libultraship`, branch `port-maintenance`, **pinned `f30fe0ed`
  = `1.3.1-463`**. `add_subdirectory` at root `:197`; SoH **forces** `GFX_DEBUG_DISASSEMBLER ON`
  (`:180`), `GBI_UCODE F3DEX_GBI_2` (`:183`), `INCLUDE_MPQ_SUPPORT ON` (`:187`) before adding it.
- **ZAPDTR** — `github.com/harbourmasters/ZAPDTR`: `ZAPDLib` (linked into `soh`) + `ZAPD` (the exe
  extractor). Vendors `tinyxml2` + `libgfxd`.
- **OTRExporter** — `github.com/harbourmasters/OTRExporter`: per-asset exporters + the Python
  extraction driver (`extract_assets.py`, `rom_info.py`).

**libultraship transitive deps** (`libultraship/cmake/dependencies/common.cmake`): ImGui
`v1.91.9b-docking`, StormLib `v9.25` (only under `INCLUDE_MPQ_SUPPORT`, which SoH forces ON), stb,
libgfxd, thread-pool `v4.1.0`, prism, monocypher, tinycc (only `ENABLE_SCRIPTING`, OFF). Via
`find_package`/vcpkg: SDL2, libzip, nlohmann_json, tinyxml2, spdlog, OpenGL. **SoH also** needs
SDL2_net, Ogg/Vorbis/Opus/OpusFile, and fetches dr_libs (custom audio).

## The asset pipeline — manual, not part of the default build

Three `add_custom_target`s (root `CMakeLists.txt:220-262`), **none `ALL`, and `soh` depends on none
of them** → **asset extraction is manual**: a plain `cmake --build` produces the exe but no playable
game (it needs `soh.o2r` always + `oot.o2r` from your ROM at runtime).
- **`ExtractAssets`** (`:223`) — full extraction from a ROM (`extract_assets.py … --port-ver`).
- **`GenerateSohOtr`** (`:249`) — ROM-less; builds only `soh.o2r` (CI/docs path).
- **`ExtractAssetHeaders`** (`:240`) — regenerate asset C headers.
- `copy-existing-otrs.cmake` distributes the produced `.o2r` to source/build dirs. `rom_info.py` maps
  ROM CRC → the `soh/assets/xml/<version>/` set. Full detail: [asset-pipeline.md](asset-pipeline.md).

## Cross-platform

Dispatch on `CMAKE_SYSTEM_NAME`: **Windows** (MSVC + vcpkg-static, DX11/OpenGL), **Linux** (`soh.elf`,
SDL2/OpenGL/GLES, AppImage), **Darwin** (`OBJCXX`+ARC, Bundle, `x86_64;arm64` fat in CI),
**NintendoSwitch** (devkitA64, `-O3`, `soh.nro`), **CafeOS/Wii U** (devkitPPC, `.rpx`/`.wuhb`).
- Windows vcpkg ports (root `:95-105`): `zlib bzip2 libzip libpng sdl2 sdl2-net glew glfw3
  nlohmann-json tinyxml2 spdlog libogg libvorbis opus opusfile`, triplet `x64-windows-static`.
- Packaging (root `:314-323`): `External`→AppImage (Linux), `ZIP` (Windows/Switch/Wii U), `Bundle`
  (macOS).
- **`Dockerfile`** — an Ubuntu 20.04 **build environment** (gcc-10; SDL2/SDL2_net from source; +
  devkitPro `switch-dev wiiu-dev` so one image cross-compiles Linux/Switch/Wii U). No build step or
  ENTRYPOINT — mount the repo and run cmake yourself.
- `linux-build-deps/` holds per-distro package lists (`apt.txt` is the CI-verified one).

## Feature flags & versioning

- `SUPPRESS_WARNINGS` ON, `USE_ASAN` OFF. LUS options as forced above; LUS defaults `NON_PORTABLE`/
  `ENABLE_SCRIPTING`/`LUS_BUILD_TESTS` OFF.
- **CVar name prefixes** injected as compile-defs from `CMake/soh-cvars.cmake` (`gEnhancements`,
  `gCheats`, `gRandoSettings`, `gRemote`, …) + `CMake/lus-cvars.cmake`.
- **`docs/VERSIONING.md`**: `x.y.z` + codename. **`x`** = update **requiring a new `oot.o2r`** (bumps
  invalidate users' extracted assets); `y` = features not needing a new `oot.o2r`; `z` = bugfixes.
  Codename = sci-fi character (x/y) + NATO phonetic word (z; 9.2.**3** = "Golf"). `--port-ver` bakes
  the version into every `.o2r` for gating.

## Newcomer trip-hazards

- **Assets are a separate manual step** — nothing depends on `ExtractAssets`/`GenerateSohOtr`; run the
  target explicitly (BUILDING.md: `--target GenerateSohOtr` then build).
- **`.o2r`, not `.otr`**; **you supply the ROM** (identified by CRC; unlisted revision won't extract).
- **Default build is Debug and warnings are hidden** (`SUPPRESS_WARNINGS=ON`) — pass
  `-DSUPPRESS_WARNINGS=0` / `-DCMAKE_BUILD_TYPE=Release`.
- **`GLOB_RECURSE` sources** — adding a `.c/.cpp` needs a CMake re-run.
- **`gamecontrollerdb.txt` is curl-downloaded at configure time** (`soh/CMakeLists.txt:754`) — a
  configure step silently needs network.
- **`BUILD_REMOTE_CONTROL=1` is passed by every CI workflow but consumed nowhere** — a probable dead
  flag; the Network/remote features compile **unconditionally** via the `soh/*.cpp` glob, not gated.
