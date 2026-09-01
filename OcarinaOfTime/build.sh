#!/usr/bin/env bash
#
# build.sh — configure, build, and install Ship of Harkinian into bldInstall/.
# Fetches the pinned source first when Shipwright/ is missing, so a fresh
# clone of imps needs only this one script to get to a built game.

set -e
cd "$(dirname "$0")"

[ -d Shipwright ] || ./fetch.sh

# Install prefix lives next to this script — no hardcoded home paths.
PREFIX="$(pwd)/bldInstall"

# Generate Ninja project
# Add `-DCMAKE_BUILD_TYPE:STRING=Release` if you're packaging
# Add `-DSUPPRESS_WARNINGS=0` to prevent suppression of warnings from LUS and decomp (src) files. set to 1 to re-enable suppression
# Add `-DPython3_EXECUTABLE=$(which python3)` if you are using non-standard Python installations such as PyEnv
cmake -HShipwright -Bbuild-cmake -GNinja -DCMAKE_INSTALL_PREFIX="$PREFIX"

# Generate soh.o2r
cmake --build build-cmake --target GenerateSohOtr

# Compile the project
# Add `--config Release` if you're packaging
cmake --build build-cmake
cmake --install build-cmake
