# PaperMario — PaperBoat (Paper Mario 64 PC port), under imps

**PaperBoat** is the HarbourMasters PC port of Paper Mario (N64), in the
same lineage as the other n64/ ports: a Paper Mario decomp (`src/`,
ROM-derived) plus a C++ port layer (`src/port/`), with **libultraship**
(the runtime) and **Torch** (the asset extractor) as submodules under
`external/`.

Managed by imps: `PaperBoat/` here is a pristine clone of
https://github.com/HarbourMasters/PaperBoat, pinned by `fetch.sh` at
`611f5b68` (tip of upstream `develop` as of 2026-09-21). **No patches yet** —
this project is at the first-step "compile pristine upstream as-is" stage
(the path every n64/ port went through before carrying a series). Task:
`../../tasks/papermario-add-port.md`.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps (inline
  list, translated from the upstream Linux CI apt line; run once, as root).
- `./fetch.sh` — clone if missing, checkout the pin, init submodules
  (`external/libultraship`, `external/torch`), disable gpg signing
  repo-locally in the checkout and each submodule.
- `./build.sh` — `cmake --preset ninja-release` + build into
  `PaperBoat/build/ninja-release`; the main target depends on
  `GeneratePortO2R`, so a plain build produces `paperboat.o2r` (port-side
  shader archive, no ROM) and copies it + `assets/` next to the binary.
  Configure/build needs network (libultraship fetches gamecontrollerdb.txt).
- `./run.sh` — launch `PaperBoat/build/ninja-release/Paperboat` with `runDir/`
  as cwd. The ROM-extracted `pm64.o2r` is created in-app on first run. Unlike
  Ghostship's `run.sh`, no `LD_LIBRARY_PATH` is needed: this LUS fork builds no
  `libtcc.so`, and the binary bakes no RPATH (verified 2026-09-21) — so a
  binary built at one path runs at another with no shared-lib juggling.

**Build status (2026-09-21):** `installdependencies.sh` + `fetch.sh` +
`build.sh` verified green in the runClaudeInContainer sandbox (Fedora 44, gcc
16.2.1) — a full pristine build of all 3666 steps, producing a 37 MB
`Paperboat` ELF with `paperboat.o2r` + `assets/` beside it. The actual
game run (display/audio + in-app ROM extraction) is the maintainer's
host-verify step; the sandbox has no display/FUSE/audio.

There is no `apply.sh`/`patches/` yet — a pristine build needs neither. They
are scaffolded in a follow-on unit once a first patch is carried (see the
family contract in `../CLAUDE.md` and the task's follow-on list).

## Version notes

- **Pin:** PaperBoat `611f5b68` (upstream `develop`, dated 2026-09-20).
- **Submodules at the pin** (JeodC forks — distinct from every other n64/
  port's engine pins, confirmed against `.gitmodules` + `docs/BUILDING.md`):
  - `external/libultraship` @ `601f7002` — JeodC/libultraship, branch
    `lus-converge`.
  - `external/torch` @ `106f4e30` — JeodC/Torch-LH, branch `pm64`.
  These do NOT match the libultraship reference crawl's pin
  (`../../tasks/reference/libultraship/`, currently Ghostship's `c151cc91`);
  a libultraship-lane patch would reopen that crawl (deferred — a bare build
  needs no LUS docs).
- **Build (Linux):** CMake presets (`ninja-release`), binary
  `build/ninja-release/Paperboat`. Upstream CI uses gcc-14 on Ubuntu and
  builds SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 from source only
  because Ubuntu's are stale; Fedora 44's dnf packages are current, so
  `installdependencies.sh` uses them (same choice as the other n64/ ports).
  cmake fetches a few deps via FetchContent (stb, zlib, yaml-cpp, imgui,
  prism), which is why the build needs network.
- **Dependency deltas vs the Ghostship (SuperMario64) Fedora list**, all from
  PaperBoat's own CI apt line: `+SDL2_net-devel`, `+fmt-devel`,
  `+zlib-devel`, `+bzip2-devel`, `+mesa-libGL-devel`/`libglvnd-devel` (for
  the Linux `find_package(OpenGL REQUIRED)`), `+file`. `libshaderc-devel` is
  **confirmed used** here — configure logs "Vulkan rendering backend enabled
  (shaderc_shared)". `mbedtls-devel` is carried over from the Ghostship
  Fedora build (libultraship/ixwebsocket) and not independently reconfirmed;
  keep it unless a future audit shows this LUS fork drops ixwebsocket.
- **Build-stamp warning (harmless):** CMake runs `git describe --tags` for a
  version stamp; the pinned checkout has no exact tag, so configure prints
  `fatal: no tag exactly matches <sha>`. It does not fail the build.
- **Windows/macOS** are supported by upstream (clang-cl + vcpkg on Windows,
  MacPorts on macOS) but out of scope here — imps builds the Linux target.
