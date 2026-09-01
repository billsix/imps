# BanjoKazooie — Lighthouse

```sh
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/ + copies lighthouse.o2r into runDir/
./run.sh      # launch build-cmake/Lighthouse with runDir/ as the game's working dir
```

Clean rebuild from nothing:

```sh
rm -rf Lighthouse build-cmake bldInstall     # add runDir to also wipe saves + bk.o2r
./fetch.sh && ./apply.sh && ./build.sh && ./run.sh
```

- Upstream: <https://github.com/HarbourMasters/Lighthouse>, pinned in
  `fetch.sh` (`PIN_SHA`, tip of `develop` as of 2026-09-01).
- `apply.sh` is optional — skip it for a pristine upstream build. It refuses
  to run unless the checkout is exactly at the pin; `./fetch.sh` gets you
  back there. **Without the patches the game freezes right after ROM
  import** (patch 0003 is the fix).
- The game binary runs from the **build tree** (`build-cmake/Lighthouse`) —
  `cmake --install` installs assets, not the executable.
- > `runDir/` holds your saves, config, `lighthouse.o2r`, and the extracted
  > `bk.o2r`. On a first run (or after wiping `runDir/`) the game asks for a
  > legally-acquired Banjo-Kazooie ROM (`.z64`) and extracts.
- Patch details and architecture notes: `CLAUDE.md` here, and
  `../tasks/reference/banjo/`.

## Podman build → AppImage (alternative to the host build)

```sh
make image      # build the ubuntu-24.04 builder image (mirrors upstream CI)
make appimage   # compile in the container → out/lighthouse.appimage
make run        # run the AppImage on the host, from runDir/ (same saves as run.sh)
```

- `make help` lists all targets (build, image-export/import, shell,
  clean, distclean).
- Builds whatever the checkout holds — run `./fetch.sh && ./apply.sh`
  first for the patched build.
- > The container build dir is `Lighthouse/build-cmake` (inside the
  > checkout); the host build.sh uses the sibling `build-cmake/`. They
  > don't clobber each other, and `make clean` touches only the
  > container's.
