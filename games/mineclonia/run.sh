#!/usr/bin/env bash
#
# run.sh — launch the natively-built Luanti with Mineclonia selected.
# runDir/ holds everything the player creates: luanti.conf (settings, key
# bindings) and worlds/ (saves). Luanti's own install tree (bldInstall/) can be
# rebuilt at will without touching them. Needs a real display + audio.
#
# Usage:  ./run.sh                     # main menu, Mineclonia as the default game
#         ./run.sh --go --world NAME   # straight into runDir/worlds/NAME
#         BUILD_TYPE=Debug ./run.sh
# Extra arguments are passed to luanti as-is.

set -e
cd "$(dirname "$0")"

BUILD_TYPE="${BUILD_TYPE:-Release}"
PREFIX="$(pwd)/bldInstall/$BUILD_TYPE"
LUANTI="$PREFIX/bin/luanti"

if [ ! -x "$LUANTI" ]; then
    echo "No built luanti at $LUANTI — run ./build.sh first." >&2
    exit 1
fi

mkdir -p runDir/worlds
RUN_DIR="$(pwd)/runDir"

# Translate a bare "--world NAME" into runDir/worlds/NAME so saves land in runDir.
args=()
while [ "$#" -gt 0 ]; do
    if [ "$1" = --world ] && [ -n "$2" ] && [ "${2#/}" = "$2" ]; then
        args+=(--world "$RUN_DIR/worlds/$2"); shift 2
    else
        args+=("$1"); shift
    fi
done

# A RUN_IN_PLACE build keeps worlds in <prefix>/worlds; point that at runDir/worlds
# so the main menu lists (and creates) the saves there and a rebuild can't touch
# them. Only a symlink (or nothing) is ever replaced here — never a real directory.
if [ -L "$PREFIX/worlds" ] || [ ! -e "$PREFIX/worlds" ]; then
    ln -sfn "$RUN_DIR/worlds" "$PREFIX/worlds"
else
    echo "warning: $PREFIX/worlds is a real directory; worlds stay there, not in runDir/" >&2
fi

# --config keeps settings in runDir/luanti.conf; --gameid preselects Mineclonia.
cd "$RUN_DIR"
exec "$LUANTI" --config "$RUN_DIR/luanti.conf" --gameid mineclonia "${args[@]}"
