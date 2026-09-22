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

# The pinned base commit: the stable release tag 1.0.1 (dated 2026-09-18).
# NOTE: 1.0.1 vs tip-of-develop does NOT affect ROM O2R extraction — the
# extraction code (Engine.cpp, GameExtractor, Torch pin) is byte-identical
# between them, and the one libultraship-commit difference is HD-art
# rendering only.  The "extraction does nothing" symptom was a ROM problem,
# not a pin problem (see CLAUDE.md "ROM requirements").  1.0.1 is pinned
# simply because it is the newest tagged release; tip-of-develop
# (611f5b685750e3e7f3a99eefe90fd874e8f1eb7b) is the alternative if the newer
# gameplay fixes are wanted.  First step for this port is a pristine
# compile-as-is — no patches carried yet.
PIN_SHA=424c220f0863c29b9fe55cc674baceff88e9e14f

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
git -C PaperBoat submodule update --init --recursive

# PaperBoat pins JeodC forks for both submodules (see docs/BUILDING.md and
# .gitmodules): external/libultraship on branch lus-converge, external/torch
# on branch pm64 — distinct from the other n64/ ports' engine pins.
git -C PaperBoat submodule foreach --recursive \
    'git config commit.gpgsign false || true'
