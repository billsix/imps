#!/usr/bin/env bash
# Pin bump for a docs-only carrier in unixutils/: fetch the given release tag, replay the
# comment-only docs stream onto it, and when it replays cleanly regenerate the patch files
# and set PIN_SHA. On a conflict the `git am` is left in progress for a hand resolution;
# re-run with RESUME=1 after `git am --continue` to regenerate from the checkout's HEAD.
#
#   bash tasks/adhoc/imps-third-sweep/replay_docs_stream.sh <project> <tag>
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/unixutils/$1" || exit 1
tag="$2"

git -C checkout fetch -q origin "refs/tags/$tag:refs/tags/$tag" || exit 1
new_pin="$(git -C checkout rev-parse "$tag^{commit}")"
echo "$1: $(sed -n 's/^PIN_SHA=\([0-9a-f]*\).*/\1/p' fetch.sh) -> $new_pin ($tag)"
if [ "${RESUME:-0}" != 1 ]; then
    git -C checkout checkout -q -f -B imps-docs "$new_pin" || exit 1
    if ! git -C checkout am -q --3way "$PWD"/patches/docs/*.patch; then
        echo "CONFLICT at patch $(cat checkout/.git/rebase-apply/next):"
        git -C checkout status --short | grep -v '^??' | grep -v '^[AM]  '
        exit 1
    fi
fi
echo "  docs: $(git -C checkout rev-list --count "$new_pin..HEAD") patch(es) on the new pin"
rm -f patches/docs/*.patch
git -C checkout format-patch -q --no-cover-letter --base="$new_pin" -o "$PWD/patches/docs" "$new_pin..HEAD"
sed -i "s/^PIN_SHA=[0-9a-f]*/PIN_SHA=$new_pin/" fetch.sh
