#!/usr/bin/env python3
# save_generator.py — interactive Ship of Harkinian save-file generator.
#
# Interviews you about the save you want (dungeons beaten first, then item
# loadout with progression-consistent defaults, full stocks assumed for
# everything you own), writes a base-quest .sav locally, and tells you where
# to install it and how to back up your old save.  It never installs or
# overwrites anything itself.
#
# Base quest only (decided 2026-09-01): randomizer saves carry a seed/check
# section and a build-version lock and are out of scope.
#
# Format and field semantics: tasks/reference/ocarina/save-file-generator.md
# (derived from SaveManager.cpp / z64save.h / z_play.c at the imps pin, and
# validated against a real fresh save).  Self-test:
#   python3 save_generator.py --selftest ../runDir/Save/file1.sav

import argparse
import copy
import datetime
import json
import sys

# ---------------------------------------------------------------------------
# Constants from the SoH source (file:line anchors in the reference doc)
# ---------------------------------------------------------------------------

STARTING_HEALTH = 48          # 3 hearts, 16 per heart
HEART = 16
MAGIC_METER = 48              # per magic level
CUTSCENE_NONE = 0
CUTSCENE_INTRO = 65521        # 0xFFF1, fresh-file Deku Tree intro
ENTR_LINKS_HOUSE_CHILD = 187
ENTR_TEMPLE_OF_TIME_ADULT = 1524
SCENE_LINKS_HOUSE = 52        # non-dungeon, so entranceIndex is honored on load

# inventory.items slot order (z64item.h InventorySlot)
SLOTS = {"stick": 0, "nut": 1, "bomb": 2, "bow": 3, "arrow_fire": 4,
         "dins_fire": 5, "slingshot": 6, "ocarina": 7, "bombchu": 8,
         "hookshot": 9, "arrow_ice": 10, "farores_wind": 11, "boomerang": 12,
         "lens": 13, "bean": 14, "hammer": 15, "arrow_light": 16,
         "nayrus_love": 17, "bottle1": 18, "bottle2": 19, "bottle3": 20,
         "bottle4": 21, "trade_adult": 22, "trade_child": 23}

ITEM = {"stick": 0x00, "nut": 0x01, "bomb": 0x02, "bow": 0x03,
        "arrow_fire": 0x04, "dins_fire": 0x05, "slingshot": 0x06,
        "ocarina_fairy": 0x07, "ocarina_time": 0x08, "bombchu": 0x09,
        "hookshot": 0x0A, "longshot": 0x0B, "arrow_ice": 0x0C,
        "farores_wind": 0x0D, "boomerang": 0x0E, "lens": 0x0F, "bean": 0x10,
        "hammer": 0x11, "arrow_light": 0x12, "nayrus_love": 0x13,
        "bottle": 0x14, "none": 255}

# inventory.equipment (owned): one nibble per type, bit per item
EQUIP_OWNED = {"kokiri_sword": 1 << 0, "master_sword": 1 << 1,
               "biggoron_sword": 1 << 2,
               "deku_shield": 1 << 4, "hylian_shield": 1 << 5,
               "mirror_shield": 1 << 6,
               "kokiri_tunic": 1 << 8, "goron_tunic": 1 << 9,
               "zora_tunic": 1 << 10,
               "kokiri_boots": 1 << 12, "iron_boots": 1 << 13,
               "hover_boots": 1 << 14}

# upgrades bit-packing: (shift, capacity table). Wallet has no item slot.
UPGRADES = {"quiver": (0, [0, 30, 40, 50]),
            "bomb_bag": (3, [0, 20, 30, 40]),
            "strength": (6, None),
            "scale": (9, None),
            "wallet": (12, [99, 200, 500, 999]),
            "bullet_bag": (14, [0, 30, 40, 50]),
            "sticks": (17, [0, 10, 20, 30]),
            "nuts": (20, [0, 20, 30, 40])}

# questItems bits (z64item.h QuestItem)
QUEST = {"medallion_forest": 1 << 0, "medallion_fire": 1 << 1,
         "medallion_water": 1 << 2, "medallion_spirit": 1 << 3,
         "medallion_shadow": 1 << 4, "medallion_light": 1 << 5,
         "song_minuet": 1 << 6, "song_bolero": 1 << 7,
         "song_serenade": 1 << 8, "song_requiem": 1 << 9,
         "song_nocturne": 1 << 10, "song_prelude": 1 << 11,
         "song_lullaby": 1 << 12, "song_epona": 1 << 13,
         "song_saria": 1 << 14, "song_sun": 1 << 15,
         "song_time": 1 << 16, "song_storms": 1 << 17,
         "kokiri_emerald": 1 << 18, "goron_ruby": 1 << 19,
         "zora_sapphire": 1 << 20, "stone_of_agony": 1 << 21,
         "gerudo_card": 1 << 22, "skull_token": 1 << 23}

