#!/usr/bin/env bash
#
# fetch.sh — get the pristine Ship of Harkinian source at the pinned commit.
#
# Clones upstream if Shipwright/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (libultraship, torch — the
# build fails at cmake configure if torch is empty).  Idempotent: a re-run
# just re-detaches HEAD at the pin; it does not delete local branches or
# discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/Shipwright.git

# The pinned base commit: tip of upstream's 'develop' branch.
# Bumped 41ae6cd3 -> develop HEAD 64df9cb8 (2026-11-23) on 2026-11-26 (third
# sweep, ../../tasks/imps-check-upstreams-and-rebase-patches.md). All three
# streams replay with no conflict: standard-c (36), the rename stream (490, on
# the standard-c tip) and ci-appimage (1). check_renames all, check_patches_apply
# and check_upstreamable_applies green; the standard-c asmdiff tree gate is green
# (486/486 identical). Build + play-test pending. (Was 41ae6cd3, bumped 2026-10-20 from 9.3.0 / ecd889c2.)
PIN_SHA=64df9cb8e3cd1ad0bcae17d6db2cf98b5d3027eb

if [ ! -d Shipwright ]; then
    git clone "$UPSTREAM" Shipwright
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Shipwright config commit.gpgsign false

git -C Shipwright checkout "$PIN_SHA"
git -C Shipwright submodule update --init --recursive
