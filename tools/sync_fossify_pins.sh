#!/usr/bin/env bash
# Move every android/fossify/repos pin to its repo's newest release tag. A repo with a
# docs stream has the stream replayed onto the new tag first (`git am --3way` on branch
# imps-docs); its manifest line moves and its patches are regenerated only when the replay
# is clean. A conflicting repo is reported, its `git am` aborted, and its line left alone.
# Idempotent: a repo already at its newest tag is reported as current.
#
#   bash tools/sync_fossify_pins.sh [<repo> ...]   # default: all
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/android/fossify" || exit 1

status=0
while read -r url old_pin _; do
    name="$(basename "$url" .git)"
    if [ "$#" -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$name"; then continue; fi
    dir="checkout/$name"
    git -C "$dir" fetch -q --tags origin || { echo "$name: fetch failed"; status=1; continue; }
    tag="$(git -C "$dir" tag | grep -v -i -E 'pre|rc|beta|alpha|nightly' | sort -V | tail -1)"
    new_pin="$(git -C "$dir" rev-parse "$tag^{commit}")"
    if [ "$old_pin" = "$new_pin" ]; then
        echo "$name: current ($tag)"
        continue
    fi
    if ls "patches/$name/docs/"*.patch >/dev/null 2>&1; then
        git -C "$dir" checkout -q -f -B imps-docs "$new_pin"
        if ! git -C "$dir" am -q --3way "$PWD/patches/$name/docs/"*.patch >/dev/null 2>&1; then
            echo "$name: CONFLICT at docs patch $(cat "$dir/.git/rebase-apply/next") replaying onto $tag: $(git -C "$dir" diff --name-only --diff-filter=U | tr '\n' ' ')"
            git -C "$dir" am --abort
            git -C "$dir" checkout -q --detach "$old_pin"
            status=1
            continue
        fi
        git -C "$dir" format-patch -q --no-cover-letter --base="$new_pin" -o "$PWD/patches/$name/docs" "$new_pin..HEAD"
    fi
    git -C "$dir" checkout -q --detach "$new_pin"
    date="$(git -C "$dir" log -1 --format=%cd --date=short "$new_pin")"
    sed -i -E "s|^($url[[:space:]]+)$old_pin([[:space:]]+)#.*|\1$new_pin\2# $tag $date|" repos
    echo "$name: $old_pin -> $new_pin ($tag, $date)"
done < <(grep -v -E '^\s*(#|$)' repos)
exit "$status"
