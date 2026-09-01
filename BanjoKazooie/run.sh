#!/usr/bin/env bash
#
# run.sh — launch the game.  The binary runs from the BUILD tree
# (cmake --install does not install the Lighthouse executable, only assets
# and headers).  runDir/ is the game's working directory: config, saves,
# logs, mods, lighthouse.o2r, and the extracted bk.o2r live there instead
# of polluting the build tree.

set -e
cd "$(dirname "$0")"
mkdir -p runDir
cd runDir && ../build-cmake/Lighthouse
