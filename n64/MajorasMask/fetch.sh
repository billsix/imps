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

# The pinned base commit: tip of upstream's 'develop' branch as of
# 2026-09-25 ("Update build doc and readme"; develop is unversioned — no tag).
PIN_SHA=e8757c14a0fc8701461b0458c9ed72c118bcfc67

if [ ! -d 2ship2harkinian ]; then
    git clone "$UPSTREAM" 2ship2harkinian
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C 2ship2harkinian config commit.gpgsign false

git -C 2ship2harkinian checkout "$PIN_SHA"
git -C 2ship2harkinian submodule update --init --recursive
