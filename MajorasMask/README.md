# MajorasMask — 2 Ship 2 Harkinian

```sh
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/  (fetches first if you skipped fetch.sh)
./run.sh      # launch bldInstall/2s2h.elf with runDir/ as the game's working dir
```

Clean rebuild from nothing:

```sh
rm -rf 2ship2harkinian build-cmake bldInstall   # add runDir to also wipe saves + mm.o2r
./fetch.sh && ./apply.sh && ./build.sh && ./run.sh
```

- Upstream: <https://github.com/HarbourMasters/2ship2harkinian>, pinned in
  `fetch.sh` (`PIN_SHA`, tip of `develop` as of 2026-05-31).
- `apply.sh` is optional — skip it for a pristine upstream build. It refuses
  to run unless the checkout is exactly at the pin; `./fetch.sh` gets you
  back there.
- > `runDir/` holds your saves, config, and the extracted `mm.o2r`. On a
  > first run (or after wiping `runDir/`) the game asks for a legally-acquired
  > Majora's Mask ROM and re-extracts.
- Patch details: `CLAUDE.md` here.

## Podman build → AppImage (alternative to the host build)

```sh
make image      # build the Ubuntu 26.04 builder image (~10 min first time)
make appimage   # compile in the container → out/2ship.appimage
make run        # run the AppImage on the host, from runDir/ (same saves as run.sh)
```

- `make help` lists all targets (image-export/import, shell, clean, distclean).
- Builds whatever the checkout holds — run `./fetch.sh && ./apply.sh` first
  for the patched build.
- > The container build dir is `2ship2harkinian/build-cmake` (inside the
  > checkout); the host build.sh uses the sibling `build-cmake/`. They don't
  > clobber each other, and `make clean` touches only the container's.
