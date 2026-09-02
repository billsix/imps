# Reference: The build system

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference. How Ghostship is configured, compiled, and packaged, across platforms.
Read before touching CMake, adding source files, or debugging a build. Companions:
[asset-pipeline.md](asset-pipeline.md) (the o2r targets), [architecture-overview.md](architecture-overview.md).
Human-facing build steps: Ghostship's `docs/building.md` (in the checkout).*

The build is **CMake-driven** (`CMakeLists.txt`, ~700 lines). The shipping launcher pair
`build.sh` + `run.sh` lives **one dir up** at `/foo/opt/n64/mario64/`. Per the root
`CLAUDE.md`, **Claude does not build/run** here — the maintainer (William Emerison Six <billsix@gmail.com>) builds on their Fedora host outside the
sandbox; edits are handed back with a "try this" prompt.

## The executable

- Single target `Ghostship` (`project(...)` `:4`; `add_executable` `:268`, iOS variant `:259`).
- Sources come from **one recursive `file(GLOB_RECURSE ALL_FILES ...)`** (`:187-235`) — a
  glob, not a hand-maintained list. **Adding a `.c`/`.cpp` needs a re-configure** to be
  picked up. Dirs compiled in: decomp (`src/{audio,buffers,engine,game,goddard,menu}`),
  data (`actors/`, `data/`, `levels/`, `sound/`, selected `lib/src/*.c` gu-matrix helpers),
  port glue (`src/pc/*`, `src/port/*`, `src/port/Enhancements/**`, `src/port/importer/**`),
  and `Resource.rc`.
