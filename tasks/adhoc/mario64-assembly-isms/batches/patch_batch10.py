#!/usr/bin/env python3
"""Batch 10 — the constructs the regexes missed: boolean `++`, `switch (bool)`, Yoda conditions,
comma-chained assignment, `if (FALSE) {}`, the dead `else`, open-coded memset/memcpy loops.
usage: patch_batch10.py <checkout> <group>"""
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


if group == "tilting_bool":
    patch("src/game/behaviors/tilting_inverted_pyramid.inc.c", [
        ("        if (o->oTiltingPyramidMarioOnPlatform == TRUE) {\n            marioOnPlatform++;\n        }\n",
         "        if (o->oTiltingPyramidMarioOnPlatform == TRUE) {\n            marioOnPlatform = TRUE;\n        }\n"),
    ])
elif group == "tilting_dead_else":
    patch("src/game/behaviors/tilting_inverted_pyramid.inc.c", [
        ("""        //! Always true since dy = 500, making d >= 500.
        if (d != 0.0f) {
            // Normalizing
            d = 1.0 / d;
            dx *= d;
            dy *= d;
            dz *= d;
        } else {
            dx = 0.0f;
            dy = 1.0f;
            dz = 0.0f;
        }
""",
         """        // Normalizing (d >= 500 since dy = 500, so no zero check is needed)
        d = 1.0 / d;
        dx *= d;
        dy *= d;
        dz *= d;
"""),
    ])
elif group == "bowser_bool_inc":
    patch("src/game/behaviors/bowser.inc.c", [
        ("        o->oBowserIsReacting++;\n", "        o->oBowserIsReacting = TRUE;\n", 2),
    ])
elif group == "bowser_switch_bool":
    patch("src/game/behaviors/bowser.inc.c", [
        ("""void bowser_bits_actions(void) {
    switch (o->oBowserIsReacting) {
        case FALSE:
            // oBowserBitsJustJump never changes value,
            // so its always FALSE, maybe a debug define
            if (o->oBowserBitsJustJump == FALSE) {
                bowser_bits_action_list();
            } else {
                bowser_set_act_big_jump();
            }
            o->oBowserIsReacting = TRUE;
            break;

        case TRUE:
            o->oBowserIsReacting = FALSE;
            o->oAction = BOWSER_ACT_WALK_TO_MARIO;
            break;
    }
}""",
         """void bowser_bits_actions(void) {
    if (!o->oBowserIsReacting) {
        // oBowserBitsJustJump never changes value,
        // so its always FALSE, maybe a debug define
        if (o->oBowserBitsJustJump == FALSE) {
            bowser_bits_action_list();
        } else {
            bowser_set_act_big_jump();
        }
        o->oBowserIsReacting = TRUE;
    } else {
        o->oBowserIsReacting = FALSE;
        o->oAction = BOWSER_ACT_WALK_TO_MARIO;
    }
}"""),
    ])
elif group == "bowser_comma":
    patch("src/game/behaviors/bowser.inc.c", [
        ("                o->oPosZ = 0.0f, o->oPosX = o->oPosZ;\n", "                o->oPosX = o->oPosZ = 0.0f;\n"),
    ])
elif group == "yoda":
    patch("src/game/mario_actions_cutscene.c", [
        ("    if (15 < m->actionTimer++\n", "    if (m->actionTimer++ > 15\n", 2),
    ])
elif group == "if_false":
    patch("src/goddard/draw_objects.c", [
        ("        }\n\n        if (FALSE) {\n        }\n    }\n", "        }\n    }\n"),
    ])
elif group == "memset_objects":
    patch("src/goddard/objects.c", [
        ("    // Zero out the object\n    newObjBytes = (u8 *) newObj;\n    for (i = 0; i < objSize; i++) {\n        newObjBytes[i] = 0;\n    }\n",
         "    // Zero out the object\n    memset(newObj, 0, objSize);\n"),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
