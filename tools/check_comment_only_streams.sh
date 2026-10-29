#!/usr/bin/env bash
# Thin shim: the logic lives in check_comment_only_streams.py (ported from this bash
# 2026-10-29; behaviour-identical). Callers (the per-project check-comment-only.sh
# wrappers, Makefiles, n64/CLAUDE.md) keep using tools/check_comment_only_streams.sh.
exec python3 "$(dirname "$0")/check_comment_only_streams.py" "$@"
