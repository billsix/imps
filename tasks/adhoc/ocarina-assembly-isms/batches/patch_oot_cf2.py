#!/usr/bin/env python3
"""OoT control-flow groups, second set: test-first search loops and stale matching/annotation comments.
usage: patch_oot_cf2.py <checkout> <group>   (loops | eff_blure_loop | stale_comments)"""

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


if group == "loops":
    patch("soh/src/code/audio_load.c", [
        ("    while (true) {\n        if (size < 0x400) {\n            break;\n        }\n", "    while (size >= 0x400) {\n"),
    ])
    patch("soh/src/code/z_jpeg.c", [
        ("    while (true) {\n        if (exit) {\n            break;\n        }\n\n", "    while (!exit) {\n"),
    ])
    patch("soh/src/code/z_map_mark.c", [
        ("    while (true) {\n        if (mapMarkIconData->markType == MAP_MARK_NONE) {\n            break;\n        }\n\n",
         "    while (mapMarkIconData->markType != MAP_MARK_NONE) {\n"),
    ])
    patch("soh/src/overlays/misc/ovl_kaleido_scope/z_lmap_mark.c", [
        ("    while (true) {\n        if (mapMarkData->markType == PAUSE_MAP_MARK_NONE) {\n            break;\n        }\n\n",
         "    while (mapMarkData->markType != PAUSE_MAP_MARK_NONE) {\n"),
    ])
    patch("soh/src/overlays/gamestates/ovl_file_choose/z_file_choose.c", [
        ("    while (true) {\n        if ((*ones - 100) < 0) {\n            break;\n        }\n", "    while (*ones >= 100) {\n"),
        ("    while (true) {\n        if ((*ones - 10) < 0) {\n            break;\n        }\n", "    while (*ones >= 10) {\n"),
    ])
    patch(f"{A}/ovl_Bg_Spot16_Bombstone/z_bg_spot16_bombstone.c", [
        ("    while (true) {\n        if ((u32)this->unk_158 >= ARRAY_COUNTU(D_808B5EB0) || this->unk_154 < D_808B5EB0[this->unk_158][0]) {\n            break;\n        }\n\n",
         "    while ((u32)this->unk_158 < ARRAY_COUNTU(D_808B5EB0) && this->unk_154 >= D_808B5EB0[this->unk_158][0]) {\n"),
    ])
    patch("soh/src/code/code_800EC960.c", [
        ("    while (true) {\n        if (!func_800F6BB8()) {\n            return;\n        }\n    }\n}",
         "    while (func_800F6BB8()) {\n    }\n}"),
    ])
elif group == "eff_blure_loop":
    p: Path = root / "soh/src/code/z_eff_blure.c"
    lines: list[str] = p.read_text().split("\n")
    start: int = lines.index("    while (true) {")
    assert lines[start + 1] == "        if (this->elements[0].state == 0) {"
    tail: list[str] = ["        } else {", "            break;", "        }", "    }"]
    end: int = next(k for k in range(start, len(lines)) if lines[k : k + 4] == tail)
    body: list[str] = [ln[4:] if ln.startswith("    ") else ln for ln in lines[start + 2 : end]]
    lines[start : end + 4] = ["    while (this->elements[0].state == 0) {"] + body + ["    }"]
    p.write_text("\n".join(lines))
    print("patched soh/src/code/z_eff_blure.c")
elif group == "stale_comments":
    patch(f"{A}/ovl_Bg_Gnd_Soulmeiro/z_bg_gnd_soulmeiro.c", [
        ("    // This should be this->unk_198 == 0, this is required to match\n", ""),
    ])
    patch(f"{A}/ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c", [
        (" // thisx is required to match here", ""),
    ])
    patch(f"{A}/ovl_Demo_Ik/z_demo_ik.c", [("            // No break is required for matching\n", "")])
    patch(f"{A}/ovl_En_Zl4/z_en_zl4.c", [("            // no break here is required for matching\n", "")])
    patch("soh/src/code/z_actor.c", [
        ("    // This is convoluted but it seems like it must be a single if statement to match\n", ""),
    ])
    patch("soh/src/code/z_en_item00.c", [
        ("    // This is convoluted but it seems like it must be a single condition to match\n", ""),
    ])
    patch("soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_item.c", [
        ("                // Seem necessary to match\n\n", ""),
        (" // required to match?", ""),
    ])
    patch("soh/src/code/z_lights.c", [("// return type must not be void to match\n", "")])
    patch(f"{A}/ovl_player_actor/z_player.c", [
        ("// return type can't be void due to regalloc in func_8083F72C\n", ""),
    ])
    patch("soh/src/code/audio_heap.c", [
        ("    //! @bug UB: missing return. \"ret\" is in v0 at this point, but doing an\n    // explicit return uses an additional register.\n",
         "    // The ROM fell off the end here with `ret` still in v0; the port returns it explicitly.\n"),
    ])
    patch(f"{A}/ovl_En_Po_Sisters/z_en_po_sisters.c", [
        ("        //! @bug uninitialised spE7\n", "        // spE7 was uninitialised in the ROM; the port zeroes it at its declaration.\n"),
    ])
    patch("soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_equipment.c", [
        ("    if ((pauseCtx->unk_1E4 == 7) && (sEquipTimer == 9)) {\n        //! @bug: This function shouldn't take any arguments\n        // KaleidoScope_ProcessPlayerPreRender(play);\n    }\n",
         ""),
    ])
    patch(f"{A}/ovl_En_Tana/z_en_tana.c", [
        ("//! @bug A third entry is missing here. When printing the string indexed by `params` for type 2, the\n//! next data entry will be dereferenced and print garbage, stopping any future printing.\n//! In a non-matching context, this can cause a crash if the next item isn't a valid pointer.\n",
         "// The ROM's table had only two entries, so type 2 printed whatever followed; the port adds the third.\n"),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
