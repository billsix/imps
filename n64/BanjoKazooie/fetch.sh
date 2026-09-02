#!/usr/bin/env bash
#
# fetch.sh — get the pristine Lighthouse source at the pinned commit.
#
# Clones upstream if Lighthouse/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (libultraship, Torch).
# Idempotent: a re-run just re-detaches HEAD at the pin; it does not delete
# local branches or discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/Lighthouse.git

# The pinned base commit: tip of upstream's 'develop' branch as of
# 2026-09-01 ("Add project description", shortly after the 1.0.0 release).
PIN_SHA=6d30df9aa9240b2da393d7a8ac1194fcbfc89156

if [ ! -d Lighthouse ]; then
    git clone "$UPSTREAM" Lighthouse
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Lighthouse config commit.gpgsign false

git -C Lighthouse checkout "$PIN_SHA"
git -C Lighthouse submodule update --init --recursive
