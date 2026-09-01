# MajorasMask — 2 Ship 2 Harkinian (MM PC port), under imps

**2S2H** is the PC port of *The Legend of Zelda: Majora's Mask* from the
Ship of Harkinian family — same shape as SoH (see
`../OcarinaOfTime/CLAUDE.md`): the MM decomp (`mm/src/`), a C++ port layer
(`mm/2s2h/`), and the **libultraship** runtime as a submodule.

Managed by imps: `2ship2harkinian/` here is a pristine clone of
https://github.com/HarbourMasters/2ship2harkinian, pinned by `fetch.sh` at
`04a1a4319` (tip of upstream `develop` as of 2026-05-31), with the
maintainer's patches applied by `apply.sh`. Not a fork; the patch series is
the whole delta.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps
  (inline list; run once, as root). Verified 2026-09-01 in a fresh
  fedora:44 container: script + full configure + o2r + build all green.
- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/` (fetches first if needed).
- `./run.sh` — launch `bldInstall/2s2h.elf` with `runDir/` as cwd.

## Patches

- `patches/0001-Fix-silent-SFX-and-several-64-bit-host-audio-crashes.patch` —
  8 files in the audio stack + scheduler. Fixes, per its commit message:
  (a) removes a `(uintptr_t)parentLayer < 0x7FFFFFFF` port guard in
  `AudioPlayback_ProcessNotes` that silently skipped ALL note playback in
  non-PIE 64-bit builds (upstream CI builds PIE, which masks it);
  (b) `osRecvMesg` receiving an 8-byte `OSMesg` into a 4-byte `u32` — a
  stack overwrite that crashed `AudioLoad_ProcessScriptLoads`;
  (c) `sched.c` reading `.ptr` where `.data32` is meant;
  (d) a `u32` → `uintptr_t` segment address in `z_scene.c`;
  (e) a `numSamplesUntilEnd >= 0` clamp in `synthesis.c` — marked in the
  message as a stopgap, not a root-cause fix.
  Exported verbatim 2026-09-01 from the maintainer's old fork branch
  (`fedora44Fixes`, same base) and verified byte-identical on apply;
  patched tree build- and run-verified on the maintainer's host
  2026-09-01. **Good upstream-submission candidate** — surgical,
  well-documented, fixes real 64-bit portability bugs.
- `patches/0002-docs-add-the-required-audio-libraries-...patch` —
  adds libogg/libvorbis/opus/opusfile dev packages to BUILDING.md's
  Ubuntu and Fedora lines (the build hard-requires all four; the Nix
  section already listed them). Found by the install-script
  fresh-container verification. **Upstream-submission candidate.**

## Version notes

- Submodules at the pin: **libultraship `7f2baa10` (1.3.1-397)**, plus
  ZAPDTR `ee3397a3` and OTRExporter `32e088e2` — this pin predates the
  torch asset-pipeline migration that OcarinaOfTime's newer pin has; 2S2H
  still extracts via ZAPD/OTRExporter here.
- No 2S2H-specific reference-doc set exists yet (the old fork carried
  none). The ocarina docs in `../tasks/reference/ocarina/` describe the
  sibling architecture (directionally useful, not authoritative) — and
  the LUS crawl set at `../tasks/reference/libultraship/` documents this
  project's exact libultraship pin (`7f2baa10`, 1.3.1-397) as
  **iteration 15**: read it via git history (commit "1.3.1-397
  (7f2baa10)"); the working tree shows a newer pin.
## Podman build (Dockerfile + Makefile)

Ported 2026-09-01 from the maintainer's old fork's `podmanBuildAppImage`
branch (2 commits: "Added Bill's Dockerfile based on the github action" +
"updated to ubuntu 26.04") — as **native imps files, not patches**, per the
patches-carry-code-only principle. The branch's two Dockerfile versions
were kept as **two selectable variants** instead of the second overwriting
the first:

- `Dockerfile` (default, `VARIANT=ci`) — mirrors upstream CI:
  ubuntu 22.04, gcc-12 pin, Kitware cmake. Use for CI fidelity.
- `Dockerfile.ubuntu26.04` (`VARIANT=2604`) — ubuntu 26.04,
  distro-default gcc-15/cmake. The modern-toolchain build.
- Both: apt list **`COPY`d** from the checkout's
  `.github/workflows/apt-deps.txt` (`COPY` not `RUN --mount=type=bind` —
  the latter is read by the confined `container_t` RUN process and fails
  on a `:Z`-poisoned checkout, see the SuperMario64 Dockerfile comment,
  fixed 2026-09-01), SDL 2.30.3 / tinyxml2 10.0.0 /
  libzip 1.10.1 built from source. Each variant gets its own image tag.
- The branch's v2 also dropped `--userns=keep-id` from the `shell` target
  only; with one shared Makefile that difference was deliberately NOT
  carried — `shell` keeps `--userns=keep-id` in both variants, matching
  `PODMAN_RUN` (without it a rootless-podman shell can't write the
  bind-mounted source).

The Makefile was adapted for the imps layout, everything else verbatim:

- `SRC` = `2ship2harkinian/` (the imps checkout) instead of the Makefile's
  own directory;
- `make image` passes the checkout as the build **context**
  (`-f Dockerfile $(SRC)`) so the apt-deps bind mount still resolves, and
  auto-runs `fetch.sh` if the checkout is missing;
- the standard `PODMAN_RUN_FLAGS` nested-podman auto-default was added and
  threaded into the `run` invocations (never `build`);
- the old branch's `.gitignore` hunk became entries in this folder's
  `.gitignore` (`out/`, image tars) — the checkout itself is already
  ignored.

`make build`/`make appimage` compile the checkout as-is — normally pin +
applied series — into `2ship2harkinian/build-cmake` (in-checkout, distinct
from the host build.sh's sibling `build-cmake/`). `make run` executes the
AppImage on the host from the shared `runDir/`.
