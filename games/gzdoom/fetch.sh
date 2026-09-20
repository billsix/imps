#!/usr/bin/env bash
#
# fetch.sh — get the pristine GZDoom + ZMusic sources at their pinned commits.
#
# GZDoom (github.com/ZDoom/gzdoom) is the Doom-engine source port we carry; it
# links against ZMusic (github.com/ZDoom/ZMusic), which must be built first.
# Both are cloned into a gitignored checkout/ and detached at their pins, then
# their submodules are initialized.  Idempotent: a re-run just re-detaches HEAD
# at each pin; it does not delete local branches or discard committed work.

set -e
cd "$(dirname "$0")"

GZDOOM_UPSTREAM=https://github.com/ZDoom/gzdoom.git
ZMUSIC_UPSTREAM=https://github.com/ZDoom/ZMusic.git

# Pinned base commits (lightweight tags → the SHA is the commit itself).
#   GZDoom tag g4.14.2, resolved 2026-09-20.
GZDOOM_PIN_SHA=99aa489d09015a95bb78df2b30ede29f328cc874
#   ZMusic tag 1.3.0, resolved 2026-09-20.
ZMUSIC_PIN_SHA=95efd37ca0832855a9afd8af48c74c389d614ae5

mkdir -p checkout

fetch_one() {
    local dir=$1 upstream=$2 pin=$3
    if [ ! -d "checkout/$dir" ]; then
        git clone "$upstream" "checkout/$dir"
    fi
    # Scaffolding commits made here (git am of the series, rebases) must not
    # require the maintainer's GPG key — disable signing repo-locally, never
    # globally (a failed signature aborts `git am` mid-series).
    git -C "checkout/$dir" config commit.gpgsign false
    git -C "checkout/$dir" checkout "$pin"
    git -C "checkout/$dir" submodule update --init --recursive
}

fetch_one gzdoom "$GZDOOM_UPSTREAM" "$GZDOOM_PIN_SHA"
fetch_one zmusic "$ZMUSIC_UPSTREAM" "$ZMUSIC_PIN_SHA"
