#!/usr/bin/env bash
#
# check-comment-only.sh — prove the doc/book patch streams change nothing the
# Kotlin compiler sees. This is the android family's analogue of the C
# `tools/check_comment_only_streams.sh` gate (see ../CLAUDE.md).
#
# Kotlin has no `gcc -fpreprocessed`, and diffing compiled .class output is
# unreliable for this purpose: inserting comment lines shifts source line
# numbers, which changes the .class LineNumberTable (and Kotlin @Metadata) even
# for a purely comment-only edit. But Kotlin comments and KDoc are NON-semantic
# — the lexer discards them and nothing about them reaches bytecode — so a
# SOURCE-level proof is both correct and cheap: every line a doc/book patch adds
# or removes must be a comment or a blank line. If that holds, the compiler's
# input (post-lexing) is identical and so is its output.
#
# This runs on the host (or in the container) with no Android SDK. A heavier
# compile-and-compare alternative (compile the module at the pin, apply the
# stream, recompile, diff a COMMENT-STRIPPED disassembly) is described in
# CLAUDE.md and left best-effort/UNVERIFIED given how heavy an Android build is.
#
# Usage:
#   ./check-comment-only.sh            # every repo in the manifest
#   ./check-comment-only.sh Commons    # just one repo

set -e
cd "$(dirname "$0")"

# A changed line (with its leading +/- already stripped) is acceptable iff,
# ignoring leading whitespace, it is empty or begins a // line comment, or is
# part of a /* ... */ (KDoc /** ... */) block: opener `/*`, body `*`, closer.
# The doc streams only ever add whole comment lines, so this conservative test
# is sufficient; a changed line that is code (or code with a trailing comment)
# fails it, which is exactly what we want to catch.
is_comment_or_blank() {
    case "$1" in
        *[![:space:]]*)
            case "${1#"${1%%[![:space:]]*}"}" in   # strip leading whitespace
                //*|/\**|\**) return 0 ;;
                *) return 1 ;;
            esac
            ;;
        *) return 0 ;;                               # blank / whitespace only
    esac
}

# A patch file is a mail-formatted diff: a header, then one or more `@@` hunks
# of context (' '), added ('+') and removed ('-') lines, then a `-- ` signature
# trailer. Only hunk bodies matter — and the `-- ` trailer starts with '-', so
# we must not mistake it for a removed line. Bound each hunk exactly by the line
# counts in its header, `@@ -old_start,old_len +new_start,new_len @@`: a context
# line consumes one old and one new, a '-' one old, a '+' one new; once both
# counters reach zero the hunk is over and everything after (until the next
# `@@`) is ignored. Line counts are 1 when omitted (`@@ -a +b @@`).
check_patch() {
    local patch=$1 bad=0 line body old=0 new=0 hdr marker
    while IFS= read -r line; do
        if [ "$old" -le 0 ] && [ "$new" -le 0 ]; then
            case "$line" in
                '@@'*)
                    # Extract "old_len" and "new_len" from -a,b +c,d (default 1).
                    hdr=${line#@@ }
                    hdr=${hdr%% @@*}
                    local oldpart=${hdr%% *} newpart=${hdr#* }
                    old=${oldpart#*,}; [ "$old" = "${oldpart}" ] && old=1
                    new=${newpart#*,}; [ "$new" = "${newpart}" ] && new=1
                    old=${old#-}; new=${new#+}
                    ;;
            esac
            continue
        fi
        marker=${line:0:1}
        body=${line:1}
        case "$marker" in
            ' ') old=$((old - 1)); new=$((new - 1)) ;;
            '-') old=$((old - 1)); check_line "$patch" "$line" "$body" || bad=1 ;;
            '+') new=$((new - 1)); check_line "$patch" "$line" "$body" || bad=1 ;;
            '\') : ;;                                # "\ No newline at end of file"
        esac
    done < "$patch"
    return $bad
}

# Report and fail if a changed line's body is not a comment or blank.
check_line() {
    local patch=$1 raw=$2 body=$3
    if is_comment_or_blank "$body"; then
        return 0
    fi
    echo "  NON-COMMENT change in $patch:" >&2
    echo "    ${raw}" >&2
    return 1
}

check_repo() {
    local repo=$1 status=0 stream patch found=0
    for stream in docs book; do
        for patch in "patches/$repo/$stream"/*.patch; do
            [ -e "$patch" ] || continue
            found=1
            if check_patch "$patch"; then
                echo "  OK  $patch"
            else
                status=1
            fi
        done
    done
    if [ "$found" -eq 0 ]; then
        echo "  (no patches for $repo yet)"
    fi
    return $status
}

# Repos to check: the argument, or every repo in the manifest.
if [ $# -ge 1 ]; then
    repos=("$@")
else
    repos=()
    while read -r url _; do
        case "$url" in ''|\#*) continue ;; esac
        repos+=("$(basename "$url" .git)")
    done < repos
fi

status=0
for repo in "${repos[@]}"; do
    echo "== $repo =="
    check_repo "$repo" || status=1
done

if [ "$status" -eq 0 ]; then
    echo "comment-only: PASS"
else
    echo "comment-only: FAIL — a doc/book patch changed a non-comment line" >&2
fi
exit $status
