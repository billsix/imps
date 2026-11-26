#!/usr/bin/env bash
# Pin bump for a project whose game-tree streams each stand on the bare pin (the
# upstreamable-* streams): fetch upstream's branch head, replay every stream onto it on
# its own branch, and only when ALL replay cleanly regenerate the patch files and set
# PIN_SHA. On any conflict it aborts that `git am`, changes nothing in imps, and exits 1.
#
# A stream whose branch imps-<stream> already sits on the new pin (a conflict resolved by
# hand there) is not replayed again, so a re-run after a hand resolution finishes the bump.
#
#   bash tasks/adhoc/imps-third-sweep/replay_independent_streams.sh <Project> [<branch>]
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 1
project="n64/$1"
branch="${2:-develop}"

checkout="$(dirname "$(find "$project" -mindepth 2 -maxdepth 2 -name .git | head -1)")"
old_pin="$(sed -n 's/^PIN_SHA=//p' "$project/fetch.sh")"
git -C "$checkout" fetch -q origin "$branch" || exit 1
new_pin="$(git -C "$checkout" rev-parse FETCH_HEAD)"
echo "$1: $old_pin -> $new_pin"
[ "$old_pin" = "$new_pin" ] && { echo "already at upstream head"; exit 0; }

# Replay each stream on its own branch at the new pin.
for stream in "$project"/patches/*/; do
    name="$(basename "$stream")"
    if [ "$(git -C "$checkout" merge-base "imps-$name" "$new_pin" 2>/dev/null)" = "$new_pin" ]; then
        echo "  $name: branch already on the new pin, $(git -C "$checkout" rev-list --count "$new_pin..imps-$name") patch(es)"
        continue
    fi
    git -C "$checkout" checkout -q -f -B "imps-$name" "$new_pin" || exit 1
    if ! git -C "$checkout" am -q --3way "$PWD/$stream"*.patch; then
        echo "CONFLICT in stream $name:"
        git -C "$checkout" status --short | grep -v '^??' | head -20
        git -C "$checkout" am --abort
        exit 1
    fi
    echo "  $name: $(git -C "$checkout" rev-list --count "$new_pin..HEAD") patch(es) replay cleanly"
done

# Every stream replayed: regenerate the series and move the pin.
for stream in "$project"/patches/*/; do
    name="$(basename "$stream")"
    rm -f "$stream"*.patch
    git -C "$checkout" format-patch -q --no-cover-letter --base="$new_pin" -o "$PWD/$stream" "$new_pin..imps-$name"
done
sed -i "s/^PIN_SHA=.*/PIN_SHA=$new_pin/" "$project/fetch.sh"
