#!/usr/bin/env bash
#
# fetch.sh — get the pristine Luanti engine + Mineclonia game at their pinned commits.
#
# Mineclonia (codeberg.org/mineclonia/mineclonia) is a Lua game: it is not
# compiled, it runs on the Luanti engine (github.com/luanti-org/luanti, C++),
# which is what build.sh compiles. Both are cloned into a gitignored checkout/ and
# detached at their pins. Idempotent: a re-run just re-detaches HEAD at each pin;
# it does not delete local branches or discard committed work.

set -e
cd "$(dirname "$0")"

LUANTI_UPSTREAM=https://github.com/luanti-org/luanti.git
MINECLONIA_UPSTREAM=https://codeberg.org/mineclonia/mineclonia.git

# Pinned base commits (annotated tags → these are the peeled commit SHAs).
#   Luanti tag 5.18.0 (latest stable), resolved 2026-11-07.
LUANTI_PIN_SHA=e8f12bf1b93245cfc479ea21787beb1ec472cce9
#   Mineclonia tag 0.124.1 (needs Luanti >= 5.10, stable releases only), resolved 2026-11-07.
MINECLONIA_PIN_SHA=7410cf18a231b4dd094bd90dc534951ef17b4275

mkdir -p checkout

fetch_one() {
    local dir=$1 upstream=$2 pin=$3
    if [ ! -d "checkout/$dir" ]; then
        git clone "$upstream" "checkout/$dir"
    fi
    # Any scaffolding commit made in a checkout must not need the maintainer's
    # GPG key — disable signing repo-locally, never globally.
    git -C "checkout/$dir" config commit.gpgsign false
    git -C "checkout/$dir" checkout "$pin"
    git -C "checkout/$dir" submodule update --init --recursive
}

fetch_one luanti "$LUANTI_UPSTREAM" "$LUANTI_PIN_SHA"
fetch_one mineclonia "$MINECLONIA_UPSTREAM" "$MINECLONIA_PIN_SHA"
