# Ship of Harkinian save files — format, semantics, and the generator

> **Provenance:** authored 2026-09-01 against the imps pin `acdbc651d`
> (9.2.3-421) **with the patch series applied**, by two verified source
> readers plus field-level validation against a real pristine save
> (`n64/OcarinaOfTime/runDir/Save/file1.sav`). Online research was authorized
> but not needed — the code and the real save answered everything.
> The tool this documents: `n64/OcarinaOfTime/tools/save_generator.py`.

## The container (SaveManager.cpp)

SoH saves are **plain JSON — no checksums, no magic bytes, no binary**:

```json
{ "version": 1, "fileType": 0,
  "sections": { "<name>": { "version": N, "data": { ... } }, ... } }
```

- 3 slots: `Save/file1.sav`..`file3.sav`, read from `<cwd>/Save/` (run.sh
  runs from `runDir/`, so `runDir/Save/`). `global.sav` is only
  cross-file settings (audio/z-target/language) — irrelevant to slots.
- `fileType`: 0 vanilla, 1 randomizer. Container `version` is always 1.
- Sections written for a vanilla save (all present in the real file):
  `base` (version **4**), `sohStats` (1), `trackerData` (1),
  `hintTrackerData` (1), `itemTrackerData` (1). The `randomizer` section
  is skipped for vanilla; `entrances`/`scenes` are subsections folded
  into `sohStats`.
- Writer formatting: `indent=1`, keys alphabetically sorted, trailing
  newline, UTF-8, **no floating-point values anywhere** (`fw.pos` is
  `Vec3i`; the whole 43 KB real file contains one `.`, inside
  `buildVersion`). Emit integers only.
- On load, `InitFileNormal` runs FIRST, then JSON overlays it — missing
  `data` fields default to new-game values, never fail.

### What makes a file valid vs destroyed

Two distinct gates (SaveManager.cpp:548-699 and :1369-1447):

1. **Startup meta scan** (decides if the slot shows as occupied). Reads
   with bare `operator[]` — hard-requires, inside `sections.base.data`:
   `deaths`, `playerName` (≥8 numbers), `healthCapacity`, `health`,
   `isMagicAcquired`, `isDoubleMagicAcquired`, `rupees`, and `inventory`
   with `questItems`, `items` (≥24), `equipment`, `upgrades`,
   `gsTokens`, `defenseHearts`. Plus `sections.sohStats.data` must exist
   **as an object**. Failure → slot silently empty, file left on disk.
