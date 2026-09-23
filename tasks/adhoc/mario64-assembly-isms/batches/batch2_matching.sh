#!/usr/bin/env bash
# Batch 2 — matching-era residue, one commit per directory/class, gate every file.
set -e
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }

echo "== goddard: lone ';' and the unreachable break"
python3 "$S/patch_batch2.py" "$G" goddard
F="src/goddard/draw_objects.c src/goddard/joints.c src/goddard/particles.c src/goddard/renderer.c"
gate $F; git add $F
git commit -q -F - <<'MSG'
goddard: delete the empty statements and the unreachable `break` kept "to match"

Five `; // needed to match` lines (draw_objects.c x3, joints.c, particles.c)
are empty statements that only nudged IDO's instruction scheduling, and
gd_printf's second `break;` after a `break;` (renderer.c) is unreachable.
None of them exists at the C level; delete them with their comments. The one
comment that carried a real note ("presumably setting up the color to draw
the plane with") is kept as a plain comment.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

echo "== game/camera.c: do { } while (0) wrappers and same-line-to-match"
python3 "$S/patch_batch2.py" "$G" camera
gate src/game/camera.c; git add src/game/camera.c
git commit -q -F - <<'MSG'
camera: unwrap four `do { … } while (0);` and two same-line-to-match statements

copy_spline_segment (already marked "TODO: (Scrub C)") wraps four single
init_spline_point calls in `do { … } while (0);` — a constant-false loop with
no break/continue inside is the statement it wraps. Two other sites kept a
statement on the `if` line or two statements on one line "to match on -O2";
give them braces and one statement per line and drop the comments.

Verified: camera.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

echo "== game: one-line-to-match one-liners"
python3 "$S/patch_batch2.py" "$G" game
F="src/game/mario_actions_airborne.c src/game/mario_actions_submerged.c src/game/game_init.c src/game/level_update.c src/game/behaviors/fish.inc.c"
gate $F; git add $F
git commit -q -F - <<'MSG'
game: braces and one statement per line where "one line to match on -O2" was the only reason

Five sites keep a statement on the `if`/`for`/`case` line (two of them
fenced with `// clang-format off`) because IDO only produced the ROM's code
that way. The port does not match a ROM; write them as ordinary braced
statements, one per line, and delete the comments and fences with them.
fish.inc.c's four column-aligned multi-assignment cases become four
assignments each.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

echo "== engine/math_util.c: mtxf_identity loops"
python3 "$S/patch_batch2.py" "$G" engine
gate src/engine/math_util.c; git add src/engine/math_util.c
git commit -q -F - <<'MSG'
engine: brace the two one-line loops in mtxf_identity

"These loops must be one line to match on -O2" no longer applies; give
each loop body its braces and drop the comment.

Verified: math_util.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

echo "== audio: dead struct vNote"
python3 "$S/patch_batch2.py" "$G" audio
gate src/audio/synthesis.c; git add src/audio/internal.h src/audio/synthesis.c
git commit -q -F - <<'MSG'
audio: remove the unreferenced `struct vNote` and refresh the comment that described it

`struct vNote` (a twin of `struct Note` with a `volatile` bitfield) existed
so synthesis_process_notes could be cast to it and read `enabled` through a
volatile access, reproducing IDO's codegen. Nothing references the type any
more; the two `//!` lines in synthesis.c describe a workaround that is not
in the tree. Delete the struct and say what the comment used to mean.

Verified: synthesis.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1
echo "== residue:"; grep -rn "needed to match\|one line to match\|same line to match\|while (0);" src/game src/engine src/goddard src/audio src/menu | grep -v "^src/audio/.*#\|copt\|load_sh\|port_sh\|port_eu" || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD
