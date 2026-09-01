#!/usr/bin/env bash
#
# build.sh — configure, build, and install Lighthouse into bldInstall/.
# Fetches the pinned source first when Lighthouse/ is missing, so a fresh
# clone of imps needs only this one script to get to a built game.
#
# Deliberately does NOT run the ExtractAssets target: it requires a
# baserom.z64 placed in the Lighthouse/ source root (ROMs are out of imps'
# scope).  The game's first run extracts bk.o2r in-app instead.

set -e
cd "$(dirname "$0")"

[ -d Lighthouse ] || ./fetch.sh

# Install prefix lives next to this script — no hardcoded home paths.
PREFIX="$(pwd)/bldInstall"

# Generate Ninja project
# Add `-DCMAKE_BUILD_TYPE:STRING=Release` if you're packaging
cmake -HLighthouse -Bbuild-cmake -GNinja -DCMAKE_INSTALL_PREFIX="$PREFIX"

# Generate lighthouse.o2r (port-side assets; no ROM needed)
cmake --build build-cmake --target GeneratePortO2R

# Compile the project
# Add `--config Release` if you're packaging
cmake --build build-cmake
cmake --install build-cmake

# The game loads its archives from the current working directory, and run.sh
# runs from runDir/ — put the port archive there (bk.o2r arrives via the
# in-app extraction on first run).
mkdir -p runDir
cp build-cmake/lighthouse.o2r runDir/
