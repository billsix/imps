#!/usr/bin/env bash
#
# check-comment-only.sh — thin shim to the SHARED, family-agnostic comment-only
# gate. Kept under its original name so this project's CLAUDE.md, README and
# Makefile keep working; the real logic now lives in one place:
#   ../../tools/check_comment_only_streams.sh
# which discovers this multi-repo project, reads patches/LANG (fossify →
# kotlin), and hands each repo's comment-only stream to
# tools/prove_comment_only_strip.py --lang kotlin (the Kotlin-aware comment
# stripper, strip-then-compare — stronger than the old per-hunk source check).
#
# Runs on the host (git + python3; no SDK, no container). NOTE: the shared gate
# filters by PROJECT, not by repo-within-fossify, so a per-repo argument
# (./check-comment-only.sh Commons) is no longer honored — every repo in the
# manifest is always checked.
set -eu
cd "$(dirname "$0")"
if [ "$#" -gt 0 ]; then
    echo "note: per-repo filtering was dropped; checking every fossify repo." >&2
fi
exec ../../tools/check_comment_only_streams.sh fossify
