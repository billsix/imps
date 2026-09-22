#!/usr/bin/env bash
# Batch 7 — UNUSED residue. Named groups first (commit only if IDENTICAL), then the filler-local
# sweep: per file, gate, keep IDENTICAL files, revert the rest, commit the kept per directory.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
run_group() { local grp=$1 msg=$2; shift 2; echo "== $grp"; python3 "$S/patch_batch7.py" "$G" "$grp" || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    if gate "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — reverted, listed for Phase B.11: $*"; git checkout -- "$@"; fi; }

cat > "$W/m7_side.txt" <<'MSG'
game: call the side-effecting initialisers directly instead of through an UNUSED local

`UNUSED f32 sp30 = random_float();` is there for the call, not the value:
the RNG must advance, `object_step()` must move the object, `find_floor`
must run. Writing the call as a statement says so; the dead local said
the opposite.

Verified: each file, through its including translation unit, compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m7_ny.txt" <<'MSG'
game: `ny` in cur_obj_resolve_wall_collisions is used — drop the UNUSED

The attribute was pasted with the filler beside it; `ny` is assigned and
read in the `else if` below.

Verified: object_helpers.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m7_camera.txt" <<'MSG'
game: remove the dead UNUSED locals in camera.c

Locals that are declared, at most initialised or zeroed, and never read:
`cenDistX/Z` (recomputed as `areaDistX/Z` two lines later), `unused1/2`,
`unusedScale`, the zeroed `Vec3f unused`, three bare `unused`, and the
`start`/`end` transition pointers in reset_camera. They were stack-frame
padding to match; the `UNUSED u8 fillerN[]` arrays that do the same job
are removed separately.

Verified: camera.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m7_collision.txt" <<'MSG'
game: remove the dead `sp30` in the two hitbox-overlap functions

`sp30 = sp3C - sp38` is the vertical distance between the two objects'
bottoms, computed and never read in either function (the overlap test
below uses `sp3C`/`sp38` directly).

Verified: object_collision.c compiles to byte-identical assembly before
and after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m7_shape.txt" <<'MSG'
goddard: remove the unreferenced stub animation data and the two sUnref arrays

Three one-frame `GdAnimTransform` tables, their `AnimDataInfo` headers
and two zeroed s32 arrays, all `static`, none referenced anywhere in
goddard. They reproduced the ROM's data layout; the compiler drops them
either way.

Verified: shape_helper.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group side_effects "$W/m7_side.txt" src/game/behaviors/end_birds_1.inc.c src/game/behaviors/end_birds_2.inc.c src/game/behaviors/bowling_ball.inc.c src/game/behaviors/snowman.inc.c src/game/behaviors/red_coin.inc.c
run_group ny           "$W/m7_ny.txt"        src/game/object_helpers.c
run_group camera_dead  "$W/m7_camera.txt"    src/game/camera.c
run_group collision_dead "$W/m7_collision.txt" src/game/object_collision.c
run_group shape_helper_dead "$W/m7_shape.txt" src/goddard/shape_helper.c

echo "==== filler sweep"
FILES=$(grep -rlE '^\s+UNUSED u8 [A-Za-z_0-9]*[fF]iller[A-Za-z_0-9]*\[[^]]*\];\s*$' src --include='*.c' | sort)
echo "files: $(echo $FILES | wc -w)"
KEPT=(); DEFERRED=(); : > "$W/b7_filler_log.txt"
for f in $FILES; do
    out=$(python3 "$TOOL/standard-c/drop_filler_locals.py" "$f" 2>&1) || { echo "!! tool failed on $f"; git checkout -- "$f"; continue; }
    echo "$out" >> "$W/b7_filler_log.txt"
    n=$(grep -oE '^# .*: [0-9]+ deleted' <<<"$out" | grep -oE '[0-9]+ deleted' | grep -oE '^[0-9]+')
    [ "${n:-0}" -gt 0 ] || continue
    r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1)
    case "$r" in
        IDENTICAL*) echo "OK  $f ($n)"; KEPT+=("$f");;
        *) echo "DEF $f ($n): ${r%% —*}"; git checkout -- "$f"; DEFERRED+=("$f");;
    esac
done
echo "== kept: ${#KEPT[@]}  deferred: ${#DEFERRED[@]}"
printf '%s\n' "${DEFERRED[@]}" > "$W/b7_deferred.txt"

commit_dir() { # <dir-label> <pattern>
    local label=$1 pat=$2 files=() n
    for f in "${KEPT[@]}"; do case "$f" in $pat) files+=("$f");; esac; done
    [ ${#files[@]} -gt 0 ] || return 0
    git add "${files[@]}"
    n=$(git diff --cached --numstat | awk '{s+=$2} END {print s}')
    git commit -q -F - <<MSG
$label: remove the function-local \`UNUSED u8 fillerN[]\` stack padding

These arrays exist to reproduce the ROM's stack-frame layout for the
matching build; they are never read or written and the UNUSED attribute
is the only reason the compiler tolerates them. $n declarations across
${#files[@]} file(s) in $label/. Struct members are untouched — the fillers
that fix a layout (save files, object rawData, audio structs) all live in
headers, which this patch does not visit.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1
}
commit_dir engine  'src/engine/*'
commit_dir game    'src/game/*'
commit_dir goddard 'src/goddard/*'
commit_dir menu    'src/menu/*'
commit_dir audio   'src/audio/*'
echo "== uncommitted:"; git status --short | grep -v '^?? \| libultraship' || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -12
