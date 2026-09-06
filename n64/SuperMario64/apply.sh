#!/usr/bin/env bash
#
# apply.sh — apply the imps patch STREAMS on top of the pristine pinned checkout.
# Run after fetch.sh (or after build.sh's first-run fetch).
#
# Patches are grouped into purpose STREAMS (subfolders): cheats, book (doc-region
# markers), upstream-candidates, etc. WITHIN a stream, order matters (numbered).
# ACROSS streams it does NOT — the streams touch disjoint files and therefore
# commute, so there is no total ordering to maintain. See SuperMario64/CLAUDE.md.
#
# Two lanes (n64/CLAUDE.md "Patches live in TWO lanes"), each streamed:
#   game tree     patches/<stream>/*.patch              -> Ghostship/
#   libultraship  patches-libultraship/<stream>/*.patch -> Ghostship/libultraship/

set -e
cd "$(dirname "$0")"

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)
if [ "$(git -C Ghostship rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "Ghostship/ is not at the pristine pin ($PIN_SHA). Run ./fetch.sh first." >&2
    exit 1
fi

# --- Lane 1: game tree — apply each stream (subfolder), in-folder order ---
for stream in patches/*/; do
    if ls "$stream"*.patch >/dev/null 2>&1; then
        echo "apply game-tree stream: $stream"
        git -C Ghostship am --3way "$PWD/$stream"*.patch
    fi
done

# --- Lane 2: libultraship submodule — apply each stream (if the lane has any) ---
LUS_DIR="Ghostship/libultraship"
if ls patches-libultraship/*/*.patch >/dev/null 2>&1; then
    LUS_PIN=$(git -C Ghostship rev-parse "$PIN_SHA":libultraship)
    if [ "$(git -C "$LUS_DIR" rev-parse HEAD)" != "$LUS_PIN" ]; then
        echo "$LUS_DIR is not at its pristine pin ($LUS_PIN). Run ./fetch.sh first." >&2
        exit 1
    fi
    # git am commits inside the submodule; signing fails in the sandbox — off it.
    git -C "$LUS_DIR" config commit.gpgsign false
    for stream in patches-libultraship/*/; do
        if ls "$stream"*.patch >/dev/null 2>&1; then
            echo "apply libultraship stream: $stream"
            git -C "$LUS_DIR" am --3way "$PWD/$stream"*.patch
        fi
    done
fi
