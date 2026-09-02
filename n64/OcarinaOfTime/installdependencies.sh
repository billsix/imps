#!/usr/bin/env bash
#
# installdependencies.sh — Fedora build dependencies for Ship of Harkinian.
#
# Package list copied from the checkout's own linux-build-deps/dnf.txt plus
# the `gcc gcc-c++` prefix from docs/BUILDING.md (Fedora section), at the
# imps pin acdbc651d.  Inlined rather than read at runtime so this works
# before the first fetch.  python3 is added on top: the GenerateSohOtr
# asset step runs extract_assets.py (CI runners pre-provide python; a
# minimal box may not).
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
    SDL2-devel SDL2_net-devel libpng-devel \
    libzip-devel libzip-tools \
    nlohmann-json-devel tinyxml2-devel spdlog-devel \
    opusfile-devel libvorbis-devel \
    python3
