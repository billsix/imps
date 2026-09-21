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
  `fetch.sh` (`PIN_SHA`, tip of `develop` as of 2026-09-21).
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
- Build facts, submodule pins, and dependency notes: `CLAUDE.md` here.
