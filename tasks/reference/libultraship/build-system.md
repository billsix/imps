# libultraship — build system and dependencies

> **Pinned:** libultraship tag **1.0.1**
> (`22bd2a04ed45c9807d71908e08462542f89f7ed3`, 2023-06-07). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## Shape

Root `CMakeLists.txt` is 27 lines: platform prologue (ObjC++/ARC on
Darwin, static CRT on Windows), optional vcpkg automation, then
`add_subdirectory(extern)` + `add_subdirectory(src)`. The product is
**one static library**: `add_library(libultraship STATIC)` with
`PREFIX ""` and C++20 (`src/CMakeLists.txt:1-3`) → `libultraship.a` /
`.lib`. **No `install()`, `export()`, tests, FetchContent, or
ExternalProject anywhere** — consumption is `add_subdirectory` only.
`project()` carries **no VERSION**; no version constant exists in code.

## Dependencies — all vendored, none pinned machine-readably

**There is no `.gitmodules`.** Every `extern/` dependency is a
hand-copied source tree; the upstream commit is recorded only in commit
messages.

| Dep | Version | Mechanism |
|---|---|---|
| ImGui | 1.89.3 WIP, **docking branch** (`extern/ImGui/imgui.h:25-29`) | hand-rolled `add_library(ImGui STATIC)` (`extern/CMakeLists.txt:35`), per-platform backends `:47-76` |
| StormLib (MPQ) | 9.24 | `add_subdirectory` (`extern/CMakeLists.txt:19`); bundles its own zlib/bzip2 fallbacks |
| spdlog | 1.11.0 | header-only via PUBLIC include dir (`src/CMakeLists.txt:355`) |
| nlohmann-json | 3.11.2 | `add_subdirectory`, tests off |
| tinyxml2 | 7.0.1 | hand-rolled STATIC target (`extern/CMakeLists.txt:110`), not its own CMake |
| StrHash64 (CRC64) | LUS-local | STATIC (`extern/CMakeLists.txt:130`) |
| ZAPDUtils | vendored ZAPD subset | `add_subdirectory` (`extern/CMakeLists.txt:118`) |
| BS::thread_pool | header | INTERFACE target **never linked** — reached via the PRIVATE `../extern` include dir instead |
| stb (image/write) | headers + `stb_impl.c` | compiled directly into libultraship (`src/CMakeLists.txt:336-342`) |
| dr_libs | mp3/wav headers | INTERFACE target — **entirely unused** (no link, no include anywhere) |
| metal-cpp | — | Darwin-only include dir |
| d3d12 SDK headers | — | vendored inside `src/graphic/Fast3D/dxsdk/` |

`find_package`: SDL2 (REQUIRED everywhere; CONFIG on Windows), GLEW
(REQUIRED Win/Mac/Linux), OpenGL (QUIET), X11/PulseAudio (Linux,
optional), Threads (Darwin/Switch), Apple frameworks via `find_library`.

Link graph (`src/CMakeLists.txt`): PRIVATE `StrHash64`; PUBLIC
`ZAPDUtils ImGui storm tinyxml2 nlohmann_json::nlohmann_json`
(ZAPDUtils moved to PUBLIC in 1.0.1, closing the
FileHelper/PathHelper include leak).
PUBLIC include dirs include **`src/` itself** — the reason the
include/src boundary is advisory (see `architecture-overview.md`).

## vcpkg (Windows)

`USE_AUTO_VCPKG` (consumed, never `option()`-declared) clones vcpkg and
**`git pull`s it on every reconfigure** — unpinned by construction; the
pinning line is commented out (`cmake/automate-vcpkg.cmake:123`).
Installs `zlib bzip2 sdl2 glew` for `x64-windows-static`.

## Platform matrix

Keyed off `CMAKE_SYSTEM_NAME`: `Windows`, `Darwin`, `Linux`,
`NintendoSwitch`, and **`CafeOS` = Wii U** (maps to `src/port/wiiu/`,
`__WIIU__`). Per-platform source selection in `src/CMakeLists.txt`:
audio backends (`:22-39` — note PulseAudio is listed unconditionally
AND again for Linux; its own `#if __linux__` guard saves other
platforms), controller (`:57-62`), port dirs (`:208-223`, empty on
desktop), Fast3D backends (`:281-329`), ImGui backends
(`extern/CMakeLists.txt:47-76`).

Compile definitions (not options): `ENABLE_DX11` (Windows),
`ENABLE_OPENGL` (non-CafeOS), `SPDLOG_ACTIVE_LEVEL`, `_DEBUG`/`NDEBUG`.
**Referenced but never defined** — the two famous dead backends:

- `ENABLE_DX12` — `gfx_direct3d12.cpp` (~1000 lines) compiles to an
  empty TU on Windows; `WindowBackend::DX12` unreachable.
- `X11_SUPPORTED` — `gfx_glx.cpp` (554 lines) compiles to nothing on
  Linux; `WindowBackend::GLX_OPENGL` unreachable, and the
  `find_package(X11)` link is for nothing.

## Known build-system quirks at this tag

- `${Source_Files__Log__SPDLog}` referenced but never set
  (`src/CMakeLists.txt:129`) — expands to nothing.
- `OSXFolderManager.mm` compiled with `-fno-objc-arc`, opposing the
  global ARC flags set at root `:6-7`.
- `GameVersions.h` and `binarytools/{FileHelper,PathHelper}.h` are not
  listed in `src/CMakeLists.txt` (header-only stragglers).
- CI (`.github/workflows/build-validation.yml`) builds mac/linux/windows
  and lints (clang-tidy/format); artifacts are still named `soh-*`.
  Linux CI hand-builds SDL2 2.24.1 with gcc-10.
