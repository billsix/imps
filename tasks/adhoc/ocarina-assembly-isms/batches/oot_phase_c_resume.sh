#!/usr/bin/env bash
# Resume Phase C step 3 from a stopped `git am` on imps-applied, then steps 4-5.
set -u
. "$(dirname "$0")/oot_lib.sh"
OOTTOOL="$IMPS/tools/standard-c"
P="$IMPS/n64/OcarinaOfTime"; LOG="$W/oot_phase_c.log"
[ "$(git branch --show-current)" = imps-applied ] || git checkout -q imps-applied
RESOLVED=(); UNRESOLVED=()
resolve_current() { # the patch whose `git am` stopped: resolve, add, continue
    local p=$1 conflicted; conflicted=$(git diff --name-only --diff-filter=U)
    [ -n "$conflicted" ] || { echo "  !! $(basename "$p") failed without conflicts"; git am --abort; UNRESOLVED+=("$(basename "$p")"); return 1; }
    if python3 "$IMPS/tools/resolve_rename_conflicts.py" "$G" "$p" $conflicted >>"$LOG" 2>&1; then
        git add $conflicted; GIT_EDITOR=true git am --continue -q >>"$LOG" 2>&1 || { echo "  !! continue failed on $(basename "$p")"; UNRESOLVED+=("$(basename "$p")"); return 1; }
        RESOLVED+=("$(basename "$p"): $(echo "$conflicted" | tr '\n' ' ')"); return 0
    fi
    echo "  !! unresolved conflict in $(basename "$p"): $conflicted"; UNRESOLVED+=("$(basename "$p")"); return 1
}
if [ -d .git/rebase-apply ]; then
    n=$(git rev-list --count imps-standard-c..HEAD); cur=$(printf '%04d' $((n + 1)))
    echo "== resuming at patch $cur"; resolve_current "$P/patches/personal/$cur"-*.patch || { echo "STOPPED"; exit 3; }
fi
n=$(git rev-list --count imps-standard-c..HEAD)
for p in "$P/patches/personal"/*.patch; do
    num=$(basename "$p" | cut -d- -f1); [ "$((10#$num))" -gt "$n" ] || continue
    git -c merge.conflictStyle=diff3 am -q --3way "$p" >>"$LOG" 2>&1 && continue
    resolve_current "$p" || { echo "STOPPED (git am in progress)"; exit 3; }
done
echo "  applied: $(git rev-list --count imps-standard-c..HEAD) of 488; resolved this run: ${#RESOLVED[@]}"
printf '%s\n' "${RESOLVED[@]}" >> "$W/oot_phase_c_resolved.txt"
echo "== 4. rename totality gates"
(cd "$P" && python3 tools/check_renames.py series 2>&1 | tail -5)
(cd "$P" && python3 tools/check_renames.py traceable 2>&1 | tail -3)
(cd "$P" && python3 tools/check_renames.py declarations 2>&1 | tail -3)
echo "== 5. re-export personal against the standard-c tip"
rm -f "$P/patches/personal"/*.patch
git format-patch --no-cover-letter --base=imps-standard-c imps-standard-c..imps-applied -o "$P/patches/personal/" >/dev/null; ls "$P/patches/personal" | wc -l
echo "PHASE C DONE (checkout on imps-applied)"
