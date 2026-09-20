#!/usr/bin/env bash
#
# check-comment-only.sh — thin shim to the SHARED, family-agnostic comment-only
# gate. Kept under its original name so this project's CLAUDE.md, README and
# Makefile keep working; the real logic now lives in one place:
#   ../../tools/check_comment_only_streams.sh
# which discovers this project, reads patches/LANG (ripgrep → rust), and hands
# each comment-only stream to tools/prove_comment_only_strip.py --lang rust
# (the Rust-aware comment stripper, strip-then-compare).
#
# Runs on the host (git + python3; no build, no container). The former inline
# `cargo build` "does it still compile" check is not part of the comment-only
# gate any more — use `make build` for that. Args are ignored.
set -eu
cd "$(dirname "$0")"
exec ../../tools/check_comment_only_streams.sh ripgrep
