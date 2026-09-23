#!/usr/bin/env python3
"""Batch 2 — matching-era residue: lone `; // needed to match`, an unreachable `break`, four
`do { … } while (0);` wrappers, "must be one line to match on -O2" one-liners (+ clang-format
fences), and the dead `struct vNote`. Exact-match, single-occurrence replacements, grouped by the
commit they belong to. usage: patch_batch2.py <checkout> <group>   (group: goddard|camera|game|engine|audio)"""
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


if group == "goddard":
    patch("src/goddard/draw_objects.c", [
    ("""        sp44.z += cam->lookAt.z;
        ; // needed to match
    } else {""",
     """        sp44.z += cam->lookAt.z;
    } else {"""),
    ("""        sLightColours[0].b = (white->b - black->b) * brightness + black->b;
        ; // needed to match
    } else {""",
     """        sLightColours[0].b = (white->b - black->b) * brightness + black->b;
    } else {"""),
    ("""        obj->drawFlags &= ~OBJ_HIGHLIGHTED;
        ; // needed to match; presumably setting up the color to draw the plane with
    } else {""",
     """        obj->drawFlags &= ~OBJ_HIGHLIGHTED;
        // presumably setting up the color to draw the plane with
    } else {"""),
    ])
    patch("src/goddard/joints.c", [
    ("""        self->flags |= 0x2000;
        ;  // needed to match
    } else {""",
     """        self->flags |= 0x2000;
    } else {"""),
    ])
    patch("src/goddard/particles.c", [
    ("""                    ptc->flags |= 0x20;
                    ; // needed to match
                } else {""",
     """                    ptc->flags |= 0x20;
                } else {"""),
    ])
    patch("src/goddard/renderer.c", [
    ("""                        *csr = '\\0';
                        break;
                        break; // needed to match
                    case 'f':""",
     """                        *csr = '\\0';
                        break;
                    case 'f':"""),
    ])

elif group == "camera":
    patch("src/game/camera.c", [
    ("""    // Create the end of the spline by duplicating the last point
    do { init_spline_point(&dst[i], 0, src[j].speed, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 1], 0, 0, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 2], 0, 0, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 3], -1, 0, src[j].point); } while (0);
}""",
     """    // Create the end of the spline by duplicating the last point
    init_spline_point(&dst[i], 0, src[j].speed, src[j].point);
    init_spline_point(&dst[i + 1], 0, 0, src[j].point);
    init_spline_point(&dst[i + 2], 0, 0, src[j].point);
    init_spline_point(&dst[i + 3], -1, 0, src[j].point);
}"""),
    ("""    //! Must be same line to match on -O2
    // Prevent the camera from going to the ground in the outside boss fight
    if (gCurrLevelNum == LEVEL_BBH) { pos[1] = 2047.f; }""",
     """    // Prevent the camera from going to the ground in the outside boss fight
    if (gCurrLevelNum == LEVEL_BBH) {
        pos[1] = 2047.f;
    }"""),
    ("""            //! Must be same line to match on -O2
            pitch -= goalPitch; yaw -= goalYaw;""",
     """            pitch -= goalPitch;
            yaw -= goalYaw;"""),
    ])

