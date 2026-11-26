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
# Bumped to the develop HEAD of 2026-11-16 on 2026-11-26 (agent sweep,
# tasks/imps-check-upstreams-and-rebase-patches.md): both streams apply
# (tools/check_patches_apply.sh BanjoKazooie green); the libultraship gitlink moved
# 62e973ae -> 92ed57bc and Torch 72960ca1 -> 7f5d55f9; the project version is 1.2.2.
# BUILD + play-test pending. (Was 4e8dfd23, bumped 2026-10-19; before that 5c948c59.)
PIN_SHA=f757b547c8996ad0d67647560098c76bac0898a6

if [ ! -d Lighthouse ]; then
    git clone "$UPSTREAM" Lighthouse
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Lighthouse config commit.gpgsign false

git -C Lighthouse checkout "$PIN_SHA"
git -C Lighthouse submodule update --init --recursive
