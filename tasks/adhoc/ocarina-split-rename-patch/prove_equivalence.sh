#!/usr/bin/env bash
#
# prove_equivalence.sh -- prove the 225-patch rename series produces the same
# PROGRAM as the single 6,854-line patch it replaced.
#
# The argument, in three steps:
#
#   1. Build both trees from the pristine pin: the OLD monolithic patch (read
#      out of git history) and the NEW 225-patch series.
#   2. Show no file changes LINE COUNT. That is what keeps __LINE__/__FILE__ --
#      and every debug print built on them -- identical.
#   3. Hand every differing file to the C preprocessor with comments stripped
#      (gcc -fpreprocessed -dD -E -P) and show the results are byte-identical.
#      A real compiler does the stripping, not a regex in this repo.
#
# Steps 2+3 together mean the compiler receives an identical token stream from
# an identical number of lines, so the two trees compile to the same object
# code. The only difference is comments, which the compiler discards.
#
# Usage (from anywhere):
#   bash tasks/adhoc/ocarina-split-rename-patch/prove_equivalence.sh
#
# It works on scratch branches and leaves the checkout on the applied series.
# Needs the old patch to still be reachable in imps history -- pass a different
# commit as $1 if it has scrolled out of the default search.

set -u

cd "$(dirname "$0")/../../.."           # imps repo root
IMPS=$PWD
PROJ=$IMPS/n64/OcarinaOfTime
SW=$PROJ/Shipwright
PIN=$(sed -n 's/^PIN_SHA=//p' "$PROJ/fetch.sh")
OLD_PATCH_PATH=n64/OcarinaOfTime/patches/personal/0001-LLM-generated-renames.patch

status=0
step() { printf '\n=== %s ===\n' "$1"; }

# --- locate the old monolithic patch in history -----------------------------
# --diff-filter=AMR: the last commit that ADDED or MODIFIED the file, not the
# one that deleted it when the split landed.
OLD_COMMIT=${1:-$(git -C "$IMPS" log --format=%H --diff-filter=AMR -1 \
                      -- "$OLD_PATCH_PATH")}
if [ -z "$OLD_COMMIT" ]; then
    echo "cannot find $OLD_PATCH_PATH in history; pass its commit as \$1" >&2
    exit 1
fi
step "old patch found in $(git -C "$IMPS" rev-parse --short "$OLD_COMMIT")"
git -C "$IMPS" show "$OLD_COMMIT:$OLD_PATCH_PATH" > /tmp/old-renames.patch
echo "  $(wc -l < /tmp/old-renames.patch) lines"

# --- build the OLD tree ------------------------------------------------------
step "applying the OLD single patch onto the pin"
git -C "$SW" checkout -q -B proof-old "$PIN"
git -C "$SW" reset -q --hard "$PIN"
git -C "$SW" clean -qfd soh
git -C "$SW" am --3way -q /tmp/old-renames.patch || { echo "OLD patch failed"; exit 1; }
echo "  ok, 1 commit"

# --- build the NEW tree ------------------------------------------------------
step "applying the NEW $(ls "$PROJ"/patches/personal/*.patch | wc -l)-patch series onto the pin"
git -C "$SW" checkout -q -B proof-new "$PIN"
git -C "$SW" reset -q --hard "$PIN"
git -C "$SW" clean -qfd soh
( cd "$PROJ" && ./apply.sh ) >/tmp/proof-apply.log 2>&1 \
    || { echo "NEW series failed to apply; see /tmp/proof-apply.log"; exit 1; }
echo "  ok, $(git -C "$SW" rev-list --count "$PIN"..HEAD) commits"

# --- 1. which files differ at all? ------------------------------------------
step "files differing between OLD and NEW"
mapfile -t DIFFERING < <(git -C "$SW" diff --name-only proof-old proof-new)
if [ "${#DIFFERING[@]}" -eq 0 ]; then
    echo "  none -- the trees are already byte-identical"
else
    printf '  %s\n' "${DIFFERING[@]}"
fi

# --- 2. line counts must be unchanged ---------------------------------------
step "line-count check (protects __LINE__ / __FILE__)"
for f in "${DIFFERING[@]}"; do
    a=$(git -C "$SW" show "proof-old:$f" | wc -l)
    b=$(git -C "$SW" show "proof-new:$f" | wc -l)
    if [ "$a" != "$b" ]; then
        echo "  MISMATCH $f: old=$a new=$b"
        status=1
    else
        echo "  ok  $f  ($a lines in both)"
    fi
done

# --- 3. identical after the compiler strips comments ------------------------
step "compiler check: identical with comments stripped"
echo "  (gcc -fpreprocessed -dD -E -P: strips comments, expands nothing)"
tmp=$(mktemp -d)
for f in "${DIFFERING[@]}"; do
    git -C "$SW" show "proof-old:$f" > "$tmp/old"
    git -C "$SW" show "proof-new:$f" > "$tmp/new"
    # -x c forces C even for .h; the input is treated as already preprocessed,
    # so no include resolution is needed and nothing but comments is removed.
    gcc -xc -fpreprocessed -dD -E -P "$tmp/old" > "$tmp/old.i" 2>/dev/null
    gcc -xc -fpreprocessed -dD -E -P "$tmp/new" > "$tmp/new.i" 2>/dev/null
    if cmp -s "$tmp/old.i" "$tmp/new.i"; then
        echo "  ok  $f  identical to the compiler"
    else
        echo "  DIFFERS $f -- NOT comment-only:"
        diff "$tmp/old.i" "$tmp/new.i" | head -20
        status=1
    fi
done
rm -rf "$tmp"

# --- verdict -----------------------------------------------------------------
step "VERDICT"
if [ "$status" -eq 0 ]; then
    cat <<'MSG'
  PROVEN. The 225-patch series and the old single patch produce trees that
  differ only in comments, on the same number of lines, in the same files.
  The compiler sees an identical token stream, so the built program is the
  same. The split changed history and traceability, not behaviour.
MSG
else
    echo "  FAILED -- see the mismatches above. Do not trust the split."
fi

git -C "$SW" checkout -q proof-new
exit "$status"
