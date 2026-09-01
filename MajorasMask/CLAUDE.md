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
  (`fedora44Fixes`, same base) and verified byte-identical on apply.
  **Good upstream-submission candidate** — surgical, well-documented,
  fixes real 64-bit portability bugs.

## Version notes

- Submodules at the pin: **libultraship `7f2baa10` (1.3.1-397)**, plus
  ZAPDTR `ee3397a3` and OTRExporter `32e088e2` — this pin predates the
  torch asset-pipeline migration that OcarinaOfTime's newer pin has; 2S2H
  still extracts via ZAPD/OTRExporter here.
- No reference-doc set exists for this project yet (the old fork carried
  none). The ocarina docs in `../tasks/reference/ocarina/` describe the
  sibling architecture and are directionally useful, not authoritative,
  for 2S2H.
- The maintainer's old fork also had a `podmanBuildAppImage` branch
  (Ubuntu-based Dockerfile + Makefile building 2S2H in podman) — prior art
  for imps' planned container builds, not yet ported.
