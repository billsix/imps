#!/usr/bin/env python3
"""OoT numeric groups (reports/raw-memory-and-numeric.md §1-§4 DO rows).
usage: patch_oot_num.py <checkout> <group>   (masks | ub_shifts | casts_f32 | casts_s32 | names | pointers)"""

import re
import subprocess
import sys
from pathlib import Path

root: Path = Path(sys.argv[1])
group: str = sys.argv[2]
Pairs = list[tuple[str, str] | tuple[str, str, int]]
A: str = "soh/src/overlays/actors"


def patch(rel: str, pairs: Pairs) -> None:
    p: Path = root / rel
    s: str = p.read_text()
    for item in pairs:
        old: str = item[0]
        new: str = item[1]
        want: int = item[2] if len(item) > 2 else 1
        n: int = s.count(old)
        assert n == want, f"{rel}: expected {want} match(es) for {old[:70]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


if group == "masks":
    patch(f"{A}/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c", [
        ("    this->switchFlag = this->dyna.actor.params & 0xFFFF;", "    this->switchFlag = this->dyna.actor.params;"),
    ])
    patch(f"{A}/ovl_Door_Ana/z_door_ana.c", [
        ("gSaveContext.respawn[RESPAWN_MODE_RETURN].data = this->actor.params & 0xFFFF;",
         "gSaveContext.respawn[RESPAWN_MODE_RETURN].data = this->actor.params;"),
    ])
    patch(f"{A}/ovl_En_Elf/z_en_elf.c", [
        ("    this->unk_2AA = (this->unk_2AC * 2) & 0xFFFF;", "    this->unk_2AA = this->unk_2AC * 2;"),
    ])
    patch(f"{A}/ovl_player_actor/z_player.c", [
        ("(Rand_CenteredFloat(2.0f) + 10.0f)) & 0xFFFF;", "(Rand_CenteredFloat(2.0f) + 10.0f));", 2),
    ])
    patch(f"{A}/ovl_En_GeldB/z_en_geldb.c", [
        ("        this->actor.world.rot.y = (u16)this->actor.shape.rot.y & 0xFFFF;",
         "        this->actor.world.rot.y = this->actor.shape.rot.y;"),
    ])
    patch(f"{A}/ovl_En_Wf/z_en_wf.c", [
        ("        this->actor.world.rot.y = (u16)this->actor.shape.rot.y & 0xFFFF;",
         "        this->actor.world.rot.y = this->actor.shape.rot.y;"),
    ])
    patch(f"{A}/ovl_En_Zl2/z_en_zl2.c", [
        ("        temp_v1 = (s16)(phi_v0 & 0xFFFF);", "        temp_v1 = (s16)phi_v0;"),
    ])
    patch("soh/src/code/z_room.c", [
        ("    iREG(87) = polygon2->num & 0xFFFF & 0xFFFF & 0xFFFF; // if this is real then I might not be\n",
         "    iREG(87) = polygon2->num;\n"),
    ])
    patch("soh/src/code/z_kaleido_scope_call.c", [
        ("pauseCtx->state = (pauseCtx->state & 0xFFFF) + 1;", "pauseCtx->state = pauseCtx->state + 1;", 2),
    ])
    patch(f"{A}/ovl_Bg_Spot02_Objects/z_bg_spot02_objects.c", [
        ("        // should be able to remove & 0xFFFF with some other change\n        if ((play->csCtx.npcActions[2]->action & 0xFFFF) == 2) {",
         "        if (play->csCtx.npcActions[2]->action == 2) {"),
    ])
    patch(f"{A}/ovl_En_Ani/z_en_ani.c", [
        ("    textId = textId2 & 0xFFFF;", "    textId = textId2;"),
    ])
    patch(f"{A}/ovl_En_In/z_en_in.c", [
        ("        gSaveContext.eventInf[0] = (gSaveContext.eventInf[0] & 0xFFFF) | 0x20;",
         "        gSaveContext.eventInf[0] = gSaveContext.eventInf[0] | 0x20;"),
        ("        gSaveContext.eventInf[0] = (gSaveContext.eventInf[0] & 0xFFFF) | 0x40;",
         "        gSaveContext.eventInf[0] = gSaveContext.eventInf[0] | 0x40;"),
    ])
    patch(f"{A}/ovl_En_Ru2/z_en_ru2.c", [
        ("    funcFloat = Environment_LerpWeightAccelDecel((kREG(2) + 0x96) & 0xFFFF, 0, this->swimmingUpFrame, 8, 0);",
         "    funcFloat = Environment_LerpWeightAccelDecel(kREG(2) + 0x96, 0, this->swimmingUpFrame, 8, 0);"),
    ])
    patch("soh/src/code/code_800EC960.c", [
        ("            phi_v1 = (((phi_v0 & 0xFFFF) * 10) - 300) / 34;", "            phi_v1 = ((phi_v0 * 10) - 300) / 34;"),
    ])
    patch("soh/src/code/z_scene_table.c", [
        ("coss((play->gameplayFrames * 1500) & 0xFFFF) >> 8;", "coss(play->gameplayFrames * 1500) >> 8;", 4),
    ])
elif group == "fault_sext":
    patch("soh/src/code/fault.c", [
        ("    s32 causeStrIdx = (s32)((((u32)t->context.cause >> 2) & 0x1F) << 0x10) >> 0x10;",
         "    s32 causeStrIdx = (s32)(((u32)t->context.cause >> 2) & 0x1F);", 2),
    ])
