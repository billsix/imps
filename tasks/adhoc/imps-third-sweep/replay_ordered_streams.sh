#!/usr/bin/env bash
# Pin bump for a project whose game-tree streams stack on each other (patches/ORDER):
# fetch upstream's branch head, replay the streams onto it cumulatively in apply.sh's
# order (ORDER entries first, the rest alphabetically), and only when ALL replay cleanly
# regenerate each stream's patch files from its own commit range and set PIN_SHA. On a
# conflict it aborts that `git am`, changes nothing in imps, and exits 1. The
# libultraship lane is not handled here.
#
#   bash tasks/adhoc/imps-third-sweep/replay_ordered_streams.sh <Project> [<branch>]
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

mapfile -t streams < <(
    { grep -v '^\s*#' "$project/patches/ORDER" 2>/dev/null | tr -d '[:blank:]' | grep .
      find "$project/patches" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort; } | awk '!seen[$0]++'
)

git -C "$checkout" checkout -q -f -B imps-replay "$new_pin" || exit 1
tips=("$new_pin")
for name in "${streams[@]}"; do
    if ! git -C "$checkout" am -q --3way "$PWD/$project/patches/$name/"*.patch; then
        echo "CONFLICT in stream $name, at: $(git -C "$checkout" am --show-current-patch=diff 2>/dev/null | head -0)$(cat "$checkout/.git/rebase-apply/next" 2>/dev/null) of $(cat "$checkout/.git/rebase-apply/last" 2>/dev/null)"
        git -C "$checkout" status --short | grep -v '^??' | grep -v '^[AM]  ' | head -20
        [ "${KEEP_CONFLICT:-0}" = 1 ] || git -C "$checkout" am --abort
        exit 1
    fi
    tips+=("$(git -C "$checkout" rev-parse HEAD)")
    echo "  $name: $(git -C "$checkout" rev-list --count "${tips[-2]}..HEAD") patch(es) replay cleanly"
done

for index in "${!streams[@]}"; do
    stream="$project/patches/${streams[$index]}"
    rm -f "$stream"/*.patch
    git -C "$checkout" format-patch -q --no-cover-letter --base="$new_pin" -o "$PWD/$stream" "${tips[$index]}..${tips[$((index + 1))]}"
done
sed -i "s/^PIN_SHA=.*/PIN_SHA=$new_pin/" "$project/fetch.sh"
