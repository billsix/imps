#!/usr/bin/env bash
# Batch 6 — 16-bit residue. Commit a group only when every touched file gates IDENTICAL.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
run_group() { local grp=$1 msg=$2; shift 2; echo "== $grp"; python3 "$S/patch_batch6.py" "$G" "$grp" || { echo "  patch failed"; return 1; }
    if gate "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — reverted, listed for Phase B.11: $*"; git checkout -- "$@"; fi; }

cat > "$W/m6_bs.txt" <<'MSG'
engine: drop the `& 0xFFFF` before the s16 stores in obj_update_gfx_pos_and_angle

`gfx.angle` is a Vec3s; storing an s32 into an s16 keeps the low 16 bits
whether or not they were masked first, so the mask only restates what
the assignment already does.

Verified: behavior_script.c compiles to byte-identical assembly before
and after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m6_oh.txt" <<'MSG'
game: drop the `& 0xFFFF` before the s16 stores in obj_set_gfx_pos_at_obj_pos

Same as the engine twin (obj_update_gfx_pos_and_angle): `gfx.angle` is a
Vec3s, so the store keeps the low 16 bits with or without the mask.

Verified: object_helpers.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m6_cutscene.txt" <<'MSG'
game: write the two `<< 16 >> 16` angle-difference wraps as `(s16)` casts

`(a - b) << 16 >> 16` is the MIPS idiom for "sign-extend the low half";
in C, left-shifting a negative int is undefined behaviour, while the cast
to s16 is the conversion the code means (and what GCC compiles it to).

Verified: mario_actions_cutscene.c compiles to byte-identical assembly
before and after with the port's own flags (asmdiff over
compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m6_rotating.txt" <<'MSG'
game: multiply instead of left-shifting a signed platform speed

`sp1F` is an s8 read from the top byte of oBehParams and is routinely
negative (platforms rotate both ways); `sp1F << 4` on a negative value is
undefined behaviour in C, `sp1F * 16` is not, and both produce the same
bits on every target.

Verified: rotating_platform.inc.c, through obj_behaviors.c, compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m6_pokey.txt" <<'MSG'
game: multiply instead of left-shifting the pokey death-delay parameter

`oBehParams2ndByte << 2` is a multiplication written for the MIPS `sll`;
`* 4` says so and is defined for negative values too (the field is an
s32 that other spawners fill from an s16 behaviour-command operand).

Verified: pokey.inc.c, through obj_behaviors_2.c, compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m6_save.txt" <<'MSG'
game: spell the EEPROM offset the same way in read and write, and put the buffer first

read_eeprom_data divides the byte offset by 8 and write_eeprom_data shifts
it right by 3; both are the same unsigned division. The two signature
functions compute `(size - 4) + (u8 *) buffer` — integer first, pointer
second — the reversed order `(u8 *) buffer + size - 4` is how the address
of the trailing signature block reads.

Verified: save_file.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group bs_mask      "$W/m6_bs.txt"       src/engine/behavior_script.c
run_group oh_mask      "$W/m6_oh.txt"       src/game/object_helpers.c
run_group cutscene_s16 "$W/m6_cutscene.txt" src/game/mario_actions_cutscene.c
run_group rotating     "$W/m6_rotating.txt" src/game/behaviors/rotating_platform.inc.c
run_group pokey        "$W/m6_pokey.txt"    src/game/behaviors/pokey.inc.c
run_group save_file    "$W/m6_save.txt"     src/game/save_file.c
echo "== uncommitted:"; git status --short | grep -v "^?? \| libultraship" || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -7
