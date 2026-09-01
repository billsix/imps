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
# 2026-05-31 ("Lazy load sort DL Viewer unfiltered results (#1718)").
PIN_SHA=04a1a43197f067afd60a9043512755edc14f4f19

if [ ! -d 2ship2harkinian ]; then
    git clone "$UPSTREAM" 2ship2harkinian
fi

git -C 2ship2harkinian checkout "$PIN_SHA"
git -C 2ship2harkinian submodule update --init --recursive