# eventChkInf "learned warp song" duplicates (z64save.h EVENTCHKINF_LEARNED_*)
SONG_EVENTS = {"song_minuet": (5, 1 << 0), "song_bolero": (5, 1 << 1),
               "song_serenade": (5, 1 << 2), "song_nocturne": (5, 1 << 4),
               "song_prelude": (5, 1 << 5), "song_requiem": (10, 1 << 12)}

# The dungeon table.  beat: ("evt", word, bit) for the six vanilla blue-warp
# flags, ("rand", bit) for SoH's randomizerInf flags (Spirit/Shadow have NO
# vanilla flag — the #1 trap).  companions: extra eventChkInf set alongside.
DUNGEONS = [
    # key, label, era, beat-encoding, quest reward, boss scene, companions
    ("deku",    "Deku Tree (Gohma)",              "child",
     ("evt", 0, 0x0200), "kokiri_emerald",  17, [(0, 0x0080)]),
    ("dodongo", "Dodongo's Cavern (King Dodongo)", "child",
     ("evt", 2, 0x0020), "goron_ruby",      18, []),
    ("jabu",    "Jabu-Jabu's Belly (Barinade)",    "child",
     ("evt", 3, 0x0080), "zora_sapphire",   19, []),
    ("forest",  "Forest Temple (Phantom Ganon)",   "adult",
     ("evt", 4, 0x0100), "medallion_forest", 20, []),
    ("fire",    "Fire Temple (Volvagia)",          "adult",
     ("evt", 4, 0x0200), "medallion_fire",  21, []),
    ("water",   "Water Temple (Morpha)",           "adult",
     ("evt", 4, 0x0400), "medallion_water", 22, []),
    ("spirit",  "Spirit Temple (Twinrova)",        "adult",
     ("rand", 1 << 0),   "medallion_spirit", 23, []),
    ("shadow",  "Shadow Temple (Bongo Bongo)",     "adult",
     ("rand", 1 << 1),   "medallion_shadow", 24, []),
]

PRESETS = [
    ("fresh",  "Fresh file (nothing beaten)", []),
    ("child",  "All child dungeons beaten", ["deku", "dodongo", "jabu"]),
    ("forest", "Child dungeons + Forest Temple",
     ["deku", "dodongo", "jabu", "forest"]),
    ("water",  "Everything through Water Temple",
     ["deku", "dodongo", "jabu", "forest", "fire", "water"]),
    ("all",    "All eight dungeons beaten",
     [d[0] for d in DUNGEONS]),
    ("custom", "Pick dungeon by dungeon", None),
]

# In-game filename charset (z_file_nameset_data.c): A=0xAB.., a=0xC5..,
# digits 0xA1.., blank 0xDF.  Verified against a real save ("Bill").
NAME_BLANK = 0xDF


def encode_name(name):
    out = []
    for ch in name[:8]:
        if "A" <= ch <= "Z":
            out.append(0xAB + ord(ch) - ord("A"))
        elif "a" <= ch <= "z":
            out.append(0xC5 + ord(ch) - ord("a"))
        elif "0" <= ch <= "9":
            out.append(0xA1 + ord(ch) - ord("0"))
        else:
            out.append(NAME_BLANK)
    while len(out) < 8:
        out.append(NAME_BLANK)
    return out


# ---------------------------------------------------------------------------
# The baseline: a fresh new-game save, matching SaveManager::InitFileNormal +
# SaveBase (base section version 4) key-for-key.
# ---------------------------------------------------------------------------

def scene_flags_entry():
    return {"chest": 0, "swch": 0, "clear": 0, "collect": 0, "unk": 0,
            "rooms": 0, "floors": 0}


def scarecrow_note():
    return {"noteIdx": 0, "unk_02": 0, "volume": 0, "vibrato": 0,
            "tone": 0, "semitone": 0}


def equips_block(equipment=0):
    return {"buttonItems": [255] * 8, "cButtonSlots": [255] * 7,
            "equipment": equipment}


