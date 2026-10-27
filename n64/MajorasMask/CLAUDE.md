# MajorasMask — 2 Ship 2 Harkinian (MM PC port), under imps

**2S2H** is the PC port of *The Legend of Zelda: Majora's Mask* from the
Ship of Harkinian family — same shape as SoH (see
`../OcarinaOfTime/CLAUDE.md`): the MM decomp (`mm/src/`), a C++ port layer
(`mm/2s2h/`), and the **libultraship** runtime as a submodule.

Managed by imps: `2ship2harkinian/` here is a pristine clone of
https://github.com/HarbourMasters/2ship2harkinian, pinned by `fetch.sh` at
`f1dda4c2` (tip of upstream `develop`; re-bumped from `e8757c14` 2026-10-19,
which was bumped from `04a1a4319` 2026-10-08), with the maintainer's patches
applied by `apply.sh`. Not a fork; the patch series is the whole delta. The
1-patch audio series replays **clean** at `f1dda4c2` (content byte-identical,
`tools/check_patches_apply.sh MajorasMask` green; upstream has not absorbed it);
the libultraship gitlink is unchanged (`7f9b86a5`). BUILD + play-test pending.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps
  (inline list; run once, as root). Verified 2026-09-01 in a fresh
  fedora:44 container: script + full configure + o2r + build all green.
- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/` (fetches first if needed).
- `./run.sh` — launch `bldInstall/2s2h.elf` with `runDir/` as cwd.

## Patches

- `patches/upstreamable-ci-appimage/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch`
  — **upstream-bound CI patch** (`../../tasks/archive/imps/2026/10/27/n64-upstreamable-appimage-make-target.md`): adds
  `docker/Dockerfile` + `docker/Makefile` (CI-mirror ubuntu-22.04/gcc-12 build env, `make -C docker
  appimage`) and rewires the `build-linux` job to call it; the generate-2ship-otr job + artifact
  unchanged. Apply-gate green; nested `make -C docker appimage` build **verified**
  2026-10-27 (16 MB x86-64 ELF AppImage).
- `patches/upstreamable-audio-64bit/0001-Fix-silent-SFX-and-several-64-bit-host-audio-crashes.patch` —
  8 files in the audio stack + scheduler. Fixes, per its commit message:
  (a) removes a `(uintptr_t)parentLayer < 0x7FFFFFFF` port guard in
  `AudioPlayback_ProcessNotes` that silently skipped ALL note playback in
  non-PIE 64-bit builds (upstream CI builds PIE, which masks it). **At the
  `e8757c14` pin upstream had wrapped that guard in `#ifndef __WIIU__`** —
  which excludes WiiU but leaves it live on desktop, so it does NOT fix our
  case; the 3-way resolution removes the guard entirely (a superset of
  upstream's WiiU exclusion). An upstream submission should note this;
  (b) `osRecvMesg` receiving an 8-byte `OSMesg` into a 4-byte `u32` — a
  stack overwrite that crashed `AudioLoad_ProcessScriptLoads`;
  (c) `sched.c` reading `.ptr` where `.data32` is meant;
  (d) a `u32` → `uintptr_t` segment address in `z_scene.c`;
  (e) a `numSamplesUntilEnd >= 0` clamp in `synthesis.c` — marked in the
  message as a stopgap, not a root-cause fix.
  **Good upstream-submission candidate** — surgical, well-documented, fixes real
  64-bit portability bugs.
- *(A second patch added libogg/libvorbis/opus/opusfile to BUILDING.md's
  Ubuntu and Fedora dependency lines. **Dropped at the 2026-10-08 bump** —
  upstream independently added all four to the Ubuntu, Fedora and Arch lists in
  its "Update build doc and readme" commit, so our patch was fully absorbed.)*

Export & build/run verification history:
`../../tasks/reference/imps/game-port-history.md`.

## Version notes

- Submodules at the pin: **libultraship `7f9b86a5` (1.3.1-490)** (bumped from
  `7f2baa10`/1.3.1-397 with the pin), plus ZAPDTR `ee3397a3` and OTRExporter
  `32e088e2` (both unchanged) — this pin still predates the torch
  asset-pipeline migration that OcarinaOfTime's newer pin has; 2S2H still
  extracts via ZAPD/OTRExporter here.
- No 2S2H-specific reference-doc set exists yet (the old fork carried
  none). The ocarina docs in `../../tasks/reference/ocarina/` describe the
  sibling architecture (directionally useful, not authoritative) — and
  the LUS crawl set at `../../tasks/reference/libultraship/` does NOT document
  this project's current libultraship pin (`7f9b86a5`, 1.3.1-490): its closest
  iteration is **15** (`7f2baa10`, 1.3.1-397, our previous pin) — read that via
  git history (commit "1.3.1-397 (7f2baa10)"), but it predates this pin by ~93
  LUS commits, so spot-check against the checkout.

## Podman build (Dockerfile + Makefile)

**This folder is the imps reference implementation of the N64 podman build.**
Native imps files (not patches), with **two selectable Dockerfile variants**:

- `Dockerfile` (default, `VARIANT=ci`) — mirrors upstream CI: ubuntu 22.04,
  gcc-12 pin, Kitware cmake. Use for CI fidelity.
- `Dockerfile.ubuntu26.04` (`VARIANT=2604`) — ubuntu 26.04, distro-default
  gcc-15/cmake. The modern-toolchain build.
- Both: apt list **`COPY`d** from the checkout's
  `.github/workflows/apt-deps.txt` (`COPY` not `RUN --mount=type=bind` — see the
  SuperMario64 Dockerfile comment and the drift table), SDL 2.30.3 / tinyxml2
  10.0.0 / libzip 1.10.1 built from source. Each variant gets its own image tag.
- `shell` keeps `--userns=keep-id` in both variants (without it a rootless-podman
  shell can't write the bind-mounted source).

Makefile adapted for the imps layout: `SRC` = `2ship2harkinian/`; `make image`
passes the checkout as the build **context** (`-f Dockerfile $(SRC)`) so the
apt-deps bind mount resolves, and auto-runs `fetch.sh` if the checkout is
missing; standard `PODMAN_RUN_FLAGS` threaded into the `run` invocations (never
`build`). `make build`/`make appimage` compile the checkout as-is into
`2ship2harkinian/build-cmake` (in-checkout, distinct from the host build.sh's
sibling `build-cmake/`); `make run` executes the AppImage from the shared
`runDir/`.

Porting & verification history (from the old fork's `podmanBuildAppImage` branch;
only the `ci` variant was on-host-verified):
`../../tasks/reference/imps/game-port-history.md`.
