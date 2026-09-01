# imps — Island of Misfit Patches Storage

Patches I want carried on top of other people's projects, without maintaining
forks of those projects. Each project gets one folder holding a pinned
upstream commit, a patch series (coming), and short scripts to fetch, build,
and run. The upstream checkout and all build products are gitignored — the
scripts and patches ARE the repo.

## Ocarina of Time (Ship of Harkinian)

Upstream: <https://github.com/HarbourMasters/Shipwright>

```sh
cd OcarinaOfTime
./build.sh    # fetches the pinned source on first run, then cmake+ninja → bldInstall/
./run.sh      # launches bldInstall/soh.elf with runDir/ as the game's working dir
```

- `./fetch.sh` can also be run alone: clone if missing, checkout the pinned
  commit (tip of upstream `develop` as of 2026-09-01), init submodules.
- > On first launch the game asks for a legally-acquired OoT ROM and
  > generates `runDir/oot.o2r` from it; saves, config, and logs also land in
  > `runDir/`. Nothing ROM-derived is ever committed.

## Status / planned

- **OcarinaOfTime** — pristine upstream builds and runs; my patch series is
  not yet ported.
- **Planned:** per-project `patches/` (a `git format-patch` series applied
  with `git am` on top of the pin); more projects (the Majora's Mask,
  Super Mario 64, and Banjo-Kazooie ports); podman container builds
  alongside the host builds.
