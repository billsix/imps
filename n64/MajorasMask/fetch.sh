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
# Bumped to the develop HEAD of 2026-11-23 on 2026-11-26 (agent sweep,
# ../../tasks/imps-check-upstreams-and-rebase-patches.md); the libultraship gitlink
# is unchanged (7f9b86a5). AppImage build verified 2026-11-26; play-test pending
# (the maintainer's).
# (Was f1dda4c2, bumped 2026-10-19; before that e8757c14.)
PIN_SHA=7e3d051be3f344df026d44f3dee140e76cf226a8

if [ ! -d 2ship2harkinian ]; then
    git clone "$UPSTREAM" 2ship2harkinian
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C 2ship2harkinian config commit.gpgsign false

git -C 2ship2harkinian checkout "$PIN_SHA"
git -C 2ship2harkinian submodule update --init --recursive
