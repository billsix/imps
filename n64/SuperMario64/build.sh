#!/usr/bin/env bash
#
# build.sh — configure, build, and install Ghostship into bldInstall/.
# Fetches the pinned source first when Ghostship/ is missing, so a fresh
# clone of imps needs only this one script to get to a built game.
#
# Deliberately does NOT run the ExtractAssets target: it requires a
# baserom.us.z64 placed in the Ghostship/ source root (ROMs are out of
# imps' scope).  The game's first run extracts sm64.o2r in-app instead.
#
# Caveat: cmake configure downloads gamecontrollerdb.txt from GitHub, so
# the configure step needs network.

set -e
cd "$(dirname "$0")"

[ -d Ghostship ] || ./fetch.sh

# Install prefix lives next to this script — no hardcoded home paths.
PREFIX="$(pwd)/bldInstall"

# Generate Ninja project
# Add `-DCMAKE_BUILD_TYPE:STRING=Release` if you're packaging
cmake -HGhostship -Bbuild-cmake -GNinja -DCMAKE_INSTALL_PREFIX="$PREFIX"

# Generate ghostship.o2r (port-side assets; no ROM needed)
cmake --build build-cmake --target GeneratePortO2R

# Compile the project
# Add `--config Release` if you're packaging
cmake --build build-cmake
cmake --install build-cmake
