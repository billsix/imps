#!/usr/bin/env bash
#
# warm-cargo-cache.sh — bake ripgrep's Cargo dependency graph into CARGO_HOME at
# IMAGE-BUILD time, so an EXPORTED image builds ripgrep with the network cut
# (`cargo build --offline`) years later. This is the Cargo analogue of how
# modelviewprojection bakes pip deps into a committed /venv layer, and of the
# Fossify sibling's Gradle warm (android/fossify/entrypoint/warm-gradle-cache.sh):
# the deps land in a committed image layer (CARGO_HOME=/opt/cargo-cache) instead
# of being fetched on the first `make build`.
#
# The chicken-and-egg (same as the Gradle sibling): the ripgrep checkout is
# fetched at RUNTIME (gitignored), so at image-build there is no
# Cargo.toml/Cargo.lock to resolve against. Fix: clone ripgrep at the SAME pin
# fetch.sh uses into a throwaway dir, run `cargo fetch --locked` (which downloads
# EVERY crate named in Cargo.lock — all targets, all features — regardless of
# feature flags), then discard the clone. Because the clone is created and
# removed inside ONE Docker `RUN` layer, it never enters the committed image;
# only CARGO_HOME (under /opt) persists.
#
# The pin is passed in (the Dockerfile's RIPGREP_PIN ARG, defaulted to match
# fetch.sh's PIN_SHA — the single source of truth). The runtime bind-mounted
# checkout is the SAME pin, so its Cargo.lock matches and every crate it needs is
# already cached here. On a pin bump: move PIN_SHA in fetch.sh AND RIPGREP_PIN in
# the Dockerfile together, then rebuild the image to re-warm the cache.
#
# Usage (from the Dockerfile, network on):
#   warm-cargo-cache.sh <pin-sha> <scratch-dir>
# Runs standalone on a bare host too (needs git, cargo, network, and a writable
# CARGO_HOME exported in the environment).

set -euo pipefail

PIN_SHA="${1:?usage: warm-cargo-cache.sh <pin-sha> <scratch-dir>}"
SCRATCH="${2:-/tmp/warm-ripgrep}"
UPSTREAM="https://github.com/BurntSushi/ripgrep.git"

: "${CARGO_HOME:?CARGO_HOME must be set (the committed cache layer to warm)}"

echo "==> warming Cargo cache for ripgrep at $PIN_SHA into $CARGO_HOME"
rm -rf "$SCRATCH"
git clone --quiet "$UPSTREAM" "$SCRATCH"
git -C "$SCRATCH" checkout -q "$PIN_SHA"

# cargo fetch --locked downloads every dependency pinned in Cargo.lock (all
# targets when --target is omitted, all features), populating $CARGO_HOME/registry
# so a later `cargo build --offline` resolves entirely from cache. --locked
# refuses if Cargo.lock is stale — a warm must use the checked-in lockfile
# verbatim, exactly as the runtime build does.
( cd "$SCRATCH" && cargo fetch --locked )

rm -rf "$SCRATCH"
echo "==> Cargo cache warm complete"
