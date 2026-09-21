#!/usr/bin/env bash
#
# run.sh — launch PaperBoat.  The binary runs from the BUILD tree (the
# GeneratePortO2R post-build step copies paperboat.o2r and assets/ next to
# the executable, where libultraship looks for them).  runDir/ is the game's
# working directory: config, saves, logs, mods, and the in-app-extracted
# pm64.o2r live there instead of polluting the build tree.
#
# ROM note: PaperBoat needs a supported Paper Mario (US) ROM, extracted
# in-app on first launch into runDir/ (ROMs are out of imps' scope — see the
# repo README).

set -e
cd "$(dirname "$0")"
mkdir -p runDir

BIN="$(pwd)/PaperBoat/build/ninja-release/Paperboat"
if [ ! -x "$BIN" ]; then
    echo "PaperBoat is not built yet — run ./build.sh first." >&2
    exit 1
fi

cd runDir
exec "$BIN"