elif group == "ub_shift_seq":
    patch("soh/src/code/audio_seqplayer.c", [
        ("(u32)(temp + (seqScript->value << 1));", "(u32)(temp + (seqScript->value * 2));"),
    ])
elif group == "ub_shifts":
    patch(f"{A}/ovl_En_Wood02/z_en_wood02.c", [
        ("        this->actor.home.rot.z = (this->actor.home.rot.z << 8) | this->unk_14C;",
         "        this->actor.home.rot.z = (this->actor.home.rot.z * 256) | this->unk_14C;"),
        ("            this->drawType |= this->unk_14C << 4;", "            this->drawType |= this->unk_14C * 16;"),
        ("Item_DropCollectibleRandom(play, &this->actor, &dropsSpawnPt, this->unk_14C << 4);",
         "Item_DropCollectibleRandom(play, &this->actor, &dropsSpawnPt, this->unk_14C * 16);"),
        ("((this->unk_14C << 4) | 0x8000));", "((this->unk_14C * 16) | 0x8000));"),
    ])
elif group == "casts_f32":
    out: str = subprocess.run(
        ["grep", "-rl", "(f32)Animation_GetLastFrame(", str(root / "soh/src"), "--include=*.c"],
        capture_output=True, text=True, check=True,
    ).stdout
    f: str
    for f in sorted(out.split()):
        p: Path = Path(f)
        s: str = p.read_text()
        n: int = s.count("(f32)Animation_GetLastFrame(")
        p.write_text(s.replace("(f32)Animation_GetLastFrame(", "Animation_GetLastFrame("))
        print(f"patched {p.relative_to(root)} x{n}")
elif group == "casts_s32":
    patch(f"{A}/ovl_Bg_Hidan_Kousi/z_bg_hidan_kousi.c", [
        ("((s32)thisx->params >> 8) & 0xFF", "(thisx->params >> 8) & 0xFF"),
    ])
    patch(f"{A}/ovl_Bg_Spot01_Objects2/z_bg_spot01_objects2.c", [
        ("((s32)thisx->params >> 8) & 0xFF", "(thisx->params >> 8) & 0xFF", 2),
    ])
    patch(f"{A}/ovl_En_Wallmas/z_en_wallmas.c", [
        ("(s16)((s32)this->actor.yawTowardsPlayer + 0x8000)", "(s16)(this->actor.yawTowardsPlayer + 0x8000)"),
    ])
    patch(f"{A}/ovl_Obj_Bean/z_obj_bean.c", [
        ("    if ((s32)this->unk_1C0 < 0) {", "    if (this->unk_1C0 < 0) {"),
    ])
    patch(f"{A}/ovl_En_Fr/z_en_fr.c", [
        ("        index = ocarinaNoteIndex < 4 ? (s32)ocarinaNoteIndex : 4;", "        index = ocarinaNoteIndex < 4 ? ocarinaNoteIndex : 4;"),
    ])
    patch("soh/src/code/z_skin_awb.c", [
        ("        mtx = &limbMatrices[(s32)parentIndex];", "        mtx = &limbMatrices[parentIndex];"),
    ])
elif group == "names":
    patch(f"{A}/ovl_Boss_Ganon/z_boss_ganon.c", [
        ("this->fwork[1]", "this->fwork[GDF_FWORK_1]", 5),
    ])
    st: str = "(gSaveContext.eventInf[0] & 0xF)"
    macro: str = "GET_EVENTINF_HORSES_STATE()"
    patch("soh/src/code/z_horse.c", [
        (st, macro, 2),
        ("((gSaveContext.eventInf[0] & 0x10) >> 4)", "GET_EVENTINF_HORSES_HORSETYPE()"),
    ])
    patch("soh/src/code/z_message_PAL.c", [
        (st, macro, 1),
        ("gSaveContext.eventInf[0] & 0xF, 1,", "GET_EVENTINF_HORSES_STATE(), 1,"),
    ])
    patch("soh/src/code/z_parameter.c", [(st, macro, 1)])
    patch(f"{A}/ovl_Bg_Ingate/z_bg_ingate.c", [(st, macro, 1)])
    patch(f"{A}/ovl_En_Horse/z_en_horse.c", [(st, macro, 2)])
    patch(f"{A}/ovl_Oceff_Spot/z_oceff_spot.c", [(st, macro, 1)])
    patch(f"{A}/ovl_En_In/z_en_in.c", [
        (st, macro, 4),
        ("""            gSaveContext.eventInf[0] =
                (gSaveContext.eventInf[0] & ~0x10) | (((EnHorse*)GET_PLAYER(play)->rideActor)->type << 4);""",
         """            SET_EVENTINF_HORSES_HORSETYPE(((EnHorse*)GET_PLAYER(play)->rideActor)->type);"""),
    ])
elif group == "pointers":
    patch(f"{A}/ovl_Boss_Va/z_boss_va.c", [
        ("memset((u8*)sEffects, 0, ARRAY_COUNT(sEffects) * sizeof(BossVaEffect));",
         "memset(sEffects, 0, ARRAY_COUNT(sEffects) * sizeof(BossVaEffect));"),
    ])
    patch("soh/src/code/z_message_PAL.c", [
        ("memcpy((uintptr_t)msgCtx->textboxSegment + MESSAGE_STATIC_TEX_SIZE,",
         "memcpy((u8*)msgCtx->textboxSegment + MESSAGE_STATIC_TEX_SIZE,", 4),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
