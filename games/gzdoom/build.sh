#!/usr/bin/env bash
#
# build.sh — native (no container) host build of GZDoom + its ZMusic dependency.
# Configures, builds, and installs both with CMake/Ninja into a prefix beside this
# script (bldInstall/<BUILD_TYPE>/). Fetches the pinned source first when the
# checkout is missing, so — together with installdependencies.sh — this one script
# is all a fresh clone needs to reach a built game.
#
# Usage:  ./build.sh                 # Release (default)
#         BUILD_TYPE=Debug ./build.sh
#
# Run ./installdependencies.sh once first (Fedora build deps). The container path
# (make image && make build) is the alternative; this is the native baseline.

set -e
cd "$(dirname "$0")"

BUILD_TYPE="${BUILD_TYPE:-Release}"

# Only the source fetch is a prerequisite; get it if it is not here yet.
[ -d checkout/gzdoom ] || ./fetch.sh

# Everything lives beside this script — no hardcoded home paths. Each BUILD_TYPE
# gets its own build + install subtree so Release and Debug never clobber.
PREFIX="$(pwd)/bldInstall/$BUILD_TYPE"
ZMUSIC_BUILD="$(pwd)/build-cmake/$BUILD_TYPE/zmusic"
GZDOOM_BUILD="$(pwd)/build-cmake/$BUILD_TYPE/gzdoom"
NPROC="$(nproc)"

# ZMusic first, installed into the shared prefix so GZDoom's FindZMusic.cmake
# locates it via CMAKE_PREFIX_PATH.
cmake -S checkout/zmusic -B "$ZMUSIC_BUILD" -G Ninja \
      -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
cmake --build "$ZMUSIC_BUILD" -j"$NPROC"
cmake --install "$ZMUSIC_BUILD"

# GZDoom. -DSYSTEMINSTALL=ON bakes PROGDIR=<prefix>/share/games/doom into the
# binary so it finds its own gzdoom.pk3 (and the other resource .pk3s) from this
# non-standard prefix; without it GZDoom only looks next to the binary and in
# /usr/share, cannot find gzdoom.pk3, and drops to the GTK IWAD picker. PROGDIR is
# an ABSOLUTE path, so this host-built binary must run on this host — which is why
# the native build exists (the container build bakes /work/... and won't run here).
cmake -S checkout/gzdoom -B "$GZDOOM_BUILD" -G Ninja \
      -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
      -DCMAKE_PREFIX_PATH="$PREFIX" -DSYSTEMINSTALL=ON
cmake --build "$GZDOOM_BUILD" -j"$NPROC"
cmake --install "$GZDOOM_BUILD"

echo "==> built gzdoom: bldInstall/$BUILD_TYPE/bin/gzdoom"
