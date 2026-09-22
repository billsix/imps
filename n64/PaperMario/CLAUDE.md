# PaperMario — PaperBoat (Paper Mario 64 PC port), under imps

**PaperBoat** is the HarbourMasters PC port of Paper Mario (N64), in the
same lineage as the other n64/ ports: a Paper Mario decomp (`src/`,
ROM-derived) plus a C++ port layer (`src/port/`), with **libultraship**
(the runtime) and **Torch** (the asset extractor) as submodules under
`external/`.

Managed by imps: `PaperBoat/` here is a pristine clone of
https://github.com/HarbourMasters/PaperBoat, pinned by `fetch.sh` at the
stable release tag **`1.0.1`** (`424c220f0`, dated 2026-09-18). **No patches
yet** — this project is at the first-step "compile pristine upstream as-is"
stage (the path every n64/ port went through before carrying a series). Task:
`../../tasks/papermario-add-port.md`.

> Pin history: first pinned at tip-of-`develop` (`611f5b68`) 2026-09-21, then
> moved to `1.0.1` while diagnosing an extraction failure. The pin turned out
> to be irrelevant to that failure (it was a ROM problem — see "ROM
> requirements"); `1.0.1` is kept simply as the newest tagged release.

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
16.2.1) — a full pristine build (~3663 steps at `1.0.1`), producing a 37 MB
`Paperboat` ELF with `paperboat.o2r` + `assets/` beside it. **In-app ROM
extraction was also verified** headless (Xvfb + software GL): with a
correctly-sized US ROM, Torch extracted a valid 40 MB `pm64.o2r` in ~27 s.
Interactive gameplay (display/audio) is still the maintainer's host-verify.

There is no `apply.sh`/`patches/` yet — a pristine build needs neither. They
are scaffolded in a follow-on unit once a first patch is carried (see the
family contract in `../CLAUDE.md` and the task's follow-on list).

## ROM requirements — the file must be EXACTLY the 40 MB US ROM

(William Emerison Six <billsix@gmail.com>, 2026-09-21.) PaperBoat's in-app
extractor hashes the **entire ROM file** with SHA-1 (`Companion::CalculateHash`
over all bytes) and looks the digest up in `config.yml`, whose only US recipe
key is **`3837f44cda784b466c9a2d99df70d77c322b97a0`** — the hash of a **40 MB**
(41,943,040-byte) US Paper Mario ROM. Consequences:

- **An over-dumped / padded ROM silently fails.** A full-cart 64 MB dump (the
  40 MB game + 24 MB trailing cart data) hashes to something else, matches no
  recipe, extracts nothing, and the game shows the misleading **"Extraction
  error — No ROM O2R file detected. Please generate a ROM O2R and relaunch."**
  The extractor never actually ran. This is NOT a build or pin bug.
- **Why only Paper Mario hits this in the maintainer's ROM set:** every other
  HM-port ROM there is already exactly game-sized (SM64 8 MB, OoT/MM 32 MB, BK
  16 MB), so their whole-file hashes match; only `PaperMario/ROMF.z64` is a
  64 MB over-dump.
- **Fix / how to feed it a good ROM:** trim to the first 40 MB —
  `head -c 41943040 ROMF.z64 > pm64.z64` — and verify
  `sha1sum pm64.z64` prints `3837f44c…`. That trimmed file extracts a valid
  40 MB `pm64.o2r` (proven headless, ~27 s). Also confirm big-endian `.z64`
  byte order (`80 37 12 40`); a byte-swapped `.n64`/`.v64` hashes differently
  too. ROMs stay out of imps' scope — this is guidance, not a committed file.

Deep mechanism: `src/port/Engine.cpp` (`RunExtract` state machine,
`AnyRomArchiveExists`), `src/port/extractor/GameExtractor.cpp`
(`GetSupportedRomNode`, `RunStandalone`, `GenerateOTR`), and Torch's
`Companion::CalculateHash`.

## Version notes

- **Pin:** PaperBoat `1.0.1` (`424c220f0`, tagged release, dated 2026-09-18).
- **Submodules at the pin** (JeodC forks — distinct from every other n64/
  port's engine pins, confirmed against `.gitmodules` + `docs/BUILDING.md`):
  - `external/libultraship` @ `7aa03b6c` — JeodC/libultraship, branch
    `lus-converge` (`port-maintenance-45`). Tip-of-`develop` pinned
    `601f7002` (`-46`); the single-commit delta is HD-art rendering only and
    does not affect extraction.
  - `external/torch` @ `106f4e30` — JeodC/Torch-LH, branch `pm64` (same at
    both `1.0.1` and tip-of-develop).
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
- **Build-stamp note:** CMake runs `git describe --tags` for a version stamp.
  At `1.0.1` this resolves cleanly (the pin IS the tag). On an untagged pin
  such as tip-of-develop it prints a harmless `fatal: no tag exactly matches
  <sha>` and continues.
- **Windows/macOS** are supported by upstream (clang-cl + vcpkg on Windows,
  MacPorts on macOS) but out of scope here — imps builds the Linux target.
