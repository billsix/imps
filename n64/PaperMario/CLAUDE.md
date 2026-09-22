# PaperMario — PaperBoat (Paper Mario 64 PC port), under imps

**PaperBoat** is the HarbourMasters PC port of Paper Mario (N64), in the
same lineage as the other n64/ ports: a Paper Mario decomp (`src/`,
ROM-derived) plus a C++ port layer (`src/port/`), with **libultraship**
(the runtime) and **Torch** (the asset extractor) as submodules under
`external/`.

Managed by imps: `PaperBoat/` here is a clone of
https://github.com/HarbourMasters/PaperBoat, pinned by `fetch.sh` at the
stable release tag **`1.0.1`** (`424c220f0`, dated 2026-09-18), carrying a
**three-patch series on two lanes** (below) since 2026-09-22. Task history:
`../../tasks/archive/papermario/2026/09/22/papermario-add-port.md`; the ROM-import investigation that
produced the series: `../../tasks/reference/papermario/rom-import-investigation.md` (the full account; the ROM facts alone: `rom-overdump-and-trimming.md`).

> Pin history: first pinned at tip-of-`develop` (`611f5b68`) 2026-09-21, then
> moved to `1.0.1` while diagnosing an extraction failure; `1.0.1` is kept as
> the newest tagged release.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps (inline
  list, translated from the upstream Linux CI apt line; run once, as root).
- `./fetch.sh` — clone if missing, checkout the pin, init submodules
  (`external/libultraship`, `external/torch`), disable gpg signing
  repo-locally in the checkout and each submodule.
- `./apply.sh` — `git am --3way` the patch streams onto the pristine pin:
  `patches/<stream>/` into `PaperBoat/`, `patches-libultraship/<stream>/`
  into `PaperBoat/external/libultraship/` (the family two-lane machinery,
  `../CLAUDE.md`). Refuses to run unless the checkout is at the bare pin.
- `./build.sh` — `cmake --preset ninja-release` + build into
  `PaperBoat/build/ninja-release`; the main target depends on
  `GeneratePortO2R`, so a plain build produces `paperboat.o2r` (port-side
  shader archive, no ROM) and copies it + `assets/` next to the binary.
  Configure/build needs network (libultraship fetches gamecontrollerdb.txt).
  **Install `libshaderc-devel` before the first configure** — added after
  configure it is not picked up until `cmake --preset` runs again, and the
  build then fails at the final link on `shaderc_*` undefined references.
- `./run.sh [ROM]` — launch `PaperBoat/build/ninja-release/Paperboat` with
  `runDir/` as cwd. With a ROM path, it **verifies the file's SHA-1 against
  the recipes in the built `config.yml`, trims a padded over-dump to the 40 MB
  image (`runDir/pm64.z64`) when its first 40 MB match, refuses anything else
  with the expected hash printed**, and passes the accepted file on the
  command line (the CLI patch below makes the app extract it with no
  prompt). It also **seeds `runDir/paperboat.cfg.json` to the OpenGL
  backend** on first launch — see "Vulkan crash" below. Unlike Ghostship's
  `run.sh`, no `LD_LIBRARY_PATH` is needed: this LUS fork builds no
  `libtcc.so`, and the binary bakes no RPATH.

## Patches

Game-tree lane, stream `patches/upstream-candidates/` (both shaped for a
PaperBoat PR; they touch only `src/port/Engine.cpp` and
`src/port/extractor/GameExtractor.cpp`):

- `0001-extractor-honour-a-ROM-path-on-the-command-line-on-L.patch` —
  `RunExtract` collected argv but only the Windows-only `ES_WINDOWS` branch
  ever moved to `ES_EXTRACT_ARGS`; on Linux/macOS `Paperboat rom.z64` silently
  fell into the interactive prompts. Take the same branch on the non-Windows
  path. This is what `run.sh <ROM>` relies on.
- `0002-extractor-refuse-a-picked-ROM-that-matches-no-config.patch`
  — the file dialog's `LoadRomFromPath` accepted any readable file; an
  unsupported one made Torch log "No config found" and return without an
  archive, and the user got the generic "No ROM O2R file detected". Check
  the hash there (the same test `RunStandalone` already makes) and show why
  the file was refused (size, byte order, "trim a padded dump").

libultraship lane, stream `patches-libultraship/upstream-candidates/` (for
the JeodC fork PaperBoat pins, `lus-converge`):

- `0001-fast3d-vulkan-do-not-depend-on-constructor-injected-.patch`
  — the **Vulkan crash**: `GfxRenderingAPIVK` takes a console-variable store
  and a resource manager in its constructor (CVAR lookups, shader templates),
  but `Fast3dWindow` constructs the backend with the default (null) arguments,
  so the first shader build and the first draw dereference null
  (`BuildVulkanShader → ResourceManager::LoadResource`, then
  `DrawTriangles → ConsoleVariable::GetInteger`; both SIGSEGV). libultraship
  picks Vulkan first on Linux whenever `Vulkan_IsSupported()`, so **every
  Linux box crashed on the first frame after extraction** — the maintainer's
  RADV host and Xvfb/lavapipe alike. Resolve both through the Context on
  use, the way the OpenGL backend does.

