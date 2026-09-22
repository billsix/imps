# PaperMario — PaperBoat

HarbourMasters' PC port of Paper Mario 64. **Pristine upstream, no patches
yet** — this port is at the "compile it as-is" stage.

```sh
sudo ./installdependencies.sh   # Fedora: dnf install the build deps (once per machine)
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./build.sh    # cmake --preset ninja-release → PaperBoat/build/ninja-release (fetches first if needed)
./run.sh      # launch the Paperboat binary with runDir/ as the game's working dir
```

Clean rebuild from nothing:

```sh
rm -rf PaperBoat        # add runDir to also wipe saves + the extracted pm64.o2r
./fetch.sh && ./build.sh && ./run.sh
```

- Upstream: <https://github.com/HarbourMasters/PaperBoat>, pinned in
  `fetch.sh` (`PIN_SHA`) at the stable release tag `1.0.1`.
- **No `apply.sh`/`patches/` yet** — a pristine upstream build needs neither;
  they get scaffolded once a first patch is carried (see `CLAUDE.md`).
- The game binary runs from the **build tree**
  (`PaperBoat/build/ninja-release/Paperboat`); the port asset archive
  `paperboat.o2r` and `assets/` are copied next to it at build time.
- > The configure/build step downloads `gamecontrollerdb.txt` and a few
  > FetchContent deps, so it needs network.
- > `runDir/` holds your saves, config, and the in-app-extracted `pm64.o2r`.
  > On a first run the game asks for a legally-acquired Paper Mario (US) ROM
  > and extracts it. ROMs are out of scope here — see the repo README.
- > **The ROM must be EXACTLY the 40 MB US dump** (SHA-1
  > `3837f44cda784b466c9a2d99df70d77c322b97a0`, big-endian `.z64`). PaperBoat
  > hashes the whole file, so a padded/over-dumped ROM (e.g. a 64 MB full-cart
  > dump) matches no recipe and fails with the misleading *"No ROM O2R file
  > detected"* — extraction never runs. Trim an over-dump with
  > `head -c 41943040 in.z64 > pm64.z64` and check `sha1sum`. Details:
  > `CLAUDE.md` → "ROM requirements".
- Build facts, submodule pins, and dependency notes: `CLAUDE.md` here.
