#!/usr/bin/env python3
"""Batch 7 — UNUSED residue: side-effecting initialisers hidden behind an UNUSED local, an UNUSED
that lies, dead UNUSED locals, and dead UNUSED file-scope data.
usage: patch_batch7.py <checkout> <group>   (group: side_effects|ny|camera_dead|collision_dead|shape_helper_dead)"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
group = sys.argv[2]


def patch(rel, pairs):
    p = root / rel
    s = p.read_text()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f"{rel}: expected exactly one match for {old[:60]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


if group == "side_effects":
    patch("src/game/behaviors/end_birds_1.inc.c", [
        ("    Vec3f sp34;\n    UNUSED f32 sp30 = random_float();\n",
         "    Vec3f sp34;\n\n    random_float();\n"),
    ])
    patch("src/game/behaviors/end_birds_2.inc.c", [
        ("    Vec3f sp3C;\n    UNUSED f32 sp38 = random_float();\n    f32 sp34;\n    s16 sp32, sp30;\n\n",
         "    Vec3f sp3C;\n    f32 sp34;\n    s16 sp32, sp30;\n\n    random_float();\n"),
    ])
    patch("src/game/behaviors/bowling_ball.inc.c", [
        ("    struct FloorGeometry *sp1c;\n    UNUSED s16 collisionFlags = object_step();\n\n",
         "    struct FloorGeometry *sp1c;\n\n    object_step();\n"),
    ])
    patch("src/game/behaviors/snowman.inc.c", [
        ("void snowmans_bottom_act_2(void) {\n    UNUSED s16 collisionFlags = object_step_without_floor_orient();\n",
         "void snowmans_bottom_act_2(void) {\n    object_step_without_floor_orient();\n"),
    ])
    patch("src/game/behaviors/red_coin.inc.c", [
        ("    struct Surface *dummyFloor;\n    UNUSED f32 floorHeight = find_floor(o->oPosX, o->oPosY, o->oPosZ, &dummyFloor);\n",
         "    struct Surface *dummyFloor;\n    find_floor(o->oPosX, o->oPosY, o->oPosZ, &dummyFloor);\n"),
    ])
elif group == "ny":
    patch("src/game/object_helpers.c", [
        ("    UNUSED u8 filler[4];\n    UNUSED f32 ny;\n", "    UNUSED u8 filler[4];\n    f32 ny;\n"),
    ])
elif group == "camera_dead":
    patch("src/game/camera.c", [
        ("    UNUSED f32 cenDistX = sMarioCamState->pos[0] - c->areaCenX;\n    UNUSED f32 cenDistZ = sMarioCamState->pos[2] - c->areaCenZ;\n    s16 camYaw = s8DirModeBaseYaw", "    s16 camYaw = s8DirModeBaseYaw"),
        ("    s32 avoidStatus;\n    UNUSED s16 unused1 = 0;\n    UNUSED s32 unused2 = 0;\n", "    s32 avoidStatus;\n"),
        ("    UNUSED u8 filler3[8];\n    UNUSED f32 unusedScale = 0.5f;\n    f32 parScale = 0.5f;\n", "    UNUSED u8 filler3[8];\n    f32 parScale = 0.5f;\n"),
        ("    UNUSED u8 filler4[12];\n    UNUSED Vec3f unused;\n    Vec3s pathAngle;\n", "    UNUSED u8 filler4[12];\n    Vec3s pathAngle;\n"),
        ("    unused[0] = 0.f;\n    unused[1] = 0.f;\n    unused[2] = 0.f;\n\n    // Store camera pos, for changing between paths\n", "    // Store camera pos, for changing between paths\n"),
        ("    UNUSED u8 filler4[4];\n    UNUSED s16 unused;\n    s16 yaw;\n    s16 heldState;\n", "    UNUSED u8 filler4[4];\n    s16 yaw;\n    s16 heldState;\n"),
        ("s32 update_spiral_stairs_camera(struct Camera *c, Vec3f focus, Vec3f pos) {\n    UNUSED s16 unused;\n    /// The returned yaw\n", "s32 update_spiral_stairs_camera(struct Camera *c, Vec3f focus, Vec3f pos) {\n    /// The returned yaw\n"),
        ("void reset_camera(struct Camera *c) {\n    UNUSED s32 unused = 0;\n    UNUSED u8 filler[16];\n    UNUSED struct LinearTransitionPoint *start = &sModeInfo.transitionStart;\n    UNUSED struct LinearTransitionPoint *end = &sModeInfo.transitionEnd;\n",
         "void reset_camera(struct Camera *c) {\n    UNUSED u8 filler[16];\n"),
        ("    UNUSED u8 filler[34]; // Debug print buffer? ;)\n    UNUSED s32 unused1 = 0;\n    UNUSED s32 unused2 = 0;\n", "    UNUSED u8 filler[34]; // Debug print buffer? ;)\n"),
        ("    s16 yaw;\n    UNUSED u16 unused;\n    f32 focFloorYOff;\n", "    s16 yaw;\n    f32 focFloorYOff;\n"),
    ])
elif group == "collision_dead":
    patch("src/game/object_collision.c", [
        ("    f32 dx = a->oPosX - b->oPosX;\n    UNUSED f32 sp30 = sp3C - sp38;\n    f32 dz = a->oPosZ - b->oPosZ;\n",
         "    f32 dx = a->oPosX - b->oPosX;\n    f32 dz = a->oPosZ - b->oPosZ;\n"),
        ("    f32 sp34 = a->oPosX - b->oPosX;\n    UNUSED f32 sp30 = sp3C - sp38;\n    f32 sp2C = a->oPosZ - b->oPosZ;\n",
         "    f32 sp34 = a->oPosX - b->oPosX;\n    f32 sp2C = a->oPosZ - b->oPosZ;\n"),
    ])
elif group == "shape_helper_dead":
    patch("src/goddard/shape_helper.c", [
        ("""// Not sure what this data is, but it looks like stub animation data

static struct GdAnimTransform unusedAnimData1[] = {
    { {1.0, 1.0, 1.0}, {0.0, 0.0, 0.0}, {0.0, 0.0, 0.0} },
};

UNUSED static struct AnimDataInfo unusedAnim1 = { ARRAY_COUNT(unusedAnimData1), GD_ANIM_SCALE3F_ROT3F_POS3F_2, unusedAnimData1 };

static struct GdAnimTransform unusedAnimData2[] = {
    { {1.0, 1.0, 1.0}, {0.0, 0.0, 0.0}, {0.0, 0.0, 0.0} },
};

UNUSED static struct AnimDataInfo unusedAnim2 = { ARRAY_COUNT(unusedAnimData2), GD_ANIM_SCALE3F_ROT3F_POS3F_2, unusedAnimData2 };

static struct GdAnimTransform unusedAnimData3[] = {
    { {1.0, 1.0, 1.0}, {0.0, 0.0, 0.0}, {0.0, 0.0, 0.0} },
};

UNUSED static struct AnimDataInfo unusedAnim3 = { ARRAY_COUNT(unusedAnimData3), GD_ANIM_SCALE3F_ROT3F_POS3F_2, unusedAnimData3 };

UNUSED static s32 sUnref801A838C[6] = { 0 };
struct ObjShape *sSimpleShape = NULL;
UNUSED static s32 sUnref801A83A8[31] = { 0 };
""",
         """struct ObjShape *sSimpleShape = NULL;
"""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
