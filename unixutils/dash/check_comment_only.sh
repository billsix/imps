#!/usr/bin/env bash
#
# check_comment_only.sh — prove every comment-only stream (patches/docs/,
# patches/book/) changes nothing the C compiler sees.
#
# dash is C, so the repo-root proof engine tools/prove_comment_only.sh applies
# directly (gcc -fpreprocessed strips comments, then the token streams are
# compared). The n64 wrapper tools/check_comment_only_streams.sh is hardcoded to
# the n64/ family, so this local wrapper does the same job for dash's single
# checkout/ lane and hands each stream to that shared engine.
#
# Per stream: build a BEFORE branch (the pin plus every OTHER comment-only
# stream) and an AFTER branch (that stream on top), then prove they are
# comment-only with --allow-line-shift (a doc comment / doc-region marker
# occupies its own line, so line shifts are inherent; only __LINE__/__FILE__
# strings can move — dash uses neither in a way that reaches program logic).
#
# Restores the checkout to where it was and drops the scratch branches. Needs
# git + gcc (both present in the Fedora image and on a typical host).

set -u
cd "$(dirname "$0")"
SELF=$PWD
ROOT=$SELF/../..
PROVE=$ROOT/tools/prove_comment_only.sh
REPO=$SELF/checkout

[ -x "$PROVE" ] || { echo "missing proof engine: $PROVE" >&2; exit 2; }
[ -d "$REPO/.git" ] || { echo "no checkout/ — run ./fetch.sh first" >&2; exit 2; }

PIN_SHA=$(sed -n 's/^PIN_SHA=//p' fetch.sh | awk '{print $1}')
git -C "$REPO" config commit.gpgsign false

if [ -d "$REPO/.git/rebase-apply" ]; then
    echo "interrupted 'git am' in $REPO — run: git -C $REPO am --abort" >&2
    exit 1
fi

# Where the checkout rests now, so the scratch branches do not park it somewhere
# unexpected (its documented resting state is the pin plus the full series).
prev_ref=$(git -C "$REPO" symbolic-ref --quiet --short HEAD \
           || git -C "$REPO" rev-parse HEAD)

status=0
checked=0
for stream in patches/*/; do
    name=$(basename "$stream")
    ls "$stream"*.patch >/dev/null 2>&1 || continue

    echo
    echo "############ dash / patches/$name ############"

    # BEFORE: the pin plus every OTHER comment-only stream.
    git -C "$REPO" checkout -q -B cos-before "$PIN_SHA"
    git -C "$REPO" reset -q --hard "$PIN_SHA"
    for other in patches/*/; do
        [ "$other" = "$stream" ] && continue
        ls "$other"*.patch >/dev/null 2>&1 || continue
        git -C "$REPO" am --3way -q "$SELF/$other"*.patch || {
            echo "  FAILED to apply $other — cannot build the baseline" >&2
            git -C "$REPO" am --abort 2>/dev/null
            status=1; continue 2; }
    done

    # AFTER: this stream on top.
    git -C "$REPO" checkout -q -b cos-after
    git -C "$REPO" am --3way -q "$SELF/$stream"*.patch || {
        echo "  FAILED to apply patches/$name" >&2
        git -C "$REPO" am --abort 2>/dev/null
        status=1
        git -C "$REPO" checkout -q "$prev_ref" 2>/dev/null || true
        git -C "$REPO" branch -q -D cos-before cos-after 2>/dev/null || true
        continue; }

    "$PROVE" --allow-line-shift "$REPO" cos-before cos-after || status=1
    checked=$((checked + 1))

    git -C "$REPO" checkout -q "$prev_ref" 2>/dev/null \
        || git -C "$REPO" checkout -q --detach "$prev_ref"
    git -C "$REPO" branch -q -D cos-before cos-after 2>/dev/null || true
done

echo
echo "############ SUMMARY ############"
if [ "$checked" -eq 0 ]; then
    echo "  no comment-only streams populated — nothing to check"
elif [ "$status" -eq 0 ]; then
    echo "  $checked stream(s) checked, all PROVEN comment-only"
else
    echo "  failures above"
fi
exit "$status"
