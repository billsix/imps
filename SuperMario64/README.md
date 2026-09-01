# SuperMario64 — Ghostship

```sh
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/  (fetches first if you skipped fetch.sh)
./run.sh      # launch build-cmake/Ghostship with runDir/ as the game's working dir
```

Clean rebuild from nothing:

```sh
rm -rf Ghostship build-cmake bldInstall     # add runDir to also wipe saves + sm64.o2r
./fetch.sh && ./apply.sh && ./build.sh && ./run.sh
```

- Upstream: <https://github.com/HarbourMasters/Ghostship>, pinned in
  `fetch.sh` (`PIN_SHA`, tip of `develop` as of 2026-09-01 — deliberately
  modern: it already contains my always-fly-on-triple-jump cheat, merged
  upstream, so that one needs no patch).
- The three patches are cheats: Super Jump (high jump), Infinite Air
  Jumps, and Disable Skybox — each a menu checkbox under Cheats /
  Enhancements.
- `apply.sh` is optional — skip it for a pristine upstream build. It
  refuses to run unless the checkout is exactly at the pin; `./fetch.sh`
  gets you back there.
- The game binary runs from the **build tree** (`build-cmake/Ghostship`);
  the game finds its o2r archives next to the executable.
- > cmake's configure step downloads `gamecontrollerdb.txt`, so configure
  > needs network.
- > `runDir/` holds your saves, config, and the extracted `sm64.o2r`. On a
  > first run (or after wiping `runDir/`) the game asks for a
  > legally-acquired SM64 ROM and extracts. Copying your old runDir
  > contents in preserves saves.
- Patch details and architecture notes: `CLAUDE.md` here, and
  `../tasks/reference/mario64/`.
