#!/usr/bin/env bash
#
# apply.sh — apply the imps patch STREAMS on top of the pristine pinned GZDoom
# checkout. Run after fetch.sh. Patches are grouped into purpose STREAMS
# (subfolders, e.g. upstream-candidates/): WITHIN a stream order matters
# (numbered); ACROSS streams it does not, because the streams touch disjoint
# files and commute. See ../CLAUDE.md and ../../n64/CLAUDE.md for the model.
#
# One lane only (GZDoom has no in-repo engine submodule of ours to patch; ZMusic
# is a separate pristine build, not carried):
#   game tree   patches/<stream>/*.patch  ->  checkout/gzdoom/
#
# Patches apply to the GZDoom checkout at its pin. ZMusic is never patched.

set -e
cd "$(dirname "$0")"

GZDOOM=checkout/gzdoom

# A `git am` interrupted midway leaves .git/rebase-apply behind, and the next
# run dies with the unhelpful "previous rebase directory ... still exists but
# mbox given". Say what is wrong instead.
if [ -d "$GZDOOM/.git/rebase-apply" ]; then
    echo "$GZDOOM has an interrupted 'git am' in progress." >&2
    echo "Finish or discard it first:  git -C $GZDOOM am --abort" >&2
    exit 1
fi

PIN_SHA=$(sed -n 's/^GZDOOM_PIN_SHA=//p' fetch.sh)
if [ "$(git -C "$GZDOOM" rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "$GZDOOM is not at the pristine pin ($PIN_SHA). Run ./fetch.sh first." >&2
    exit 1
fi

# Stream apply order. Normally irrelevant (streams commute), but a project may
# pin an order in patches/ORDER when one stream must precede the others. Listed
# streams come first, in file order; the rest follow alphabetically.
ordered_streams() {
    local dir=$1 listed=() rest=() name
    if [ -f "$dir/ORDER" ]; then
        while read -r name; do
            name=${name%%#*}                       # strip comments
            name=$(echo "$name" | tr -d '[:space:]')
            [ -n "$name" ] || continue
            if [ -d "$dir/$name" ]; then
                listed+=("$dir/$name/")
            else
                echo "$dir/ORDER names a missing stream: $name" >&2
                exit 1
            fi
        done < "$dir/ORDER"
    fi
    for stream in "$dir"/*/; do
        case " ${listed[*]-} " in
            *" $stream "*) ;;
            *) rest+=("$stream") ;;
        esac
    done
    printf '%s\n' ${listed[@]+"${listed[@]}"} ${rest[@]+"${rest[@]}"}
}

# Apply each stream (subfolder), in-folder order. Today: the comment-only `book`
# doc-region stream (a future `upstream-candidates` CLI-WAD stream will join it).
for stream in $(ordered_streams patches); do
    if ls "$stream"*.patch >/dev/null 2>&1; then
        echo "apply game-tree stream: $stream"
        git -C "$GZDOOM" am --3way "$PWD/$stream"*.patch
    fi
done
