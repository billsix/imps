# Reference: the build system (CMake + Torch + libultraship)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference. The CMake graph, feature flags, and what to pass to build Lighthouse —
especially in a headless/sandbox environment. Companions:
[architecture-overview.md](architecture-overview.md), [asset-pipeline.md](asset-pipeline.md).*

*Banner: Lighthouse at branch `bill`. All line anchors are into the root `CMakeLists.txt`
(~30 KB) unless another file is named.*

## Target graph

- **`Lighthouse`** executable — `project(Lighthouse VERSION 1.0.0 LANGUAGES C CXX ASM)`
  (`:6`); target created at `:252` (`add_executable(${PROJECT_NAME} ${ALL_FILES})`). Requires
  **C++20** (`:73`) and **C11** (`:74`); `cmake_minimum_required(VERSION 3.26.0)` (`:1`) — the
  BUILDING.md's "CMake ≤ 3.3" note is stale/wrong.
- **`libultraship`** — `add_subdirectory` (`:369`), `add_dependencies` (`:370`),
  `target_link_libraries(... PRIVATE libultraship)` (`:371`). Own `cmake_minimum_required` 3.24.0.
- **Torch built twice:** static lib `torch` linked into the game (`:505-506`, in-app extractor)
  **and** a standalone host exe via `ExternalProject_Add(TorchExternal)` (`:737-741`, guarded
  `NOT NintendoSwitch`, `-DENABLE_ASAN` propagated) → `${TORCH_EXECUTABLE}` (`:743-748`).
- **Asset targets** (custom, manually invoked — see [asset-pipeline.md](asset-pipeline.md)):
  `ExtractAssets` (`:749-755`, `torch o2r baserom.z64` → `bk.o2r`), `GeneratePortO2R`
  (`:757-766`, `torch pack port_staging lighthouse.o2r o2r` → `lighthouse.o2r`).

**Everything compiles into the one executable** — the decomp (`src/core1`, `src/core2`, level
dirs), the port layer (`src/port`), `lib/ultralib`, and `include` are globbed into `ALL_FILES`
(`:201-219`), with `src/unused/` filtered out (`:221`). There is no separate decomp lib.

## Feature flags (`option()`), defaults, and what they gate

| Option | Line | Default | Gates |
|---|---|---|---|
| `ENABLE_ASAN` | 75 | OFF | AddressSanitizer flags; propagated to Torch/prism |
| **`USE_NETWORKING`** | 162 | **ON** | `find_package(SDL2_net REQUIRED)` + `USE_NETWORKING` def + `SDL2_net::*` links |
| `USE_STANDALONE` | 493 | OFF | Torch exe vs static lib |
| `BUILD_STORMLIB` | 494 | OFF | StormLib/MPQ (note: MPQ hard-off at `:16`) |
| **`BUILD_BK64`** | 496 | **ON** | Banjo-Kazooie support in Torch |
| `BUILD_PM64` / `SM64` / `MK64` / `SF64` / `FZERO` / `OOT` / `MARIO_ARTIST` / `NAUDIO` | 497-504 | OFF | other games in Torch |

There is **no `NON_PORTABLE`** option; instead a fixed `add_compile_definitions` block (`:166-178`)
sets `VERSION_US=1`, `ENABLE_RUMBLE=1`, `F3DEX_GBI=1`, `NON_MATCHING=1`, `NON_EQUIVALENT=1`,
`AVOID_UB=1`, `GBI_FLOATS=1`, `N_MICRO=1`, … Game version is fixed `us` (`:161`).
`BUILD_CROWD_CONTROL` is referenced (`:428`) but declared in libultraship, not here.

## ⚠ Building in this sandbox (headless container)

Two things bite a local/sandbox build:

1. **`USE_NETWORKING` defaults ON and hard-requires `SDL2_net`** (`find_package(... REQUIRED)`,
   `:441`), which this container lacks. **Configure with `-DUSE_NETWORKING=OFF`** — that skips the
   `find_package` and the `SDL2_net::*` links (guarded by generator expressions `:453`/`:482`) and
   compiles out `#ifdef USE_NETWORKING` code (Anchor/netplay). CI always installs
   `libsdl2-net-dev`, so upstream never hits this.
