#!/usr/bin/env bash
#
# installdependencies.sh — Fedora build dependencies for PaperBoat.
#
# Package list translated from the upstream CI (build-linux job in
# .github/workflows/build.yml) at the imps pin 611f5b68, mapping its
# Ubuntu apt line to Fedora packages.  Inlined rather than read at runtime
# so this works before the first fetch.
#
# Deviations from the sibling SuperMario64 (Ghostship) list, all from
# PaperBoat's own CI apt line: SDL2_net-devel (libsdl2-net-dev), fmt-devel
# (libfmt-dev), zlib-devel (zlib1g-dev), bzip2-devel (libbz2-dev), and the
# explicit desktop-OpenGL devel packages (libopengl-dev/libgl1-mesa-dev)
# that PaperBoat's CMakeLists needs for its `find_package(OpenGL REQUIRED)`.
# libshaderc-devel and mbedtls-devel are NOT in PaperBoat's CI apt line, but
# the shared libultraship engine needs them on Fedora (Vulkan backend +
# ixwebsocket) — carried over from the verified Ghostship Fedora build.
#
# Upstream CI builds SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 from
# source only because Ubuntu's packages are too old; Fedora 44's are current
# enough, so we install them from dnf like the other n64/ ports do.
#
# Note: cmake's configure/build also needs network access (libultraship
# fetches gamecontrollerdb.txt).
#
# Run as root, or via sudo.

set -e

if ! command -v dnf >/dev/null; then
    echo "This script installs Fedora packages and needs dnf." >&2
    exit 1
fi

dnf install -y \
    gcc gcc-c++ \
    git cmake ninja-build lsb_release file \
    SDL2-devel SDL2_net-devel libpng-devel \
    libzip-devel libzip-tools \
    nlohmann-json-devel tinyxml2-devel spdlog-devel fmt-devel \
    boost-devel \
    mesa-libGL-devel libglvnd-devel \
    libogg-devel libvorbis-devel \
    zlib-devel bzip2-devel \
    libshaderc-devel mbedtls-devel
