#!/usr/bin/env python3
"""OoT boolean-shape groups (reports/booleans-comments-whole-functions.md class 2 + C2).
usage: patch_oot_bool2.py <checkout> <group>"""

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


A: str = "soh/src/overlays/actors"

if group == "bool_inc":
    patch(f"{A}/ovl_En_Clear_Tag/z_en_clear_tag.c", [
        ("                isMaterialApplied++;\n", "                isMaterialApplied = true;\n", 5),
    ])
elif group == "ternary_bool":
    patch(f"{A}/ovl_En_Fr/z_en_fr.c", [
        ("        this->isBelowWaterSurfaceCurrent = this->actor.world.pos.y <= waterSurface ? true : false;",
         "        this->isBelowWaterSurfaceCurrent = this->actor.world.pos.y <= waterSurface;"),
        ("        frog->isButterflyDrawn = frogIndex == frogIndexButterfly ? true : false;",
         "        frog->isButterflyDrawn = frogIndex == frogIndexButterfly;"),
    ])
    patch(f"{A}/ovl_En_Hy/z_en_hy.c", [
        ("                return !LINK_IS_ADULT ? false : true;", "                return LINK_IS_ADULT;"),
    ])
    patch(f"{A}/ovl_En_Ssh/z_en_ssh.c", [
        ("    if (!!(acFlags & AC_HIT) == 0) {", "    if (!(acFlags & AC_HIT)) {"),
    ])
    patch(f"{A}/ovl_En_St/z_en_st.c", [
        ("    if (!!(acFlags & AC_HIT) == 0) {", "    if (!(acFlags & AC_HIT)) {"),
    ])
    patch(f"{A}/ovl_En_Ko/z_en_ko.c", [
        ("""    if (yawDiffAbs < 0x3FFC) {
        result = true;
    } else {
        result = false;
    }
    return result;
}""", """    return yawDiffAbs < 0x3FFC;
}"""),
        ("""    s16 yawDiffAbs;
    s32 result;

    yawDiff = this->actor.yawTowardsPlayer""", """    s16 yawDiffAbs;

    yawDiff = this->actor.yawTowardsPlayer"""),
    ])
elif group == "eq1_bitfield":
    patch("soh/src/code/code_800EC960.c", [
        ("        if (gAudioContext.notes[i].noteSubEu.bitField0.enabled == 1) {",
         "        if (gAudioContext.notes[i].noteSubEu.bitField0.enabled) {"),
    ])
    patch("soh/src/code/audio_effects.c", [
        ("        if (seqPlayer->channels[i]->enabled == 1) {", "        if (seqPlayer->channels[i]->enabled) {"),
    ])
    patch("soh/src/code/audio_load.c", [
        ("    if (sample->isRelocated == 1) {", "    if (sample->isRelocated) {"),
    ])
    patch(f"{A}/ovl_Fishing/z_fishing.c", [
        ("            if (this->isLoach == 1) {", "            if (this->isLoach) {"),
        ("                    if (this->isLoach == 1) {", "                    if (this->isLoach) {"),
    ])
elif group == "ossan_dead":
    patch(f"{A}/ovl_En_Ossan/z_en_ossan.c", [
        ("""    //! @bug This check will always evaluate to false, it should be || not &&
    if (this->actor.params > OSSAN_TYPE_MASK && this->actor.params < OSSAN_TYPE_KOKIRI) {
        Actor_Kill(&this->actor);
        osSyncPrintf(VT_COL(RED, WHITE));
        osSyncPrintf("引数がおかしいよ(arg_data=%d)！！\\n", this->actor.params);
        osSyncPrintf(VT_RST);
        assert(this->actor.params > OSSAN_TYPE_MASK && this->actor.params < OSSAN_TYPE_KOKIRI);
        return;
    }

""", ""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
