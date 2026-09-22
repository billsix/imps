#!/usr/bin/env bash
#
# run.sh [ROM] — launch PaperBoat, optionally importing a Paper Mario ROM on
# this launch.
#
#   ./run.sh                       # play (pm64.o2r already in runDir/)
#   ./run.sh /path/to/PaperMario.z64   # verify the ROM, extract it, then play
#
# The binary runs from the BUILD tree (the GeneratePortO2R post-build step
# copies paperboat.o2r and assets/ next to the executable, where libultraship
# looks for them).  runDir/ is the game's working directory: config, saves,
# logs, mods, and the ROM-extracted pm64.o2r live there instead of polluting
# the build tree.
#
# ROM: the in-app extractor accepts a file only if its whole-file SHA-1 is a
# key in PaperBoat/config.yml (the 40 MB US ROM).  Before handing the file
# over, this script checks that hash itself and, for the one common failure —
# an over-dumped cart, i.e. the game plus trailing padding — trims a copy to
# the recipe size into runDir/ and imports that.  Any other mismatch stops
# here with the expected hash, instead of a silent "No ROM O2R" in the app.
# The ROM path reaches the app on the command line, which the imps patch
# `extractor-cli-rom-on-linux` makes work on Linux (upstream only reads argv
# on Windows).  ROMs themselves stay out of imps' scope — see the repo README.

set -e
cd "$(dirname "$0")"
mkdir -p runDir

BIN="$(pwd)/PaperBoat/build/ninja-release/Paperboat"
if [ ! -x "$BIN" ]; then
    echo "PaperBoat is not built yet — run ./build.sh first." >&2
    exit 1
fi

# The hashes config.yml has recipes for (one today: the US ROM), read from the
# built tree so a pin bump that adds a version needs no edit here.
CONFIG="$(dirname "$BIN")/config.yml"
supported_hashes() {
    sed -n 's/^\([0-9a-f]\{40\}\):.*/\1/p' "$CONFIG"
}

# import_rom SRC -> prints the path to hand to the app, or fails with a reason.
import_rom() {
    local src=$1 hash size trimmed
    [ -f "$src" ] || { echo "ROM not found: $src" >&2; return 1; }
    hash=$(sha1sum "$src" | cut -c1-40)
    if supported_hashes | grep -qx "$hash"; then
        echo "$src"
        return 0
    fi
    # Over-dump? The US ROM is 41943040 bytes (40 MB); if that prefix of a
    # longer file hashes to a recipe, only padding followed it.
    size=$(stat -c %s "$src")
    cut=41943040
    if [ "$size" -gt "$cut" ]; then
        hash=$(head -c "$cut" "$src" | sha1sum | cut -c1-40)
        if supported_hashes | grep -qx "$hash"; then
            trimmed="$(pwd)/runDir/pm64.z64"
            echo "ROM is $size bytes with a supported $cut-byte image at the front (padded cart" >&2
            echo "dump); writing the trimmed copy to $trimmed" >&2
            head -c "$cut" "$src" > "$trimmed"
            echo "$trimmed"
            return 0
        fi
    fi
    {
        echo "ROM rejected: $src"
        echo "  size $size bytes, SHA-1 $(sha1sum "$src" | cut -c1-40)"
        echo "  PaperBoat's config.yml accepts (whole-file SHA-1):"
        supported_hashes | sed 's/^/    /'
        echo "  Wanted: the US Paper Mario ROM, big-endian .z64 (starts 80 37 12 40), 41943040 bytes."
        echo "  A byte-swapped .n64/.v64 hashes differently — convert it; a dump padded past 40 MB"
        echo "  is trimmed automatically only if its first 40 MB match."
    } >&2
    return 1
}

ROM_ARGS=()
if [ "$#" -ge 1 ]; then
    ROM_ARGS=("$(import_rom "$1")")
fi

cd runDir

# Default to the OpenGL renderer on first launch.  libultraship registers
# Vulkan before OpenGL on Linux and picks the front of that list when no
# config exists, and PaperBoat's Vulkan backend crashes on its first shader
# build (Fast::BuildVulkanShader -> ResourceManager::LoadResource, SIGSEGV —
# seen on the maintainer's RADV host and under Xvfb/lavapipe alike).  Seed the
# config to select OpenGL (Window.Backend.Id 2 = FAST3D_SDL_OPENGL in this LUS
# fork) only when no config exists yet, so a first run is safe while a later
# in-menu switch is preserved.  Same approach as SuperMario64/run.sh.
if [ ! -f paperboat.cfg.json ]; then
    cat > paperboat.cfg.json <<'JSON'
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

exec "$BIN" ${ROM_ARGS[@]+"${ROM_ARGS[@]}"}
