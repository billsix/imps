#!/usr/bin/env bash
#
# check_comment_only_streams.sh -- gate every stream that is comment-only BY
# CONTRACT, across all projects and both patch lanes.
#
# WHICH STREAMS
#   `book/` streams. They add `// doc-region-begin/end` markers so a Sphinx
#   book can `literalinclude` spans by NAME instead of line numbers
#   (n64/CLAUDE.md). Adding a marker must never change the program -- if one
#   ever does, the book has silently started patching the game.
#
# WHAT IT DOES, per stream
#   Builds two scratch branches off the pin -- everything EXCEPT that stream,
#   then that stream on top -- and hands them to tools/prove_comment_only.sh
#   with --allow-line-shift (a doc-region marker must occupy its own line, so
#   line shifts are inherent; only __LINE__/__FILE__ strings can move).
#
# USAGE
#   tools/check_comment_only_streams.sh [project ...]     # default: all
#
# Projects with no book stream are skipped, not failed. Exits non-zero if any
# checked stream turns out NOT to be comment-only.
#
# It works on scratch branches inside the checkouts and never touches runDir/
# (which is a sibling of the checkout, not inside it -- see CLAUDE.md).

set -u

cd "$(dirname "$0")/.."                 # imps repo root
ROOT=$PWD
PROVE=$ROOT/tools/prove_comment_only.sh
status=0
checked=0

projects=("$@")
if [ "${#projects[@]}" -eq 0 ]; then
    mapfile -t projects < <(find n64 -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort)
fi

# checkout_for <project-dir> -> the upstream checkout inside it (one dir with a
# .git and a patches contract); empty if the project has none (docs-only).
checkout_for() {
    local proj=$1 d
    for d in "$proj"/*/; do
        [ -e "$d/.git" ] && { basename "$d"; return; }
    done
}

for name in "${projects[@]}"; do
    proj=$ROOT/n64/$name
    [ -f "$proj/fetch.sh" ] || continue
    co=$(checkout_for "$proj")
    [ -n "$co" ] || { echo "== $name: no checkout (run ./fetch.sh) -- skipped"; continue; }

    for lane in patches patches-libultraship; do
        stream=$proj/$lane/book
        ls "$stream"/*.patch >/dev/null 2>&1 || continue

        echo
        echo "############ $name / $lane/book ############"
        if [ "$lane" = "patches" ]; then
            repo=$proj/$co
            pin=$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh")
        else
            repo=$proj/$co/libultraship
            pin=$(git -C "$proj/$co" rev-parse \
                  "$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh"):libultraship")
        fi

        git -C "$repo" config commit.gpgsign false
        if [ -d "$repo/.git/rebase-apply" ]; then
            echo "  interrupted 'git am' in $repo -- run: git -C $repo am --abort" >&2
            status=1
            continue
        fi

        # BEFORE: the pin plus every OTHER stream in this lane.
        git -C "$repo" checkout -q -B cos-before "$pin"
        git -C "$repo" reset -q --hard "$pin"
        for other in "$proj/$lane"/*/; do
            case "$other" in *"/book/") continue ;; esac
            ls "$other"*.patch >/dev/null 2>&1 || continue
            git -C "$repo" am --3way -q "$other"*.patch || {
                echo "  FAILED to apply $other -- cannot build the baseline" >&2
                git -C "$repo" am --abort 2>/dev/null
                status=1; continue 2; }
        done

        # AFTER: the book stream on top.
        git -C "$repo" checkout -q -b cos-after
        git -C "$repo" am --3way -q "$stream"/*.patch || {
            echo "  FAILED to apply the book stream" >&2
            git -C "$repo" am --abort 2>/dev/null
            status=1; continue; }

        "$PROVE" --allow-line-shift "$repo" cos-before cos-after || status=1
        checked=$((checked + 1))
    done
done

echo
echo "############ SUMMARY ############"
if [ "$checked" -eq 0 ]; then
    echo "  no comment-only streams found -- nothing to check"
elif [ "$status" -eq 0 ]; then
    echo "  $checked stream(s) checked, all PROVEN comment-only"
else
    echo "  failures above"
fi
exit "$status"
