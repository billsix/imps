#!/usr/bin/env bash
#
# apply.sh — apply the imps comment-only patch STREAMS on top of the pristine
# pinned checkout. Run after fetch.sh.
#
# This is a DOCUMENTATION-ONLY carrier (../CLAUDE.md): both streams are
# COMMENT-ONLY and must change nothing the compiler sees.
#   patches/docs/  — explanatory Rust doc comments (/// and //!) on the most
#                    interesting code (the deliverable of "add docstrings").
#   patches/book/  — // doc-region-begin/end markers for the Sphinx book's
#                    literalinclude (may be empty until the book is built).
#
# Streams are applied in patches/ORDER (listed first, in order; the rest
# alphabetically). WITHIN a stream, numbered order matters; ACROSS streams it
# does not (the streams touch disjoint regions and commute).

set -e
cd "$(dirname "$0")"

# A `git am` interrupted midway leaves .git/rebase-apply behind, and the next
# run dies with an unhelpful message. Say what is wrong instead.
if [ -d checkout/.git/rebase-apply ]; then
    echo "checkout/ has an interrupted 'git am' in progress." >&2
    echo "Finish or discard it first:  git -C checkout am --abort" >&2
    exit 1
fi

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)
if [ "$(git -C checkout rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "checkout/ is not at the pristine pin ($PIN_SHA). Run ./fetch.sh first." >&2
    exit 1
fi

# Stream apply order. Listed streams (patches/ORDER) come first, in file order;
# the rest follow alphabetically. Comments and blank lines in ORDER are ignored.
ordered_streams() {
    local dir=$1 listed=() rest=() name stream
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

for stream in $(ordered_streams patches); do
    if ls "$stream"*.patch >/dev/null 2>&1; then
        echo "apply stream: $stream"
        git -C checkout am --3way "$PWD/$stream"*.patch
    fi
done
