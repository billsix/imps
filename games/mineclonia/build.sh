#!/usr/bin/env bash
#
# build.sh — native (no container) host build of the Luanti engine, with the
# Mineclonia game installed into it. Builds out of source into
# build-cmake/<BUILD_TYPE>/ and installs a self-contained RUN_IN_PLACE tree into
# bldInstall/<BUILD_TYPE>/ (bin/luanti beside builtin/, textures/, games/ …).
# Fetches the pinned sources first when the checkout is missing, so — together
# with installdependencies.sh — this one script is all a fresh clone needs.
#
# Usage:  ./build.sh                 # Release (default)
#         BUILD_TYPE=Debug ./build.sh
#
# RUN_IN_PLACE=TRUE makes Luanti resolve its data relative to the binary's parent
# directory, so the install prefix works wherever it sits (no absolute path baked
# in, unlike a system install). The player's worlds and config live in runDir/,
# not here — see run.sh.

set -e
cd "$(dirname "$0")"

BUILD_TYPE="${BUILD_TYPE:-Release}"

# Only the source fetch is a prerequisite; get it if it is not here yet.
[ -d checkout/luanti ] && [ -d checkout/mineclonia ] || ./fetch.sh

# Everything lives beside this script — no hardcoded home paths.
PREFIX="$(pwd)/bldInstall/$BUILD_TYPE"
# BUILD_ROOT separates CMake caches by environment: a cache records absolute
# paths, so the container build (Makefile: BUILD_ROOT=build-container) and a host
# build must not share one.
BUILD="$(pwd)/${BUILD_ROOT:-build-cmake}/$BUILD_TYPE/luanti"

cmake -S checkout/luanti -B "$BUILD" -G Ninja \
      -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
      -DRUN_IN_PLACE=TRUE -DBUILD_SERVER=FALSE -DBUILD_UNITTESTS=FALSE
cmake --build "$BUILD" -j"$(nproc)"
cmake --install "$BUILD"

# Install the game: a fresh copy of the pinned tree (minus its .git) into the
# engine's games/ dir. A copy, not a symlink, so the install is self-contained.
rm -rf "$PREFIX/games/mineclonia"
mkdir -p "$PREFIX/games"
git -C checkout/mineclonia archive --format=tar --prefix=mineclonia/ HEAD \
    | tar -x -C "$PREFIX/games"

echo "==> built luanti + mineclonia: bldInstall/$BUILD_TYPE/bin/luanti"
