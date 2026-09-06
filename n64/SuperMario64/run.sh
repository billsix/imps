#!/usr/bin/env bash
#
# run.sh — launch the game.  The binary runs from the BUILD tree (the
# install step installs assets, not the executable; the game finds its
# o2r archives next to the executable).  runDir/ is the game's working
# directory: config, saves, logs, mods, and the extracted sm64.o2r live
# there instead of polluting the build tree.

set -e
cd "$(dirname "$0")"
mkdir -p runDir
# The build produces libtcc.so (the scripting engine) inside the checkout's
# libultraship/ dir, and the binary's rpath bakes in the ABSOLUTE build-time
# path — which breaks when the repo is mounted at a different path (e.g. a
# binary built in the sandbox, run on the host).  LD_LIBRARY_PATH makes the
# lookup path-independent.
cd runDir

# Default to the OpenGL renderer on first launch.  libultraship registers
# Vulkan before OpenGL on Linux and picks the front of that list when no
# config exists, so the built-in default is Vulkan whenever it was compiled
# in — and that backend hangs or crashes on some GPUs/drivers (RADV among
# them).  Seed the config to select OpenGL (Window.Backend.Id 2) only when
# it does not exist yet, so a first run is safe while a later in-menu switch
# to Vulkan (written back as Id 4) is preserved.  All backends stay built;
# this changes only the default.
if [ ! -f ghostship.cfg.json ]; then
    cat > ghostship.cfg.json <<'JSON'
{
    "Window": {
        "Backend": {
            "Id": 2,
            "Name": "OpenGL"
        }
    }
}
JSON
fi

LD_LIBRARY_PATH="../Ghostship/libultraship${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    ../build-cmake/Ghostship