def fw_block():
    return {"pos": {"x": 0, "y": 0, "z": 0}, "yaw": 0, "playerParams": 0,
            "entranceIndex": 0, "roomIndex": 0, "set": 0,
            "tempSwchFlags": 0, "tempCollectFlags": 0}


def fresh_base():
    scene_flags = [scene_flags_entry() for _ in range(124)]
    scene_flags[5]["swch"] = 1073741824  # InitFileNormal quirk (0x40000000)
    inf_table = [0] * 30
    inf_table[29] = 1                    # "no sword on B" flag
    return {
        "entranceIndex": ENTR_LINKS_HOUSE_CHILD,
        "linkAge": 1,
        "cutsceneIndex": CUTSCENE_INTRO,
        "dayTime": 27307,
        "nightFlag": 1,
        "totalDays": 0,
        "bgsDayCount": 0,
        "deaths": 0,
        "playerName": [NAME_BLANK] * 8,
        "healthCapacity": STARTING_HEALTH,
        "health": STARTING_HEALTH,
        "magicLevel": 0,
        "magic": MAGIC_METER,            # yes, even with no magic acquired
        "rupees": 0,
        "swordHealth": 0,
        "naviTimer": 0,
        "isMagicAcquired": 0,
        "isDoubleMagicAcquired": 0,
        "isDoubleDefenseAcquired": 0,
        "bgsFlag": 0,
        "ocarinaGameRoundNum": 0,
        "childEquips": equips_block(0),
        "adultEquips": equips_block(0),
        "unk_54": 0,
        "savedSceneNum": SCENE_LINKS_HOUSE,
        "equips": equips_block(0x1100),  # Kokiri tunic + boots worn
        "inventory": {
            "items": [255] * 24,
            "ammo": [0] * 16,
            "equipment": 0x1100,         # Kokiri tunic + boots owned
            "upgrades": 0,
            "questItems": 0,
            "dungeonItems": [0] * 20,
            "dungeonKeys": [-1] * 19,
            "defenseHearts": 0,
            "gsTokens": 0,
        },
        "sceneFlags": scene_flags,
        "fw": fw_block(),
        "backupFW": fw_block(),
        "gsFlags": [0] * 6,
        "highScores": [0] * 7,
        "eventChkInf": [0] * 14,
        "itemGetInf": [0] * 4,
        "infTable": inf_table,
        "randomizerInf": [0] * 188,
        "worldMapAreaData": 0,
        "scarecrowLongSongSet": 0,
        "scarecrowLongSong": [scarecrow_note() for _ in range(108)],
        "scarecrowSpawnSongSet": 0,
        "scarecrowSpawnSong": [scarecrow_note() for _ in range(16)],
        "horseData": {"scene": 81,
                      "pos": {"x": -1840, "y": 72, "z": 5497},
                      "angle": -27353},
        "dogParams": 0,
        "filenameLanguage": 2,           # NTSC English charset
        "maskMemory": 0,
        "isMasterQuest": False,
    }


def fresh_save(build=("Ackbar Delta (9.2.3)", 9, 2, 3)):
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    return {
        "version": 1,
        "fileType": 0,                   # vanilla; rando is out of scope
        "sections": {
            "base": {"version": 4, "data": fresh_base()},
            # sohStats.data MUST exist and be an object (meta-scan reads it
            # unconditionally); these fields keep it honest.
            "sohStats": {"version": 1, "data": {
                "buildVersion": build[0],
                "buildVersionMajor": build[1],
                "buildVersionMinor": build[2],
                "buildVersionPatch": build[3],
                "fileCreatedAt": now_ms,
            }},
            "trackerData": {"version": 1, "data": {
                "areasSpoiled": 4294967295, "checkStatus": []}},
            "hintTrackerData": {"version": 1, "data": {"readHints": []}},
            "itemTrackerData": {"version": 1, "data": {"personalNotes": ""}},
        },
    }


# ---------------------------------------------------------------------------
# Progression model: what a player who beat these dungeons plausibly has.
# Everything here is a DEFAULT the user can toggle in the review step.
# ---------------------------------------------------------------------------

