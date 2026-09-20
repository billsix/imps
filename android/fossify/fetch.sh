#!/usr/bin/env bash
#
# fetch.sh — get the pristine Fossify sources at their pinned commits.
#
# This is a MULTI-REPO, DOCUMENTATION-ONLY carrier (see CLAUDE.md and
# ../CLAUDE.md): the Fossify apps share a Commons library, so this one carrier
# pins SEVERAL upstreams — Commons plus a chosen set of exemplar apps. The only
# patch streams are comment-only (patches/<repo>/docs KDoc, patches/<repo>/book
# Sphinx doc-region markers). Nothing here changes what any app does.
#
# The upstreams and their pins live in the `repos` manifest (one line each:
# URL, pin SHA, then a `# tag date` comment). fetch.sh loops over it, cloning
# each into checkout/<name>/ (name = the repo's basename) and detaching HEAD at
# that repo's pin. Idempotent: a re-run just re-detaches each HEAD at its pin;
# it does not delete local branches or discard committed work.

set -e
cd "$(dirname "$0")"

MANIFEST=repos
[ -f "$MANIFEST" ] || { echo "missing manifest: $MANIFEST" >&2; exit 1; }

mkdir -p checkout

# Read the manifest: strip #-comments, skip blanks, take the first two fields
# (URL, SHA) of each remaining line.
while read -r url sha _; do
    case "$url" in ''|\#*) continue ;; esac   # blank / comment line
    [ -n "$sha" ] || { echo "manifest line for $url has no pin SHA" >&2; exit 1; }

    # Checkout dir = the repo basename with any .git stripped (Commons, Gallery…).
    name=$(basename "$url" .git)
    dir="checkout/$name"

    if [ ! -d "$dir" ]; then
        echo "==> cloning $name"
        git clone "$url" "$dir"
    fi

    # Scaffolding commits made in this checkout (the git am of the doc streams,
    # and the commits that PRODUCE those streams) must not require the
    # maintainer's GPG key — a failed signature aborts `git am` mid-series.
    # Disable signing repo-locally in each checkout, never globally.
    git -C "$dir" config commit.gpgsign false

    echo "==> $name -> $sha"
    git -C "$dir" checkout -q "$sha"
done < "$MANIFEST"

echo "==> fetch complete"
