#!/usr/bin/env bash
#
# fetch.sh — get the pristine ripgrep source at the pinned commit.
#
# Clones upstream if checkout/ does not exist yet, then detaches HEAD at the
# pinned commit. Idempotent: a re-run just re-detaches HEAD at the pin; it does
# not delete local branches or discard committed work.
#
# This is a DOCUMENTATION-ONLY carrier (see ../CLAUDE.md): the only patch
# streams are comment-only (patches/docs/ doc comments, patches/book/ Sphinx
# doc-region markers). Nothing here changes what ripgrep does.

set -e
cd "$(dirname "$0")"

UPSTREAM=https://github.com/BurntSushi/ripgrep.git

# The pinned base commit: the commit tag 14.1.1 points at (released
# 2024-09-08), the latest stable ripgrep release. Pinned to a released TAG's
# commit (not a moving main tip) so the reference docs' file:line anchors and
# the book's doc-region spans stay valid.
#   NB: 14.1.1 is an ANNOTATED tag; this is the COMMIT it peels to
#   (git rev-parse 14.1.1^{}), not the tag-object SHA — so `git rev-parse HEAD`
#   equals PIN_SHA and apply.sh's pin guard matches.
PIN_SHA=4649aa9700619f94cf9c66876e9549d83420e16c

if [ ! -d checkout ]; then
    git clone "$UPSTREAM" checkout
fi

# Scaffolding commits made in this checkout (the git am of the doc streams,
# and the commits that PRODUCE those streams) must not require the maintainer's
# GPG key — disable signing repo-locally, never globally. A failed signature
# aborts `git am` mid-series.
git -C checkout config commit.gpgsign false

git -C checkout checkout "$PIN_SHA"
