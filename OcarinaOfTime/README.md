# OcarinaOfTime — Ship of Harkinian

```sh
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/  (fetches first if you skipped fetch.sh)
./run.sh      # launch bldInstall/soh.elf with runDir/ as the game's working dir
```

Clean rebuild from nothing:

```sh
rm -rf Shipwright build-cmake bldInstall     # add runDir to also wipe saves + oot.o2r
./fetch.sh && ./apply.sh && ./build.sh && ./run.sh
```

- Upstream: <https://github.com/HarbourMasters/Shipwright>, pinned in
  `fetch.sh` (`PIN_SHA`, tip of `develop` as of 2026-09-01).
- `apply.sh` is optional — skip it for a pristine upstream build. It refuses
  to run unless the checkout is exactly at the pin; `./fetch.sh` gets you
  back there.
- > `runDir/` holds your saves, config, and the extracted `oot.o2r`. On a
  > first run (or after wiping `runDir/`) the game asks for a legally-acquired
  > OoT ROM and re-extracts.
- Patch details and architecture notes: `CLAUDE.md` here, and
  `../tasks/reference/ocarina/`.
- `tools/save_generator.py` — interactive save-file generator (base
  quest): asks dungeons-beaten first, derives an item loadout you can
  override, assumes full stocks, writes a `.sav` locally and prints
  install + backup steps. Format details:
  `../tasks/reference/ocarina/save-file-generator.md`.
