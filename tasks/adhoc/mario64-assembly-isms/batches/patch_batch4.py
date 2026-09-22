#!/usr/bin/env python3
"""Batch 4 — conditionals: redundant `else if (state == 1)`, a grouped value ladder that is a switch,
two complementary ifs that are an if/else, three nested ifs that are one condition.
usage: patch_batch4.py <checkout> <group>   (group: intro_geo|spindel|file_select|renderer)"""
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


if group == "intro_geo":
    patch("src/menu/intro_geo.c", [
    ("""    if (state != 1) {
        sIntroFrameCounter = 0;
    } else if (state == 1) {
        graphNode->flags = (graphNode->flags & 0xFF) | (LAYER_OPAQUE << 8);
        scaleMat = alloc_display_list(sizeof(*scaleMat));""",
     """    if (state != 1) {
        sIntroFrameCounter = 0;
    } else {
        graphNode->flags = (graphNode->flags & 0xFF) | (LAYER_OPAQUE << 8);
        scaleMat = alloc_display_list(sizeof(*scaleMat));"""),
    ("""    if (state != 1) {  // reset
        sTmCopyrightAlpha = 0;
    } else if (state == 1) {  // draw
        dl = alloc_display_list(6 * sizeof(*dl));""",
     """    if (state != 1) {  // reset
        sTmCopyrightAlpha = 0;
    } else {  // draw
        dl = alloc_display_list(6 * sizeof(*dl));"""),
    ("""            sFaceVisible[i] = 0;
        }

    } else if (state == 1) {
        if (sFaceCounter == 0) {""",
     """            sFaceVisible[i] = 0;
        }

    } else {
        if (sFaceCounter == 0) {"""),
    ("""    if (state != 1) {
        dl = NULL;
    } else if (state == 1) {
        genNode->fnNode.node.flags = (genNode->fnNode.node.flags & 0xFF) | (LAYER_OPAQUE << 8);""",
     """    if (state != 1) {
        dl = NULL;
    } else {
        genNode->fnNode.node.flags = (genNode->fnNode.node.flags & 0xFF) | (LAYER_OPAQUE << 8);"""),
    ])

elif group == "spindel":
    patch("src/game/behaviors/spindel.inc.c", [
    ("""    if (sp18 == 4 || sp18 == 3) {
        sp18 = 4;
    } else if (sp18 == 2 || sp18 == 1) {
        sp18 = 2;
    } else if (sp18 == 0) {
        sp18 = 1;
    }
""",
     """    switch (sp18) {
        case 4:
        case 3:
            sp18 = 4;
            break;
        case 2:
        case 1:
            sp18 = 2;
            break;
        case 0:
            sp18 = 1;
            break;
    }
"""),
    ])

elif group == "file_select":
    patch("src/menu/file_select.c", [
    ("""    if (sCursorClickingTimer == 0)
        gSPDisplayList(gDisplayListHead++, dl_menu_idle_hand);
    if (sCursorClickingTimer != 0)
        gSPDisplayList(gDisplayListHead++, dl_menu_grabbing_hand);
    gSPPopMatrix(gDisplayListHead++, G_MTX_MODELVIEW);""",
     """    if (sCursorClickingTimer == 0) {
        gSPDisplayList(gDisplayListHead++, dl_menu_idle_hand);
    } else {
        gSPDisplayList(gDisplayListHead++, dl_menu_grabbing_hand);
    }
    gSPPopMatrix(gDisplayListHead++, G_MTX_MODELVIEW);"""),
    ])

elif group == "renderer":
    patch("src/goddard/renderer.c", [
    ("""    for (i = sVertexBufStartIndex; i < (sVertexBufStartIndex + sVertexBufCount); i++) {
        // the ifs need to be separate to match...
        if (sCurrentGdDl->vtx[i].n.ob[0] == (s16) x) {
            if (sCurrentGdDl->vtx[i].n.ob[1] == (s16) y) {
                if (sCurrentGdDl->vtx[i].n.ob[2] == (s16) z) {
                    sTriangleBuf[sTriangleBufCount][D_801BB0B4++] = (s16) i;
                    return NULL;
                }
            }
        }
    }""",
     """    for (i = sVertexBufStartIndex; i < (sVertexBufStartIndex + sVertexBufCount); i++) {
        if (sCurrentGdDl->vtx[i].n.ob[0] == (s16) x && sCurrentGdDl->vtx[i].n.ob[1] == (s16) y
            && sCurrentGdDl->vtx[i].n.ob[2] == (s16) z) {
            sTriangleBuf[sTriangleBufCount][D_801BB0B4++] = (s16) i;
            return NULL;
        }
    }"""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
