#!/usr/bin/env python3
"""Batch 8 — raw memory by index and bare magic: rawData indices → field names, the layer
constants, behaviour-parameter masks.
usage: patch_batch8.py <checkout> <group>   (group: excl_home|jumbo_star|angle_s32|layer_consts|bp_masks)"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
group = sys.argv[2]


def patch(rel, pairs):
    p = root / rel
    s = p.read_text()
    for item in pairs:
        old, new = item[0], item[1]
        want = item[2] if len(item) > 2 else 1
        n = s.count(old)
        assert n == want, f"{rel}: expected {want} match(es) for {old[:60]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


if group == "excl_home":
    patch("src/game/behaviors/exclamation_box.inc.c", [
        ("CALL_CANCELLABLE_EVENT(MacroObjectOverride, a0->model, o->rawData.asF32[0x37], o->rawData.asF32[0x38],\n                                   o->rawData.asF32[0x39]) {",
         "CALL_CANCELLABLE_EVENT(MacroObjectOverride, a0->model, o->oHomeX, o->oHomeY, o->oHomeZ) {"),
    ])
elif group == "jumbo_star":
    patch("include/object_fields.h", [
        ("#define /*0x110*/ oMarioWalkingPitch     OBJECT_FIELD_S32(0x22)\n",
         "#define /*0x110*/ oMarioWalkingPitch     OBJECT_FIELD_S32(0x22)\n#define /*0x110*/ oMarioJumboStarCutscenePosZ OBJECT_FIELD_F32(0x22)\n"),
    ])
    patch("src/game/mario_actions_cutscene.c", [
        ("marioObj->rawData.asF32[0x22]", "marioObj->oMarioJumboStarCutscenePosZ", 3),
    ])
elif group == "angle_s32":
    patch("src/game/object_helpers.c", [
        ("    startAngle = o->rawData.asU32[angleIndex];\n    o->rawData.asU32[angleIndex] = approach_s16_symmetric(startAngle, targetAngle, turnAmount);",
         "    startAngle = o->rawData.asS32[angleIndex];\n    o->rawData.asS32[angleIndex] = approach_s16_symmetric(startAngle, targetAngle, turnAmount);"),
    ])
elif group == "layer_consts":
    patch("src/game/object_helpers.c", [
        ("0x600 | (currentGraphNode->fnNode.node.flags & 0xFF);", "(LAYER_TRANSPARENT_DECAL << 8) | (currentGraphNode->fnNode.node.flags & 0xFF);", 2),
        ("0x100 | (currentGraphNode->fnNode.node.flags & 0xFF);", "(LAYER_OPAQUE << 8) | (currentGraphNode->fnNode.node.flags & 0xFF);"),
    ])
elif group == "bp_masks":
    patch("include/object_constants.h", [
        ("""/* Activated Back-and-Forth Platform */
    /* ((u16)(o->oBehParams >> 16) & 0x0300) >> 8 aka platform type */
    #define ACTIVATED_BF_PLAT_TYPE_BITS_ARROW_PLAT 0
    #define ACTIVATED_BF_PLAT_TYPE_BITFS_MESH_PLAT 1
    #define ACTIVATED_BF_PLAT_TYPE_BITFS_ELEVATOR  2
""",
         """/* Activated Back-and-Forth Platform */
    /* oBehParams >> 16 */
    #define ACTIVATED_BF_PLAT_BP_MASK_MAX_OFFSET 0x007F
    #define ACTIVATED_BF_PLAT_BP_VERTICAL        (1 << 7)
    #define ACTIVATED_BF_PLAT_BP_MASK_TYPE       (0x3 << 8)
    /* ((u16)(o->oBehParams >> 16) & ACTIVATED_BF_PLAT_BP_MASK_TYPE) >> 8 aka platform type */
    #define ACTIVATED_BF_PLAT_TYPE_BITS_ARROW_PLAT 0
    #define ACTIVATED_BF_PLAT_TYPE_BITFS_MESH_PLAT 1
    #define ACTIVATED_BF_PLAT_TYPE_BITFS_ELEVATOR  2

/* Sliding Platform 2 */
    /* oBehParams >> 16 */
    #define SLIDING_PLATFORM_2_BP_MASK_PATH_LENGTH 0x003F
    #define SLIDING_PLATFORM_2_BP_REVERSE          (1 << 6)
    #define SLIDING_PLATFORM_2_BP_MASK_COLLISION   (0x7 << 7)
"""),
    ])
    patch("src/game/behaviors/activated_bf_plat.inc.c", [
        ("((u16)(o->oBehParams >> 16) & 0x0300) >> 8", "((u16)(o->oBehParams >> 16) & ACTIVATED_BF_PLAT_BP_MASK_TYPE) >> 8"),
        ("50.0f * ((u16)(o->oBehParams >> 16) & 0x007F)", "50.0f * ((u16)(o->oBehParams >> 16) & ACTIVATED_BF_PLAT_BP_MASK_MAX_OFFSET)"),
        ("(u16)(o->oBehParams >> 16) & 0x0080;", "(u16)(o->oBehParams >> 16) & ACTIVATED_BF_PLAT_BP_VERTICAL;"),
    ])
    patch("src/game/behaviors/sliding_platform_2.inc.c", [
        ("((u16)(o->oBehParams >> 16) & 0x0380) >> 7", "((u16)(o->oBehParams >> 16) & SLIDING_PLATFORM_2_BP_MASK_COLLISION) >> 7"),
        ("50.0f * ((u16)(o->oBehParams >> 16) & 0x003F)", "50.0f * ((u16)(o->oBehParams >> 16) & SLIDING_PLATFORM_2_BP_MASK_PATH_LENGTH)"),
        ("if ((u16)(o->oBehParams >> 16) & 0x0040) {", "if ((u16)(o->oBehParams >> 16) & SLIDING_PLATFORM_2_BP_REVERSE) {", 2),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
