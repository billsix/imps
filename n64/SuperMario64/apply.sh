#!/usr/bin/env bash
#
# apply.sh — apply the imps patch series on top of the pristine pinned
# checkout.  Run it after fetch.sh (or after build.sh's first-run fetch).
# It refuses to run unless the trees are exactly at their pins, so it cannot
# double-apply a series or stack it onto the wrong base.
#
# TWO lanes (see n64/CLAUDE.md "Patches live in TWO lanes"):
#   1. Game tree      — patches/*.patch              onto Ghostship/
#   2. libultraship   — patches-libultraship/*.patch onto Ghostship/libultraship/
# The submodule is already fetched + checked out at its pin by fetch.sh's
# `git submodule update`, so this just applies its series in place.

set -e
cd "$(dirname "$0")"

# Single source of truth for the game pin is fetch.sh — read it from there.
PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)

if [ "$(git -C Ghostship rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "Ghostship/ is not at the pristine pin ($PIN_SHA)." >&2
    echo "Run ./fetch.sh first, then apply." >&2
    exit 1
fi

# --- Lane 1: game tree ---
git -C Ghostship am --3way "$PWD"/patches/*.patch

# --- Lane 2: libultraship submodule (only if that lane has patches) ---
LUS_DIR="Ghostship/libultraship"
if ls patches-libultraship/*.patch >/dev/null 2>&1; then
    # The submodule's pinned SHA is the gitlink recorded at the game pin.
    LUS_PIN=$(git -C Ghostship rev-parse "$PIN_SHA":libultraship)
    if [ "$(git -C "$LUS_DIR" rev-parse HEAD)" != "$LUS_PIN" ]; then
        echo "$LUS_DIR is not at its pristine pin ($LUS_PIN)." >&2
        echo "Run ./fetch.sh first (it does 'git submodule update'), then apply." >&2
        exit 1
    fi
    # git am commits inside the submodule; the maintainer's gitconfig signs
    # commits, which fails in the sandbox — disable it repo-locally here.
    git -C "$LUS_DIR" config commit.gpgsign false
    git -C "$LUS_DIR" am --3way "$PWD"/patches-libultraship/*.patch
fi
