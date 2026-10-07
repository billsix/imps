#!/usr/bin/env bash
#
# fetch.sh — get the pristine PaperBoat source at the pinned commit.
#
# Clones upstream if PaperBoat/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (external/libultraship,
# external/torch).  Idempotent: a re-run just re-detaches HEAD at the pin;
# it does not delete local branches or discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/PaperBoat.git

# The pinned base commit: the stable release tag 1.0.2.
# Bumped 1.0.1 -> 1.0.2 on 2026-10-08 (overnight sweep follow-up,
# tasks/imps-check-upstreams-and-rebase-patches.md): PaperMario is tag-pinned
# (newest tagged release), NOT tip-of-develop.  Both patch lanes replay clean
# onto 1.0.2 (game-tree + the libultraship-lane Vulkan fix, still unmerged
# upstream); config.yml (ROM hashes) is unchanged, the CMakeLists change is
# internal to the o2r-staging step (build.sh uses the ninja-release preset, so
# it is unaffected), and the CI dep list is unchanged.  The external/libultraship
# submodule moves 7aa03b6c -> 3e3cd2ed with the tag; apply.sh derives that from
# the pin's tree, so only this SHA changes here.  BUILD + play-test pending
# (the maintainer's).  tip-of-develop (newer, unreleased) is the alternative if
# the latest gameplay fixes are wanted.
PIN_SHA=b721efd6b5ad6dce9cdef25a6b93b2fdc8b04309

if [ ! -d PaperBoat ]; then
    git clone "$UPSTREAM" PaperBoat
fi

# Scaffolding commits made in this checkout (a future git am of a series,
# ports, rebases) must not require the maintainer's GPG key — disable
# signing repo-locally, never globally.  The submodules are their own git
# repos, so disable it in theirs too (a signed submodule commit would abort
# a git am mid-series in the libultraship lane).
git -C PaperBoat config commit.gpgsign false

git -C PaperBoat checkout "$PIN_SHA"
# A pin bump can change a submodule's URL (the 1.0.1 -> 1.0.2 bump moved torch
# from the JeodC fork to upstream HarbourMasters/Torch); `sync` rewrites each
# already-initialized submodule's remote from the checked-out .gitmodules before
# `update`, so it fetches from the new remote instead of the stale one.
git -C PaperBoat submodule sync --recursive
git -C PaperBoat submodule update --init --recursive

# At 1.0.2 PaperBoat pins external/libultraship to the JeodC fork (branch
# lus-converge) but external/torch to upstream HarbourMasters/Torch (branch
# main) — torch moved upstream from the JeodC/Torch-LH `pm64` fork at this tag
# (see .gitmodules); the `submodule sync` above picks up that URL change.
git -C PaperBoat submodule foreach --recursive \
    'git config commit.gpgsign false || true'
