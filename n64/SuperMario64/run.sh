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
cd runDir && LD_LIBRARY_PATH="../Ghostship/libultraship${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    ../build-cmake/Ghostship
