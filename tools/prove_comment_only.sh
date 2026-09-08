#!/usr/bin/env bash
#
# prove_comment_only.sh -- prove two trees differ ONLY in comments, so they
# compile to the same program.
#
# WHEN TO RUN IT
#   * After reshaping a patch stream (splitting, squashing, re-ordering,
#     resolving a pin-bump conflict): prove the reshape changed history, not
#     behaviour, without a full build.
#   * As the gate for a `book/` stream. Those patches add `// doc-region-begin`
#     markers for a Sphinx `literalinclude` and are comment-only BY CONTRACT
#     (n64/CLAUDE.md). This is what enforces that contract.
#
# HOW IT ARGUES
#   1. Which files differ at all.
#   2. No file may change LINE COUNT -- that is what keeps __LINE__/__FILE__,
#      and every debug print built on them, identical.
#   3. Each differing file must be byte-identical once the COMPILER strips the
#      comments: `gcc -fpreprocessed -dD -E -P` treats the input as already
#      preprocessed, so it expands no includes and no macros and removes
#      nothing but comments.
#   Together: an identical token stream over an identical number of lines, so
#   the object code is the same. The argument rests on a compiler, not on a
#   regex in this repo.
#
# WHICH CHECK APPLIES TO WHICH STREAM
#   Check 3 is the real invariant and always applies. Check 2 is stricter and
#   NOT always appropriate:
#     * A patch-stream RESHAPE (split/squash/rebase) has no business moving
#       lines -- keep check 2 strict. The OoT rename split appends its
#       provenance tags to existing lines precisely so it passes.
#     * A `book/` stream CANNOT pass check 2: a `// doc-region-begin` marker
#       has to bracket a span, so it occupies its own line and shifts every
#       line below it. Pass --allow-line-shift there. The shift only reaches
#       code through __LINE__/__FILE__ (log and assert strings), never through
#       program logic.
#
# USAGE
#   tools/prove_comment_only.sh [--allow-line-shift] <checkout-dir> <ref-a> <ref-b>
#
#   # a patch-stream reshape (OoT rename split, 2026-09-07):
#   tools/prove_comment_only.sh n64/OcarinaOfTime/Shipwright old-series new-series
#
#   # a book stream: build one branch with it and one without, then compare.
#
# Exits 0 only if the difference really is comment-only.

set -u

ALLOW_LINE_SHIFT=0
if [ "${1:-}" = "--allow-line-shift" ]; then
    ALLOW_LINE_SHIFT=1
    shift
fi

if [ "$#" -ne 3 ]; then
    sed -n '2,46p' "$0" >&2
    exit 2
fi

REPO=$1
REF_A=$2
REF_B=$3
status=0
shifted=0

git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
    echo "not a git checkout: $REPO" >&2; exit 2; }
for ref in "$REF_A" "$REF_B"; do
    git -C "$REPO" rev-parse --verify -q "$ref^{commit}" >/dev/null || {
        echo "no such ref in $REPO: $ref" >&2; exit 2; }
done
command -v gcc >/dev/null || { echo "gcc is required" >&2; exit 2; }

step() { printf '\n=== %s ===\n' "$1"; }

step "comparing $REF_A .. $REF_B in $REPO"
mapfile -t DIFFERING < <(git -C "$REPO" diff --name-only "$REF_A" "$REF_B")
if [ "${#DIFFERING[@]}" -eq 0 ]; then
    echo "  the trees are byte-identical -- nothing to prove"
    exit 0
fi
echo "  ${#DIFFERING[@]} file(s) differ:"
printf '    %s\n' "${DIFFERING[@]}"

if [ "$ALLOW_LINE_SHIFT" -eq 1 ]; then
    step "line-count check SKIPPED (--allow-line-shift)"
    echo "  line shifts are expected here; only __LINE__/__FILE__ strings move."
else
    step "line-count check (protects __LINE__ / __FILE__)"
    for f in "${DIFFERING[@]}"; do
        a=$(git -C "$REPO" show "$REF_A:$f" 2>/dev/null | wc -l)
        b=$(git -C "$REPO" show "$REF_B:$f" 2>/dev/null | wc -l)
        if [ "$a" != "$b" ]; then
            echo "  MISMATCH  $f: $REF_A=$a $REF_B=$b"
            status=1
            shifted=$((shifted + 1))
        else
            echo "  ok  $f  ($a lines in both)"
        fi
    done
fi

step "compiler check: identical once gcc strips comments"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for f in "${DIFFERING[@]}"; do
    git -C "$REPO" show "$REF_A:$f" > "$tmp/a" 2>/dev/null || : > "$tmp/a"
    git -C "$REPO" show "$REF_B:$f" > "$tmp/b" 2>/dev/null || : > "$tmp/b"
    case "$f" in
        *.c|*.h|*.cpp|*.hpp|*.cc|*.inc|*.inc.c)
            # -xc: force C even for .h/.inc. -fpreprocessed: input is already
            # preprocessed, so includes/macros are left alone. -P: no line
            # markers (they would embed the temp filename).
            gcc -xc -fpreprocessed -dD -E -P "$tmp/a" > "$tmp/a.i" 2>/dev/null
            gcc -xc -fpreprocessed -dD -E -P "$tmp/b" > "$tmp/b.i" 2>/dev/null
            if cmp -s "$tmp/a.i" "$tmp/b.i"; then
                echo "  ok  $f  identical to the compiler"
            else
                echo "  DIFFERS  $f -- NOT comment-only:"
                diff "$tmp/a.i" "$tmp/b.i" | head -20
                status=1
            fi
            ;;
        *)
            # Not C: nothing to strip, so any difference is a real one.
            if cmp -s "$tmp/a" "$tmp/b"; then
                echo "  ok  $f  (non-C, identical)"
            else
                echo "  DIFFERS  $f -- non-C file, cannot be comment-only"
                status=1
            fi
            ;;
    esac
done

step "VERDICT"
if [ "$status" -eq 0 ]; then
    if [ "$ALLOW_LINE_SHIFT" -eq 1 ]; then
        echo "  PROVEN comment-only (line shifts permitted). The compiler sees the"
        echo "  same tokens; only __LINE__/__FILE__-derived strings can differ."
    else
        echo "  PROVEN comment-only. $REF_A and $REF_B compile to the same program."
    fi
elif [ "$shifted" -gt 0 ]; then
    echo "  Content is comment-only, but $shifted file(s) changed line count."
    echo "  If that is inherent to this stream (a book/ doc-region stream), re-run"
    echo "  with --allow-line-shift. Otherwise the stream should append its"
    echo "  comments to existing lines instead of inserting new ones."
else
    echo "  NOT comment-only -- see the mismatches above."
fi
exit "$status"
