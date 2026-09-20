#!/usr/bin/env bash
#
# check-comment-only.sh — the docs-only family gate for ripgrep (Rust).
#
# Proves the patches/docs/ stream is comment-only, then proves it still
# compiles. Two independent checks:
#
#   1. Comment-stripped equality (check_comment_only.py): for every file the
#      stream touches, the pinned upstream version and the applied version are
#      identical once comments are removed. This is the Rust analogue of the C
#      `gcc -fpreprocessed` proof used by ../tools/check_comment_only_streams.sh.
#   2. `cargo build` of the applied checkout, so a doc comment that broke the
#      build (e.g. a malformed doctest) is caught.
#
# Runs both in-container (make check-comment-only) and on the host from this
# directory. Idempotent: it fetches/applies the stream if the checkout is bare.

set -e
cd "$(dirname "$0")"
HERE=$PWD

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)

[ -d checkout ] || ./fetch.sh

# Ensure the docs stream is applied (HEAD past the pin). If the checkout is
# sitting at the bare pin, apply it; otherwise assume it is already applied.
if [ "$(git -C checkout rev-parse HEAD)" = "$PIN_SHA" ]; then
    ./apply.sh
fi

# The files the stream touches, relative to the checkout root.
mapfile -t FILES < <(git -C checkout diff --name-only "$PIN_SHA" HEAD)
if [ "${#FILES[@]}" -eq 0 ]; then
    echo "no files changed by the stream; nothing to check." >&2
    exit 1
fi

echo "== comment-only proof (${#FILES[@]} file(s)) =="
( cd checkout && python3 "$HERE/check_comment_only.py" "$PIN_SHA" "${FILES[@]}" )

echo
echo "== cargo build (proves the docs still compile) =="
# Prefer --offline (the container bakes the crate cache); fall back to a
# networked build if the cache is not yet populated.
if ! cargo build --manifest-path checkout/Cargo.toml --offline 2>/dev/null; then
    cargo build --manifest-path checkout/Cargo.toml
fi

echo
echo "PASS: patches/docs/ is comment-only and the checkout builds."
