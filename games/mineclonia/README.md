# Mineclonia (on Luanti) — pinned build

A Minecraft-like survival game (Mineclonia 0.124.1) on the Luanti 5.18.0 engine,
built from pinned upstream source. No patches.

```sh
sudo ./installdependencies.sh   # [HOST] Fedora build deps (once)
./build.sh                      # [HOST] fetch (first time) + build into bldInstall/Release/
./run.sh                        # [HOST] play; worlds + settings live in runDir/
```

Container alternative (no host deps; `make help` lists every target):

```sh
make build                      # [HOST] build inside a Fedora-45 podman image
make smoke                      # [HOST] headless check: Mineclonia server loads, no Lua errors
make run                        # [HOST] play via X11/Wayland passthrough
```

- `BUILD_TYPE=Debug ./build.sh` for a debug build.
- Clean rebuild: `make clean && ./build.sh`. `runDir/` (your worlds) is never touched.
- Pins and how to bump them: `CLAUDE.md`.
