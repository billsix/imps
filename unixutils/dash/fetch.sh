#!/usr/bin/env bash
#
# fetch.sh — get the pristine dash source at the pinned release commit.
#
# Clones dash into a gitignored checkout/ if it is not there yet, then
# detaches HEAD at the pinned commit. Idempotent: a re-run just re-detaches
# at the pin; it never deletes local branches or discards committed work.
#
# dash is documentation-only here (the unixutils family): we pin a RELEASE
# tag so the reference set's file:line anchors stay stable, and carry only
# comment-only patch streams (patches/docs/, later patches/book/).

set -e
cd "$(dirname "$0")"

# Canonical upstream (Herbert Xu). kernel.org's smart-HTTP endpoint returns
# 403 to some fetch tools; if the clone fails we fall back to the GitHub
# mirror, which tracks the same history.
UPSTREAM_KERNEL=https://git.kernel.org/pub/scm/utils/dash/dash.git
UPSTREAM_MIRROR=https://github.com/tklauser/dash.git

# The pinned base commit: release tag v0.5.13.5 (the newest dash release as
# of 2026-09-20; tip of upstream master at that time). Documentation and the
# file:line anchors in tasks/reference/dash/ are written against this commit.
PIN_SHA=037bbdfd330017c368caf6242f977974123239b5   # v0.5.13.5

if [ ! -d checkout/.git ]; then
    if ! git clone "$UPSTREAM_KERNEL" checkout; then
        echo "kernel.org clone failed — falling back to the GitHub mirror." >&2
        rm -rf checkout
        git clone "$UPSTREAM_MIRROR" checkout
    fi
fi

# Scaffolding commits made in this checkout (git am of the doc streams) must
# not require the maintainer's GPG key — signing fails in the sandbox and a
# failed signature aborts git am mid-series. Disable it repo-locally, never
# globally.
git -C checkout config commit.gpgsign false

# The pin may not be present if the checkout predates a bump; fetch first so a
# re-run after a PIN_SHA change still resolves.
git -C checkout fetch --tags origin
git -C checkout checkout --detach "$PIN_SHA"
