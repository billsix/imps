#!/usr/bin/env python3
"""Batch 6 — 16-bit residue: masks before an s16 store, `<< 16 >> 16` as sign-narrowing, shifts
used as multiplication on signed values, and save_file.c's mixed `/ 8` vs `>> 3` + operand order.
usage: patch_batch6.py <checkout> <group>   (group: bs_mask|oh_mask|cutscene_s16|rotating|pokey|save_file)"""
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


if group == "bs_mask":
    patch("src/engine/behavior_script.c", [
    ("""    obj->header.gfx.angle[0] = obj->oFaceAnglePitch & 0xFFFF;
    obj->header.gfx.angle[1] = obj->oFaceAngleYaw & 0xFFFF;
    obj->header.gfx.angle[2] = obj->oFaceAngleRoll & 0xFFFF;""",
     """    obj->header.gfx.angle[0] = obj->oFaceAnglePitch;
    obj->header.gfx.angle[1] = obj->oFaceAngleYaw;
    obj->header.gfx.angle[2] = obj->oFaceAngleRoll;"""),
    ])
elif group == "oh_mask":
    patch("src/game/object_helpers.c", [
    ("""    obj1->header.gfx.angle[0] = obj2->oMoveAnglePitch & 0xFFFF;
    obj1->header.gfx.angle[1] = obj2->oMoveAngleYaw & 0xFFFF;
    obj1->header.gfx.angle[2] = obj2->oMoveAngleRoll & 0xFFFF;""",
     """    obj1->header.gfx.angle[0] = obj2->oMoveAnglePitch;
    obj1->header.gfx.angle[1] = obj2->oMoveAngleYaw;
    obj1->header.gfx.angle[2] = obj2->oMoveAngleRoll;"""),
    ])
elif group == "cutscene_s16":
    patch("src/game/mario_actions_cutscene.c", [
    ("""            angleToNPC - approach_s32((angleToNPC - m->faceAngle[1]) << 16 >> 16, 0, 2048, 2048);""",
     """            angleToNPC - approach_s32((s16)(angleToNPC - m->faceAngle[1]), 0, 2048, 2048);"""),
    ("""                m->marioObj->header.gfx.angle[2] = ((m->faceAngle[1] - targetAngle) << 16 >> 16) * 20;""",
     """                m->marioObj->header.gfx.angle[2] = (s16)(m->faceAngle[1] - targetAngle) * 20;"""),
    ])
elif group == "rotating":
    patch("src/game/behaviors/rotating_platform.inc.c", [
    ("""    o->oAngleVelYaw = sp1F << 4;""",
     """    o->oAngleVelYaw = sp1F * 16;"""),
    ])
elif group == "pokey":
    patch("src/game/behaviors/pokey.inc.c", [
    ("""                o->oPokeyBodyPartDeathDelayAfterHeadKilled = (o->oBehParams2ndByte << 2) + 20;""",
     """                o->oPokeyBodyPartDeathDelayAfterHeadKilled = o->oBehParams2ndByte * 4 + 20;"""),
    ])
elif group == "save_file":
    patch("src/game/save_file.c", [
    ("""        u32 offset = (u32)((u8 *) buffer - (u8 *) &gSaveBuffer) >> 3;""",
     """        u32 offset = (u32)((u8 *) buffer - (u8 *) &gSaveBuffer) / 8;"""),
    ("""s32 verify_save_block_signature(void *buffer, s32 size, u16 magic) {
    struct SaveBlockSignature *sig = (struct SaveBlockSignature *) ((size - 4) + (u8 *) buffer);""",
     """s32 verify_save_block_signature(void *buffer, s32 size, u16 magic) {
    struct SaveBlockSignature *sig = (struct SaveBlockSignature *) ((u8 *) buffer + size - 4);"""),
    ("""void add_save_block_signature(void *buffer, s32 size, u16 magic) {
    struct SaveBlockSignature *sig = (struct SaveBlockSignature *) ((size - 4) + (u8 *) buffer);""",
     """void add_save_block_signature(void *buffer, s32 size, u16 magic) {
    struct SaveBlockSignature *sig = (struct SaveBlockSignature *) ((u8 *) buffer + size - 4);"""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
