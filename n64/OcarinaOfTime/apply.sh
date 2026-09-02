#!/usr/bin/env bash
#
# apply.sh — apply the imps patch series on top of the pristine pinned
# checkout.  Run it after fetch.sh (or after build.sh's first-run fetch).
# It refuses to run unless Shipwright/ is exactly at the pin, so it cannot
# double-apply the series or stack it onto the wrong base.

set -e
cd "$(dirname "$0")"

# Single source of truth for the pin is fetch.sh — read it from there.
PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)

if [ "$(git -C Shipwright rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "Shipwright/ is not at the pristine pin ($PIN_SHA)." >&2
    echo "Run ./fetch.sh first, then apply." >&2
    exit 1
fi

git -C Shipwright am --3way "$PWD"/patches/*.patch
