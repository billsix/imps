#!/usr/bin/env bash
#
# fetch.sh — get the libultraship source at the pinned commit.
#
# This project dir exists for the reference-documentation crawl
# (tasks/libultraship-reference-docs.md): no patches, no build scripts —
# the games vendor LUS as a submodule; imps documents it.  PIN_SHA
# advances tag by tag as the crawl proceeds, so each checkpoint commit
# records which version the doc state describes.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/Kenix3/libultraship

# Crawl position: tag 1.3.3 (2023-11-15) — iteration 10 of the reference
# crawl.
PIN_SHA=f717dd265aff2eff359de26915d8ad4e498ffdaf

if [ ! -d libultraship ]; then
    git clone "$UPSTREAM" libultraship
fi

# Scaffolding commits made in this checkout (git am of the series, ports,
# rebases) must not require the maintainer's GPG key — disable signing
# repo-locally, never globally.
git -C libultraship config commit.gpgsign false

git -C libultraship checkout "$PIN_SHA"
git -C libultraship submodule update --init --recursive
