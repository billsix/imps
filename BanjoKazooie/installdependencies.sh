#!/usr/bin/env bash
#
# installdependencies.sh — Fedora build dependencies for Lighthouse.
#
# Package list copied from docs/BUILDING.md (Fedora section, gcc line) at
# the imps pin 6d30df9a WITH the patch series applied — patch 0001 of the
# series is the maintainer's own upstream fix adding SDL2_net to this very
# line.  Inlined rather than read at runtime so this works before the
# first fetch.
#
# Environments without SDL2_net can instead configure the build with
# -DUSE_NETWORKING=OFF.
#
# Run as root, or via sudo.

set -e

if ! command -v dnf >/dev/null; then
    echo "This script installs Fedora packages and needs dnf." >&2
    exit 1
fi

dnf install -y \
    gcc gcc-c++ \
    git cmake ninja-build lsb_release \
    SDL2-devel SDL2_net SDL2_net-devel libpng-devel \
    libzip-devel libzip-tools \
    nlohmann-json-devel tinyxml2-devel spdlog-devel \
    boost-devel libogg-devel libvorbis-devel
