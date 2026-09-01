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

# The pinned base commit: tip of upstream's 'develop' branch as of
# 2026-09-01 (git describe: 9.2.3-421-gacdbc651d).
PIN_SHA=acdbc651d4b11e29518442d6875a3ec181414cfc

if [ ! -d Shipwright ]; then
    git clone "$UPSTREAM" Shipwright
fi

git -C Shipwright checkout "$PIN_SHA"
git -C Shipwright submodule update --init --recursive
