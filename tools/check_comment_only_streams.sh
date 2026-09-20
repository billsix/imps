#!/usr/bin/env bash
#
# check_comment_only_streams.sh -- gate every patch stream that is comment-only
# BY CONTRACT, across ALL families and every project, in ONE place.
#
# WHICH STREAMS
#   Streams named `docs` or `book`:
#     * `docs/` -- explanatory doc comments added to interesting source (the
#       docs-only carriers: unixutils/, android/).
#     * `book/` -- `// doc-region-begin/end` markers so a Sphinx book can
#       `literalinclude` spans by NAME (the mario64 mechanism; n64/CLAUDE.md).
#   A code stream (n64's cheats/, personal/, upstream-candidates/) is NEVER
#   checked -- it is not comment-only. Adding a doc comment or a doc-region
#   marker must never change the program; if one ever does, the docs have
#   silently started patching the code.
#
# HOW IT DISCOVERS PROJECTS (no family is hardcoded)
#   Every `<family>/<project>/patches/` dir whose project has a `fetch.sh`.
#   Three project shapes are handled:
#     * multi-repo carrier  -- a `repos` manifest + checkout/<repo>/ per repo
#       and patches/<repo>/ (android/fossify).
#     * single-repo carrier -- a checkout/ + patches/ (unixutils/dash, ripgrep).
#     * n64 port            -- a named checkout subdir + two lanes,
#       patches/ (game tree, pinned by fetch.sh's PIN_SHA) and
#       patches-libultraship/ (the submodule, pinned by <PIN_SHA>:libultraship).
#
# HOW IT PICKS THE PROVER (dispatch, not one engine)
#   Each project declares its source language in `patches/LANG` (one word: c,
#   rust or kotlin). An UNDECLARED project is treated as C -- that keeps the n64
#   ports working unchanged. Then, per comment-only stream:
#     * c            -> tools/prove_comment_only.sh   (gcc -fpreprocessed strips
#                       comments, then the token streams are compared).
#     * rust|kotlin  -> tools/prove_comment_only_strip.py --lang <lang>
#                       (a language-aware comment stripper; same strip-then-
#                       compare argument, since those languages have no cpp).
#
# WHAT IT DOES, per comment-only stream
#   Builds two scratch branches inside the checkout -- BEFORE = the pin plus
#   every stream that applies before this one (so a `book` stream sees the
#   `docs` it was written against, and an n64 `book` sees `cheats`), and AFTER =
#   that plus this stream -- then hands them to the right prover with
#   --allow-line-shift (a doc comment / doc-region marker occupies its own line,
#   so line shifts are inherent; only __LINE__/__FILE__ strings can move). The
#   BEFORE..AFTER diff is therefore exactly this stream's patches.
#
# USAGE
#   tools/check_comment_only_streams.sh [project ...]     # default: all
#   tools/check_comment_only_streams.sh dash ripgrep SuperMario64
#
#   A `project` is a project's directory basename (dash, ripgrep, fossify,
#   SuperMario64, ...). Projects with no populated comment-only stream are
#   skipped, not failed. Exits non-zero if any checked stream is NOT
#   comment-only.
#
# It works on scratch branches inside the checkouts, RESTORES each checkout to
# the state it was in beforehand, and never touches runDir/ (a sibling of the
# checkout, not inside it -- see the master CLAUDE.md).

set -u
shopt -s nullglob

cd "$(dirname "$0")/.."                 # imps repo root
ROOT=$PWD
PROVE_C=$ROOT/tools/prove_comment_only.sh
PROVE_STRIP=$ROOT/tools/prove_comment_only_strip.py
status=0
checked=0

# The comment-only stream names, space-padded for a substring membership test.
COS_NAMES=" docs book "

# --- helpers ------------------------------------------------------------------

