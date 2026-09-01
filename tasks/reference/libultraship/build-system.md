# libultraship — build system and dependencies

> **Pinned:** libultraship **1.3.1-482**
> (`2917d0f4fe62c579174561dcd34f327c9410bb72`, 2026-07-29 —
> BanjoKazooie's pin; direct descendant of 1.3.1-397, 85 commits).
> Updated 2026-09-01, iteration 16 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## Shape

One STATIC lib, `PREFIX ""`, C++20 + C11, `file(GLOB)` sources; still
**no `install()`/`export()` and no `project()` VERSION** — but the
target now sets **`ENABLE_EXPORTS TRUE` + `WINDOWS_EXPORT_ALL_SYMBOLS
TRUE`** (`src/CMakeLists.txt:8-9`, #1051): the bridge is a
dynamic-loading surface (scripts/DLLs resolve symbols from the game
binary), not just a link-time one. **`enable_testing()` now exists**:
`LUS_BUILD_TESTS=ON` → `add_subdirectory("tests")`
(`CMakeLists.txt:86-91`).

**Python 3 is an unconditional configure-time hard dep**
(`find_package(Python3 REQUIRED COMPONENTS Interpreter)`,
`src/CMakeLists.txt:10`) even with scripting off; a repo-root
`requirements.txt` (`cryptography`, `Pillow`) is pip-installed by every
CI job.

## Options

| Option | Default | Notes |
|---|---|---|
| `INCLUDE_MPQ_SUPPORT` | OFF (`CMakeLists.txt:41`) | `.otr`/MPQ opt-in, unchanged |
| `NON_PORTABLE` | OFF | unchanged |
| `GBI_UCODE` | `F3DEX_GBI_2` | unchanged, incl. the PRIVATE-def/public-header ABI trap |
| **`ENABLE_SCRIPTING`** | **OFF** (`CMakeLists.txt:12`; #1084 flipped it opt-in) | TinyCC scripting + keystore + signed archives |
| **`DISABLE_DLL_LOADER`** | **OFF** (`CMakeLists.txt:11`, #1051) | runtime kill-switch for the dlopen loader (the .cpp itself only compiles under ENABLE_SCRIPTING) |
| **`LUS_BUILD_TESTS`** | **OFF** (`CMakeLists.txt:84`) | googletest suite |
| `USE_OPENGLES` / `GFX_DEBUG_DISASSEMBLER` / `SPDLOG_MIN_CUTOFF` | as before | `SPDLOG_MIN_CUTOFF` now `src/CMakeLists.txt:163-169` |
| `USE_AUTO_VCPKG` | still never `option()`-declared | vcpkg still `git pull`s unpinned |

`cmake/cvars.cmake` is now **24 macros**: added
`CVAR_ALLOW_BACKGROUND_INPUTS` (`gAllowBackgroundInputs`, #994) and
`CVAR_SCRIPT_SAFE_LEVEL` (`gScriptSafeLevel` — defined, **zero code
references** at this pin).

## Dependencies

Deltas vs 397 (mechanism still FetchContent + find_package, no
submodules, no vendoring):

- **monocypher** (ed25519/BLAKE2b) — NEW, **unconditional**: FetchContent
  SHA `0d85f98c`, hand-rolled STATIC target, linked **PUBLIC**
  (`common.cmake:136-155`, `src/CMakeLists.txt:137`) — even though its
  only consumer is inside `#ifdef ENABLE_SCRIPTING`
  (`Archive.cpp:14-21`).
- **TinyCC** — NEW, scripting-gated: FetchContent from `TinyCC/tinycc`
  **`GIT_TAG mob` — a moving branch, not a pin**
  (`common.cmake:160-161`), running upstream `./configure` at
  CMake-configure time via `execute_process` (+ a host-compiler `c2str`
  bootstrap when cross-compiling). Linked `libtcc libtcc1` PUBLIC.
- **Key-embedding pipeline** (scripting): `file(GLOB keys/script/*.pem)`
  → `tools/generate_keys_header.py` → generated `DefaultKeys.h`
  (`src/CMakeLists.txt:24-45`). The repo ships 6 public keys
  (`keys/script/`: HM64, Kenix1-5) plus `tools/generate_keys.py` and
  `tools/sign.py` (archive signing, needs python `cryptography`).
- **googletest v1.16.0** — FetchContent, tests-gated.
- **prism** pin bumped `bbcbc7e3` → `1de05445`
  (`common.cmake:110-111`), + an MSVC/sccache workaround clearing
  prism's compiler launcher (`:117-133`).
- **spdlog** mac fallback `v1.14.1` → `v1.16.0` (`mac.cmake:11`).
- Everything else as at 397: ImGui `v1.91.9b-docking` + patch, StormLib
  v9.25 (MPQ-gated), stb via `file(DOWNLOAD)`, libgfxd (disassembler-
  gated), BS::thread-pool v4.1.0 include-only, SDL2 2.32.10, libzip
  system dep, **Linux still has NO FetchContent fallback**
  (`linux.cmake` unchanged; bare `find_package(... REQUIRED)` at
  `src/CMakeLists.txt:92-102`).

## Platform matrix

Windows, Darwin, iOS, Linux, Android, **OpenBSD (NEW, #971)**:
dispatch `CMakeLists.txt:67-69` → `cmake/dependencies/openbsd.cmake`
(`/usr/X11R6/include` hack), OpenGLES link special-case
(`src/CMakeLists.txt:127-129`). #1023 added `sysctl kern.clockrate`
frame-pacing calibration for OpenBSD/macOS (SDL backend — NOT an
osGetTime change). Switch/WiiU still absent; `ENABLE_DX12` still only
dead guards. GCC 16 fixed by one `<stdint.h>` include (#1100).

## Tests and CI

- `tests/` (#1033/#1066): **16 gtest files** — binary_io,
  string_helper, crc64, stox, utils, bitconverter, event_system,
  sound_matrix_decoder, path/file helpers, glob, splittext,
  archive_resource (753 lines), archive_self, resource_type, +
  `script_test.cpp` under scripting. Coverage = utils/resource/events/
  audio-decoder units; **no renderer, no Config/CVars/Console/logging**.
- NEW `.github/workflows/test-validation.yml` (#1092): Linux (gcc-12)
  + Windows both run `ctest` with `SDL_VIDEODRIVER=dummy` /
  `SDL_AUDIODRIVER=dummy`.
- `build-validation.yml`: windows-arm64 pinned to `windows-2022`
  (#1130); all jobs pip-install `requirements.txt`; `apt-deps.txt` adds
  `tcc libtcc-dev`. Artifacts **still named `soh-*`**; Linux CI still
  hand-builds SDL2 **2.24.1**.

## Known quirks at this pin

- Fast3D backend exclusion filters still dead
  (`src/fast/CMakeLists.txt:26` vs the stale `graphic/Fast3D/` regexes
  `:28-40`) — per-file `#ifdef`s remain the only guard.
- `.mm` files still `-fno-objc-arc` (`src/CMakeLists.txt:58-64`).
- vcpkg unpinned-pull; port list unchanged.