elif group == "game":
    patch("src/game/mario_actions_airborne.c", [
    ("""    // This must be one line to match on -O2
    // clang-format off
    if (m->marioObj->header.gfx.animInfo.animFrame == 6) play_sound(SOUND_ACTION_SIDE_FLIP_UNK, m->marioObj->header.gfx.cameraToObject);
    // clang-format on
    return FALSE;""",
     """    if (m->marioObj->header.gfx.animInfo.animFrame == 6) {
        play_sound(SOUND_ACTION_SIDE_FLIP_UNK, m->marioObj->header.gfx.cameraToObject);
    }
    return FALSE;"""),
    ])
    patch("src/game/mario_actions_submerged.c", [
    ("""    // This must be one line to match on -O2
    if (animFrame == 0 || animFrame == 12) play_sound(SOUND_ACTION_UNKNOWN434, m->marioObj->header.gfx.cameraToObject);
}""",
     """    if (animFrame == 0 || animFrame == 12) {
        play_sound(SOUND_ACTION_UNKNOWN434, m->marioObj->header.gfx.cameraToObject);
    }
}"""),
    ])
    patch("src/game/game_init.c", [
    ("""            // Loop must be one line to match on -O2
            for (height = 0; height < (SCREEN_WIDTH / 4); height++) *fbPtr++ = 0;""",
     """            for (height = 0; height < (SCREEN_WIDTH / 4); height++) {
                *fbPtr++ = 0;
            }"""),
    ])
    patch("src/game/level_update.c", [
    ("""            case WARP_OP_DEMO_END: sDelayedWarpTimer = 20; // Must be one line to match on -O2
                sSourceWarpNodeId = WARP_NODE_F0;""",
     """            case WARP_OP_DEMO_END:
                sDelayedWarpTimer = 20;
                sSourceWarpNodeId = WARP_NODE_F0;"""),
    ])
    patch("src/game/behaviors/fish.inc.c", [
    ("""        // Cases need to be on one line to match with and without optimizations.
        case FISH_SPAWNER_BP_MANY_BLUE:
            model = MODEL_FISH;      schoolQuantity = 20; minDistToMario = 1500.0f; fishAnimation = blue_fish_seg3_anims_0301C2B0;
            break;

        case FISH_SPAWNER_BP_FEW_BLUE:
            model = MODEL_FISH;      schoolQuantity = 5;  minDistToMario = 1500.0f; fishAnimation = blue_fish_seg3_anims_0301C2B0;
            break;

        case FISH_SPAWNER_BP_MANY_CYAN:
            model = MODEL_CYAN_FISH; schoolQuantity = 20; minDistToMario = 1500.0f; fishAnimation = cyan_fish_seg6_anims_0600E264;
            break;

        case FISH_SPAWNER_BP_FEW_CYAN:
            model = MODEL_CYAN_FISH; schoolQuantity = 5;  minDistToMario = 1500.0f; fishAnimation = cyan_fish_seg6_anims_0600E264;
            break;""",
     """        case FISH_SPAWNER_BP_MANY_BLUE:
            model = MODEL_FISH;
            schoolQuantity = 20;
            minDistToMario = 1500.0f;
            fishAnimation = blue_fish_seg3_anims_0301C2B0;
            break;

        case FISH_SPAWNER_BP_FEW_BLUE:
            model = MODEL_FISH;
            schoolQuantity = 5;
            minDistToMario = 1500.0f;
            fishAnimation = blue_fish_seg3_anims_0301C2B0;
            break;

        case FISH_SPAWNER_BP_MANY_CYAN:
            model = MODEL_CYAN_FISH;
            schoolQuantity = 20;
            minDistToMario = 1500.0f;
            fishAnimation = cyan_fish_seg6_anims_0600E264;
            break;

        case FISH_SPAWNER_BP_FEW_CYAN:
            model = MODEL_CYAN_FISH;
            schoolQuantity = 5;
            minDistToMario = 1500.0f;
            fishAnimation = cyan_fish_seg6_anims_0600E264;
            break;"""),
    ])

elif group == "engine":
    patch("src/engine/math_util.c", [
    ("""    // These loops must be one line to match on -O2

    // initialize everything except the first and last cells to 0
    for (dest = (f32 *) mtx + 1, i = 0; i < 14; dest++, i++) *dest = 0;

    // initialize the diagonal cells to 1
    for (dest = (f32 *) mtx, i = 0; i < 4; dest += 5, i++) *dest = 1;""",
     """    // initialize everything except the first and last cells to 0
    for (dest = (f32 *) mtx + 1, i = 0; i < 14; dest++, i++) {
        *dest = 0;
    }

    // initialize the diagonal cells to 1
    for (dest = (f32 *) mtx, i = 0; i < 4; dest += 5, i++) {
        *dest = 1;
    }"""),
    ])

elif group == "audio":
    patch("src/audio/internal.h", [
    ("""#else
// volatile Note, needed in synthesis_process_notes
struct vNote {
    /* U/J, EU  */
    /*0x00*/ volatile u8 enabled : 1;
    long long int force_structure_alignment;
}; // size = 0xC0
struct Note {""",
     """#else
struct Note {"""),
    ])
    patch("src/audio/synthesis.c", [
    ("""        //! This function requires note->enabled to be volatile, but it breaks other functions like note_enable.
        //! Casting to a struct with just the volatile bitfield works, but there may be a better way to match.
        if (note->enabled == TRUE && IS_BANK_LOAD_COMPLETE(note->bankId) == FALSE) {""",
     """        // The matching build read note->enabled through a volatile-bitfield twin of struct Note
        // (`struct vNote`) to reproduce IDO's codegen; the port reads the field directly.
        if (note->enabled == TRUE && IS_BANK_LOAD_COMPLETE(note->bankId) == FALSE) {"""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