# read_lang <patches-dir> -> the declared language (c/rust/kotlin), or empty.
# LANG is one word; #-comments and blank lines are ignored.
read_lang() {
    local f=$1/LANG line w
    [ -f "$f" ] || return 0
    while IFS= read -r line; do
        line=${line%%#*}
        w=$(echo "$line" | tr -d '[:space:]')
        [ -n "$w" ] && { echo "$w"; return 0; }
    done < "$f"
}

# The upstream checkout inside an n64 project: the one subdir holding a .git.
checkout_for() {
    local proj=$1 d
    for d in "$proj"/*/; do
        [ -e "$d/.git" ] && { basename "$d"; return 0; }
    done
}

# ordered_streams <patch-base> -> stream NAMES in apply order. Listed streams
# (from ORDER) come first in file order; the rest follow alphabetically. ORDER
# lives at <patch-base>/ORDER, or one level up (a multi-repo carrier shares one
# patches/ORDER across every patches/<repo>/). Comments/blanks in ORDER ignored.
ordered_streams() {
    local pdir=$1 orderfile="" name stream base
    if [ -f "$pdir/ORDER" ]; then
        orderfile="$pdir/ORDER"
    elif [ -f "$(dirname "$pdir")/ORDER" ]; then
        orderfile="$(dirname "$pdir")/ORDER"
    fi
    local listed=() rest=()
    if [ -n "$orderfile" ]; then
        while IFS= read -r name; do
            name=${name%%#*}
            name=$(echo "$name" | tr -d '[:space:]')
            [ -n "$name" ] || continue
            [ -d "$pdir/$name" ] && listed+=("$name")
        done < "$orderfile"
    fi
    for stream in "$pdir"/*/; do
        base=$(basename "$stream")
        case " ${listed[*]-} " in
            *" $base "*) ;;
            *) rest+=("$base") ;;
        esac
    done
    printf '%s\n' ${listed[@]+"${listed[@]}"} ${rest[@]+"${rest[@]}"}
}

# restore <repo> <prev-ref>: put the checkout back where it was and drop the
# scratch branches. A checkout's documented resting state is "pin + full series"
# (master CLAUDE.md); leaving it on a half-built branch would surprise later.
restore() {
    local repo=$1 prev=$2
    git -C "$repo" checkout -q "$prev" 2>/dev/null \
        || git -C "$repo" checkout -q --detach "$prev"
    git -C "$repo" branch -q -D cos-before cos-after 2>/dev/null || true
}

# check_unit <repo> <pin> <patch-base> <lang> <label>
#   Prove every populated comment-only stream in <patch-base> is comment-only,
#   against <repo> at <pin>, using the prover for <lang>.
check_unit() {
    local repo=$1 pin=$2 patchbase=$3 lang=$4 label=$5

    # Absolute paths: `git -C "$repo" am <patch>` resolves <patch> relative to
    # the repo dir, so a repo-root-relative patch path would not be found.
    [ "${repo#/}" = "$repo" ] && repo="$ROOT/$repo"
    [ "${patchbase#/}" = "$patchbase" ] && patchbase="$ROOT/$patchbase"

    [ -e "$repo/.git" ] || { echo "== $label: no checkout ($repo) -- run ./fetch.sh; skipped"; return 0; }
    git -C "$repo" cat-file -e "${pin}^{commit}" 2>/dev/null || {
        echo "== $label: pin ${pin:0:9} not in $repo -- run ./fetch.sh; skipped"; return 0; }

    local ordered=()
    mapfile -t ordered < <(ordered_streams "$patchbase")

    # Is any comment-only stream populated in this unit?
    local any=0 s
    for s in ${ordered[@]+"${ordered[@]}"}; do
        case "$COS_NAMES" in *" $s "*) ;; *) continue ;; esac
        [ -n "$(echo "$patchbase/$s"/*.patch)" ] && any=1
    done
    [ "$any" = 1 ] || return 0

    git -C "$repo" config commit.gpgsign false
    if [ -d "$repo/.git/rebase-apply" ]; then
        echo "  interrupted 'git am' in $repo -- run: git -C $repo am --abort" >&2
        status=1; return 0
    fi
    local prev_ref
    prev_ref=$(git -C "$repo" symbolic-ref --quiet --short HEAD \
               || git -C "$repo" rev-parse HEAD)

    # Prove each comment-only stream against the pin plus the streams before it.
    local other ok
    for s in "${ordered[@]}"; do
        case "$COS_NAMES" in *" $s "*) ;; *) continue ;; esac
        [ -n "$(echo "$patchbase/$s"/*.patch)" ] || continue

        echo
        echo "############ $label / $s ($lang) ############"

        # BEFORE: the pin plus every stream that applies before this one.
        git -C "$repo" checkout -q -B cos-before "$pin"
        git -C "$repo" reset -q --hard "$pin"
        ok=1
        for other in "${ordered[@]}"; do
            [ "$other" = "$s" ] && break        # only streams before S
            [ -n "$(echo "$patchbase/$other"/*.patch)" ] || continue
            git -C "$repo" am --3way -q "$patchbase/$other"/*.patch || {
                echo "  FAILED to apply $other -- cannot build the baseline" >&2
                git -C "$repo" am --abort 2>/dev/null
                status=1; ok=0; break; }
        done
        [ "$ok" = 1 ] || { restore "$repo" "$prev_ref"; continue; }

        # AFTER: this stream on top.
        git -C "$repo" checkout -q -b cos-after
        git -C "$repo" am --3way -q "$patchbase/$s"/*.patch || {
            echo "  FAILED to apply the $s stream" >&2
            git -C "$repo" am --abort 2>/dev/null
            status=1; restore "$repo" "$prev_ref"; continue; }

        case "$lang" in
            c)
                "$PROVE_C" --allow-line-shift "$repo" cos-before cos-after \
                    || status=1 ;;
            rust|kotlin)
                python3 "$PROVE_STRIP" --lang "$lang" --allow-line-shift \
                    "$repo" cos-before cos-after || status=1 ;;
            *)
                echo "  UNKNOWN language '$lang' for $label -- cannot prove" >&2
                status=1 ;;
        esac
        checked=$((checked + 1))
        restore "$repo" "$prev_ref"
    done
}

# --- discover projects --------------------------------------------------------

all_projects=()
for pd in */*/patches; do
    proj=${pd%/patches}
    [ -f "$proj/fetch.sh" ] || continue
    all_projects+=("$proj")
