#!/usr/bin/env bash
#
# check_comment_only.sh — thin shim to the SHARED, family-agnostic comment-only
# gate. Kept under its original name so this project's CLAUDE.md, README and
# Makefile keep working; the real logic now lives in one place:
#   ../../tools/check_comment_only_streams.sh
# which discovers this project, reads patches/LANG (dash → c), and hands each
# comment-only stream to tools/prove_comment_only.sh (gcc -fpreprocessed).
#
# Runs on the host (git + gcc; no build, no container). Args are ignored — this
# shim always checks the dash project.
set -eu
cd "$(dirname "$0")"
exec ../../tools/check_comment_only_streams.sh dash
