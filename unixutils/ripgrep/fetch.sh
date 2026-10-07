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

# The pinned base commit: the commit tag 15.2.0 points at, the latest stable
# ripgrep release. Bumped 14.1.1 -> 15.2.0 on 2026-10-08 (overnight sweep
# follow-up, tasks/imps-check-upstreams-and-rebase-patches.md): a major-version
# jump; the 3 comment-only docs patches replay (patch 0003's glue.rs doc comment
# was re-placed after upstream inserted a consume_remaining() method 14->15 --
# the fill() docstring still describes the code). Pinned to a released TAG's
# commit (not a moving main tip) so the reference docs' file:line anchors and the
# book's doc-region spans stay valid.
#   NB: 15.2.0 is an ANNOTATED tag; this is the COMMIT it peels to
#   (git rev-parse 15.2.0^{}), not the tag-object SHA — so `git rev-parse HEAD`
#   equals PIN_SHA and apply.sh's pin guard matches.
#   REMEMBER: the pin lives twice -- also update RIPGREP_PIN in the Dockerfile
#   and rebuild `make image` to re-warm the offline Cargo cache for the new lockfile.
PIN_SHA=e89fff89ac9af12e8d4ce9d5fd07beb408ca730f

if [ ! -d checkout ]; then
    git clone "$UPSTREAM" checkout
fi

# Scaffolding commits made in this checkout (the git am of the doc streams,
# and the commits that PRODUCE those streams) must not require the maintainer's
# GPG key — disable signing repo-locally, never globally. A failed signature
# aborts `git am` mid-series.
git -C checkout config commit.gpgsign false

git -C checkout checkout "$PIN_SHA"
