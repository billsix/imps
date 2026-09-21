#!/usr/bin/env bash
#
# run.sh — launch the natively-built GZDoom with a WAD passed on the command line.
# runDir/ is GZDoom's working directory: gzdoom.ini, saves, screenshots, and any
# downloaded content accumulate there instead of polluting the source/build tree
# or $HOME. Needs a real display (X11/Wayland) and audio, which the host provides.
#
# Usage:  ./run.sh /path/to/DOOM2.WAD [extra gzdoom args, e.g. -file my_mod.wad]
#         BUILD_TYPE=Debug ./run.sh /path/to/DOOM2.WAD
#
# WADs/IWADs are the maintainer's own game data — passed at run time, never
# committed, and their location is not recorded here.

set -e
cd "$(dirname "$0")"

BUILD_TYPE="${BUILD_TYPE:-Release}"
PREFIX="$(pwd)/bldInstall/$BUILD_TYPE"
GZDOOM="$PREFIX/bin/gzdoom"

if [ ! -x "$GZDOOM" ]; then
    echo "No built gzdoom at $GZDOOM — run ./build.sh first." >&2
    exit 1
fi
if [ -z "$1" ]; then
    echo "usage: ./run.sh /path/to/base.wad [extra gzdoom args...]" >&2
    exit 2
fi

WAD="$1"; shift
[ -f "$WAD" ] || { echo "WAD not found: $WAD" >&2; exit 2; }
# Resolve to an absolute path BEFORE cd'ing into runDir/, so a relative WAD works.
WAD="$(cd "$(dirname "$WAD")" && pwd)/$(basename "$WAD")"

mkdir -p runDir

# libzmusic.so.1 lives in the prefix, not a system dir — point the loader at it.
export LD_LIBRARY_PATH="$PREFIX/lib64:$PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Run from runDir/ so GZDoom writes its config/saves there, not the repo root.
cd runDir
exec "$GZDOOM" -iwad "$WAD" "$@"
