#!/usr/bin/env bash
#
# apply.sh — apply the imps comment-only patch STREAMS on top of each pristine
# pinned checkout. Run after fetch.sh.
#
# This is a MULTI-REPO, DOCUMENTATION-ONLY carrier (CLAUDE.md, ../CLAUDE.md):
# for EACH repo in the `repos` manifest, both streams are COMMENT-ONLY and must
# change nothing the Kotlin compiler sees.
#   patches/<repo>/docs/  — explanatory KDoc (/** … */) on the most interesting
#                           code (the deliverable of "add docstrings").
#   patches/<repo>/book/  — // doc-region-begin/end markers for the Sphinx
#                           book's literalinclude (may be empty until the book
#                           is built).
#
# Within a repo, streams are applied in patches/ORDER (listed first, in order;
# the rest alphabetically). WITHIN a stream, numbered order matters; ACROSS
# streams it does not (the streams touch disjoint regions and commute).

set -e
cd "$(dirname "$0")"

MANIFEST=repos
[ -f "$MANIFEST" ] || { echo "missing manifest: $MANIFEST" >&2; exit 1; }

# Stream apply order within a repo. Listed streams (patches/ORDER) come first,
# in file order; the rest follow alphabetically. Comments/blanks in ORDER are
# ignored. `pdir` is the repo's patch dir (patches/<repo>); ORDER is shared at
# patches/ORDER (docs then book) since every repo uses the same two streams.
ordered_streams() {
    local pdir=$1 orderfile=patches/ORDER listed=() rest=() name stream
    if [ -f "$orderfile" ]; then
        while read -r name; do
            name=${name%%#*}                       # strip comments
            name=$(echo "$name" | tr -d '[:space:]')
            [ -n "$name" ] || continue
            if [ -d "$pdir/$name" ]; then
                listed+=("$pdir/$name/")
            fi
        done < "$orderfile"
    fi
    for stream in "$pdir"/*/; do
        [ -d "$stream" ] || continue
        case " ${listed[*]-} " in
            *" $stream "*) ;;
            *) rest+=("$stream") ;;
        esac
    done
    printf '%s\n' ${listed[@]+"${listed[@]}"} ${rest[@]+"${rest[@]}"}
}

# Apply every stream of one repo's checkout, guarded at that repo's pin.
apply_repo() {
    local name=$1 sha=$2 dir="checkout/$name" pdir="patches/$name"

    [ -d "$dir" ] || { echo "checkout/$name missing — run ./fetch.sh first." >&2; exit 1; }
    [ -d "$pdir" ] || { echo "no patch dir for $name (patches/$name) — skipping." >&2; return 0; }

    # A `git am` interrupted midway leaves .git/rebase-apply behind, and the
    # next run dies with an unhelpful message. Say what is wrong instead.
    if [ -d "$dir/.git/rebase-apply" ]; then
        echo "checkout/$name has an interrupted 'git am' in progress." >&2
        echo "Finish or discard it first:  git -C $dir am --abort" >&2
        exit 1
    fi

    if [ "$(git -C "$dir" rev-parse HEAD)" != "$sha" ]; then
        echo "checkout/$name is not at its pristine pin ($sha). Run ./fetch.sh first." >&2
        exit 1
    fi

    local stream
    for stream in $(ordered_streams "$pdir"); do
        if ls "$stream"*.patch >/dev/null 2>&1; then
            echo "apply $name stream: $stream"
            git -C "$dir" am --3way "$PWD/$stream"*.patch
        fi
    done
}

# Loop the manifest (same parse as fetch.sh) and apply each repo's streams.
while read -r url sha _; do
    case "$url" in ''|\#*) continue ;; esac
    [ -n "$sha" ] || { echo "manifest line for $url has no pin SHA" >&2; exit 1; }
    name=$(basename "$url" .git)
    apply_repo "$name" "$sha"
done < "$MANIFEST"

echo "==> apply complete"
