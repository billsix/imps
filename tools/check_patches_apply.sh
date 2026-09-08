#!/usr/bin/env bash
#
# check_patches_apply.sh -- prove every project's patch series still applies
# cleanly onto its pin.
#
# WHY THIS IS THE MOST IMPORTANT GATE IN THE REPO
#   imps exists so the maintainer's patches keep WORKING over time, across
#   machines, as he pulls from upstream -- goal 0 in the master CLAUDE.md.
#   A patch that no longer applies has failed at its primary job. Until now
#   that invariant was only ever spot-checked by hand.
#
# WHAT IT DOES, per project
#   Resets the checkout to the pin from fetch.sh and runs the project's own
#   apply.sh -- so it exercises the REAL apply path, including stream ORDER,
#   both lanes (game tree + libultraship), and the pin guard. Then reports the
#   commit count per lane.
#
# WHAT IT LEAVES BEHIND
#   The checkout on the fully-applied series -- which is its documented default
#   working state (master CLAUDE.md, "Working on a project"). So running this is
#   also how you get every project back into a known-good state.
#
#   It never touches runDir/ (saves, extracted .o2r, texture-pack mods): that is
#   a SIBLING of the checkout, not inside it, so no git command here can reach
#   it. See "runDir/ IS SACRED" in the master CLAUDE.md.
#
# USAGE
#   tools/check_patches_apply.sh [project ...]      # default: every project
#   tools/check_patches_apply.sh OcarinaOfTime
#
# Exits non-zero if any project's series fails to apply.
#
# WHEN A PROJECT FAILS
#   That is the pin-bump conflict surfacing early, which is the point. Rebase
#   the series onto the new pin (the pin-bump operation in the master
#   CLAUDE.md), regenerate the affected stream, and re-run.

set -u

cd "$(dirname "$0")/.."                 # imps repo root
ROOT=$PWD
status=0
ok_count=0
skipped=()
failed=()

projects=("$@")
if [ "${#projects[@]}" -eq 0 ]; then
    mapfile -t projects < <(find n64 -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort)
fi

# The upstream checkout inside a project: the one subdirectory holding a .git.
checkout_for() {
    local proj=$1 d
    for d in "$proj"/*/; do
        [ -e "$d/.git" ] && { basename "$d"; return; }
    done
}

for name in "${projects[@]}"; do
    proj=$ROOT/n64/$name
    [ -f "$proj/apply.sh" ] || { skipped+=("$name (docs-only: no apply.sh)"); continue; }
    co=$(checkout_for "$proj")
    [ -z "$co" ] && { skipped+=("$name (no checkout -- run ./fetch.sh)"); continue; }

    repo=$proj/$co
    pin=$(sed -n 's/^PIN_SHA=//p' "$proj/fetch.sh")
    echo
    echo "############ $name ############"
    echo "  checkout $co @ ${pin:0:9}"

    if [ -d "$repo/.git/rebase-apply" ]; then
        echo "  FAIL: interrupted 'git am' -- run: git -C $repo am --abort"
        failed+=("$name (interrupted git am)")
        status=1
        continue
    fi
    if ! git -C "$repo" cat-file -e "${pin}^{commit}" 2>/dev/null; then
        echo "  FAIL: the pin is not in the checkout -- run ./fetch.sh"
        failed+=("$name (pin missing)")
        status=1
        continue
    fi

    # Reset the GAME tree to the pin. Scope the clean to the checkout; runDir/
    # is outside it and is never at risk.
    git -C "$repo" checkout -q --detach "$pin"
    git -C "$repo" reset -q --hard "$pin"
    git -C "$repo" clean -qfd

    # Reset the libultraship submodule too, when that lane carries patches.
    if ls "$proj"/patches-libultraship/*/*.patch >/dev/null 2>&1; then
        lus_pin=$(git -C "$repo" rev-parse "${pin}:libultraship" 2>/dev/null)
        if [ -n "${lus_pin:-}" ]; then
            git -C "$repo/libultraship" checkout -q --detach "$lus_pin"
            git -C "$repo/libultraship" reset -q --hard "$lus_pin"
        fi
    fi

    if ( cd "$proj" && ./apply.sh ) > /tmp/cpa-$name.log 2>&1; then
        game=$(git -C "$repo" rev-list --count "${pin}..HEAD")
        line="  ok: $game patch(es) applied to the game tree"
        if ls "$proj"/patches-libultraship/*/*.patch >/dev/null 2>&1; then
            lus=$(git -C "$repo/libultraship" rev-list --count "${lus_pin}..HEAD" 2>/dev/null || echo 0)
            line="$line, $lus to libultraship"
        fi
        echo "$line"
        grep '^apply .*stream:' /tmp/cpa-$name.log | sed 's/^/    /'
        ok_count=$((ok_count + 1))
    else
        echo "  FAIL: apply.sh failed -- see /tmp/cpa-$name.log"
        tail -5 /tmp/cpa-$name.log | sed 's/^/    /'
        git -C "$repo" am --abort 2>/dev/null
        failed+=("$name")
        status=1
    fi
done

echo
echo "############ SUMMARY ############"
echo "  applied cleanly : $ok_count"
for s in ${skipped[@]+"${skipped[@]}"}; do echo "  skipped         : $s"; done
for f in ${failed[@]+"${failed[@]}"}; do echo "  FAILED          : $f"; done
exit "$status"
