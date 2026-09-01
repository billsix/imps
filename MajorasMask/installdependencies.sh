#!/usr/bin/env bash
#
# installdependencies.sh — Fedora build dependencies for 2 Ship 2 Harkinian.
#
# Package list copied from docs/BUILDING.md (Fedora section, gcc line) at
# the imps pin 04a1a4319.  Inlined rather than read at runtime so this
# works before the first fetch.  python3 is added on top: the
# Generate2ShipOtr asset step runs extract_assets.py (CI runners
# pre-provide python; a minimal box may not).
#
# Run as root, or via sudo.

set -e

if ! command -v dnf >/dev/null; then
    echo "This script installs Fedora packages and needs dnf." >&2
    exit 1
fi

# libogg-devel, libvorbis-devel, opus-devel, and opusfile-devel were
# missing from upstream's BUILDING.md Fedora list (found by the
# fresh-container verification; the build hard-requires all four).
# Fixed as patch 0002 of the series, so the PATCHED doc now matches
# this list.
dnf install -y \
    gcc gcc-c++ \
    git cmake ninja-build lsb_release \
    SDL2-devel libpng-devel \
    libzip-devel libzip-tools \
    nlohmann-json-devel tinyxml2-devel spdlog-devel \
    libogg-devel libvorbis-devel opus-devel opusfile-devel \
    python3
