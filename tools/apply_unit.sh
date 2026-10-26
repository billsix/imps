#!/usr/bin/env bash
#
# apply_unit.sh -- apply ONE upstreamable unit (one PR's worth) in ISOLATION on
# pristine upstream, so it can be built and submitted without the personal
# patches underneath it.
#
# WHY
#   The currency of upstreaming is a unit of work (one PR), carried as an
#   `upstreamable-<slug>/` stream (master CLAUDE.md, "Patch philosophy"). apply.sh
#   applies the WHOLE series (your full personal stack); this applies only the
#   named unit plus its declared upstreamable prerequisites -- the honest "will
#   this PR build on upstream by itself" setup.
#
# THE INVARIANT IT RELIES ON
#   An upstreamable unit depends only on pristine upstream and OTHER upstreamable
#   units -- never on personal/cheats/book. Prerequisites are declared in
#   patches/<slug>/DEPENDS (one upstreamable stream name per line; absent = depends
#   only on the bare pin). check_upstreamable_applies.sh enforces this.
#
# USAGE
#   tools/apply_unit.sh <Project> <slug>            # reset to pin, apply the closure
#   tools/apply_unit.sh --closure <Project> <slug>  # print the closure, mutate nothing
#   # then, to build the isolated AppImage:
#   make -C n64/<Project>/<checkout>/docker appimage
#
# Leaves the checkout on branch imps-<slug> at pin + the unit's closure. Never
# touches runDir/ (a sibling of the checkout). Game-tree lane only (no
# upstreamable unit lives in the libultraship lane today).

set -u
cd "$(dirname "$0")/.."                 # imps repo root
ROOT=$PWD

closure_only=0
if [ "${1:-}" = "--closure" ]; then closure_only=1; shift; fi
proj_name=${1:-}; slug=${2:-}
if [ -z "$proj_name" ] || [ -z "$slug" ]; then
    echo "usage: tools/apply_unit.sh [--closure] <Project> <slug>" >&2
    exit 2
fi

proj=$ROOT/n64/$proj_name
pdir=$proj/patches
[ -d "$pdir/$slug" ] || { echo "no such stream: n64/$proj_name/patches/$slug" >&2; exit 2; }

# Transitive DEPENDS closure, prerequisites first, deduped and cycle-safe.
declare -A VISITED=()
closure() {
    local slug=$1 dep
    [ -n "${VISITED[$slug]:-}" ] && return 0
    VISITED[$slug]=1
    [ -d "$pdir/$slug" ] || { echo "DEPENDS names a missing stream: $slug" >&2; exit 1; }
    if [ -f "$pdir/$slug/DEPENDS" ]; then
        while read -r dep; do
            dep=${dep%%#*}; dep=$(echo "$dep" | tr -d '[:space:]')
            [ -n "$dep" ] || continue
            closure "$dep"
        done < "$pdir/$slug/DEPENDS"
    fi
    echo "$slug"
}

mapfile -t streams < <(closure "$slug")

if [ "$closure_only" -eq 1 ]; then
    printf '%s\n' "${streams[@]}"
    exit 0
fi

# Locate the checkout (the one subdir holding a .git) and the pin.
co=""
for d in "$proj"/*/; do [ -e "$d/.git" ] && { co=$(basename "$d"); break; }; done
[ -z "$co" ] && { echo "no checkout in n64/$proj_name -- run ./fetch.sh" >&2; exit 1; }
repo=$proj/$co
pin=$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh")

[ -d "$repo/.git/rebase-apply" ] && { echo "interrupted 'git am' -- run: git -C $repo am --abort" >&2; exit 1; }
git -C "$repo" cat-file -e "${pin}^{commit}" 2>/dev/null || { echo "pin not in checkout -- run ./fetch.sh" >&2; exit 1; }

branch="imps-$slug"
echo "==> $proj_name: reset $co to pin ${pin:0:9}, branch $branch"
# Repo-local only (never imps itself): signing fails in the sandbox and aborts git am.
git -C "$repo" config commit.gpgsign false
git -C "$repo" checkout -q -B "$branch" "$pin"
git -C "$repo" reset -q --hard "$pin"
git -C "$repo" clean -qfd

for s in "${streams[@]}"; do
    if ls "$pdir/$s/"*.patch >/dev/null 2>&1; then
        echo "    apply unit stream: patches/$s/"
        git -C "$repo" am --3way "$pdir/$s/"*.patch || {
            echo "FAIL: $s did not apply cleanly on pristine upstream (+closure)" >&2
            git -C "$repo" am --abort 2>/dev/null
            exit 1
        }
    fi
done

n=$(git -C "$repo" rev-list --count "${pin}..HEAD")
echo "==> applied $n patch(es) for '$slug' (closure: ${streams[*]})"
echo "    build it:  make -C n64/$proj_name/$co/docker appimage"
