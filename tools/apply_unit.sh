#!/usr/bin/env bash
# Thin shim: the logic lives in apply_unit.py (ported from this bash 2026-10-29;
# behaviour-identical, incl. the --closure stdout and the "applied N patch(es)" line
# that check_upstreamable_applies.sh consumes). Callers keep using tools/apply_unit.sh.
exec python3 "$(dirname "$0")/apply_unit.py" "$@"
