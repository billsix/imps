#!/usr/bin/env bash
# Batch 10 — constructs the regexes missed. Commit a group only when every gated file is IDENTICAL.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
run_group() { local grp=$1 msg=$2; shift 2; echo "== $grp"; python3 "$S/patch_batch10.py" "$G" "$grp" || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    if gate "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — reverted, listed for Phase B.11: $*"; git checkout -- "$@"; fi; }

cat > "$W/m10_tilt_bool.txt" <<'MSG'
game: set the tilting pyramid's marioOnPlatform flag instead of incrementing it

`marioOnPlatform` starts FALSE and is tested with `if (marioOnPlatform)`;
the `++` that turns it on is a boolean assignment written for a MIPS
`addiu`.

Verified: tilting_inverted_pyramid.inc.c, through its including
translation unit, compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m10_tilt_else.txt" <<'MSG'
game: drop the unreachable zero-length branch in the tilting pyramid normaliser

`d = sqrtf(dx*dx + 500*500 + dz*dz)` is at least 500, which the decomp's
own `//!` note already says; the `else` that would handle d == 0 cannot
run.

Verified: tilting_inverted_pyramid.inc.c, through its including
translation unit, compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m10_bowser_inc.txt" <<'MSG'
game: set oBowserIsReacting instead of incrementing it

Both `++` sites sit under `if (!o->oBowserIsReacting)`, so they take the
flag from FALSE to TRUE; every other write is `= TRUE` / `= FALSE`.

Verified: bowser.inc.c, through its including translation unit, compiles
to byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m10_bowser_switch.txt" <<'MSG'
game: `if`/`else` instead of `switch` on the boolean oBowserIsReacting

bowser_bits_actions switches on a flag that is only ever TRUE or FALSE
(the remaining writes are `= TRUE` / `= FALSE`); a two-case switch on a
boolean is an if/else.

Verified: bowser.inc.c, through its including translation unit, compiles
to byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m10_yoda.txt" <<'MSG'
game: `actionTimer++ > 15` instead of `15 < actionTimer++` in the two exit actions

The constant-first spelling is the compiler's operand order, not the
reader's.

Verified: mario_actions_cutscene.c compiles to byte-identical assembly
before and after with the port's own flags (asmdiff over
compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m10_if_false.txt" <<'MSG'
goddard: delete the empty `if (FALSE) {}` in draw_face

A statement that can neither run nor be reached, kept only because the
matching build needed the basic block.

Verified: draw_objects.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group tilting_bool       "$W/m10_tilt_bool.txt"     src/game/behaviors/tilting_inverted_pyramid.inc.c
run_group tilting_dead_else  "$W/m10_tilt_else.txt"     src/game/behaviors/tilting_inverted_pyramid.inc.c
run_group bowser_bool_inc    "$W/m10_bowser_inc.txt"    src/game/behaviors/bowser.inc.c
run_group bowser_switch_bool "$W/m10_bowser_switch.txt" src/game/behaviors/bowser.inc.c
run_group yoda               "$W/m10_yoda.txt"          src/game/mario_actions_cutscene.c
run_group if_false           "$W/m10_if_false.txt"      src/goddard/draw_objects.c
echo "== uncommitted:"; git status --short | grep -v '^?? \| libultraship' || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -7
