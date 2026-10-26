#!/usr/bin/env bash
#
# check_upstreamable_applies.sh -- prove every upstreamable UNIT applies on
# pristine upstream in ISOLATION, and enforce the invariant that makes a unit
# submittable.
#
# THE INVARIANT
#   An `upstreamable-<slug>` unit may depend only on pristine upstream and OTHER
#   upstreamable units -- NEVER on a personal/cheats/book patch. If a candidate
#   needs your cheats to apply, it is not upstreamable; that dependency is the
#   bug. This gate fails if any unit's DEPENDS closure pulls in a
#   non-`upstreamable-*` stream, and if the unit does not `git am` cleanly on the
#   bare pin + its closure.
#
# RELATION TO check_patches_apply.sh
#   That gate proves the WHOLE series (your personal stack) still applies -- goal
#   0. This gate proves each PR-sized unit stands on its own on upstream -- goal 1
#   (master CLAUDE.md, "Patch philosophy"). Both matter; they answer different
#   questions.
#
# USAGE
#   tools/check_upstreamable_applies.sh [Project [slug]]   # default: every project
#   tools/check_upstreamable_applies.sh --build [Project [slug]]  # also build the AppImage
#
# Host-side (git only) unless --build. Leaves each checkout on the LAST isolated
# unit's branch -- run tools/check_patches_apply.sh afterwards to restore the
# full-series working state. Never touches runDir/.

set -u
cd "$(dirname "$0")/.."
ROOT=$PWD
HERE=$ROOT/tools

do_build=0
if [ "${1:-}" = "--build" ]; then do_build=1; shift; fi
one_proj=${1:-}
one_slug=${2:-}

status=0
ok=0
bad=()

if [ -n "$one_proj" ]; then
    projects=("$one_proj")
else
    mapfile -t projects < <(find n64 -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort)
fi

for name in "${projects[@]}"; do
    proj=$ROOT/n64/$name
    pdir=$proj/patches
    [ -d "$pdir" ] || continue

    # upstreamable units in this project (optionally just the one named).
    mapfile -t units < <(for s in "$pdir"/upstreamable-*/; do [ -d "$s" ] && basename "$s"; done)
    [ "${#units[@]}" -eq 0 ] && continue

    echo
    echo "############ $name ############"
    for slug in "${units[@]}"; do
        [ -n "$one_slug" ] && [ "$slug" != "$one_slug" ] && continue

        # Invariant: the DEPENDS closure must be all upstreamable-*.
        mapfile -t cl < <("$HERE/apply_unit.sh" --closure "$name" "$slug") || {
            echo "  $slug: FAIL (closure error)"; bad+=("$name/$slug"); status=1; continue; }
        bad_dep=""
        for s in "${cl[@]}"; do
            case "$s" in upstreamable-*) ;; *) bad_dep="$s"; break;; esac
        done
        if [ -n "$bad_dep" ]; then
            echo "  $slug: FAIL -- depends on non-upstreamable stream '$bad_dep' (closure: ${cl[*]})"
            bad+=("$name/$slug"); status=1; continue
        fi

        # Apply the closure on the bare pin.
        if "$HERE/apply_unit.sh" "$name" "$slug" >/tmp/cua-$name-$slug.log 2>&1; then
            n=$(grep -oE 'applied [0-9]+ patch' /tmp/cua-$name-$slug.log | grep -oE '[0-9]+' | head -1)
            dep_note=""
            [ "${#cl[@]}" -gt 1 ] && dep_note=" (closure: ${cl[*]})"
            if [ "$do_build" -eq 1 ]; then
                co=""; for d in "$proj"/*/; do [ -e "$d/.git" ] && { co=$(basename "$d"); break; }; done
                if make -C "$proj/$co/docker" appimage >/tmp/cua-$name-$slug-build.log 2>&1; then
                    echo "  $slug: OK -- ${n:-?} patch(es) apply + AppImage built$dep_note"
                else
                    echo "  $slug: APPLY-OK but BUILD FAILED -- see /tmp/cua-$name-$slug-build.log$dep_note"
                    bad+=("$name/$slug (build)"); status=1; continue
                fi
            else
                echo "  $slug: OK -- ${n:-?} patch(es) apply on pristine upstream$dep_note"
            fi
            ok=$((ok + 1))
        else
            echo "  $slug: FAIL -- does not apply in isolation (see /tmp/cua-$name-$slug.log)"
            tail -4 /tmp/cua-$name-$slug.log | sed 's/^/      /'
            bad+=("$name/$slug"); status=1
        fi
    done
done

echo
echo "############ SUMMARY ############"
echo "  units OK : $ok"
for b in ${bad[@]+"${bad[@]}"}; do echo "  FAILED   : $b"; done
echo "  (checkouts left on isolated unit branches; run tools/check_patches_apply.sh to restore)"
exit "$status"
