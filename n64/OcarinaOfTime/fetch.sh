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
# Bumped from 9.3.0 (ecd889c2, 2026-10-06) -> develop HEAD 41ae6cd3 on 2026-10-20
# (agent resync, ../../tasks/imps-check-upstreams-and-rebase-patches.md). The
# standard-c stream (36) replays byte-clean onto the new base; the rename stream
# was RE-CUT onto it (resolve_rename_conflicts.py: 2 conflicts / 8 blocks, all
# mechanical) + a new tail patch reconciling one develop-new reference
# (func_800FA0B4 -> Audio_GetActiveSeqId). check_renames all green,
# check_patches_apply green. asmdiff codegen gate + build + play-test pending.
PIN_SHA=41ae6cd3b68c7cf1855bd865f3d00bd2013667da

if [ ! -d Shipwright ]; then
    git clone "$UPSTREAM" Shipwright
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Shipwright config commit.gpgsign false

git -C Shipwright checkout "$PIN_SHA"
git -C Shipwright submodule update --init --recursive
