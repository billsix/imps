#!/usr/bin/env bash
#
# installdependencies.sh — install GZDoom's + ZMusic's build dependencies on the
# HOST (Fedora, dnf). Run as root, or via sudo. The package list is inlined (not
# read from the checkout) so this works on a bare machine BEFORE the first fetch.
#
# This is the native-build counterpart of the Dockerfile's dnf install: the same
# set, MINUS the container-only headless-smoke deps (xorg-x11-server-Xvfb,
# mesa-dri-drivers) — a real host already has its own display/GPU/GL. Keep this in
# sync with the Dockerfile when the dependency list changes.
#
#   toolchain           gcc-c++ cmake make git ninja-build pkgconf-pkg-config
#   core libs           SDL2 zlib libjpeg-turbo bzip2
#   audio               openal-soft fluidsynth  (ZMusic backends)
#   video (cutscenes)   libvpx  (GZDoom 4.14 cmake/FindVPX.cmake)
#   GL / Vulkan render  mesa-libGL vulkan-loader vulkan-headers
#   IWAD-picker GUI     gtk3  (GZDoom's GTK startup dialog on Linux)

set -e

if ! command -v dnf >/dev/null; then
    echo "This script installs Fedora packages and needs dnf." >&2
    exit 1
fi

# One dnf call, so its own exit status is the gate.
dnf install -y \
    gcc-c++ cmake make git ninja-build pkgconf-pkg-config \
    SDL2-devel zlib-devel libjpeg-turbo-devel bzip2-devel \
    openal-soft-devel fluidsynth-devel \
    libvpx-devel \
    mesa-libGL-devel vulkan-loader-devel vulkan-headers \
    gtk3-devel
