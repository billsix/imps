#!/usr/bin/env bash
#
# installdependencies.sh — install Luanti's build dependencies on the HOST
# (Fedora, dnf). Run as root, or via sudo. The list is inlined (not read from the
# checkout) so this works on a bare machine BEFORE the first fetch. Mineclonia
# itself is Lua + assets and needs nothing.
#
# Source: the "For Fedora users" list in Luanti 5.18.0's doc/compiling/linux.md,
# minus kernel-devel/automake (not used by the CMake build), plus git and
# ninja-build. This is the native-build counterpart of the Dockerfile's dnf
# install: the same set MINUS the container-only headless-smoke deps
# (xorg-x11-server-Xvfb, mesa-dri-drivers). Keep the two in sync.
#
#   toolchain        gcc gcc-c++ cmake make git ninja-build gettext
#   engine libs      SDL2 freetype libpng libjpeg zlib libzstd libzip sqlite
#   scripting        luajit  (else Luanti falls back to its bundled Lua 5.1)
#   bundled-if-absent jsoncpp gmp
#   audio            openal-soft libvorbis libogg
#   network/storage  libcurl leveldb spatialindex ncurses
#   rendering        mesa-libGL

set -e

if ! command -v dnf >/dev/null; then
    echo "This script installs Fedora packages and needs dnf." >&2
    exit 1
fi

# One dnf call, so its own exit status is the gate.
dnf install -y \
    gcc gcc-c++ cmake make git ninja-build gettext \
    SDL2-devel freetype-devel libpng-devel libjpeg-devel zlib-devel \
    libzstd-devel libzip-devel sqlite-devel \
    luajit-devel jsoncpp-devel gmp-devel \
    openal-soft-devel libvorbis-devel libogg-devel \
    libcurl-devel leveldb-devel spatialindex-devel ncurses-devel \
    mesa-libGL-devel
