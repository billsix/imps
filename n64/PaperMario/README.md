# PaperMario — PaperBoat

HarbourMasters' PC port of Paper Mario 64, pinned upstream plus a
three-patch series (command-line ROM import on Linux, a precise refusal of
unsupported ROMs, and the Vulkan first-frame crash fix in libultraship).

```sh
sudo ./installdependencies.sh   # Fedora: dnf install the build deps (once per machine)
./fetch.sh    # clone upstream if missing, checkout the pinned commit, init submodules
./apply.sh    # git am the patch streams (patches/ + patches-libultraship/) onto the pin
./build.sh    # cmake --preset ninja-release → PaperBoat/build/ninja-release (fetches first if needed)
./run.sh /path/to/PaperMario.z64   # first time: verify + extract the ROM, then play
./run.sh      # after that: just play (pm64.o2r is in runDir/)
```

Clean rebuild from nothing:

```sh
rm -rf PaperBoat        # add runDir to also wipe saves + the extracted pm64.o2r
./fetch.sh && ./apply.sh && ./build.sh && ./run.sh /path/to/PaperMario.z64
```

- Upstream: <https://github.com/HarbourMasters/PaperBoat>, pinned in
  `fetch.sh` (`PIN_SHA`) at the stable release tag `1.0.1`.
- Patches: `patches/upstream-candidates/` (game tree) and
  `patches-libultraship/upstream-candidates/` (the LUS submodule) — what each
  does, and the verification record: `CLAUDE.md` → "Patches".
- The game binary runs from the **build tree**
  (`PaperBoat/build/ninja-release/Paperboat`); the port asset archive
  `paperboat.o2r` and `assets/` are copied next to it at build time.
- > The configure/build step downloads `gamecontrollerdb.txt` and a few
  > FetchContent deps, so it needs network. Have `libshaderc-devel`
  > installed **before** the first configure (`installdependencies.sh` does).
- > `runDir/` holds your saves, config, and the extracted `pm64.o2r`. ROMs are
  > out of scope here — see the repo README. `run.sh <ROM>` checks the
  > file's SHA-1 against PaperBoat's recipes first: the US ROM is the 40 MB
  > big-endian `.z64` (`3837f44cda784b466c9a2d99df70d77c322b97a0`); a padded
  > cart dump (e.g. 64 MB) is trimmed to a copy in `runDir/` automatically
  > when its first 40 MB match; anything else is refused with the reason.
- > First launch is seeded to the **OpenGL** renderer (`runDir/paperboat.cfg.json`);
  > switch in the menu if you want Vulkan. Why: `CLAUDE.md` → "Vulkan crash".
- Build facts, submodule pins, and dependency notes: `CLAUDE.md` here.
