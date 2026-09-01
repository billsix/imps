#!/usr/bin/env bash
#
# build.sh — configure, build, and install 2 Ship 2 Harkinian into
# bldInstall/.  Fetches the pinned source first when 2ship2harkinian/ is
# missing, so a fresh clone of imps needs only this one script to get to a
# built game.

set -e
cd "$(dirname "$0")"

[ -d 2ship2harkinian ] || ./fetch.sh

# Install prefix lives next to this script — no hardcoded home paths.
PREFIX="$(pwd)/bldInstall"

# Generate Ninja project
# Add `-DCMAKE_BUILD_TYPE:STRING=Release` if you're packaging
# Add `-DPython3_EXECUTABLE=$(which python3)` if you are using non-standard Python installations such as PyEnv
cmake -H2ship2harkinian -Bbuild-cmake -GNinja -DCMAKE_INSTALL_PREFIX="$PREFIX"

# Generate 2ship.o2r
cmake --build build-cmake --target Generate2ShipOtr

# Compile the project
# Add `--config Release` if you're packaging
cmake --build build-cmake
cmake --install build-cmake
