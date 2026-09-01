# imps — Island of Misfit Patches Storage

Patches I want carried on top of other people's projects, without maintaining
forks of those projects. Each project gets one folder holding a pinned
upstream commit, a patch series, and short scripts to fetch, build, and run.
The upstream checkout and all build products are gitignored — the scripts,
patches, and docs ARE the repo.

## Layout

- `<Project>/` — scripts (`fetch.sh`, `apply.sh`, `build.sh`, `run.sh`),
  `patches/` (**code changes only**), and that project's `CLAUDE.md`.
- `tasks/` — shared across all projects: task docs, plus deep-dive
  reference docs under `tasks/reference/<project>/`.
- Prose about a project lives here in imps, never inside the patches — a
  patch carries only what must change upstream's own files. The full
  doc-structure contract is in `CLAUDE.md`.

## Ocarina of Time (Ship of Harkinian)

Upstream: <https://github.com/HarbourMasters/Shipwright>

```sh
cd OcarinaOfTime
./fetch.sh    # clone if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/  (fetches first if you skipped fetch.sh)
./run.sh      # launches bldInstall/soh.elf with runDir/ as the game's working dir
```

- `apply.sh` is optional — skip it for a pristine upstream build. It refuses
  to run unless the checkout is exactly at the pin (re-run `fetch.sh` to get
  back there; local branches survive).
- The pin is the tip of upstream `develop` as of 2026-09-01; it lives in
  `fetch.sh` (`SHIPWRIGHT_SHA`).
- > On first launch the game asks for a legally-acquired OoT ROM and
  > generates `runDir/oot.o2r` from it; saves, config, and logs also land in
  > `runDir/`. Nothing ROM-derived is ever committed.

## Status / planned

- **OcarinaOfTime** — builds and runs with the patch series applied
  (verified 2026-09-01). One code patch (decomp renames), ported from my
  old fork; the fork's docs now live in `OcarinaOfTime/CLAUDE.md` and
  `tasks/reference/ocarina/`.
- **MajorasMask** — one code patch (64-bit audio/scheduler fixes) exported
  from my old `fedora44Fixes` fork branch, verified to apply byte-identical
  on the pin. Build verification pending.
- **Planned:** more projects (the Majora's Mask, Super Mario 64, and
  Banjo-Kazooie ports); podman container builds alongside the host builds.
