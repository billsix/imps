# gzdoom — GZDoom (Doom-engine source port)

Fetch pristine GZDoom + its ZMusic dependency at pinned tags, apply the imps
patch series, build both with CMake, and launch the result with a WAD. Two ways
to build: a **native host build** (the baseline — plain scripts, no container)
and a **podman** build (an extra convenience). Both produce the same game.

## Native build (host — no container)

```sh
./installdependencies.sh          # [root/sudo] Fedora build deps for GZDoom + ZMusic
./fetch.sh                        # clone GZDoom @ g4.14.2 + ZMusic @ 1.3.0 into checkout/
./apply.sh                        # apply patches/ onto checkout/gzdoom/ (optional)
./build.sh                        # ZMusic then GZDoom -> bldInstall/Release/bin/gzdoom
./run.sh /path/to/DOOM2.WAD       # launch with a CLI WAD (extra gzdoom args pass through)
```

`build.sh` runs `fetch.sh` itself when the checkout is missing, so after
`installdependencies.sh` a fresh clone needs only `./build.sh` to reach a built
game. Debug build: `BUILD_TYPE=Debug ./build.sh` (its own `bldInstall/Debug`;
Release is the default). `run.sh` uses `runDir/` as GZDoom's working directory,
so config and saves land there, not in `$HOME`.

## Podman build (container — optional)

```sh
make image                        # build the Fedora-44 builder image (~few min first time)
make build                        # ZMusic then GZDoom -> install/Release/bin/gzdoom
make version                      # print the built gzdoom's version (headless)
make run WAD=/path/to/DOOM2.WAD   # launch with a CLI WAD (X11/Wayland display)
```

`make help` lists every target (`shell`, `shell-exec`, `smoke`,
`image-export`/`image-import`, `clean`, `distclean`).

## Clean rebuild from nothing

```sh
rm -rf checkout build install build-cmake bldInstall   # (leaves runDir/ — game data — untouched)
./installdependencies.sh && ./build.sh                 # native
# or, container:  ./fetch.sh && ./apply.sh && make image && make build
```

## Notes

- **Upstream + pins:** GZDoom <https://github.com/ZDoom/gzdoom> @ `g4.14.2`,
  ZMusic <https://github.com/ZDoom/ZMusic> @ `1.3.0` — both in `fetch.sh`
  (`GZDOOM_PIN_SHA` / `ZMUSIC_PIN_SHA`). ZMusic is a build dependency (built
  first, installed into the shared prefix); it is never patched.
- **`apply.sh` is optional** — skip it for a pristine upstream build. It refuses
  to run unless `checkout/gzdoom/` is exactly at the pin; `./fetch.sh` resets it.
- The native build installs into `bldInstall/<BUILD_TYPE>/`; the container build
  into `install/<BUILD_TYPE>/`. They are kept separate because `-DSYSTEMINSTALL=ON`
  bakes an **absolute** resource path into the binary, so a container-built
  `gzdoom` (path `/work/...`) won't run on the host, and vice versa — build with
  the path you'll run from.

## Running a WAD from the CLI

GZDoom takes `-iwad <base-game WAD>` and `-file <pwad>`.

```sh
./run.sh /path/to/DOOM2.WAD -file my_mod.wad        # native, on your display
make run WAD=/path/to/DOOM2.WAD ARGS='-file my_mod.wad'   # container equivalent
make smoke WAD=/path/to/DOOM2.WAD                   # headless (Xvfb) launch, prints the exit
```

> WADs/IWADs are **your own game data** — supply them at run time; they are never
> committed and their location is not recorded here.

> GZDoom's Linux startup shows a **GTK IWAD-selection dialog** when the IWAD isn't
> unambiguously resolved. Making a CLI-passed WAD play without that GUI is the goal
> of the planned `patches/` fix — see `CLAUDE.md`.
