#!/usr/bin/env bash
# Batch 8 — raw memory by index and bare magic. Commit a group only when every gated file is IDENTICAL.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
# run_group <group> <msgfile> <files-to-commit...> -- the gate runs over the .c/.inc.c files only (headers ride along)
run_group() { local grp=$1 msg=$2; shift 2; local gated=(); for f in "$@"; do case "$f" in *.h) ;; *) gated+=("$f");; esac; done
    echo "== $grp"; python3 "$S/patch_batch8.py" "$G" "$grp" || { echo "  patch failed"; git checkout -- "$@"; return 1; }
    if gate "${gated[@]}"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — reverted, listed for Phase B.11: $*"; git checkout -- "$@"; fi; }

cat > "$W/m8_excl.txt" <<'MSG'
game: name the home position instead of indexing rawData in the exclamation box

`o->rawData.asF32[0x37..0x39]` is `oHomeX/Y/Z` — the same three slots
every other behaviour reads through the field macros.

Verified: exclamation_box.inc.c, through its including translation unit,
compiles to byte-identical assembly before and after with the port's own
flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m8_jumbo.txt" <<'MSG'
game: give the jumbo-star cutscene's rawData slot a field name

`marioObj->rawData.asF32[0x22]` holds Mario's Z position while he floats
up during the final-Bowser star cutscene (it is zeroed, decremented, and
passed as the Z of vec3f_set). Every other cutscene alias of slot 0x22
has a name in object_fields.h; this adds `oMarioJumboStarCutscenePosZ`
beside them and uses it at the three sites.

Verified: mario_actions_cutscene.c compiles to byte-identical assembly
before and after with the port's own flags (asmdiff over
compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m8_angle.txt" <<'MSG'
game: read and write the angle slot as s32 in obj_turn_toward_object

`angleIndex` selects one of the oMoveAngle*/oFaceAngle* fields, all of
which are OBJECT_FIELD_S32; going through `asU32` only to assign into an
s16 and back is the same 32-bit load and store spelled with the wrong
sign.

Verified: object_helpers.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m8_layer.txt" <<'MSG'
game: spell the render layers by name in geo_switch_anim_state's opacity switch

`0x600 | (flags & 0xFF)` and `0x100 | (flags & 0xFF)` set the layer byte
to LAYER_TRANSPARENT_DECAL and LAYER_OPAQUE, which is how bowser.inc.c,
mario_misc.c, paintings.c and intro_geo.c already write the same update.

Verified: object_helpers.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m8_bp.txt" <<'MSG'
game: name the behaviour-parameter bit fields of the two back-and-forth platforms

activated_bf_plat and sliding_platform_2 unpack oBehParams with bare
masks (`0x0300`, `0x007F`, `0x0080`; `0x0380`, `0x003F`, `0x0040`). This
adds the masks to object_constants.h in the PLATFORM_ON_TRACK_BP_* idiom,
next to the ACTIVATED_BF_PLAT_TYPE_* values that already document the
type field, and uses them at the six sites.

Verified: both files, through their including translation units, compile
to byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group excl_home    "$W/m8_excl.txt"  src/game/behaviors/exclamation_box.inc.c
run_group jumbo_star   "$W/m8_jumbo.txt" include/object_fields.h src/game/mario_actions_cutscene.c
run_group angle_s32    "$W/m8_angle.txt" src/game/object_helpers.c
run_group layer_consts "$W/m8_layer.txt" src/game/object_helpers.c
run_group bp_masks     "$W/m8_bp.txt"    include/object_constants.h src/game/behaviors/activated_bf_plat.inc.c src/game/behaviors/sliding_platform_2.inc.c
echo "== uncommitted:"; git status --short | grep -v '^?? \| libultraship' || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -6
