#!/usr/bin/env bash
#
# apply.sh — apply the imps patch STREAMS on top of the pristine pinned checkout.
# Run after fetch.sh. Patches are grouped into purpose STREAMS (subfolders, e.g.
# cheats/, upstream-candidates/, personal/, book/): WITHIN a stream order matters
# (numbered); ACROSS streams it does not, because the streams touch disjoint files
# and commute — no total ordering to maintain. See n64/CLAUDE.md.
#
# Two lanes (n64/CLAUDE.md), each streamed:
#   game tree     patches/<stream>/*.patch              -> 2ship2harkinian/
#   libultraship  patches-libultraship/<stream>/*.patch -> 2ship2harkinian/libultraship/

set -e
cd "$(dirname "$0")"

# A `git am` interrupted midway (Ctrl-C, a closed pipe, a conflict) leaves
# .git/rebase-apply behind, and the next run dies with the unhelpful "previous
# rebase directory ... still exists but mbox given". Say what is wrong instead.
if [ -d 2ship2harkinian/.git/rebase-apply ]; then
    echo "2ship2harkinian/ has an interrupted 'git am' in progress." >&2
    echo "Finish or discard it first:  git -C 2ship2harkinian am --abort" >&2
    exit 1
fi

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh)
if [ "$(git -C 2ship2harkinian rev-parse HEAD)" != "$PIN_SHA" ]; then
    echo "2ship2harkinian/ is not at the pristine pin ($PIN_SHA). Run ./fetch.sh first." >&2
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

# --- Lane 1: game tree — apply each stream (subfolder), in-folder order ---
for stream in $(ordered_streams patches); do
    if ls "$stream"*.patch >/dev/null 2>&1; then
        echo "apply game-tree stream: $stream"
        git -C 2ship2harkinian am --3way "$PWD/$stream"*.patch
    fi
done

# --- Lane 2: libultraship submodule — apply each stream (if the lane has any) ---
LUS_DIR="2ship2harkinian/libultraship"
if ls patches-libultraship/*/*.patch >/dev/null 2>&1; then
    LUS_PIN=$(git -C 2ship2harkinian rev-parse "$PIN_SHA":libultraship)
    if [ "$(git -C "$LUS_DIR" rev-parse HEAD)" != "$LUS_PIN" ]; then
        echo "$LUS_DIR is not at its pristine pin ($LUS_PIN). Run ./fetch.sh first." >&2
        exit 1
    fi
    git -C "$LUS_DIR" config commit.gpgsign false
    for stream in $(ordered_streams patches-libultraship); do
        if ls "$stream"*.patch >/dev/null 2>&1; then
            echo "apply libultraship stream: $stream"
            git -C "$LUS_DIR" am --3way "$PWD/$stream"*.patch
        fi
    done
fi
