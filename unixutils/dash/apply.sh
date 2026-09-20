#!/usr/bin/env bash
#
# apply.sh — apply the imps comment-only patch STREAMS on top of the pristine
# pinned dash checkout. Run after fetch.sh.
#
# dash is a documentation-only carrier (the unixutils family): the only streams
# are comment-only —
#   patches/docs/  explanatory doc comments on interesting source
#   patches/book/  Sphinx doc-region markers (may be empty until the book lands)
# patches/ORDER pins the sequence (docs then book). WITHIN a stream, order
# matters (numbered); the streams touch disjoint files, so across them it does
# not — ORDER just makes the sequence explicit.
#
# Guarded to run only when HEAD is exactly at the pin (read out of fetch.sh, the
# single source of truth).

set -e
cd "$(dirname "$0")"

# A `git am` interrupted midway leaves .git/rebase-apply behind, and the next
# run dies with an unhelpful message. Say what is wrong instead.
if [ -d checkout/.git/rebase-apply ]; then
    echo "checkout/ has an interrupted 'git am' in progress." >&2
    echo "Finish or discard it first:  git -C checkout am --abort" >&2
    exit 1
fi

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh | awk '{print $1}')
if [ "$(git -C checkout rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "checkout/ is not at the pristine pin ($PIN_SHA). Run ./fetch.sh first." >&2
    exit 1
fi

# Stream apply order. Listed streams (patches/ORDER) apply first, in file order;
# any unlisted stream follows alphabetically. Comments (#) and blank lines are
# ignored.
ordered_streams() {
    local dir=$1 listed=() rest=() name stream
    if [ -f "$dir/ORDER" ]; then
        while read -r name; do
            name=${name%%#*}
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
