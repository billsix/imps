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

# The pinned base commit: tip of upstream's 'develop' branch as of
# 2026-09-01.  Notably this is AFTER upstream merged the maintainer's
# always-fly-on-triple-jump cheat (restructured into the events/ layer),
# so that cheat needs no patch here.
PIN_SHA=49c5312a0f3c0a28e1974be1923babd4f869f719

if [ ! -d Ghostship ]; then
    git clone "$UPSTREAM" Ghostship
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Ghostship config commit.gpgsign false

git -C Ghostship checkout "$PIN_SHA"
git -C Ghostship submodule update --init --recursive