def default_loadout(beaten):
    b = set(beaten)
    any_adult = any(d in b for d in ("forest", "fire", "water", "spirit",
                                     "shadow"))
    have = set()
    up = {}

    def owns(*names):
        have.update(names)

    if "deku" in b or b:
        owns("kokiri_sword", "deku_shield", "item:stick", "item:nut")
        up["sticks"] = max(up.get("sticks", 0), 1)
        up["nuts"] = max(up.get("nuts", 0), 1)
    if "deku" in b:
        owns("item:slingshot", "item:ocarina_fairy",
             "song_lullaby", "song_saria")
        up["bullet_bag"] = 1
    if "dodongo" in b:
        owns("item:bomb", "song_epona")
        up["bomb_bag"] = max(up.get("bomb_bag", 0), 1)
        up["strength"] = max(up.get("strength", 0), 1)
    if "jabu" in b:
        owns("item:boomerang", "item:bottle1", "song_sun")
        up["scale"] = max(up.get("scale", 0), 1)
    if any_adult:
        owns("master_sword", "hylian_shield", "item:ocarina_time",
             "song_time", "magic", "item:hookshot")
        up["wallet"] = max(up.get("wallet", 0), 1)
    if "forest" in b:
        owns("item:bow", "song_minuet")
        up["quiver"] = max(up.get("quiver", 0), 1)
    if "fire" in b:
        owns("item:hammer", "goron_tunic", "song_bolero")
        up["bomb_bag"] = max(up.get("bomb_bag", 0), 1)
    if "water" in b:
        owns("item:longshot", "zora_tunic", "iron_boots", "song_serenade")
    if "shadow" in b:
        owns("hover_boots", "item:lens", "item:dins_fire", "song_nocturne")
    if "spirit" in b:
        owns("mirror_shield", "song_requiem")
        up["strength"] = max(up.get("strength", 0), 2)
    if len(b) >= 2 and not any_adult:
        owns("magic")
    return have, up


# ---------------------------------------------------------------------------
# Applying answers to the save
# ---------------------------------------------------------------------------

