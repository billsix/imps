#!/usr/bin/env bash
#
# fetch.sh — get the pristine Ghostship source at the pinned commit.
#
# Clones upstream if Ghostship/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (libultraship, Torch).
# Idempotent: a re-run just re-detaches HEAD at the pin; it does not delete
# local branches or discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/Ghostship.git

# The pinned base commit: tip of upstream's 'develop' branch. Bumped to the
# 2026-10-27 develop HEAD on 2026-11-26 (third sweep,
# tasks/archive/mario64/2026/11/26/mario64-bump-pin-port-cheats-to-feature-registry.md): standard-c (46) replays
# with one hand resolution and is proven codegen-identical at this pin (104 of 104
# files); the three cheats were ported onto upstream's feature registry; the book
# markers were re-anchored in math_util.h; ci-appimage needed the usual workflow
# resolution; the fedora-shaderc-deps patch was dropped (upstream documents the
# dependency now). The libultraship submodule moves 93a1a417 -> 37daaa66 and Torch
# 106621f0 -> f83dfb3b. AppImage build verified 2026-11-26; play-test pending
# (the maintainer's).
# (Was 40eef138, bumped 2026-10-08; still AFTER upstream merged the maintainer's
# always-fly-on-triple-jump cheat, so that cheat needs no patch.)
PIN_SHA=aefb89b85e7b78daff62b491ebb2669d2d9270f0

if [ ! -d Ghostship ]; then
    git clone "$UPSTREAM" Ghostship
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Ghostship config commit.gpgsign false

git -C Ghostship checkout "$PIN_SHA"
git -C Ghostship submodule update --init --recursive
