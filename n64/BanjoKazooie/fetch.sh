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

# The pinned base commit: tip of upstream's 'develop' branch. Bumped to the
# 2026-10-03 develop HEAD on 2026-10-08 (overnight sweep follow-up,
# tasks/imps-check-upstreams-and-rebase-patches.md): the 4-patch fixOnFedora
# series replays clean; upstream only restructured its CI (consolidated the
# per-OS workflow files into main.yml -- the Dockerfile already mirrors main.yml's
# build-linux job, whose Linux apt list is unchanged) and bumped the project
# version 1.0.0 -> 1.1.0. BUILD + play-test pending (the maintainer's).
# (Was 6d30df9a, the 2026-09-01 develop HEAD after the 1.0.0 release.)
PIN_SHA=5c948c59e046a2a194dfb7e1d7d2b3046b3fbab7

if [ ! -d Lighthouse ]; then
    git clone "$UPSTREAM" Lighthouse
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Lighthouse config commit.gpgsign false

git -C Lighthouse checkout "$PIN_SHA"
git -C Lighthouse submodule update --init --recursive
