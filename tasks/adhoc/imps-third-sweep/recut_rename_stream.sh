#!/usr/bin/env bash
# Replay OcarinaOfTime's rename stream onto the checkout's current HEAD with diff3
# conflict markers, resolving each conflict with tools/resolve_rename_conflicts.py.
# Prints one "RESOLVED <patch number> <file count>" line per resolved patch and stops,
# leaving the `git am` in progress, at the first block the resolver cannot handle.
#
#   bash tasks/adhoc/imps-third-sweep/recut_rename_stream.sh
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 1
checkout=n64/OcarinaOfTime/Shipwright
stream="$PWD/n64/OcarinaOfTime/patches/upstreamable-rename-decomp"

[ -d "$checkout/.git/rebase-apply" ] ||
    git -C "$checkout" -c merge.conflictStyle=diff3 am -q --3way "$stream"/*.patch >/dev/null 2>&1
while [ -d "$checkout/.git/rebase-apply" ]; do
    number="$(cat "$checkout/.git/rebase-apply/next")"
    patch_file="$(find "$stream" -name "$(printf '%04d' "$number")-*.patch")"
    mapfile -t conflicted < <(git -C "$checkout" diff --name-only --diff-filter=U)
    [ "${#conflicted[@]}" -gt 0 ] || { echo "STOP at patch $number: no conflicted file"; exit 1; }
    if ! python3 tools/resolve_rename_conflicts.py "$checkout" "$patch_file" "${conflicted[@]}" >"/tmp/recut-$number.log" 2>&1; then
        echo "STOP at patch $number: resolver could not handle a block (see /tmp/recut-$number.log)"
        exit 1
    fi
    echo "RESOLVED $number ${#conflicted[@]} file(s), $(grep -c . "/tmp/recut-$number.log") block line(s)"
    git -C "$checkout" add -- "${conflicted[@]}"
    git -C "$checkout" -c core.editor=true -c merge.conflictStyle=diff3 am -q --continue >/dev/null 2>&1
done
echo "done: $(git -C "$checkout" rev-list --count imps-sc-tip-new..HEAD) patch(es) on the standard-c tip"