def apply(save, beaten, have, up, name, extras):
    base = save["sections"]["base"]["data"]
    inv = base["inventory"]
    quest = 0
    beaten = list(beaten)

    base["playerName"] = encode_name(name)

    for key, _label, _era, beat, reward, boss_scene, comps in DUNGEONS:
        if key not in beaten:
            continue
        if beat[0] == "evt":
            base["eventChkInf"][beat[1]] |= beat[2]
        else:  # ("rand", bit) — Spirit/Shadow live in randomizerInf, NOT
            # eventChkInf; writing eventChkInf bits for them corrupts logic.
            base["randomizerInf"][0] |= beat[1]
        quest |= QUEST[reward]           # flag AND reward, always paired
        base["sceneFlags"][boss_scene]["clear"] |= 1  # boss room cleared
        for word, bit in comps:
            base["eventChkInf"][word] |= bit

    # Nocturne's story cutscene flag rides with forest+fire+water done.
    if {"forest", "fire", "water"} <= set(beaten):
        base["eventChkInf"][10] |= 0x0400  # BONGO_BONGO_ESCAPED_FROM_WELL

    # Items and equipment
    equipment = inv["equipment"]
    for h in sorted(have):
        if h in EQUIP_OWNED:
            equipment |= EQUIP_OWNED[h]
        elif h.startswith("item:"):
            item = h[5:]
            slot_key = {"ocarina_fairy": "ocarina", "ocarina_time": "ocarina",
                        "longshot": "hookshot", "bottle1": "bottle1"}.get(
                            item, item)
            value = ITEM[item] if item != "bottle1" else ITEM["bottle"]
            inv["items"][SLOTS[slot_key]] = value
        elif h in QUEST:                 # songs
            quest |= QUEST[h]
            if h in SONG_EVENTS:
                word, bit = SONG_EVENTS[h]
                base["eventChkInf"][word] |= bit
        elif h == "magic":
            base["isMagicAcquired"] = 1
    inv["equipment"] = equipment
    inv["questItems"] = quest

    # Worn gear: best owned, 1-based nibbles (sword|shield<<4|tunic<<8|boots<<12)
    def best(*pairs):
        v = 0
        for value, flag in pairs:
            if equipment & EQUIP_OWNED[flag]:
                v = value
        return v
    worn = (best((1, "kokiri_sword"), (2, "master_sword"),
                 (3, "biggoron_sword"))
            | best((1, "deku_shield"), (2, "hylian_shield"),
                   (3, "mirror_shield")) << 4
            | best((1, "kokiri_tunic"), (2, "goron_tunic"),
                   (3, "zora_tunic")) << 8
            | best((1, "kokiri_boots"), (2, "iron_boots"),
                   (3, "hover_boots")) << 12)
    base["equips"]["equipment"] = worn
    if worn & 0xF:
        base["infTable"][29] = 0         # a sword is on B now

    # B and C buttons must be consistent with the worn gear: a save with a
    # sword equipped but buttonItems[0] empty is a state the game never
    # writes, and the HUD icon draw chokes on it (found the hard way —
    # 2026-09-01).  Mirror InitFileDebug's shape: B = worn sword, C-left/
    # down/right = up to three owned items, D-pad empty.
    sword_item = {1: 0x3B, 2: 0x3C, 3: 0x3D}   # kokiri/master/biggoron
    buttons = [255] * 8
    cslots = [255] * 7
    if worn & 0xF:
        buttons[0] = sword_item[worn & 0xF]
    ci = 0
    for pref in ("bow", "bomb", "ocarina", "slingshot", "boomerang",
                 "hookshot", "hammer", "lens", "dins_fire", "stick", "nut"):
        slot = SLOTS[pref]
        if inv["items"][slot] != 255 and ci < 3:
            buttons[1 + ci] = inv["items"][slot]
            cslots[ci] = slot
            ci += 1
    base["equips"]["buttonItems"] = buttons
    base["equips"]["cButtonSlots"] = cslots

    # Upgrades + FULL STOCKS for everything owned
    upgrades = 0
    for upg, level in up.items():
        shift, caps = UPGRADES[upg]
        upgrades |= (level & 7) << shift
        if caps is not None:
            slot = {"quiver": "bow", "bomb_bag": "bomb",
                    "bullet_bag": "slingshot", "sticks": "stick",
                    "nuts": "nut"}.get(upg)
            if slot and inv["items"][SLOTS[slot]] != 255:
                inv["ammo"][SLOTS[slot]] = caps[level]
    inv["upgrades"] = upgrades
    wallet_caps = UPGRADES["wallet"][1]
    base["rupees"] = wallet_caps[up.get("wallet", 0)]
    if inv["items"][SLOTS["bean"]] != 255:
        inv["ammo"][SLOTS["bean"]] = 10

    # Magic / health / defense
    if extras.get("double_magic"):
        base["isMagicAcquired"] = 1
        base["isDoubleMagicAcquired"] = 1
    base["magic"] = MAGIC_METER * (2 if base["isDoubleMagicAcquired"]
                                   else 1) if base["isMagicAcquired"] \
        else MAGIC_METER
    if extras.get("double_defense"):
        base["isDoubleDefenseAcquired"] = 1
        inv["defenseHearts"] = 20
    base["healthCapacity"] = STARTING_HEALTH + HEART * len(beaten) \
        + HEART * extras.get("extra_hearts", 0)
    base["healthCapacity"] = min(base["healthCapacity"], 320)
    base["health"] = base["healthCapacity"]

    # Era and spawn.  savedSceneNum stays a non-dungeon scene so the loader
    # honors entranceIndex (Sram_OpenSave rewrites it for dungeon scenes).
    adult = extras.get("adult", any(
        d in beaten for d in ("forest", "fire", "water", "spirit", "shadow")))
    base["linkAge"] = 0 if adult else 1
    base["entranceIndex"] = (ENTR_TEMPLE_OF_TIME_ADULT if adult
                             else ENTR_LINKS_HOUSE_CHILD)
    if beaten or have - {"item:stick", "item:nut"}:
        base["cutsceneIndex"] = CUTSCENE_NONE   # skip the intro cutscene
    return save


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------

def ask(prompt, default_yes=True):
    suffix = " [Y/n] " if default_yes else " [y/N] "
    while True:
        r = input(prompt + suffix).strip().lower()
        if not r:
            return default_yes
        if r in ("y", "yes"):
            return True
        if r in ("n", "no"):
            return False


