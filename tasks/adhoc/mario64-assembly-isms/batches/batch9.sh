#!/usr/bin/env bash
# Batch 9 — naming: stack-slot locals with an in-file oracle, argN parameters, register-named
# parameters. Renames are compiler-checked; commit a group only when every gated file is IDENTICAL.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
R="$TOOL/standard-c/rename_in_function.py"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
# finish <msgfile> <files...>: gate the non-header files, commit all on success, revert on failure
finish() { local msg=$1; shift; local gated=(); for f in "$@"; do case "$f" in *.h) ;; *) gated+=("$f");; esac; done
    if gate "${gated[@]}"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — reverted: $*"; git checkout -- "$@"; fi; }
ren() { python3 "$R" "$@" || { echo "  !! rename failed: $*"; return 1; }; }

echo "== collision"
ren src/game/object_collision.c detect_object_hitbox_overlap  sp3C=aBottomY sp38=bBottomY sp20=aTopY sp1C=bTopY &&
ren src/game/object_collision.c detect_object_hurtbox_overlap sp3C=aBottomY sp38=bBottomY sp34=dx sp2C=dz sp28=collisionRadius sp24=distance sp20=aTopY sp1C=bTopY &&
cat > "$W/m9_collision.txt" <<'MSG' && finish "$W/m9_collision.txt" src/game/object_collision.c
game: name the stack-slot locals in the two object-overlap tests

detect_object_hurtbox_overlap is detect_object_hitbox_overlap with the
hurtbox radius/height; the hitbox version already names `dx`, `dz`,
`collisionRadius` and `distance`, so the hurtbox twin takes the same
names, and the four Y extents in both become `aBottomY`/`bBottomY`/
`aTopY`/`bTopY` (bottom = position minus the down offset, top = bottom
plus height — the vertical-overlap test below reads as such).

Verified: object_collision.c compiles to byte-identical assembly before
and after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

echo "== mario_args"
ren src/game/mario_actions_stationary.c landing_step arg1=animation &&
ren src/game/mario_actions_stationary.h landing_step arg1=animation &&
ren src/game/mario_actions_moving.c common_ground_knockback_action arg2=accelEndFrame arg3=playHeavyLandingSound arg4=actionArg &&
ren src/game/mario_actions_submerged.c common_water_knockback_step arg3=actionArg &&
cat > "$W/m9_mario.txt" <<'MSG' && finish "$W/m9_mario.txt" src/game/mario_actions_stationary.c src/game/mario_actions_stationary.h src/game/mario_actions_moving.c src/game/mario_actions_submerged.c
game: name the argN parameters of the shared landing and knockback steps

landing_step's `arg1` is the animation it sets. In
common_ground_knockback_action, `arg2` is the frame up to which landing
deceleration applies, `arg3` says whether to play the heavy-landing
sound, and `arg4` is the action argument forwarded to the air-knockback
actions (positive = Mario was attacked, which also grants the
invincibility frames); common_water_knockback_step's `arg3` is that same
action argument (every caller passes m->actionArg).

Verified: all three files compile to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

echo "== behavior_args"
ren src/game/behaviors/king_bobomb.inc.c mario_is_far_below_object arg0=minDistBelow &&
ren src/game/behaviors/eyerok.inc.c eyerok_check_mario_relative_z arg0=maxRelZ &&
ren src/game/obj_behaviors_2.c cur_obj_init_anim_extend arg0=animIndex &&
ren src/game/obj_behaviors_2.c cur_obj_init_anim_and_check_if_end arg0=animIndex &&
ren src/game/obj_behaviors_2.c cur_obj_init_anim_check_frame arg0=animIndex arg1=animFrame &&
ren src/game/obj_behaviors_2.c cur_obj_set_anim_if_at_end arg0=animIndex &&
ren src/game/obj_behaviors_2.c cur_obj_play_sound_at_anim_range arg0=frame1 arg1=frame2 val04=frameStep &&
ren src/game/behaviors/bub.inc.c bub_move_vertically a0=increment sp1C=parentY &&
cat > "$W/m9_beh.txt" <<'MSG' && finish "$W/m9_beh.txt" src/game/behaviors/king_bobomb.inc.c src/game/behaviors/eyerok.inc.c src/game/obj_behaviors_2.c src/game/behaviors/bub.inc.c
game: name the argN / register-named parameters of the small object helpers

mario_is_far_below_object(minDistBelow), eyerok_check_mario_relative_z
(maxRelZ), the five cur_obj_*anim* wrappers in obj_behaviors_2.c
(animIndex, animFrame, frame1/frame2 and the per-tick frameStep derived
from animAccel), and bub_move_vertically(increment — the step handed to
approach_f32_symmetric; parentY for the parent's height it clamps
around).

Verified: every file, through its including translation unit where it is
an .inc.c, compiles to byte-identical assembly before and after with the
port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

echo "== register_params"
ren src/game/object_helpers.c obj_update_pos_from_parent_transformation a0=transform a1=obj spC=relX sp8=relY sp4=relZ &&
ren src/game/object_helpers.h obj_update_pos_from_parent_transformation a0=transform a1=obj &&
ren src/game/object_helpers.c create_transformation_from_matrices a0=dst a1=mtx a2=camMtx spC=transX sp8=transY sp4=transZ &&
ren src/game/object_helpers.h create_transformation_from_matrices a0=dst a1=mtx a2=camMtx &&
ren src/game/object_helpers.c cur_obj_set_vel_from_mario_vel f12=minVel f14=mult sp4=marioVel sp0=minScaledVel &&
ren src/game/object_helpers.h cur_obj_set_vel_from_mario_vel f12=minVel f14=mult &&
ren src/game/object_helpers.c cur_obj_check_frame_prior_current_frame a0=frames sp6=animFrame &&
ren src/game/object_helpers.h cur_obj_check_frame_prior_current_frame a0=frames &&
cat > "$W/m9_reg.txt" <<'MSG' && finish "$W/m9_reg.txt" src/game/object_helpers.c src/game/object_helpers.h
game: name the parameters that were called after their MIPS argument registers

`a0`/`a1`/`a2` and `f12`/`f14` are the registers the arguments arrived
in, not what they are. obj_update_pos_from_parent_transformation takes a
transform and the object whose parent-relative position it maps
(relX/Y/Z); create_transformation_from_matrices writes `dst` from `mtx`
and the camera matrix (every caller passes *gCurGraphNodeCamera->
matrixPtr), with the camera translation projected onto its axes as
transX/Y/Z; cur_obj_set_vel_from_mario_vel sets the object's forward
velocity to max(marioVel, minVel) * mult; cur_obj_check_frame_prior_
current_frame walks a -1-terminated list of frames.

Verified: object_helpers.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

echo "== uncommitted:"; git status --short | grep -v '^?? \| libultraship' || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -5
