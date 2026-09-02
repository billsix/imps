# BanjoKazooie — Lighthouse (BK PC port), under imps

**Lighthouse** is a PC/console port of *Banjo-Kazooie* in the Ship of
Harkinian family (Harbour Masters, lead Malkierian): the BK **decomp**
(`src/core1` OS/driver/audio, `src/core2` gameplay, level overlays) + a
**C++ port layer** (`src/port/`) + the **libultraship** runtime and
**Torch** asset extractor as submodules. Port tag `1.0.0` released
2026-07-31. Ships no copyrighted assets: the player supplies a ROM,
extracted in-app to `bk.o2r`; port assets ship in `lighthouse.o2r`.

Managed by imps: `Lighthouse/` here is a pristine clone of
https://github.com/HarbourMasters/Lighthouse, pinned by `fetch.sh` at
`6d30df9a` (tip of upstream `develop` as of 2026-09-01), with the
maintainer's patches applied by `apply.sh`. Not a fork; the patch series is
the whole delta.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps
  (inline list; run once, as root). Verified 2026-09-01 in a fresh
  fedora:44 container: script + full configure + o2r + build all green.
- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/`; skips the ROM-needing
  `ExtractAssets` target (in-app extraction covers it) and copies
  `lighthouse.o2r` into `runDir/`.
- `./run.sh` — launch `build-cmake/Lighthouse` (the install step does not
  install the executable) with `runDir/` as cwd.

## Patches

Exported 2026-09-01 from the maintainer's `fixOnFedora` branch (same base
as the pin) — this series was **submitted upstream as a PR and reviewed by
JeodC** (patch 0004 is the review round), so when it merges, the series
retires at the next pin bump. Patch 0002's commit subject was repaired
during export (the original commit had lost its subject line to a
formatting accident; the intended message survived in the maintainer's
draft). Byte-identical to `fixOnFedora` verified on apply.

- `0001-fix-build-dependencies-in-instructions-for-Fedora.patch` —
  `docs/BUILDING.md`: adds SDL2_net to the Fedora gcc dnf line.
- `0002-CMakeLists-stamp-bk.o2r-with-the-project-version-in-.patch` —
  passes `-u ${PROJECT_VERSION}` to `torch o2r` in `ExtractAssets` so
  `bk.o2r` records a portVersion and `VerifyArchiveVersion()` stops
  forcing a re-extract on every launch.
- `0003-core1-graphics_thread-fix-post-import-freeze-from-OS.patch` —
  **the freeze fix**: thread5's event-vs-task discriminator read
  `msg.ptr`, but on 64-bit hosts `OS_MESG_32()` leaves the OSMesg union's
  high bytes uninitialized, so SP events looked like task pointers and
  were dropped, hanging the game right after ROM import. Reads
  `msg.data32` instead. Investigation log:
  [`../../tasks/reference/banjo/freeze-after-rom-import.md`](../../tasks/reference/banjo/freeze-after-rom-import.md).
- `0004-shortened-comments-per-request-from-JeodC.patch` — collapses the
  two long explanatory comments per upstream review.

## Version notes

- Submodules at the pin: **libultraship `2917d0f4` (1.3.1-482)** — newer
  than both ocarina's (486) and mm's (397) pins — and Torch `b4b75e66`
  (v1.0.0-419). Asset extraction is Torch-based (like ocarina's pin, unlike
  mm's ZAPD pipeline).
- `ExtractAssets` (the build-time extraction) wants `baserom.z64` in the
  `Lighthouse/` source root — out of imps' scope; in-app extraction is the
  supported path. Headless/sandbox builds may need `-DUSE_NETWORKING=OFF`
  (no SDL2_net in the sandbox).
- Configure-time network caveat: the build `file(DOWNLOAD)`s `sse2neon.h`
  from an **unpinned master** and FetchContent-pins `dr_libs` — relevant
  for any future offline/container build.

## Architecture reference (read to get oriented without re-reading the code)

Deep docs in **`../../tasks/reference/banjo/`**, authored at the pin (no
version gap):

- [`architecture-overview.md`](../../tasks/reference/banjo/architecture-overview.md) —
  **read first.** The 3-layer model, two-thread frame model, and the three
  seams (graphics, asset, and the Lighthouse-specific OS-emulation seam).
- [`decomp-map.md`](../../tasks/reference/banjo/decomp-map.md) — where X lives
  in the BK decomp: core1 vs core2 vs level overlays; the actor system +
  Banjo state machine; the per-frame update chain.
- [`port-layer.md`](../../tasks/reference/banjo/port-layer.md) — `src/port/`:
  `GameEngine`, the two-thread pump, CVars, events, enhancements/rando.
- [`os-emulation-threading.md`](../../tasks/reference/banjo/os-emulation-threading.md) —
  **the biggest divergence from the siblings, and the first doc for any
  hang**: N64 threads/queues on real `std::thread`s, the ThreadWatchdog,
  a freeze-debugging playbook, 64-bit-host hazards.
- [`libultraship-integration.md`](../../tasks/reference/banjo/libultraship-integration.md) —
  the LUS seam at 1.3.1-482.
- [`frame-interpolation.md`](../../tasks/reference/banjo/frame-interpolation.md) —
  30 Hz tick decoupled from render FPS via subframe DL replay.
- [`asset-pipeline.md`](../../tasks/reference/banjo/asset-pipeline.md) — ROM →
  Torch → `bk.o2r`; `lighthouse.o2r`; the `__OTR__` seam; HD/mods.
- [`build-system.md`](../../tasks/reference/banjo/build-system.md) — CMake
  graph, feature flags, headless/sandbox gotchas.
- [`freeze-after-rom-import.md`](../../tasks/reference/banjo/freeze-after-rom-import.md) —
  the (resolved) freeze investigation behind patch 0003.

## libultraship reference docs

The crawl set at `../../tasks/reference/libultraship/` documents this
project's exact LUS pin (`2917d0f4`, 1.3.1-482) as **iteration 16** —
read it via git history (commit "1.3.1-482 (2917d0f4)"); the working
tree shows a newer pin.

## Podman build (Dockerfile + Makefile)

Created 2026-09-01 per the banjo-podman-appimage-build task (archived at
`../../tasks/archive/banjo/2026/09/01/banjo-podman-appimage-build.md`), on
the MajorasMask template. `Dockerfile` mirrors upstream CI's `build-linux`
job (`.github/workflows/main.yml` at the pin): base **ubuntu:24.04**
(CI says `ubuntu-latest`, which has resolved to the 24.04 LTS since
early 2025 — recorded in the Dockerfile header), the workflow's apt
list inlined (Lighthouse has no apt-deps.txt file), and SDL 2.30.3 /
tinyxml2 10.0.0 / libzip 1.10.1 (no crypto) built from source. The
Makefile builds `GeneratePortO2R` in-container (CI uses a separate
Torch job + artifact download; same result), then the game, then
`cpack -G External` → `out/lighthouse.appimage`.

One deviation from the MM template worth knowing:
**`USERNS_FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),,--userns=keep-id)`**
— inside the nested sandbox there are no subordinate IDs for
`--userns=keep-id` to build its user namespace from (inner runs die
with `write /proc/…/uid_map: operation not permitted`), and the inner
root already matches the mount owner, so the flag is dropped there; on
a normal host it stays, byte-identical to before. (MajorasMask's
Makefile got the same fix.)

Verified 2026-09-01: `make image` (1.08 GB), `make build` of the patched
tree (17 MB binary), and `make appimage` (`out/lighthouse.appimage`,
12.5 MB) all green nested in the sandbox, and **`make run` confirmed
working on the maintainer's host** — the full pipeline is closed.

## Conventions

- The decomp is a near-1:1 port — match surrounding style, keep edits
  surgical, don't refactor decomp code as drive-by cleanup. Gate behavior
  changes behind a CVar + event listener.
- C/C++ formatted with the project `.clang-format`.
- Unlike heavier ports, this sandbox CAN build and run Lighthouse headless
  (Xvfb + Mesa + gdb) — verify pixels, not just exit codes.
