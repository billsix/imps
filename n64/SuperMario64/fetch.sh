#!/usr/bin/env bash
#
# fetch.sh — get the pristine Ghostship source at the pinned commit.
#
# Clones upstream if Ghostship/ does not exist yet, then checks out the
# pinned commit and initializes its submodules (libultraship, Torch).
# Idempotent: a re-run just re-detaches HEAD at the pin; it does not delete
# local branches or discard committed work.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/HarbourMasters/Ghostship.git

# The pinned base commit: tip of upstream's 'develop' branch. Bumped to the
# 2026-09-10 develop HEAD on 2026-10-08 (overnight sweep follow-up,
# tasks/imps-check-upstreams-and-rebase-patches.md): all 51 game-tree patches
# (standard-c 46 + cheats 3 + book 1 + upstream-candidates 1) AND the
# libultraship doc-region lane replay clean. Derived artifacts unchanged (Linux
# apt list, docs/BUILDING.md, the GeneratePortO2R target). The libultraship
# submodule moves c151cc91 -> 93a1a417 (URL unchanged, Kenix3). BUILD + play-test
# pending (the maintainer's), AND the standard-c codegen-identity re-verification
# (tools/asmdiff.sh per patch) must be re-run once built -- see the task.
# (Was 49c5312a, the 2026-09-01 develop HEAD; still AFTER upstream merged the
# maintainer's always-fly-on-triple-jump cheat, so that cheat needs no patch.)
PIN_SHA=40eef13823a954a466574dc78e73187a17a2dd42

if [ ! -d Ghostship ]; then
    git clone "$UPSTREAM" Ghostship
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C Ghostship config commit.gpgsign false

git -C Ghostship checkout "$PIN_SHA"
git -C Ghostship submodule update --init --recursive
