#!/usr/bin/env python3
"""OoT control-flow + matching-residue groups (reports/control-flow-and-matching.md §1, §5, §7).
usage: patch_oot_cf.py <checkout> <group>"""

import sys
from pathlib import Path

root: Path = Path(sys.argv[1])
group: str = sys.argv[2]
Pairs = list[tuple[str, str] | tuple[str, str, int]]


def patch(rel: str, pairs: Pairs) -> None:
    p: Path = root / rel
    s: str = p.read_text()
    for item in pairs:
        old: str = item[0]
        new: str = item[1]
        want: int = item[2] if len(item) > 2 else 1
        n: int = s.count(old)
        assert n == want, f"{rel}: expected {want} match(es) for {old[:60]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


def unwrap_block(rel: str, open_line: str) -> None:
    """Remove the unique line `open_line` (an `if (1) {`-style opener) and its matching `}`, dedenting
    the interior by four spaces."""
    p: Path = root / rel
    lines: list[str] = p.read_text().split("\n")
    idx: list[int] = [i for i, ln in enumerate(lines) if ln == open_line]
    assert len(idx) == 1, f"{rel}: expected one line equal to {open_line!r}, got {len(idx)}"
    start: int = idx[0]
    depth: int = 0
    end: int = -1
    for j in range(start, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if depth == 0:
            end = j
            break
    assert end > start and lines[end].strip() == "}", f"{rel}: could not find the closing brace for {open_line!r}"
    inner: list[str] = [ln[4:] if ln.startswith("    ") else ln for ln in lines[start + 1 : end]]
    lines[start : end + 1] = inner
    p.write_text("\n".join(lines))
    print("unwrapped", rel, f"lines {start + 1}-{end + 1}")


if group == "goto_return":
    patch("soh/src/code/z_player_lib.c", [
        ("""        if ((sword < 0) || (sword >= 3)) {
            goto return_neg;
        }
    }

    return sword;

return_neg:
    return -1;
}""", """        if ((sword < 0) || (sword >= 3)) {
            return -1;
        }
    }

    return sword;
}"""),
    ])
    patch("soh/src/code/db_camera.c", [
        ("""                        return 1;
                    }
                    goto block_2;
                }

                case DEMO_CTRL_MENU(ACTION_SAVE, MENU_CALLBACK):""",
         """                        return 1;
                    }
                    return 1;
                }

                case DEMO_CTRL_MENU(ACTION_SAVE, MENU_CALLBACK):"""),
        ("""                        return 1;
                    }
                    goto block_2;
                }

                case DEMO_CTRL_MENU(ACTION_SAVE, MENU_ERROR):""",
         """                        return 1;
                    }
                    return 1;
                }

                case DEMO_CTRL_MENU(ACTION_SAVE, MENU_ERROR):"""),
        ("""                        dbCamera->sub.demoCtrlMenu -= 9;
                    }
                block_2:
                    return 1;
                }""", """                        dbCamera->sub.demoCtrlMenu -= 9;
                    }
                    return 1;
                }"""),
        ("""                            return 1;
                        }
                        goto block_2;
                    } else {""", """                            return 1;
                        }
                        return 1;
                    } else {"""),
    ])
    patch("soh/src/code/audio_heap.c", [
        ("""            if (tp->nextSide == 0) {
                if (firstVal == 1) {
                    if (secondVal == 1) {
                        goto fail;
                    }
                    tp->nextSide = 1;
                }
            } else {
                if (secondVal == 1) {
                    if (firstVal == 1) {
                        goto fail;
                    }
                    tp->nextSide = 0;
                }
            }

            if (0) {
            fail:
                // Both sides are being loaded into.
                return NULL;
            }
        }""", """            if (tp->nextSide == 0) {
                if (firstVal == 1) {
                    if (secondVal == 1) {
                        // Both sides are being loaded into.
                        return NULL;
                    }
                    tp->nextSide = 1;
                }
            } else {
                if (secondVal == 1) {
                    if (firstVal == 1) {
                        // Both sides are being loaded into.
                        return NULL;
                    }
                    tp->nextSide = 0;
                }
            }
        }"""),
    ])
elif group == "goto_continue":
    patch("soh/src/code/audio_playback.c", [
        ("""                            playbackState->wantedParentLayer = NO_LAYER;
                            goto skip;
                        }""", """                            playbackState->wantedParentLayer = NO_LAYER;
                            continue;
                        }"""),
        ("""            noteSubEu->bitField1.bookOffset = bookOffset;
        skip:;
        }
    }
}""", """            noteSubEu->bitField1.bookOffset = bookOffset;
        }
    }
}"""),
    ])
elif group == "goto_next":
    patch("soh/src/overlays/actors/ovl_Boss_Dodongo/z_boss_dodongo.c", [
        ("""    BossDodongo* this = (BossDodongo*)thisx;

    // required for matching
    if ((limbIndex == 6) || (limbIndex == 7)) {
        goto block_1;
    }
block_1:
    Matrix_TranslateRotateZYX(pos, rot);""", """    BossDodongo* this = (BossDodongo*)thisx;

    Matrix_TranslateRotateZYX(pos, rot);"""),
        ("""    { s32 pad; } // Required to match
    return 1;
}""", """    return 1;
}"""),
    ])
elif group == "self_assign":
    patch("soh/src/code/code_800EC960.c", [
        ("""            Audio_SetSequenceMode(sAudioBlkChgBgmWork[1]);
            ; // might be a fake match?
""", """            Audio_SetSequenceMode(sAudioBlkChgBgmWork[1]);
"""),
    ])
    patch("soh/src/code/z_eff_blure.c", [
        ("""    sp30 = sp30; // Optimized out but seems necessary to match stack usage

""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_Bg_Hidan_Hamstep/z_bg_hidan_hamstep.c", [
        ("""    pos = pos; // Required to match
""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_Mir_Ray/z_mir_ray.c", [
        ("""                spE8 = spE8; // Required to match

""", ""),
        ("""                normalVec = normalVec; // Required to match

""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Ma3/z_en_ma3.c", [
        ("""    s16* timerSecondsPtr; // weirdness with this necessary to match
""", ""),
        ("""    timerSecondsPtr = &gSaveContext.timerSeconds;
""", ""),
        ("""        gSaveContext.timerSeconds = gSaveContext.timerSeconds;
""", ""),
        ("""            HIGH_SCORE(HS_HORSE_RACE) = 0xB4;
            gSaveContext.timerSeconds = *timerSecondsPtr;
""", """            HIGH_SCORE(HS_HORSE_RACE) = 0xB4;
"""),
    ])
elif group == "fake_temps":
    patch("soh/src/code/irqmgr.c", [
        ("""    u64 temp = STATUS_PRENMI; // required to match

    gIrqMgrResetStatus = temp;
""", """    gIrqMgrResetStatus = STATUS_PRENMI;
"""),
        ("""    u64 temp = STATUS_NMI; // required to match
    gIrqMgrResetStatus = temp;
""", """    gIrqMgrResetStatus = STATUS_NMI;
"""),
    ])
    patch("soh/src/code/z_kaleido_setup.c", [
        ("""    u64 temp = 0; // Necessary to match
""", ""),
        ("""    pauseCtx->cursorX[PAUSE_QUEST] = temp;
    pauseCtx->cursorY[PAUSE_QUEST] = temp;
""", """    pauseCtx->cursorX[PAUSE_QUEST] = 0;
    pauseCtx->cursorY[PAUSE_QUEST] = 0;
"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Nb/z_en_nb.c", [
        ("""    s32 one; // required to match

""", ""),
        ("""        one = 1;
        if (!D_80AB4318) {
            D_80AB4318 = one;
        }""", """        if (!D_80AB4318) {
            D_80AB4318 = 1;
        }"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Ru2/z_en_ru2.c", [
        ("""    s32 one; // Needed to match

""", ""),
        ("""        one = 1;
        if (D_80AF4118 == 0) {
            D_80AF4118 = one;
        }""", """        if (D_80AF4118 == 0) {
            D_80AF4118 = 1;
        }"""),
    ])
    patch("soh/src/overlays/actors/ovl_Boss_Tw/z_boss_tw.c", [
        ("""                Vec3f accel = { 0.0f, 0.0f, 0.0f };
                s32 zero = 0;
""", """                Vec3f accel = { 0.0f, 0.0f, 0.0f };
"""),
        ("""
                    // fake code needed to match, tricks the compiler into allocating more stack
                    if (zero) {
                        accel.x *= 2.0;
                    }
""", ""),
    ])
elif group == "dead_locals":
    patch("soh/src/code/z_bgcheck.c", [
        ("""    WaterBox* waterBoxList = colHeader->waterBoxes; // unused, needed for matching
""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Trap/z_en_trap.c", [
        ("""    ColliderCylinder* unused = &this->collider; // required to match
""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Zl3/z_en_zl3.c", [
        ("""    // todo look into
    Actor* thisx = &this->actor; // unused, necessary to use 'this' first to fix regalloc

""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_Bg_Ice_Objects/z_bg_ice_objects.c", [
        ("""    s16 z16 = 0; // needed to match
""", """    s16 z16;
"""),
    ])
    patch("soh/src/code/z_skin_matrix.c", [
        ("""        mf->xx = cosZ;
        xz = sinZ; // required to match
        mf->yx = sinZ;""", """        mf->xx = cosZ;
        mf->yx = sinZ;"""),
        ("""        mf->zz = cosY;
        xy = sinY; // required to match
        mf->xz = sinY;""", """        mf->zz = cosY;
        mf->xz = sinY;"""),
    ])
elif group == "aliases":
    patch("soh/src/overlays/actors/ovl_En_Ru1/z_en_ru1.c", [
        ("""    EnRu1* thisx = this; // necessary to match
""", ""),
        ("""            this->sinkingStartPosY = this->actor.world.pos.y + thisx->bobDepth; // thisx only used here""",
         """            this->sinkingStartPosY = this->actor.world.pos.y + this->bobDepth;"""),
        ("""    CsCmdActorCue* csCmdNPCAction;
    CsCmdActorCue* csCmdNPCAction2;
""", """    CsCmdActorCue* csCmdNPCAction;
"""),
        ("""        // this weird part with the redundant variable is necessary to match for some reason
        csCmdNPCAction2 = play->csCtx.npcActions[3];
        csCmdNPCAction = csCmdNPCAction2;
""", """        csCmdNPCAction = play->csCtx.npcActions[3];
"""),
    ])
    patch("soh/src/overlays/actors/ovl_Obj_Mure/z_obj_mure.c", [
        ("""    ActorContext* ac = (ActorContext*)play; // fake match
""", """    ActorContext* ac;
"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Elf/z_en_elf.c", [
        ("""    u8 unk2C7;
    s32 pad;
""", """    s32 pad;
"""),
        ("""    // temp probably fake match
    unk2C7 = this->unk_2C7;
    if (unk2C7 > 0) {
        this->unk_2C7--;""", """    if (this->unk_2C7 > 0) {
        this->unk_2C7--;"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_GeldB/z_en_geldb.c", [
        ("""    playSpeed = ((void)0, ABS(this->skelAnime.playSpeed)); // Needed to match for some reason""",
         """    playSpeed = ABS(this->skelAnime.playSpeed);"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Horse/z_en_horse.c", [
        ("""    // void 0 trick required to match, but is surely not real. revisit at a later time
    if (this->actor.bgCheckFlags & 8 && Math_CosS(this->actor.wallYaw - ((void)0, this->actor.world).rot.y) < -0.3f) {""",
         """    if (this->actor.bgCheckFlags & 8 && Math_CosS(this->actor.wallYaw - this->actor.world.rot.y) < -0.3f) {"""),
    ])
    patch("soh/src/overlays/actors/ovl_En_Fr/z_en_fr.c", [
        ("""    if (this->ocarinaNote == (*msgCtx).lastOcaNoteIdx) { // required to match, possibly an array?""",
         """    if (this->ocarinaNote == msgCtx->lastOcaNoteIdx) {"""),
    ])
    patch("soh/src/code/z_bgcheck.c", [
        ("""            // Yeah, this is all kinds of fake, but my God, it matches.
            newPoly->flags_vIA =
                (COLPOLY_VTX_INDEX(newPoly->flags_vIA) + *vtxStartIndex) | ((*newPoly).flags_vIA & 0xE000);
            newPoly->flags_vIB =
                (COLPOLY_VTX_INDEX(newPoly->flags_vIB) + *vtxStartIndex) | ((*newPoly).flags_vIB & 0xE000);""",
         """            newPoly->flags_vIA =
                (COLPOLY_VTX_INDEX(newPoly->flags_vIA) + *vtxStartIndex) | (newPoly->flags_vIA & 0xE000);
            newPoly->flags_vIB =
                (COLPOLY_VTX_INDEX(newPoly->flags_vIB) + *vtxStartIndex) | (newPoly->flags_vIB & 0xE000);"""),
    ])
    patch("soh/src/code/game.c", [
        ("""            // & 0xFFFFFFFF necessary for matching.
            hexDumpSize = (HREG(83) == 0 ? 0x100 : HREG(83) * 0x10) & 0xFFFFFFFF;""",
         """            hexDumpSize = (HREG(83) == 0 ? 0x100 : HREG(83) * 0x10);"""),
    ])
elif group == "always_true_guard":
    unwrap_block("soh/src/overlays/actors/ovl_Boss_Fd/z_boss_fd.c", "                    if (sp150) { // Needed for matching")
elif group == "if1_unwrap":
    unwrap_block("soh/src/boot/z_std_dma.c", "    if (1) {")
    unwrap_block("soh/src/code/code_800EC960.c", "            if (1) {")
    unwrap_block("soh/src/code/z_actor.c", "        if (1) {")
    patch("soh/src/code/z_player_lib.c", [
        ("""    // Also matches if some of the previous graphics commands are moved inside this block too. Possible macro?
    if (1) {
        s32 pad[2];

        gSPLoadGeometryMode(POLY_OPA_DISP++, G_ZBUFFER | G_SHADE | G_CULL_BACK | G_LIGHTING | G_SHADING_SMOOTH);
    }
""", """    gSPLoadGeometryMode(POLY_OPA_DISP++, G_ZBUFFER | G_SHADE | G_CULL_BACK | G_LIGHTING | G_SHADING_SMOOTH);
"""),
    ])
    unwrap_block("soh/src/overlays/actors/ovl_Bg_Hidan_Hrock/z_bg_hidan_hrock.c", "        if (1) {")
    # these two declare locals inside the block: keep a bare scope
    patch("soh/src/overlays/actors/ovl_Boss_Fd/z_boss_fd.c", [
        ("    if (1) { // Needed for matching, and also to define new variables\n", "    {\n"),
    ])
    patch("soh/src/overlays/actors/ovl_Boss_Ganon2/z_boss_ganon2.c", [
        ("            SkelAnime_Update(&this->skelAnime);\n            if (1) {\n", "            SkelAnime_Update(&this->skelAnime);\n            {\n"),
    ])
    unwrap_block("soh/src/overlays/actors/ovl_Demo_Go/z_demo_go.c", "            if (1) {")
elif group == "empty_arms":
    patch("soh/src/code/audio_synthesis.c", [
        ("""    // Partially-optimized out no-op ifs required for matching. SM64 decomp
    // makes it clear that this is how it should look.
    if (synthState->numParts == 1 && nParts == 2) {
    } else if (synthState->numParts == 2 && nParts == 1) {
    } else {
    }

""", ""),
    ])
    patch("soh/src/overlays/actors/ovl_Bg_Treemouth/z_bg_treemouth.c", [
        ("""            alpha = 2150;
        }
    } else { // neeeded to match
    }
""", """            alpha = 2150;
        }
    }
"""),
    ])
    patch("soh/src/code/z_camera.c", [
        ("""        // needed to match
        // if (!prevTargetPlayerDist) {}
""", ""),
    ])
    patch("soh/src/code/ucode_disas.c", [
        ("""    // clang-format off
    if (this->enableLog == 0) {} else { osSyncPrintf("\\nGBL_c1(%s, %s, %s, %s)|",
        D_8012DDDC[0][a >> 12 & 3], D_8012DDDC[1][a >> 8 & 3], D_8012DDDC[2][a >> 4 & 3], D_8012DDDC[3][a >> 0 & 3]); }
    // clang-format on
""", """    if (this->enableLog != 0) {
        osSyncPrintf("\\nGBL_c1(%s, %s, %s, %s)|", D_8012DDDC[0][a >> 12 & 3], D_8012DDDC[1][a >> 8 & 3],
                     D_8012DDDC[2][a >> 4 & 3], D_8012DDDC[3][a >> 0 & 3]);
    }
"""),
    ])
elif group == "unreachable":
    patch("soh/src/overlays/actors/ovl_Obj_Oshihiki/z_obj_oshihiki.c", [
        ("            return 1;\n            break;\n", "            return 1;\n"),
        ("            return strength >= PLAYER_STR_BRACELET;\n            break;\n", "            return strength >= PLAYER_STR_BRACELET;\n"),
        ("            return strength >= PLAYER_STR_SILVER_G;\n            break;\n", "            return strength >= PLAYER_STR_SILVER_G;\n"),
    ])
    patch("soh/src/overlays/actors/ovl_Obj_Bean/z_obj_bean.c", [
        ("    this->dyna.actor.scale.x = this->dyna.actor.scale.z = Math_CosS(this->leafRotFactor) * 0.12207746f;\n    ;\n}",
         "    this->dyna.actor.scale.x = this->dyna.actor.scale.z = Math_CosS(this->leafRotFactor) * 0.12207746f;\n}"),
    ])
elif group == "parameter_tails":
    fields: list[str] = ["bottles", "tradeItems", "hookshot", "ocarina", "farores", "dinsNayrus", "all"]
    patch("soh/src/code/z_parameter.c", [
        (f"                }} else if (interfaceCtx->restrictions.{fld} == 0) {{\n", "                } else {\n")
        for fld in fields
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