def interview():
    print("Ship of Harkinian save generator — base quest only.\n")

    print("Which dungeons has this save beaten?")
    for i, (_key, label, _ids) in enumerate(PRESETS, 1):
        print(f"  {i}. {label}")
    while True:
        r = input(f"Choose 1-{len(PRESETS)} [1]: ").strip() or "1"
        if r.isdigit() and 1 <= int(r) <= len(PRESETS):
            break
    picked = PRESETS[int(r) - 1][2]
    if picked is None:
        picked = []
        for key, label, era, *_ in DUNGEONS:
            if ask(f"  beaten: {label} ({era})?", default_yes=False):
                picked.append(key)

    have, up = default_loadout(picked)
    print("\nBased on that, this loadout is assumed "
          "(full stocks for everything owned):")
    nice = sorted(h.replace("item:", "") for h in have)
    print("  " + (", ".join(nice) if nice else "(nothing)"))
    if not ask("Keep these defaults?"):
        kept = set()
        for h in sorted(have):
            if ask(f"  own {h.replace('item:', '')}?"):
                kept.add(h)
        have = kept

    extras = {}
    extras["double_magic"] = ask("Double magic?", default_yes=False)
    extras["double_defense"] = ask("Double defense?", default_yes=False)
    hearts = input("Extra heart containers beyond one per boss [0]: ").strip()
    extras["extra_hearts"] = int(hearts) if hearts.isdigit() else 0
    adult_default = any(d in picked
                        for d in ("forest", "fire", "water", "spirit",
                                  "shadow"))
    extras["adult"] = ask("Start as adult?", default_yes=adult_default)

    name = input("\nFile name shown in-game (max 8, A-z 0-9) [LINK]: ")
    return picked, have, up, (name.strip() or "LINK"), extras


# ---------------------------------------------------------------------------
# Self-test: an all-defaults fresh save must match a real pristine save.
# ---------------------------------------------------------------------------

def deep_diff(a, b, path=""):
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                diffs.append(f"{path}.{k}: missing in generated")
            elif k not in b:
                diffs.append(f"{path}.{k}: extra in generated")
            else:
                diffs.extend(deep_diff(a[k], b[k], f"{path}.{k}"))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f"{path}: length {len(a)} vs real {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diffs.extend(deep_diff(x, y, f"{path}[{i}]"))
    elif a != b:
        diffs.append(f"{path}: generated {a!r} vs real {b!r}")
    return diffs


def selftest(real_path):
    real = json.load(open(real_path))
    gen = fresh_save()
    # Fields that legitimately differ from any particular real save:
    volatile = {"playerName", "deaths"}
    diffs = []
    for k in ("version", "fileType"):
        diffs.extend(deep_diff(gen[k], real[k], k))
    for name in real["sections"]:
        if name not in gen["sections"]:
            diffs.append(f"sections.{name}: missing in generated")
    gb, rb = gen["sections"]["base"], real["sections"]["base"]
    diffs.extend(deep_diff(gb["version"], rb["version"], "base.version"))
    for k in sorted(set(gb["data"]) | set(rb["data"])):
        if k in volatile:
            continue
        if k not in gb["data"]:
            diffs.append(f"base.data.{k}: missing in generated")
        elif k not in rb["data"]:
            diffs.append(f"base.data.{k}: extra in generated")
        else:
            diffs.extend(deep_diff(gb["data"][k], rb["data"][k],
                                   f"base.data.{k}"))
    if diffs:
        print(f"SELFTEST: {len(diffs)} difference(s) vs {real_path}:")
        for d in diffs[:60]:
            print("  " + d)
        return 1
    print(f"SELFTEST OK: generated fresh save matches {real_path} "
          "(base section, name/deaths aside)")
    return 0


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", "-o", default="file1.sav",
                   help="output path (default ./file1.sav)")
    p.add_argument("--selftest", metavar="REAL_SAV",
                   help="compare an all-defaults save against a real "
                        "pristine .sav and exit")
    args = p.parse_args()

    if args.selftest:
        sys.exit(selftest(args.selftest))

    picked, have, up, name, extras = interview()
    save = apply(fresh_save(), picked, have, up, name, extras)

    with open(args.output, "w") as f:
        json.dump(save, f, indent=1, sort_keys=True)
        f.write("\n")

    slot = args.output.rsplit("/", 1)[-1]
    print(f"""
Wrote {args.output}.

To install (the game reads saves from runDir/Save/, slots file1-3.sav):

  1. Back up any existing save in that slot first:
       cp OcarinaOfTime/runDir/Save/{slot} \\
          OcarinaOfTime/runDir/Save/{slot}.backup-$(date +%Y%m%d)
  2. Install:
       cp {args.output} OcarinaOfTime/runDir/Save/{slot}
  3. Launch with ./run.sh and load the slot.

Nothing was installed automatically. If the game shows the slot as empty
or renames the file to .bak, the file was rejected — see
tasks/reference/ocarina/save-file-generator.md for the failure modes.""")


if __name__ == "__main__":
    main()
