#!/usr/bin/env bash
#
# run.sh — launch the installed game.  runDir/ is the game's working
# directory: config, saves, logs, mods, and the extracted oot.o2r live
# there instead of polluting the build tree.

set -e
cd "$(dirname "$0")"
mkdir -p runDir
cd runDir && ../bldInstall/soh.elf