done
mapfile -t all_projects < <(printf '%s\n' ${all_projects[@]+"${all_projects[@]}"} | sort)

# Optional filter: keep only projects whose basename matches an argument.
requested=("$@")
projects=()
if [ "${#requested[@]}" -eq 0 ]; then
    projects=(${all_projects[@]+"${all_projects[@]}"})
else
    for proj in ${all_projects[@]+"${all_projects[@]}"}; do
        for want in "${requested[@]}"; do
            [ "$(basename "$proj")" = "$want" ] && { projects+=("$proj"); break; }
        done
    done
fi

# --- run ----------------------------------------------------------------------

for proj in ${projects[@]+"${projects[@]}"}; do
    name=$(basename "$proj")
    lang=$(read_lang "$proj/patches")
    lang=${lang:-c}

    if [ -f "$proj/repos" ]; then
        # Multi-repo carrier: one unit per manifest repo, at that repo's pin.
        while read -r url sha _; do
            case "$url" in ''|\#*) continue ;; esac
            [ -n "${sha:-}" ] || continue
            rname=$(basename "$url" .git)
            check_unit "$proj/checkout/$rname" "$sha" \
                "$proj/patches/$rname" "$lang" "$name/$rname"
        done < "$proj/repos"

    elif [ -e "$proj/checkout/.git" ]; then
        # Single-repo docs carrier.
        pin=$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh" | awk '{print $1}')
        check_unit "$proj/checkout" "$pin" "$proj/patches" "$lang" "$name"

    else
        # n64 port shape: a named checkout subdir + up to two lanes.
        co=$(checkout_for "$proj")
        [ -n "$co" ] || { echo "== $name: no checkout (run ./fetch.sh) -- skipped"; continue; }
        pin=$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh" | awk '{print $1}')
        check_unit "$proj/$co" "$pin" "$proj/patches" "$lang" "$name"
        if [ -n "$(echo "$proj"/patches-libultraship/*/*.patch)" ]; then
            lus_pin=$(git -C "$proj/$co" rev-parse "$pin:libultraship" 2>/dev/null)
            [ -n "${lus_pin:-}" ] && check_unit "$proj/$co/libultraship" \
                "$lus_pin" "$proj/patches-libultraship" "$lang" \
                "$name/libultraship"
        fi
    fi
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
