#!/usr/bin/env bash
#
# fetch.sh — get the pristine 2 Ship 2 Harkinian source at the pinned commit.
#
# Clones upstream if 2ship2harkinian/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (libultraship, ZAPDTR,
# OTRExporter).  Idempotent: a re-run just re-detaches HEAD at the pin; it
# does not delete local branches or discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/2ship2harkinian.git

# The pinned base commit: tip of upstream's 'develop' branch (unversioned — no tag).
# Re-bumped to the current develop HEAD on 2026-10-19 (agent resync,
# ../../tasks/imps-check-upstreams-and-rebase-patches.md); the libultraship gitlink
# is unchanged (7f9b86a5). BUILD + play-test pending (the maintainer's).
# (Was e8757c14, the 2026-09-25 develop HEAD bumped 2026-10-08.)
PIN_SHA=f1dda4c28cb9ed7cc80d8c78337ee31a8d2c7d0e

if [ ! -d 2ship2harkinian ]; then
    git clone "$UPSTREAM" 2ship2harkinian
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C 2ship2harkinian config commit.gpgsign false

git -C 2ship2harkinian checkout "$PIN_SHA"
git -C 2ship2harkinian submodule update --init --recursive