2. **`ExtractAssets` runs `torch o2r baserom.z64` from the source dir** (`:753`) — it needs the ROM
   as **`baserom.z64`** in the repo root. The container ROM is `/foo/opt/n64/n64roms/BanjoKazooie/
   ROMF.z64` (US rev0, SHA-1 `1fe1632…`); symlink/copy it as `baserom.z64` before extracting.

Everything else the build needs is present here: cmake, ninja, clang/gcc, SDL2, libpng, libzip,
nlohmann_json, tinyxml2, spdlog, ogg/vorbis, boost (transitive via LUS/Torch), and the zip tools.

## Generated files — written into the SOURCE tree at configure time

`configure_file` writes two generated files **into `src`/root, not the build dir** (a staging
gotcha — they show as untracked/modified after configure):

- `properties.h.in → properties.h` (`:186`, `@ONLY`): version + `PROJECT_BUILD_NAME` =
  `"Split Rock <NATO-word>"` indexed by patch version (`:18-31`; patch 0 → "Split Rock Alfa"). **No
  git hash here.**
- `src/port/build.c.in → src/port/build.c` (`:185`): the git branch/hash/tag (`git rev-parse HEAD`
  etc., gathered `:35-67`) → `gBuildVersion`, `gGitBranch`, `gGitCommitHash`, `gGitCommitTag`,
  `gBuildDate`.

Other configure-time side effects: downloads `sse2neon.h` (`:300`) and `dr_libs` via FetchContent
(`:309`); copies `config.yml`/assets (`:111-112`, `:365`). Windows auto-bootstraps vcpkg
(`:100-105`).

## External libraries

`find_package`d here: OpenGL (`:182`, Linux non-Apple), Ogg + Vorbis (`:447-451`), SDL2_net (only
if `USE_NETWORKING`). SDL2, tinyxml2, nlohmann_json, spdlog, libzip, boost are consumed
**through libultraship** (included/vcpkg-installed, not `find_package`d here). Per-platform link
list `ADDITIONAL_LIBRARY_DEPENDENCIES` assembled `:452-491` (+ `dl` on Linux).

## CI & packaging (`.github/workflows`, `cmake/packaging.cmake`)

- `main.yml` (`GenerateBuilds`): job `generate-port-o2r` builds Torch + packs `lighthouse.o2r`
  once and uploads it; downstream `build-windows` (VS2022 → zip), `build-macos` (macos-14,
  MacPorts → dmg), `build-linux` (Ninja Release → `cpack -G External` → AppImage), `build-switch`
  (disabled). Each downstream job **downloads** the prebuilt `lighthouse.o2r` rather than
  regenerating it.
- `linux.yml`/`windows.yml`/`mac.yml`/`switch.yml`: PR-validation builds; `clang-format.yml`:
  formatting check.
- Packaging: CPACK generator `External` (AppImage) on Linux, `ZIP` on Windows/Switch, `Bundle`
  (dmg) on Darwin (`:815-821`). **No `Dockerfile`** exists (only a `.dockerignore` referencing an
  absent one).

## Quick build recipe (this container, headless)

```sh
# from the Lighthouse repo root
ln -sf /foo/opt/n64/n64roms/BanjoKazooie/ROMF.z64 baserom.z64   # ExtractAssets input
cmake -H. -Bbuild-cmake -GNinja -DUSE_NETWORKING=OFF            # SDL2_net absent here
cmake --build build-cmake --target ExtractAssets               # → bk.o2r (one-time per ROM)
cmake --build build-cmake --target GeneratePortO2R             # → lighthouse.o2r (already committed)
cmake --build build-cmake                                      # → build-cmake/Lighthouse
```

For a freeze/crash investigation, add `-DCMAKE_BUILD_TYPE=Debug` (symbols for gdb) and consider
`-DENABLE_ASAN=ON`; note ASAN finds memory bugs, not deadlocks — for a hang, the ThreadWatchdog
dump + gdb backtrace (see [os-emulation-threading.md](os-emulation-threading.md)) are the tools.