2. **LoadFile** (when the slot is opened). Every section object must
   carry a numeric `"version"` — a missing one throws here, and the
   exception handler **renames the file to `file<N>-<time>.bak`** ("the
   corruption popup"). This is the one landmine that passes gate 1 and
   then destroys the file. Unknown section *names* are fine (skipped as
   unloaded-mod data); a known name with an unknown version is skipped.
3. On load, `Sram_OpenSave` post-processes: health floors at 3 hearts,
   `magicLevel` force-reset to 0 (**set `isMagicAcquired`/
   `isDoubleMagicAcquired`, never `magicLevel`**), adult without the
   Master Sword gets it granted, and `entranceIndex` is REWRITTEN from
   `savedSceneNum` for dungeon/boss scenes — so keep `savedSceneNum` a
   non-dungeon scene (52, Link's House) and `entranceIndex` is honored
   (187 child spawn / 1524 adult Temple of Time).

Randomizer saves add the `randomizer` section, more hard-required meta
keys, and a **build-version equality lock** (mismatch → renamed to
`.bak`). **Decision: base quest only** (William Emerison Six
<billsix@gmail.com>, 2026-09-01); the
generator emits `fileType: 0` and refuses nothing else.

## The field semantics that matter

### Dungeon completion — the two traps

The game's authority is `CheckDungeonCount()` (`soh/src/code/z_play.c`),
and it is asymmetric:

| Dungeon | "Beaten" flag |
|---|---|
| Deku Tree | `eventChkInf[0] \|= 0x0200` (+ companion `0x0080`) |
| Dodongo's Cavern | `eventChkInf[2] \|= 0x0020` |
| Jabu-Jabu | `eventChkInf[3] \|= 0x0080` |
| Forest / Fire / Water | `eventChkInf[4] \|= 0x0100 / 0x0200 / 0x0400` |
| **Spirit / Shadow** | **`randomizerInf[0] \|= 0x1 / 0x2`** — SoH-invented; they have NO vanilla eventChkInf flag |

**Trap 1:** writing eventChkInf bits for Spirit/Shadow looks symmetric
and silently produces a broken save (count stays 6, blue warps re-fire).
**Trap 2:** the flag and the reward are independent — always pair the
beaten flag with the `questItems` bit (medallions bits 0-5, stones bits
18-20), or the Door of Time / rainbow bridge never open. Boss-room
`sceneFlags[bossScene].clear` is cosmetic (stops boss respawn), not what
"beaten" checks. Songs live in `questItems` bits 6-17, with warp songs
duplicated into eventChkInf "learned" bits; the Bongo-escaped flag
(`eventChkInf[10] |= 0x0400`) rides with forest+fire+water done.

### Inventory encoding (all in `base.data.inventory`)

- `items[24]`: slot order per `InventorySlot`; 255 = empty; ocarinas and
  hookshot/longshot share slots (write the better item's value).
- `equipment` (owned): bit-per-item nibbles — swords `1/2/4` << 0,
  shields << 4, tunics << 8, boots << 12. `equips.equipment` (worn) is
  DIFFERENT: 1-based values per nibble. Fresh file: `0x1100` both
  (Kokiri tunic+boots), and `infTable[29] = 1` means "no sword on B" —
  clear it when a sword is worn.
- `upgrades` bit-packed: quiver<<0, bomb bag<<3, strength<<6, scale<<9,
  wallet<<12, bullet bag<<14, sticks<<17, nuts<<20. Capacities
  (`z_inventory.c`): quiver 0/30/40/50, bombs 0/20/30/40, wallet
  99/200/500/999, bullets 0/30/40/50, sticks 0/10/20/30, nuts
  0/20/30/40. `ammo[16]` indexed by item slot (`ammo[15]` is the bean
  price counter, not hammer ammo).
- Health in 1/16 hearts (48 = 3 hearts, max 320); magic meter = 48 per
  level; double defense needs `isDoubleDefenseAcquired` **and**
  `inventory.defenseHearts = 20`.
- `playerName`: game charset — A=0xAB.., a=0xC5.., digits 0xA1..,
  blank 0xDF (verified against the real save's "Bill").
- **`equips.buttonItems`/`cButtonSlots` must be consistent with the worn
  gear** (learned from a real crash, 2026-09-01): a save wearing a sword
  in `equips.equipment` with `buttonItems[0] = 255` is a state the game
  never writes, and it crashed on the maintainer's host. Follow
  `InitFileDebug`'s shape: B = the worn sword's item value (0x3B/0x3C/
  0x3D), C-left/down/right = up to three owned items (values in
  `buttonItems[1..3]`, their slots in `cButtonSlots[0..2]`), D-pad
  empty (255).

## The generator (`n64/OcarinaOfTime/tools/save_generator.py`)

Design per the maintainer's spec: **dungeons first** (presets + custom
per-dungeon), then progressively finer questions whose **defaults derive
from the dungeon answers** (beat Forest ⇒ Fairy Bow + Minuet; any adult
temple ⇒ Master Sword/Hylian Shield/hookshot/magic; etc. — all
overridable in a review step), **full stocks assumed** for every owned
item type (ammo = capacity of the owned upgrade level, rupees = wallet
cap, health full). It writes the file locally with the game's exact
formatting and prints install + backup instructions; it never touches
`runDir/Save/` itself.

Choices baked in: baseline = a byte-honest fresh file
(`InitFileNormal`), including the odd-but-real defaults (`magic: 48`
with no magic, `sceneFlags[5].swch = 0x40000000`, `infTable[29] = 1`,
horse at Hyrule Field); `cutsceneIndex` 65521 (intro) for a truly fresh
file, 0 once any progression exists; `savedSceneNum` kept at 52 so the
chosen spawn survives `Sram_OpenSave`; era defaults to adult when any
adult temple is beaten.

## Verification (2026-09-01)

- `--selftest` mode: an all-defaults generated save matches the real
  pristine `file1.sav` **field-for-field across the entire base
  section** (name/deaths excluded). This caught one invented field
  (`eventInf`) during development — the writer emits no such key.
- A programmatic progressed-save test asserts the flag/reward pairing,
  the Spirit/Shadow randomizerInf placement, full stocks, spawn/era,
  worn-gear encoding, and cutscene suppression.
- First in-game attempt (2026-09-01) **crashed** — diagnosed to the
  empty-buttons-with-worn-sword inconsistency above (confirmed by
  inspecting the crashed file: `equips.equipment = 0x3332`,
  `buttonItems` all 255). Fixed; the button-consistency assertions are
  now part of the programmatic tests.
- **In-game load test PASSED** (William Emerison Six <billsix@gmail.com>,
  2026-09-01): the fixed generator's save loads and plays.
- **Known limitation → follow-up task:** only the mechanical progression
  is set; the story/world flags stay at minute zero (adult Link with
  medallions while the Great Deku Tree still "wants to talk"). The plan
  — diff maintainer-provided real saves per stage using the generator's
  own `deep_diff` — lives in
  `tasks/ocarina-save-generator-story-flags.md`.
