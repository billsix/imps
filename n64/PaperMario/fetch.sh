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

# The pinned base commit: the stable release tag 1.0.3.
# Bumped 1.0.2 -> 1.0.3 on 2026-10-20 (agent resync,
# tasks/imps-check-upstreams-and-rebase-patches.md): PaperMario is tag-pinned
# (newest tagged release), NOT tip-of-develop.  The game-tree lane (2 patches)
# replays CLEAN onto 1.0.3 (Engine.cpp changed elsewhere, not in the patched
# regions).  The libultraship-lane Vulkan fix is DROPPED at this bump: upstream
# (JeodC lus-converge) independently implemented the identical null-Context
# guard (vk_resource_manager() + ConsoleVariables() with a Context fallback,
# same call-site rewrites incl. DrawTriangles), so the patch is absorbed — see
# PaperMario/CLAUDE.md.  config.yml (ROM hashes) and the ninja-release preset
# are unchanged; the CI apt line now lists libvulkan-dev/glslang-dev/spirv-tools
# explicitly (installdependencies.sh covers these via libshaderc-devel + the
# Fedora Vulkan stack).  Submodules at 1.0.3: external/libultraship moves
# 3e3cd2ed -> 7f1bd60e (JeodC fork), external/torch is UNCHANGED (72960ca1,
# HarbourMasters/Torch); apply.sh derives both from the pin's tree, so only this
# SHA changes here.  BUILD + play-test pending (the maintainer's).
PIN_SHA=7f038b8552b1bf5c297a5fd06738d8f245851833

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
