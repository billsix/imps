#!/usr/bin/env bash
#
# installdependencies.sh — Fedora build dependencies for Ghostship.
#
# Package list copied from docs/building.md (Fedora section, gcc line) at
# the imps pin 49c5312a WITH the patch series applied — patch 0004 of the
# series is the maintainer's fix adding libshaderc-devel to this very line
# (the libultraship Vulkan backend needs shaderc headers).  Inlined rather
# than read at runtime so this works before the first fetch.
#
# Note: cmake's configure step also needs network access (it downloads
# gamecontrollerdb.txt).
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
    SDL2-devel libshaderc-devel libpng-devel \
    libzip-devel libzip-tools \
    nlohmann-json-devel tinyxml2-devel spdlog-devel \
    boost-devel libogg-devel libvorbis-devel mbedtls-devel