- **Exclusions** via `list(FILTER ... EXCLUDE REGEX)` (`:238-241`): all `*.inc.c`,
  `bin/eu/*.c`, **`src/game/main.c`** (the N64 entry, replaced by the port's `main()`),
  `src/pc/dlmalloc.c`. Files matching these are silently dropped.
- Generated sources compiled in: `src/port/build.c` (from `build.c.in`, `:109`, embeds
  version/git strings) and `properties.h` (from `properties.h.in`, `:174`, feeds
  `Resource.rc`). **These `configure_file` into the SOURCE tree**, so they show as
  dirty/untracked after configuring.
- `CMAKE_CXX_STANDARD 20`, `CMAKE_C_STANDARD 11` (`:69-70`).

## Submodules: Torch & libultraship

Declared in `.gitmodules` (Torch → HarbourMasters/Torch, libultraship → Kenix3/libultraship).

- **libultraship** — `add_subdirectory(libultraship)` (`:324`) + `target_link_libraries(...
  PRIVATE libultraship)` (`:326`). MPQ/OTR support disabled from the parent
  (`EXCLUDE_MPQ_SUPPORT TRUE`, `:307-309`).
- **Torch is built TWICE** (the surprising part):
  1. **Linked static lib** — `add_subdirectory(Torch)` (`:439`), `USE_STANDALONE` OFF
     (`:431`) → Torch emits a STATIC lib; provides the runtime asset importer. Non-Switch only.
  2. **Standalone `torch` executable** — `ExternalProject_Add(TorchExternal)` (`:617-621`),
     which uses Torch's own default `USE_STANDALONE ON` → an executable at
     `.../TorchExternal-build/…/torch` (`:623-627`). This executable is what the asset
     targets call. Skipped on Switch (`:615`).

## Custom targets / commands

- **POST_BUILD copy** (`:608-613`): copies `config.yml` and `assets/` next to the binary —
  runs after every link.
- **`ExtractAssets`** (`:628-634`): `torch o2r baserom.us.z64 -u <ver>` → `sm64.o2r`, copied
  to build dir. `DEPENDS TorchExternal`. **Manual, NOT in the default build** (needs the
  user's `baserom.us.z64`).
- **`GeneratePortO2R`** (`:636-642`): `torch pack port ghostship.o2r o2r -u <ver>` → packs
  the `port/` dir into `ghostship.o2r`. **Manual, NOT in the default build.**
- **`CreateOSXIcons`** (`:659-674`, Darwin only): `sips`/`iconutil` → `ghostship.icns`; wired
  as a dep of the main target so it runs in a normal macOS build.
- **`gamecontrollerdb.txt` download** (`:644-645`): **at configure time** via `curl` — an
  offline configure errors here. (Linux packaging also `file(DOWNLOAD ...)`s linuxdeploy.)

See [asset-pipeline.md](asset-pipeline.md) for what the two Torch targets actually produce and
the version-gating that makes `-u <ver>` reject mismatched archives at runtime.

## Cross-platform

Branches on `CMAKE_SYSTEM_NAME` / `MSVC` / `APPLE` / `WIN32` / `IOS`. Platforms: **Windows,
Linux, Darwin, iOS, NintendoSwitch, CafeOS (Wii U)**.
- Windows/vcpkg bootstrap (`:79-88`, `x64-windows-static`), MSVC runtime `:274-300`, DX11
  define `:340`.
- macOS/iOS: `enable_language(OBJCXX)` `:62`, deploy target 10.15 `:66`, iOS toolchain
  `cmake/ios.toolchain.cmake`, bundle install + `fixup_bundle` `:658-688`.
- Switch: flags/defines `:134-142`, `-O3`, NRO packaging `:417-429` — **excluded from the
  whole Torch/asset/o2r/install block** (`:430`, `:615`).
- CafeOS: `:353-400`. Per-compiler warning blocks throughout (`:447` MSVC … `:573-606` generic
  Unix, which adds `-msse2 -mfpmath=sse` on x86_64, `-mcpu=native` on aarch64).
- Packaging generator (`:695-701`): Linux→AppImage (linuxdeploy, `cmake/packaging.cmake`),
  Windows/Switch/CafeOS→ZIP, Darwin→Bundle.

## Feature flags / options

- Game selectors (non-Switch, `:431-438`): `BUILD_SM64` **ON**; `USE_STANDALONE`,
  `BUILD_STORMLIB`, `BUILD_MK64`/`SF64`/`FZERO`/`MARIO_ARTIST` OFF. (Torch/LUS are
  multi-game; only SM64 is on here.)
- `USE_NETWORKING` OFF (`:151`); `EXCLUDE_MPQ_SUPPORT` TRUE (`:307`);
  `ENABLE_EXP_AUTO_CONFIGURE_CONTROLLERS` ON (`:308`); `BUILD_CROWD_CONTROL` gates
  `ENABLE_CROWD_CONTROL` (`:374`).
- Hard-coded: `VERSION us` (`:150`); big `add_compile_definitions` block (`:155-167`):
  `VERSION_US=1`, `ENABLE_RUMBLE`, `F3D_OLD`/`F3D_GBI`/`GBI_FLOATS`, `AVOID_UB`,
  `ENABLE_OPENGL`.
- **CVar prefix strings are compile definitions** from `cmake/ghostship-cvars.cmake` +
  `cmake/lus-cvars.cmake` (included `:7-8`): `CVAR_PREFIX_CHEAT="gCheats"` etc. — so the C++
  menu code and CMake agree on CVar names (see [port-layer.md](port-layer.md#cvar-system-end-to-end)).
- **Optimization forced to `-O1`** on non-Switch Release (`:144-146`) — unusually low.
- ASAN present but commented out (`:71-72`).

## The Makefile is a decoy

The repo-root `Makefile` is a **generic third-party "Cool Makefile for CMake Projects"
wrapper** (`Makefile:1-5`), with an `init` target that scaffolds a hello-world CMakeLists
(`:131-151`) — project-agnostic boilerplate. It just wraps `cmake -S . -B` /`--build`/
`--install` into `cmake-build-<type>/`. **It is not the build path used here** and its build
dir differs from `build.sh`'s (`build-cmake/`). Ignore it; the real driver is CMake via
`build.sh`.

## CI (`.github/workflows/`)

`main.yml` (**GenerateBuilds** — builds `ghostship.o2r` once as an artifact, then per-OS
jobs download it and build Windows/mac/Linux), plus `linux.yml`, `mac.yml`, `windows.yml`,
`switch.yml`, and `clang-format.yml` (format gate). Nightly artifacts are the nightly.link
URLs in the README. Issue templates in `.github/ISSUE_TEMPLATE/`.

## Newcomer trip-hazards

- **Torch compiled twice** with opposite `USE_STANDALONE` — expect two Torch build trees.
- **`ExtractAssets`/`GeneratePortO2R` are NOT default** — a plain build won't run without
  running them (and `ExtractAssets` needs your ROM). `build.sh` runs them explicitly.
- **Configure-time network access** (controller DB curl; linuxdeploy download) — offline
  configure errors.
- **Generated files written into the source tree** (`build.c`, `properties.h`) — appear
  dirty after configure.
- **Source list is a recursive glob** — new files need a re-configure; excluded regexes
  silently drop files.
- **`-O1` forced** on non-Switch Release.
- **Root `Makefile` is boilerplate**, not the build. `cmake/packaging.cmake` still carries
  template placeholder metadata (`YOUR@E-MAIL.net`, "Some Company").