Verification 2026-09-22 (sandbox, headless; the test script is
`../../tasks/adhoc/papermario-rom-import/test_paperboat.sh`): with the series
applied, the game runs on Vulkan/lavapipe past the first frame; `Paperboat
<rom>` extracts with no prompt (Torch `Done!` ~27 s, 40 MB `pm64.o2r`); the
64 MB over-dump is refused with the ROM Error prompt on both the CLI and
picker paths and nothing is extracted; the good ROM still extracts through
the picker; `run.sh` trims the over-dump, rejects junk before launch, seeds
OpenGL, and the game runs on OpenGL/llvmpipe. Series byte-identity
(`apply.sh` from the bare pin reproduces the work branch) verified the same
day. **Host-verified 2026-09-22** (William Emerison Six <billsix@gmail.com>: "building and
using run.sh works as is now").

The headless proofs need two throwaway instrumentation commits that are
NOT part of the series (`PAPERBOAT_AUTOCLICK=1` takes every popup's first
button; `[trace]` lines on stderr for popups, ROM loads and the extractor's
inputs). They live on the checkout's `imps-test` branch (= `imps-work` + the
instrumentation) and are re-creatable from the test script's header; ImGui
popups cannot be clicked under Xvfb (the GL window's contents are not
capturable, so xdotool has nothing to aim at), which is why they exist.

## Vulkan crash — why `run.sh` seeds OpenGL

Even with the LUS patch applied, `run.sh` seeds `Window.Backend.Id = 2`
(`FAST3D_SDL_OPENGL` in this fork) into `runDir/paperboat.cfg.json` when no
config exists, like Ghostship's `run.sh`: OpenGL is the backend that is
proven end-to-end here, and a later in-menu switch is preserved. Without the
patch and without the seed, a first launch on a Vulkan-capable Linux box
segfaults at the first frame (`Fast::BuildVulkanShader →
ResourceManager::LoadResource`), which reads as "the game crashed right after
importing the ROM". Gotcha for headless testing: with `SHIP_HOME` set,
libultraship doubles the config path (`<dir>//<dir>/paperboat.cfg.json`) and
never reads a seeded config — run with cwd as the app directory instead
(`NON_PORTABLE` is off, so the app dir is `.`).

## ROM requirements — the file must be EXACTLY the 40 MB US ROM

PaperBoat's in-app extractor hashes the **entire ROM file** with SHA-1
(`Companion::CalculateHash` over all bytes) and looks the digest up in
`config.yml`, whose only US recipe key is
**`3837f44cda784b466c9a2d99df70d77c322b97a0`** — the hash of the **40 MB**
(41,943,040-byte) big-endian US ROM. A full-cart 64 MB dump (the game plus
24 MB of padding) hashes to something else and matches no recipe: through
the app-dir scan it is simply not offered; through the file dialog
(pristine) it "extracted" nothing and showed "No ROM O2R file detected" —
patch 0002 turns that into a precise refusal. **`run.sh <ROM>` handles the
over-dump case for you** (trims a copy when the first 40 MB match). The
maintainer's own dump was such a 64 MB over-dump; the evidence chain, the
trim and both proofs: `../../tasks/reference/papermario/rom-overdump-and-trimming.md`.
ROMs stay out of imps' scope.

## Version notes

- **Pin:** PaperBoat `1.0.1` (`424c220f0`, tagged release, dated 2026-09-18).
- **Submodules at the pin** (JeodC forks — distinct from every other n64/
  port's engine pins, confirmed against `.gitmodules` + `docs/BUILDING.md`):
  - `external/libultraship` @ `7aa03b6c` — JeodC/libultraship, branch
    `lus-converge` (`port-maintenance-45`). Tip-of-`develop` pinned
    `601f7002` (`-46`); the single-commit delta is HD-art rendering only and
    does not affect extraction. **The LUS lane carries one patch against this
    SHA** (above); the libultraship reference crawl
    (`../../tasks/reference/libultraship/`, Ghostship's `c151cc91`) does not
    cover this fork and was not reopened for a one-function fix.
  - `external/torch` @ `106f4e30` — JeodC/Torch-LH, branch `pm64` (same at
    both `1.0.1` and tip-of-develop).
- **Build (Linux):** CMake presets (`ninja-release`), binary
  `build/ninja-release/Paperboat`. Upstream CI uses gcc-14 on Ubuntu and
  builds SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 from source only
  because Ubuntu's are stale; Fedora 44's dnf packages are current, so
  `installdependencies.sh` uses them (same choice as the other n64/ ports).
  cmake fetches a few deps via FetchContent (stb, zlib, yaml-cpp, imgui,
  prism), which is why the build needs network. A pristine build is ~3663
  steps → a 37 MB `Paperboat` ELF (Fedora 44, gcc 16.2.1; ccache makes
  rebuilds fast).
- **Dependency deltas vs the Ghostship (SuperMario64) Fedora list**, all from
  PaperBoat's own CI apt line: `+SDL2_net-devel`, `+fmt-devel`,
  `+zlib-devel`, `+bzip2-devel`, `+mesa-libGL-devel`/`libglvnd-devel` (for
  the Linux `find_package(OpenGL REQUIRED)`), `+file`. `libshaderc-devel` is
  **required** (the Vulkan backend; see build.sh note above). `mbedtls-devel`
  is carried over from the Ghostship Fedora build (libultraship/ixwebsocket)
  and not independently reconfirmed; keep it unless a future audit shows this
  LUS fork drops ixwebsocket.
- **Build-stamp note:** CMake runs `git describe --tags` for a version stamp.
  At `1.0.1` this resolves cleanly (the pin IS the tag). On an untagged pin
  such as tip-of-develop it prints a harmless `fatal: no tag exactly matches
  <sha>` and continues.
- **Windows/macOS** are supported by upstream (clang-cl + vcpkg on Windows,
  MacPorts on macOS) but out of scope here — imps builds the Linux target.
