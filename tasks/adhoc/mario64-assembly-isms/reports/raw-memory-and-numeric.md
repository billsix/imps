# Assembly-isms survey — 10 classes (Ghostship SM64, `src/` minus `port/`)

Anchors are relative to `Ghostship/src` unless noted. Everything below is from source I opened.

## Shared prerequisites I verified first

These determine what "the named constant already exists" means, and several of them contradict what you'd expect from HackerSM64:

- **`DEGREES()` exists but is camera-local**: `game/camera.h:27` — `#define DEGREES(x) ((x) * 0x10000 / 360)`, with a doc comment saying "This should be used mainly to make camera code clearer at first glance." 63 uses tree-wide (`game/`+`engine/`+`menu/`), essentially all in `camera.c`.
- **There is no global `ABS`**. Three *incompatible* local definitions: `game/camera.h:20` `#define ABS(x) ((x) > 0.f ? (x) : -(x))` (note `> 0.f`, so `ABS(0)` yields `-0`), `goddard/gd_macros.h:13` `(((val) < 0 ? (-(val)) : (val)))`, and a third redefinition inside `goddard/particles.c:466`.
- **No `sqr`/`min`/`max` in `include/`** — they are in `engine/math_util.h:28-31`. `sins`/`coss` at `math_util.h:25-26` already do the 16-bit mask internally: `#define sins(x) gSineTable[(u16) (x) >> 4]`.
- **`include/macros.h` has no numeric helpers at all** beyond `ARRAY_COUNT` / `ROUND_UP_*`. Anything "named" has to come from `sm64.h`, `object_constants.h`, `object_fields.h`, or `camera.h`.
- **`BAD_RETURN(cmd)` is `void`** (`include/types.h:16`). This single macro accounts for **305 of the 516** `cast_s32` hits.

---

## 1. `raw_byte_pointer.txt` (181 hits, 34 files)

### What the hits are
True-positive rate for "rewritable assembly-ism": **~10%**. Breakdown:

- **36 hits (20%) are pure port noise**: `FrameInterpolation_RecordOpenChild("...", (uintptr_t)node)` in `game/rendering_graph_node.c` (25), `game/hud.c` (9), `game/mario_misc.c:96`, `game/skybox.c:267`. The API takes a `uintptr_t` key; the cast is required. Not upstream code either.
- **~45% are legitimate allocator/serial-stream byte arithmetic** — `game/memory.c` (23 hits), `audio/heap.c`, `engine/level_script.c`, `engine/geo_layout.c`, `goddard/gd_memory.c`. When you are writing a bump allocator or walking a byte-oriented command stream, `(u8 *)` arithmetic *is* the standard-C way; C has no other portable byte-offset operator.
- **~15% are `(uintptr_t)` used only to print a pointer** — `goddard/renderer.c` and `goddard/skin.c` (`gd_printf("%x\n", (u32)(uintptr_t) net->shapePtr)`). These are needed for varargs, and the `(u32)` narrowing is actually a latent 64-bit bug rather than an assembly-ism.
- **~10% are genuine rewritable idioms** (below).

### Exemplars

**`game/save_file.c:69` and `game/save_file.c:97`** — the same computation written two ways in adjacent functions:
```c
u32 offset = (u32)((u8 *) buffer - (u8 *) &gSaveBuffer) / 8;   // read_eeprom_data
u32 offset = (u32)((u8 *) buffer - (u8 *) &gSaveBuffer) >> 3;  // write_eeprom_data
```
Rewrite: make both `/ 8`. Behaviour-preserving: the subtraction is `ptrdiff_t`, cast to `u32` *before* the shift/divide, so the operand is unsigned — `>> 3` and `/ 8` are identical on unsigned. This is purely the IDO codegen difference leaking into source. Low value on its own; worth folding into a larger patch.

**`game/save_file.c:131` / `:146`**:
```c
struct SaveBlockSignature *sig = (struct SaveBlockSignature *) ((size - 4) + (u8 *) buffer);
```
Rewrite: `(struct SaveBlockSignature *) ((u8 *) buffer + size - 4)`. The `int + pointer` operand order is verbatim MIPS `addu` operand order. Behaviour-identical (pointer addition is commutative in C); it also reorders the arithmetic away from `int` overflow territory. Cosmetic, safe.

**`game/object_helpers.c:2236`**:
```c
s32 cur_obj_set_direction_table(s8 *a0) {
    o->oToxBoxMovementPattern = a0;
    ...
    return *(s8 *) o->oToxBoxMovementPattern;
}
```
The `(s8 *)` cast is redundant — `oToxBoxMovementPattern` is already reached through a typed pointer field. Rewrite: `return *o->oToxBoxMovementPattern;`. Safe *only if* the field's declared type in `object_fields.h` is `s8 *`; because these fields are `OBJECT_FIELD_*` union aliases, verify before submitting.

**`game/memory.c:144-145`**:
```c
struct MainPoolBlock *block       = (struct MainPoolBlock *) ((u8 *) addr - 16);
struct MainPoolBlock *oldListHead = (struct MainPoolBlock *) ((u8 *) addr - 16);
```
Two identically-initialised locals (a register-allocation artefact). The `16` is `sizeof(struct MainPoolBlock)` in disguise — same magic 16 appears at `:94`, `:95`, `:123`, `:131`, `:173`. Rewrite: named constant, or `sizeof(struct MainPoolBlock)` if it really is 16. **Do not** merge the two locals: `main_pool_free` mutates `oldListHead` in the walk loops and keeps `block` as the anchor. The cast arithmetic itself must stay.

**Leave alone**: `game/crash_screen.c:283` `(u16 *)((uintptr_t)framebuffer | 0xa0000000)` (KSEG1 uncached-segment construction — hardware semantics, and already inert on PC), and `game/game_init.c:677` `set_segment_base_addr(0, (void *) (uintptr_t) 0x80000000)`.

### Risk / upstream
**Mostly leave-alone; a thin mechanical slice.** Upstream plausibility is low-to-moderate — sm64 maintainers regard `(u8 *)` arithmetic in `memory.c` / `level_script.c` as correct code, not an artefact. The `/8` vs `>>3` and the `(size - 4) + (u8 *)buffer` operand-order fixes are the only ones I'd expect to be merged, and only bundled.

### Top 5 files
`goddard/renderer.c` (28), `game/rendering_graph_node.c` (25, all port noise), `game/memory.c` (23), `audio/load_sh.c` (19), `engine/level_script.c` (10).

---

## 2. `type_pun_deref.txt` (5 hits, 2 files) — all hits read

### What the hits are
100% true type-punning, 0% rewritable. All five are **load-defined-by-format**, not decompiler residue.

- `engine/geo_layout.h:21,24,27`:
```c
#define cur_geo_cmd_s16(offset) (*(s16 *) &gGeoLayoutCommand[CMD_PROCESS_OFFSET(offset)])
#define cur_geo_cmd_s32(offset) (*(s32 *) &gGeoLayoutCommand[CMD_PROCESS_OFFSET(offset)])
#define cur_geo_cmd_u32(offset) (*(u32 *) &gGeoLayoutCommand[CMD_PROCESS_OFFSET(offset)])
```
`gGeoLayoutCommand` is `u8 *` (declared `geo_layout.h:43`). These read a packed binary command stream at byte offsets. The only standard-C alternative is `memcpy` into a local — which **changes nothing observable** but does change alignment requirements from "must be aligned" to "any", and pessimises codegen on compilers that don't fold it. Note `CMD_PROCESS_OFFSET` already contains 64-bit pointer-widening logic (`geo_layout.h:14-15`), so these macros are actively maintained port code, not frozen decomp.
- `audio/seqplayer.c:2014,2022`: `seqChannel->unkC8 = *(u16 *) (seqPlayer->seqData + sp38);` — same thing for the sequence bytecode stream.

### Rewrite
`memcpy`-based:
```c
#define cur_geo_cmd_s16(offset) \
    ({ s16 _v; memcpy(&_v, &gGeoLayoutCommand[CMD_PROCESS_OFFSET(offset)], sizeof _v); _v; })
```
This is *not* equivalent as written: the existing macros are **lvalues** — grep before converting. And GNU statement-expressions are non-standard, which defeats the stated purpose.

### Risk / upstream
**Leave alone.** Zero readability gain, non-zero chance of breaking an lvalue use or an assignment target. Would not be accepted upstream.

### Top files
`engine/geo_layout.h` (3), `audio/seqplayer.c` (2).

---

## 3. `rawdata_union.txt` (34 hits, 6 files) — all hits read

### What the hits are
Per your scoping, the 10 `behavior_script.h:9-20` hits (`cur_obj_get_int` etc.) are the decomp's API — out of scope. Of the remaining 24:

- **Legitimate dynamic indexing (13 hits), must keep**: `game/object_helpers.c:416-417`, `:1888-1896`, `:1904-1910`, `game/spawn_object.c:249,254`. These index by a *runtime* parameter (`angleIndex`, `posIndex`, `localTranslateIndex`) or iterate the whole array to zero it. E.g. `obj_turn_toward_object` (`object_helpers.c:387-419`) dispatches on `angleIndex ∈ {O_MOVE_ANGLE_PITCH_INDEX, O_FACE_ANGLE_YAW_INDEX, ...}`; there is no named field to substitute. Not an assembly-ism — this is how the object system is designed.
- **Genuine rewritable direct indexing (7 hits)**, plus 4 `tuxie.inc.c` hits that are a different thing.
- **True-positive rate ≈ 20%.**

### Exemplars

**`game/behaviors/exclamation_box.inc.c:124-125`** — unambiguous:
```c
CALL_CANCELLABLE_EVENT(MacroObjectOverride, a0->model, o->rawData.asF32[0x37], o->rawData.asF32[0x38],
                       o->rawData.asF32[0x39]) {
```
`object_fields.h:112-114` defines exactly these: `oHomeX = OBJECT_FIELD_F32(0x37)`, `oHomeY = 0x38`, `oHomeZ = 0x39`. Rewrite to `o->oHomeX, o->oHomeY, o->oHomeZ`. **Textually identical after preprocessing** — zero behaviour risk. Caveat: `CALL_CANCELLABLE_EVENT` is a Ghostship port addition, so this is a Ghostship PR, not an upstream sm64 one.

**`game/mario_actions_cutscene.c:1845, 1857, 1881`** (`jumbo_star_cutscene_taking_off`):
```c
marioObj->rawData.asF32[0x22] = 0.0f;
...
marioObj->rawData.asF32[0x22] -= 32.0f;
...
vec3f_set(m->pos, 0.0f, 307.0, marioObj->rawData.asF32[0x22]);
```
Index `0x22` is the Mario-object scratch slot; `object_fields.h:158-166` already aliases it nine ways (`oMarioPolePos`, `oMarioTornadoPosY`, `oMarioWhirlpoolPosY`, …) but has **no jumbo-star name**. Correct patch: add `#define /*0x110*/ oMarioJumboStarCutscenePosZ OBJECT_FIELD_F32(0x22)` next to its siblings and use it. Behaviour-preserving by construction (pure macro alias). This is the single highest-value hit in the class and follows an established in-file pattern. Note from the surrounding code that the value is fed to `vec3f_set(..., z)` — it is a **Z** position despite the sibling names ending `PosY`; name it accordingly.

**`game/behaviors/tuxie.inc.c:86, 100`** — these are *not* direct indexing and should not be touched:
```c
o->prevObj->OBJECT_FIELD_S32(o->oInteractionSubtype) &= ~INT_SUBTYPE_DROP_IMMEDIATELY;
```
The index is `o->oInteractionSubtype`, i.e. a *value* used as an index. The comment at `tuxie.inc.c:81` already flags this as a known original-game bug ("rather than its offset to rawData"). **Leave alone** — rewriting it would either fix or break the bug.

**`game/object_helpers.c:416-417`** — while you're here, note the latent inconsistency:
```c
s16 targetAngle, startAngle;
...
startAngle = o->rawData.asU32[angleIndex];
o->rawData.asU32[angleIndex] = approach_s16_symmetric(startAngle, targetAngle, turnAmount);
```
`asU32` read into an `s16`, then an `s16` return stored back into a `u32` slot (sign-extending). The sibling accessors use `asS32`. Changing `asU32`→`asS32` here is behaviour-identical (same storage, same bit pattern, and the value is truncated to `s16` on the way in either way) and removes the inconsistency. Low risk but genuinely cosmetic.

### Risk / upstream
**Mechanical/safe** for the `exclamation_box` and `mario_actions_cutscene` cases (macro-alias substitution, provably textually equivalent). **Leave-alone** for the dynamic-index sites and `tuxie.inc.c`. Upstream plausibility: high for the `oMarioJumboStar*` field-name addition — it matches the file's existing convention exactly.

### Top files
`engine/behavior_script.h` (10, out of scope), `game/object_helpers.c` (13), `game/mario_actions_cutscene.c` (3), `game/behaviors/tuxie.inc.c` (4), `game/behaviors/exclamation_box.inc.c` (2), `game/spawn_object.c` (2).

---

## 4. `bit_masking_16.txt` (113 hits, 44 files) — all hits read

### What the hits are
True-positive rate **~25%**. Four distinct sub-patterns, only two of which are rewritable:

1. **Audio DSP fixed-point (28 hits, `audio/`)** — `mixer.c` (15), `synthesis*.c`, `playback.c`. `samples[j] * vols[j] >> 16`, `(state[33] << 16) | (uint16_t)state[34]`, `samplesLenFixedPoint & 0xFFFF`. This is Q16.16 fixed-point and RSP register packing. **Not an assembly-ism — it is the algorithm.** `mixer.c` is additionally hand-vectorised port code (`_mm_set1_epi32`, `vdupq_n_u32`). Leave entirely alone.
2. **Bitfield packing / sound-ID composition (~35 hits)** — `SOUND_MARIO_YAHOO_WAHA_YIPPEE + ((gAudioRandom % 5) << 16)` (`game/mario.c:248`), the seven `SOUND_MOVING_TERRAIN_SLIDE + (n << 16)` lines in `game/sound_init.c:38-44`, `(WARP_OP_WARP_OBJECT << 16) + 2` (`game/interaction.c:906`). The `<< 16` is a documented field position in the sound-ID encoding. Legitimate; at most worth a `SOUND_ARG_VARIANT(n)` macro, which is a new-API change, not a cleanup.
3. **Behaviour-parameter extraction (~20 hits)** — `(u16)(o->oBehParams >> 16) & PLATFORM_ON_TRACK_BP_MASK_PATH` (`game/behaviors/platform_on_track.inc.c:61`). Note this file *already* uses named masks from `object_constants.h`, while `sliding_platform_2.inc.c:15,18,22` and `activated_bf_plat.inc.c:31,48,56` next door still use bare `0x0380`, `0x003F`, `0x0040`, `0x0300`, `0x007F`. Naming those is a real, contained improvement — see class 6.
4. **Genuine rewritable 16-bit-wrap idioms (~10 hits)** — below.

### Exemplars

**`engine/behavior_script.c:90-92`** and the verbatim duplicate **`game/object_helpers.c:1878-1880`**:
```c
obj->header.gfx.angle[0] = obj->oFaceAnglePitch & 0xFFFF;
obj->header.gfx.angle[1] = obj->oFaceAngleYaw   & 0xFFFF;
obj->header.gfx.angle[2] = obj->oFaceAngleRoll  & 0xFFFF;
```
`header.gfx.angle` is `Vec3s` (`include/types.h:132`), i.e. `s16[3]`. `oFaceAnglePitch` is `OBJECT_FIELD_S32` (`object_fields.h:81`). Rewrite: **drop the `& 0xFFFF`**.

Why it is behaviour-preserving, precisely: with the mask, the `int` value `0..65535` is converted to `s16` — out-of-range conversion, *implementation-defined* (C99 6.3.1.3p3), and every relevant compiler wraps modulo 2¹⁶. Without the mask, the `s32` is converted to `s16` — same implementation-defined wrap, same result bit-for-bit. The mask is the MIPS `andi` that the compiler emitted before the `sh`; it is redundant at the C level. Removing it *narrows* the reliance on implementation-defined behaviour rather than widening it.

**`game/mario_actions_cutscene.c:1922`**:
```c
m->marioObj->header.gfx.angle[2] = ((m->faceAngle[1] - targetAngle) << 16 >> 16) * 20;
```
`m->faceAngle[1]` and `targetAngle` are both `s16`, so the subtraction is `int`. `<< 16 >> 16` is sign-extension of the low 16 bits. Rewrite: `(s16)(m->faceAngle[1] - targetAngle) * 20`.

This rewrite **removes undefined behaviour**: left-shifting a negative `int` is UB (C99 6.5.7p4), and `m->faceAngle[1] - targetAngle` is routinely negative here. `>> 16` on a negative `int` is implementation-defined (arithmetic on every real target). The `(s16)` cast is implementation-defined-but-universally-wrapping and gives identical results on all two's-complement targets. Strictly safer, identical output. **This is the best single hit in the class.**

**`game/object_helpers.c:805`** and **`game/spawn_object.c:324`**:
```c
objectList = (behavior[0] >> 16) & 0xFFFF;   // objectList is u32
objListIndex = (bhvScript[0] >> 16) & 0xFFFF;
```
Both read a `BehaviorScript` (`u32`) word. Since the guard immediately above is `if ((behavior[0] >> 24) == 0)`, bits 24-31 are known zero, so the `& 0xFFFF` is provably redundant. Removing it is behaviour-preserving **only under that guard** — I verified the guard at `object_helpers.c:804`. `spawn_object.c:324` lacks the equivalent guard in the same shape; check before touching. Marginal value.

**`game/hud.c:327`**:
```c
u16 timerFracSecs = ((timerValFrames - (timerMins * 1800) - (timerSecs * 30)) & 0xFFFF) / 3;
```
All three operands are `u16` (`hud.c:324-326`), so they promote to `int`; the subtraction result is in `[0, 29]` and cannot be negative. The `& 0xFFFF` is dead. But: **removing it changes nothing only because the value is provably non-negative** — if it could go negative, `& 0xFFFF` would turn `-1` into `65535` before the `/ 3` and the mask would be load-bearing. Verify the arithmetic before submitting. Same shape at `game/mario_actions_cutscene.c:431` (`(m->actionArg & 0xFFFF) == 0`) where `actionArg` is `u32` and the mask *is* load-bearing (it selects the low half of a packed warp argument, per `:432` `m->actionArg >> 16`). **Do not touch `:431`.**

**Leave alone**: `menu/intro_geo.c:380-382`, `((((u16)(r / size + 0.5) << 0xB) & 0xF800) & 0xffff)` — the doubled mask is redundant *and* the expression is doing an RGBA16 pack with a `double` rounding constant; untangling it touches three separate classes at once and the visual result is the N64 boot logo. High blast radius, zero benefit.

### Risk / upstream
**Mechanical/safe** for the six `& 0xFFFF`-before-`s16`-store lines (`behavior_script.c:90-92`, `object_helpers.c:1878-1880`) and the `<< 16 >> 16` at `mario_actions_cutscene.c:1922`. **Needs-care** for `hud.c:327` and `object_helpers.c:805`. **Leave-alone** for all of `audio/`.

Upstream plausibility: **good** for the `<< 16 >> 16` → `(s16)` fix (it is a UB removal, which sm64 upstream has historically accepted), **moderate** for the `& 0xFFFF` drops (a reviewer may argue the mask documents intent).

### Top 5 files
`audio/mixer.c` (15, all leave-alone), `game/sound_init.c` (7, legitimate), `engine/behavior_script.c` (7), `game/behaviors/platform_on_track.inc.c` (6), `audio/synthesis_sh.c` (6).

---

## 5. `angle_constants.txt` (675 hits, 147 files)

### What the hits are
The regex matched *every* occurrence of `0x1000/0x2000/0x4000/0x8000/0xC000/0x10000`, regardless of whether it is an angle. True-positive rate for "is actually an angle AND `DEGREES()` would read better": **~30%**.

Sub-patterns:
- **61 hits in `audio/` are not angles at all** — `0x8000` is a DSP gain of -100% (`audio/synthesis.c:1425` literally comments "0x8000 is -100%, so subtract sound instead of adding"), `0x4000` is a rounding constant in `(x * tbl + 0x4000) >> 15` (`audio/mixer.c:571,574,873,983`), `0x8000 / gAudioUpdatesPerFrame` is an ADSR fade rate (`audio/heap.c:1095`, `audio/playback.c:1230`), `-0x8000` is the s16 clamp bound (`audio/mixer.c:118`). **Zero of these are angles.**
- **Buffer sizes and memory**: `gThread5Stack[0x2000]` (`buffers/buffers.c:18`), `mem_pool_init(0x4000, ...)` (`game/main.c:133`), `0x1000` DMA chunk (`audio/load_sh.c:1191`). Not angles.
- **Real angle constants (~200 hits)** in `game/camera.c`, `game/mario_actions_*.c`, `game/behaviors/*.inc.c`, `game/interaction.c`.
- **Already-idiomatic**: `game/behavior_actions.c:174` `s16 separation = 0x10000 / n; // Evenly spread around a circle` — the comment makes `0x10000` = full turn explicit. `engine/surface_load.c:203,235` `// Move from range [-0x2000, 0x2000) to [0, 0x4000)` — those are **level coordinates**, not angles, and the file already uses `LEVEL_BOUNDARY_MAX` / `CELL_SIZE` correctly.

### Exemplars

**`game/behaviors/bowser.inc.c:1186, 1407, 1451`**:
```c
o->oMoveAngleYaw = o->oBowserAngleToCenter + 0x8000;      // :1186
s16 angle = o->oBowserAngleToCenter + 0x8000;             // :1407
UNUSED s16 angle = o->oBowserAngleToCenter + 0x8000;      // :1451
```
Rewrite: `+ DEGREES(180)`. `DEGREES(180)` = `180 * 0x10000 / 360` = `32768` = `0x8000` **exactly** — the constant-folding is exact for any multiple of 360/65536, and 180/90/45/270 all divide cleanly. Behaviour-identical. At `:1407` the sum is then stored in `s16`, so it wraps identically either way.

Requires `#include "game/camera.h"` in the behaviour translation unit. Check the `behavior` aggregation include before patching — `DEGREES` living in `camera.h` is a real friction point for this class and is the main reason upstream has kept it camera-only.

**`game/mario_actions_airborne.c:265`** — `m->faceAngle[1] += 0x8000;` → `+= DEGREES(180)`. Same at `game/mario_actions_moving.c:1038, 1816` (`m->marioObj->header.gfx.angle[1] += 0x8000`), `:129`, `:710-711` (`wallAngle + 0x8000`).

**`game/interaction.c:544`**:
```c
if (facingDYaw >= -0x4000 && facingDYaw <= 0x4000) {
```
→ `>= DEGREES(-90) && <= DEGREES(90)`. Note `DEGREES(-90)` = `-90 * 0x10000 / 360`. In C, `-90 * 65536 = -5898240`, and `-5898240 / 360` = `-16384` exactly (no truncation ambiguity because the division is exact). **Verified exact** — but this is the trap in this class: `DEGREES(-105)` at `camera.c:1065` is `-105*65536/360 = -19114.66…` → C99 truncates toward zero to `-19114`, while `DEGREES(105)` → `+19114`. Symmetric, but *not* what a reader assuming round-to-nearest expects, and for non-divisor angles `DEGREES(x)` and `-DEGREES(-x)` are equal only by accident of C99's toward-zero rule (C89 left it implementation-defined). For any angle that is **not** a multiple of 45°, spell out the hex and comment it rather than introducing `DEGREES()`.

**`game/behaviors/wiggler.inc.c:254`**:
```c
o->oWigglerTargetYaw = o->oMoveAngleYaw + 0x4000 * (s16) random_sign();
```
→ `+ DEGREES(90) * (s16) random_sign()`. Exact. Same shape at `game/behaviors/spiny.inc.c:90` (`* 0x2000` → `DEGREES(45)`).

**`game/object_helpers.c:1712`**:
```c
if (abs_angle_diff(o->oWallAngle, o->oMoveAngleYaw) > 0x4000) {
```
→ `> DEGREES(90)`. Reads much better and is exact.

**Leave alone**: everything in `audio/`; `game/behaviors/water_ring.inc.c:16` `(s32)(random_float() * 4096.0f) + 0x1000` (a scale phase, not an angle); `engine/behavior_script.c:72` `rnd / (double) 0x10000` (RNG normalisation).

### Risk / upstream
**Mechanical/safe for multiples of 45° only; needs-care otherwise.** The hard constraint is that `DEGREES()` truncates, so the rewrite is exact iff `x * 65536` is divisible by 360, i.e. iff `x` is a multiple of 45/8 = 5.625°. Every candidate I list above satisfies that. Anything else must be left as hex.

Upstream plausibility: **moderate**. The blocker is not correctness but that `DEGREES` is declared in `camera.h` with a comment scoping it to camera code; a patch spraying it across `behaviors/` will draw "move `DEGREES` to `macros.h` first" feedback. Propose that header move as patch #1, then the substitutions.

### Top 5 files
`game/camera.c` (103), `menu/file_select.c` (42, mostly the `-0x8000` yaw argument in `spawn_object_rel_with_rot` calls — genuinely `DEGREES(180)`), `game/mario_actions_moving.c` (39), `game/interaction.c` (15), `audio/mixer.c` (14, all false positives).

---

## 6. `hex_magic.txt` (5205 hits, 266 files) — sampled 40 across files

### What the hits are
**This log is dominated by noise; true-positive rate ≈ 8-10%.** Measured:

- **1191 hits (23%) are struct-offset comments**, not code: `/*0x0C,     */ u8 active;` (`audio/internal.h:137`), `/* 0x1F4 */ struct ObjGroup *weightGrp;` (`goddard/gd_types.h:219`), `/*0x14*/ void *displayList;` (`engine/graph_node.h:244`), `}; // size = 0xC0, known to be 0xC8 on SH` (`audio/internal.h:671`). These are the decomp's **documentation of ROM layout** and are load-bearing for anyone comparing against the original. **Never touch.** The four heaviest "files" in this class — `goddard/gd_types.h` (427), `audio/internal.h` (377), `engine/graph_node.h` (98) — are almost entirely this.
- **Static data tables**: `audio/data.c` (349 hits) is `{0x0000, 0x0fff, 0x1fff, ...}` waveform/envelope tables; `game/behaviors/donut_platform.inc.c:5` is a position table. Naming these is meaningless.
- **Already-named**: `game/save_file.h:145` `#define SAVE_FLAG_CAP_ON_KLEPTO /* 0x00020000 */ (1 << 17)`, `game/area.h:94` `#define WARP_TRANSITION_FADE_FROM_COLOR 0x00`, `game/camera.h:131` `#define CAM_MOVE_ALREADY_ZOOMED_OUT 0x1000`. The regex matched the *definition sites*. These are the desired end state, not the problem.
- **Genuinely nameable magic**: a thin but real seam.

### Exemplars (the real seam)

**`game/behaviors/activated_bf_plat.inc.c:31, 48, 56`**:
```c
s32 platformType = ((u16)(o->oBehParams >> 16) & 0x0300) >> 8;
o->oActivatedBackAndForthPlatformMaxOffset = 50.0f * ((u16)(o->oBehParams >> 16) & 0x007F);
o->oActivatedBackAndForthPlatformVertical = (u16)(o->oBehParams >> 16) & 0x0080;
```
and **`game/behaviors/sliding_platform_2.inc.c:15, 18, 22, 27`** (`0x0380`, `0x003F`, `0x0040`).

These are behaviour-parameter bitfields with **no** names, sitting directly beside `game/behaviors/platform_on_track.inc.c:47,61,62,145,192,203` which uses `PLATFORM_ON_TRACK_BP_DONT_DISAPPEAR`, `PLATFORM_ON_TRACK_BP_MASK_PATH`, `PLATFORM_ON_TRACK_BP_MASK_TYPE`, `PLATFORM_ON_TRACK_BP_RETURN_TO_START` — all defined in `include/object_constants.h` (I confirmed `PLATFORM_ON_TRACK_BP_DONT_TURN_YAW (1 << 10)` at `object_constants.h:851`). The correct patch adds `ACTIVATED_BF_PLAT_BP_MASK_TYPE (0x0300)` etc. to `object_constants.h` in the same style. **Purely additive, textually equivalent, follows an established convention in the same header.** This is the highest-value hex_magic work.

**`game/mario.c:1676`** — `bodyState->modelState |= (0x100 | m->fadeWarpOpacity);` — `0x100` is a `MODEL_STATE_*` flag; check `sm64.h` for an existing name before inventing one.

**`game/object_helpers.c:83`** — `0x100 | (currentGraphNode->fnNode.node.flags & 0xFF)` — this is the drawing-layer field; `engine/graph_node.h:105` documents it as `s16 flags; // hi = drawing layer, lo = rendering modes`. Compare `game/mario_misc.c:310` and `menu/intro_geo.c:60`, which write the *same* field as `(flags & 0xFF) | (LAYER_OPAQUE << 8)` — i.e. **a named constant for this already exists and is used three lines away in sibling files**. `0x100` == `LAYER_OPAQUE << 8` iff `LAYER_OPAQUE == 1`; verify, then substitute. Cheap, safe, and it makes three call sites agree.

**`game/level_update.c:778`** — `sSourceWarpNodeId = (m->usedObj->oBehParams & 0x00FF0000) >> 16;` — this is the standard "2nd byte of behaviour params" extraction, for which `oBehParams2ndByte` exists (`object_list_processor.c:491` computes it as `(spawnInfo->behaviorArg >> 16) & 0xFF`). Whether `usedObj->oBehParams2ndByte` is valid at this point needs checking — **not** a blind substitution.

**Leave alone**: `game/crash_screen.c:127` `*ptr & 0x7f` (ASCII mask, self-evident); `audio/playback.c:698` `gAudioErrorFlags = ((bankId << 8) + drumId) + 0x5000000` (error-code tagging, the constant *is* the name); `game/mario_actions_cutscene.c:2616` `(gCurrCreditsEntry->unk02 & 0x10 ? width : -width) * 56 / 100 + 640` (`unk02` is still unnamed — you cannot name a bit of a field you haven't identified).

### Risk / upstream
**Needs-care, high triage cost.** 90%+ of the log must be discarded before any patch exists. The `object_constants.h` behaviour-param additions are **mechanical/safe and highly plausible upstream** — they extend an existing, actively-populated header in its own idiom. Everything else in this class is a judgement call per site, and a large "name the magic numbers" PR will not be merged.

### Top 5 files (by raw hits — note these are mostly noise)
`goddard/gd_types.h` (427, ~all offset comments), `audio/internal.h` (377, ~all offset comments), `audio/data.c` (349, data tables), `audio/seqplayer.c` (289, opcode values), `game/camera.c` (261, mixed — the only one of the five worth reading).

---

## 7. `cast_s16.txt` (197 hits, 70 files) — sampled 22

### What the hits are
True-positive rate for "redundant, removable": **~15%**. The overwhelming majority **change semantics and must be kept.**

**Sub-pattern A — 16-bit angle wrap (keep, ~60%).** The object angle fields are `s32` (`object_fields.h:74,81`) but hold 16-bit angles; `(s16)` forces the wrap that makes comparisons work across the ±180° seam:
- `game/behaviors/eyerok.inc.c:402` — `if ((s16)(o->oFaceAngleYaw - o->oAngleToMario) < 0)`. Both operands are `s32`; without the cast the difference is a full 32-bit value and the sign test gives the **wrong answer** whenever the angles straddle the wrap. Load-bearing.
- `game/behaviors/manta_ray.inc.c:58` — `if ((s16) o->oMantaTargetYaw != (s16) o->oMoveAngleYaw)`. Both are `s32` fields; the casts make two values differing by a multiple of 65536 compare equal. Removing them changes behaviour.
- `game/behaviors/boo.inc.c:172` — `o->oBooMoveYawDuringHit = (s16)(o->oMoveAngleYaw + 0x8000);`
- `game/object_helpers.c:2073` — `s16 angle = o->oWallAngle - ((s16) o->oMoveAngleYaw - (s16) o->oWallAngle) + 0x8000;`
- `game/interaction.c:1726` — `s16 facingDYaw = (s16)(o->oMoveAngleYaw + 0x8000) - m->faceAngle[1];`
- `game/mario_actions_automatic.c:211` — `approach_s32((s16)(cameraAngle - m->faceAngle[1]), 0, 0x400, 0x400)`.

**Sub-pattern B — float→int truncation (keep, ~20%).** `(s16)` here converts `f32` to integer with truncation toward zero, which is the *point*:
- `game/behaviors/clam.inc.c:40` — `s16 val02 = (s16)(100.0f * coss(val06));`
- `game/mario_actions_moving.c:726` — `s16 val00 = (s16)(m->forwardVel * 170.0f);`
- `game/behaviors/snowman.inc.c:46` — `o->oFaceAnglePitch += (s16)(o->oForwardVel * (100.0f / f12));`. Here the cast is **doubly** load-bearing: `oFaceAnglePitch` is `s32`, so without it the `+=` would add in float and truncate the *sum*, not the addend — different result whenever the addend's fraction and the accumulator have opposite signs.
- `game/behaviors/ukiki.inc.c:70` — `(s16)(random_float() * 4.0f + 2.0f)`.
- `game/mario_actions_submerged.c:256` — `-(s16)(10.0f * m->controller->stickX)`. Note the negation is **outside** the cast: `-trunc(x)` ≠ `trunc(-x)` only for... actually they are equal for truncation toward zero, but the placement still matters if anyone "simplifies" it to `(s16)(-10.0f * stickX)` — that *is* equal, but only because trunc is odd-symmetric. Worth a comment, not a change.

**Sub-pattern C — genuinely redundant (remove, ~15%).**
- `engine/surface_collision.c:580` — `s16 y = (s16) yPos;` (`yPos` is `f32`). The cast is redundant with the initialiser's implicit conversion — **but leave it**: the three lines above (`:575-577`) are the famous Parallel-Universe comment (`//! (Parallel Universes) Because position is casted to an s16...`). The explicit cast documents the most-studied bug in the game. Removing it is technically behaviour-preserving and socially unacceptable. **Leave-alone.**
- `goddard/skin.c:320` — `x = (s16) vtx->pos.x;` — same shape, no such history; removable if `x` is `s16`.
- `game/ingame_menu.c:731` — `return (s16)(centerPos - (s16)(spacesWidth / 2.0));` — the *outer* `(s16)` is redundant (the function returns `s16`), the *inner* one is not. Also note `/ 2.0` is a **double** division of an integer — see class 9.

### Risk / upstream
**Leave-alone as a class.** The removable fraction is small, and each removal requires proving the operand type. A blanket "remove redundant s16 casts" patch would silently break the angle-wrap sites, which is the worst possible outcome for a no-behaviour-change PR. If you want one patch here, take only `goddard/skin.c:320`-shaped initialiser casts, and skip `surface_collision.c`.

### Top 5 files
`goddard/renderer.c` (18), `game/object_helpers.c` (12), `game/obj_behaviors_2.c` (10), `game/mario_actions_moving.c` (9), `engine/surface_collision.c` (9).

---

## 8. `cast_s32.txt` (516 hits, 87 files) — sampled 23

### What the hits are
**59% of this log is a single macro.** `grep -c BAD_RETURN` = **305**. `include/types.h:16` defines `#define BAD_RETURN(cmd) void`, and `game/camera.c` declares ~295 cutscene functions as `BAD_RETURN(s32) cutscene_foo(struct Camera *c)`. The macro exists precisely to document "the original declared this `s32` but never returns a value" while compiling as `void`. It is **not a cast**, it is already the fix. This alone explains `camera.c`'s 295 hits.

Of the remaining ~211:

**Keep — float→int truncation (~50%):**
- `game/behaviors/bowling_ball.inc.c:197` — `(s32)(random_float() * o->oBBallSpawnerSpawnOdds) == 0`
- `game/behaviors/corkbox.inc.c:16` — `o->oVelY = (s32)(random_float() * 4.0f) + 4;` — cast truncates **before** the `+ 4`; removing it would add in float then truncate. Different for no inputs here (random_float ≥ 0) but the pattern is fragile.
- `game/behaviors/breakable_box_small.inc.c:27` — `(s32)(random_float() * 80.0f) - 40`
- `game/mario_actions_moving.c:658`, `game/mario_actions_submerged.c:1264` — `(s32)(val04 / 2.0f * 0x10000)`, `(s32)(m->forwardVel / 4.0f * 0x10000)`: float→fixed-point animation accel. Load-bearing.
- `engine/math_util.c:708` — `gArctanTable[(s32)(y / x * 1024 + 0.5f)]` — this is round-half-up implemented as truncate-after-adding-0.5. The cast **is** the rounding. Keep.
- `game/behaviors/platform_on_track.inc.c:254` — `o->oFaceAngleRoll += (s32) o->oPlatformOnTrackSkiLiftRollVel;`. `oFaceAngleRoll` is `S32` (`object_fields.h`), `oPlatformOnTrackSkiLiftRollVel` is `F32` (`object_fields.h:787`). **The cast changes the result.** With it: `a = a + trunc(b)`. Without it: `a = trunc((f32)a + b)`. For `a = 5, b = -0.5`: with → `5 + 0 = 5`; without → `trunc(4.5) = 4`. Must keep. Good exemplar of a cast that *looks* removable and is not.

**Remove — genuinely redundant (~20%):**
- `game/object_helpers.c:968` — `u32 animFlags = (s32) o->header.gfx.animInfo.curAnim->flags;`. `flags` is `s16` (`include/types.h:90`), which already integer-promotes to `int`; the `(s32)` is a no-op, and the value then converts to `u32` identically either way. Rewrite: drop the cast. Fully behaviour-preserving (`s16 → int` promotion is value-preserving by definition, `int → u32` conversion is the same with or without the intermediate `(s32)` which *is* `int`).
- `audio/effects.c:230,232` — `vib->seqChannel->vibratoExtentTarget != (s32) vib->extent` / `vib->extent = (s32) vib->seqChannel->vibratoExtentTarget;`. Both fields are integer types of rank ≤ `int`; the casts are promotion no-ops.
- `goddard/renderer.c:2374` — `for (i = 0; ((s32) i) < sDebugViewsCount; i++)`. If `i` is unsigned this cast is load-bearing (it defeats the usual-arithmetic-conversion that would make the comparison unsigned); if `i` is `s32` it is a no-op. **Check before touching** — this is exactly the shape where removing a "redundant" cast flips a comparison's signedness.
- `goddard/objects.c:1561` — `currKeyFrame = (s32) animObj->frame;` — `frame` is `f32`; truncating cast, **keep**.

### Risk / upstream
**Needs-care.** The only clean, defensible patch is "drop `(s32)` where the operand already has rank ≤ `int` and no signedness flip occurs" — that is `object_helpers.c:968` and the `audio/effects.c` pair, i.e. a handful of lines. Upstream plausibility: low, because the payoff is tiny and reviewers will ask you to prove each one.

Separately: **`BAD_RETURN` is worth a note to your parent task** — it is the single largest "assembly-ism" in the tree by line count, it already has a clean macro, and the remaining question (should these just be `void`?) is a deliberate decomp-fidelity decision, not an oversight. **Leave alone.**

### Top 5 files
`game/camera.c` (295, of which ~295 are `BAD_RETURN`), `goddard/renderer.c` (16), `game/mario_actions_moving.c` (16), `audio/synthesis.c` (10), `audio/effects.c` (9).

---

## 9. `cast_f32.txt` (230 hits, 54 files) — sampled 21

### What the hits are
True-positive rate for "redundant, removable": **~35%** — the highest of the three cast classes, because `(f32)` on an integer in a float expression is usually already implied.

**Remove — redundant int→float promotion (~35%):**
- `game/hud.c:118` — `guTranslate(mtx, (f32) sPowerMeterHUD.x, (f32) sPowerMeterHUD.y, 0);`. `guTranslate` is prototyped with `f32` parameters, so the conversion happens anyway. Note the third argument is bare `0` — the file is already inconsistent with itself. Removing the two casts is behaviour-identical (same implicit conversion at the same point).
- `game/ingame_menu.c:1151` — `create_dl_translation_matrix(MENU_MTX_NOPUSH, 0, (f32) gDialogScrollOffsetY, 0);` — same shape, same file inconsistency (`0` vs `(f32)`).
- `game/mario.c:371` — `m->vel[0] = (f32) m->slideVelX;` — `vel` is `Vec3f`; assignment converts. Redundant.
- `goddard/objects.c:636` — `newView->upperLeft.x = (f32) ulx;` — 57 hits in this one file, nearly all this shape.
- `goddard/objects.c:1603,1647,1668,1683` — `nextTransform.rotate.x = (f32) animData3s16[nextKeyFrame][0] * scale;`. **Careful**: here the cast is *not* redundant in effect but *is* redundant in outcome — `s16 * f32` already promotes the `s16` to `f32` before multiplying. Same result. Removable, but the cast documents that the table is `s16`, which is genuinely useful. Marginal.

**Keep — the cast changes the computation (~40%):**
- `game/behavior_actions.c:225` — `if ((sp1C = o->header.gfx.animInfo.animAccel / (f32) 0x10000) == 0)`. Without `(f32)`, `animAccel` (integer) `/ 0x10000` (integer) would be **integer division** — completely different. Absolutely load-bearing.
- `engine/geo_layout.c:241` — `f32 scale = (f32) cur_geo_cmd_s16(0x02) / 100.0f;` — here `/ 100.0f` already forces float, so `(f32)` is redundant. Contrast with the line above: same file family, opposite answer. **This class cannot be mechanised.**
- `game/behaviors/koopa.inc.c:606` — `sins((s16)(f32) o->oPathedTargetPitch)`. Double cast: `oPathedTargetPitch` is an `S32` field read as... the `(f32)` then `(s16)` round-trips through float, which **truncates toward zero** and loses precision above 2²⁴. Removing `(f32)` changes behaviour for large values. Obfuscated but load-bearing. **Leave alone** (and flag as a possible latent bug).
- `game/behaviors/cannon.inc.c:46-47` — `o->oPosX += (f32)((o->oTimer / 2 & 1) - 0.5) * 2;`. The inner expression is already `double` (because of `0.5`), so `(f32)` is a **double→float narrowing** that happens before the `* 2`. Removing it would keep the whole thing in `double` until the `+=`. Different rounding. **Keep** — and note `0.5` here is a double literal (class 9 overlap).
- `game/shadow.c:127` — `return ((f32) atan2s(a, b) / 65535.0 * 360.0);`. `atan2s` returns `s16`; `(f32)` then `/ 65535.0` (**double**) promotes everything back to `double` anyway, so the `(f32)` is a redundant round-trip that *does* cost a rounding step. Removing it would change the result in the last bits. **Keep, or fix the whole line** — see class 9.
- `audio/external.c:1336`, `audio/seqplayer.c:885`, `audio/copt/…:447` — all inside `US_FLOAT()` / tempo arithmetic where the cast forces float division. Keep.
- `audio/heap.c:857` — `tmp[8] = (f32) (arg0 * 262159.0f);` — redundant (`arg0 * f32` is already `f32`).

### Risk / upstream
**Needs-care, but with a genuinely mechanical sub-slice.** The safe slice is: *casts on an argument to a function whose prototype already declares the parameter `f32`* (`hud.c:118`, `ingame_menu.c:1151`, and the `goddard/objects.c` assignment shape). These are provably no-ops. Everything else requires reading the full expression for an integer-division or double-narrowing trap.

Upstream plausibility: **low-moderate**. `goddard/` is regarded as low-value churn territory; `hud.c` / `ingame_menu.c` would probably pass.

### Top 5 files
`goddard/objects.c` (57), `audio/external.c` (17), `game/ingame_menu.c` (13), `audio/seqplayer.c` (11), `goddard/renderer.c` (9).

---

## 10. `double_literals.txt` (1494 hits, 130 files) — sampled 26

### The decomp's own convention — this is the key finding

The decomp has **two explicit, documented conventions** for this exact situation, and they say "preserve, annotate" rather than "fix":

1. **`//? 0.5f` trailing annotations** — 59 occurrences across `goddard/`. Examples I read: `goddard/joints.c:81-83` `self->velocity.x *= 0.8; //? 0.8f`, `goddard/joints.c:408-410` `b->worldPos.x = (spAC->worldPos.x + spA8->worldPos.x) / 2.0; //? 2.0f;`, `goddard/dynlist_proc.c:2150-2152` `dst->x *= 0.5; //? 0.5f`, `goddard/gd_memory.c:269` `(f32) block->size / 1024.0, //? 1024.0f`, `goddard/skin_movement.c:92` `if (curWeight->weightVal > 0.0) { //? 0.0f`. The `//?` means **"the ROM says double here; a float would have been the obvious choice; we are keeping the double because it matched."**
2. **Prose comments.** `game/geo_misc.c:69`, inside `round_float`:
```c
s16 round_float(f32 num) {
    // Note that double literals are used here, rather than float literals.
    if (num >= 0.0) {
        return num + 0.5;
```
3. **`US_FLOAT()` for version-conditional literals** — `audio/internal.h:59-61`: `#define US_FLOAT(x) x` vs `x ## f`, i.e. the US build uses doubles and EU/SH uses floats *for the same source line*. 66 hits in the log are inside `US_FLOAT()`. **These cannot be changed at all** — the macro exists because the two ROM versions genuinely differ.

**So: the decomp's convention is explicitly "do not add the `f`."** Any patch that does so is arguing against three separate in-tree mechanisms.

### Does adding `f` change results? — Yes, and here is exactly when

- **Storing a constant into an `f32`**: no change. `f32 x = 0.5;` and `f32 x = 0.5f;` are identical (0.5 is exactly representable, and even for inexact constants the double→float conversion at assignment gives the correctly-rounded float).
- **`f32 * double-literal`**: **changes results.** `velocity.x *= 0.8` promotes `velocity.x` to `double`, multiplies in double, rounds once back to float on store. `velocity.x *= 0.8f` rounds `0.8` to float first (introducing error ~2.4e-8 relative), then multiplies in float. **Two different roundings, two different answers.** This is `goddard/joints.c:81-83` exactly.
- **`f32 / double-literal`**: same, e.g. `goddard/joints.c:408` `/ 2.0`. Here 2.0 *is* exactly representable in float, so `x / 2.0` (widen, divide exactly, narrow) and `x / 2.0f` (divide exactly in float) give bit-identical results — **division by an exact power of two is the one safe case.**
- **Mixed chains**: `game/shadow.c:127` `((f32) atan2s(a, b) / 65535.0 * 360.0)` — 65535.0 and 360.0 are both exactly representable, but the *intermediate* `x/65535.0` is not; it is computed in double then multiplied in double, and narrowed once at return. The all-float version narrows twice. **Different result.**
- **Integer-context doubles**: `game/ingame_menu.c:731` `(s16)(spacesWidth / 2.0)` — `spacesWidth` is integer, `/ 2.0` makes it a *double division* then truncates. Writing `/ 2` would be integer division: **same for non-negative `spacesWidth`, different for negative.** Writing `/ 2.0f` is the same as `/ 2.0` here because 2.0 is exact and the magnitudes are small. Three spellings, two behaviours.

### Noise ratio
**~65% is pure noise.** 971 of 1494 hits are in `goddard/`, and 709 of those are `goddard/dynlists/dynlist_mario_master.c` — static initialiser tables like `SetSkinWeight(387, 10.0)` and `SetRotation(90.0, 180.0, 0.0)`, which expand (via `goddard/dynlists/dynlist_macros.h:64-65`) into `struct DynList { ...; struct GdVec3f vec; }` initialisers. `GdVec3f` is three `f32`s; these are **compile-time conversions of exactly-representable values**. Zero runtime effect, zero precision question. Adding `f` to 709 lines of art data is pure churn.

Also noise: the 66 `US_FLOAT()` hits, and comment-only matches such as `audio/data.c:153` (`// gNoteFrequencies[k] = 0.5 * 2^((k-39)/12)`) and `game/behaviors/cloud.inc.c:78`.

### Exemplars

| Site | Code | Verdict |
|---|---|---|
| `goddard/joints.c:81` | `self->velocity.x *= 0.8; //? 0.8f` | **Changes results** (0.8 not representable). Already annotated. Leave. |
| `goddard/joints.c:408` | `b->worldPos.x = (…x + …x) / 2.0; //? 2.0f;` | Safe to change (exact power of two) — but the `//?` says the author deliberately didn't. Leave. |
| `game/geo_misc.c:70-73` | `return num + 0.5;` / `return num - 0.5;` | Safe (0.5 exact, `f32 + 0.5` widens then narrows once — for `f32 num`, `num + 0.5` in double then narrowed to `s16` via truncation is **not** identical to `num + 0.5f` when `num` has a large magnitude, because the double add is exact and the float add rounds). **Needs-care**, and it is explicitly commented. Leave. |
| `game/shadow.c:371` | `halfScale = (xCoordUnit * s.shadowScale) / 2.0;` | `xCoordUnit` is `s8` (one of -1/0/1 per the comment at `:368`), `shadowScale` is `f32`. `/ 2.0` = exact halving. Safe to write `/ 2.0f`, and this one is **not** annotated. The best candidate in the class — and still low value. |
| `menu/file_select.c:463` | `button->oMenuButtonScale += 0.0022;` | **Changes results** — 0.0022 is not representable; double-add then narrow ≠ float-add. Leave. |
| `game/behaviors/moving_coin.inc.c:128` | `if (o->oForwardVel > 75.0)` | Comparison only, and 75.0 is exact → `> 75.0f` is identical. Safe but pointless. |
| `goddard/renderer.c:35` | `#define LOOKAT_PACK(c) ((s32) MIN(((c) * (128.0)), 127.0) & 0xff)` | 128.0 and 127.0 exact, but `c * 128.0` in double vs float differ in rounding when `c` is inexact. **Needs-care.** |

### Risk / upstream
**Leave-alone / needs-care. This is the class I'd recommend skipping entirely.**

Three independent reasons: (a) the decomp has an explicit, three-mechanism convention saying don't; (b) ~65% of hits are static data where the change is meaningless; (c) for the remaining runtime hits, adding `f` **does** change float results in the general case, so it is not a no-behaviour-change patch by definition.

Upstream plausibility: **near zero.** A PR adding `f` to these literals would be closed as "these are deliberate; see the `//?` annotations."

If the parent task wants *something* here, the defensible framing is the inverse: **extend the `//?` annotation** to the un-annotated non-goddard sites (`shadow.c:371`, `file_select.c:463`, `moving_coin.inc.c:128`), which documents the hazard without touching codegen. That is a comment-only patch and genuinely useful to a PC port.

### Top 5 files
`goddard/dynlists/dynlist_mario_master.c` (709, all static data), `goddard/dynlists/dynlist_macros.h` (42, macro definitions), `goddard/joints.c` (37, all `//?`-annotated), `audio/external.c` (36, mostly `US_FLOAT`), `goddard/draw_objects.c` (25).

---

## 11. `div_by_const_float.txt` (338 hits, 84 files) — sampled 24

### The precision question, stated precisely

**`x / C` and `x * (1/C)` are bit-identical if and only if `1/C` is exactly representable in the working format** — i.e. iff `C` is a power of two (within range, and ignoring the overflow/underflow edge cases below).

- **`C = 2.0f, 4.0f, 8.0f, 16.0f, 32.0f, 65536.0f`** → `1/C` is exact. Both operations compute the same exact real value and round it identically under any rounding mode. **Bit-identical. Rewriting is exact.** Two edge cases: if `x` is at the top of the range, `x * (1/C)` cannot overflow where `x / C` doesn't (division by ≥1 only shrinks) — fine; if `x / C` underflows into subnormals, both forms round the same exact real value, so still identical. Genuinely safe.
- **`C = 100.0f, 3.0f, 6.0f, 5.0f, 10.0f, 12.0f, 20.0f, 30.0f, 127.0f, 255.0f, 625.0f, 1000.0f, 5000.0f`** → `1/C` is **not** exactly representable. `x * (1/C)` performs two roundings (one to form the reciprocal, one for the product) versus one for the division, and the results differ for a substantial fraction of inputs — the classic worst case is `100.0f`, where `x * 0.01f` differs from `x / 100.0f` for roughly 1 in 3 mantissas. **Rewriting is NOT exact. Do not do it.**

Denominator histogram from the log: `/2.0f` 36, `/2.0` 33, `/4.0f` 21, **`/100.0f` 21**, `/8.0f` 20, `/32.0f` 14, `/6.0f` 12, `/3.0f` 12, `/20.0f` 9, `/10.0f` 9, `/255.0f` 8, `/16.0` 8, `/12.0f` 8, `/1.0f` 8, `/5.0f` 7, `/30.0f` 7, `/127.0f` 7, `/65536.0f` 5, `/1000.0f` 5.

So roughly **~95 of 338 (28%)** are power-of-two denominators where the rewrite is provably exact; the rest are not.

### But: is the rewrite even wanted?

On a PC this is a **de-optimisation to no purpose**. Modern compilers with default (non-`-ffast-math`) settings will not turn `x / 100.0f` into a multiply — correctly, because it isn't equivalent — and *will* happily strength-reduce `x / 2.0f` themselves since that one *is* equivalent. So the power-of-two cases, which are the only safe ones, are also the only ones the compiler already handles. **Net benefit: zero.**

### Noise
`engine/math_util.c` contributes 15 hits, **14 of which are compile-time constant folds**: `spline_get_weights` at `math_util.c:805-828` uses `(1 / 6.0f)`, `(7 / 12.0f)`, `(11 / 12.0f)`, `(4 / 6.0f)` — parenthesised constant expressions folded at compile time to a single float. Zero runtime division. Pure noise. Same for `audio/mixer.c:669` `_mm_setr_ps(1.0f / 8.0f, 2.0f / 8.0f, …)`.

Another ~40 hits are `/* sizeRange: */ 2.0f` style — the regex matching **struct-initialiser comments in particle-spawn tables** (`game/behaviors/ground_particles.inc.c:39`, `mr_blizzard.inc.c:30`, `water_bomb.inc.c:81`, `water_splashes_and_waves.inc.c:43`). Not divisions at all.

**True-positive rate for "a runtime division by a float constant that could be a multiply": ~40%. Of those, ~28% are safe to rewrite. Net: ~11% actionable, all of it pointless.**

### Exemplars

**Safe (power of two), and pointless:**
- `game/mario.c:1302` — `m->intendedMag = mag / 8.0f;` → `* 0.125f`. Exact.
- `game/mario_step.c:636` — `intendedPos[0] = m->pos[0] + m->vel[0] / 4.0f;` → `* 0.25f`. Exact.
- `game/rendering_graph_node.c:246` — `f32 top = (gCurGraphNodeRoot->y - gCurGraphNodeRoot->height) / 2.0f * node->scale;` → `* 0.5f`. Exact.
- `game/mario_actions_moving.c:535` — `val14 = (s32)(val04 / 4.0f * 0x10000);` → `* 0.25f`. Exact. (Note `0x10000` is an `int` promoted to `f32` — fine.)

**Unsafe (not a power of two) — must keep the division:**
- `engine/behavior_script.c:796` — `gCurrentObject->oFriction = BHV_CMD_GET_1ST_S16(3) / 100.0f;` — `1/100.0f` inexact. **Do not rewrite.**
- `game/behaviors/snufit.inc.c:59` — `scaleNode->scale = obj->oSnufitBodyScale / 1000.0f;` — inexact.
- `game/behaviors/boo.inc.c:236` — `boo_move_during_hit(TRUE, sBooHitRotations[o->oTimer] / 5000.0f * a0);` — inexact.
- `audio/effects.c:563` — `(s8)(((625.0f + posY) / 625.0f) * 31.0f) + 0xE0` — inexact, and the result feeds an `s8` truncation where a 1-ulp difference can flip the integer.
- `game/behaviors/fish.inc.c:179` — `distance = (s32)(1.0 / (o->oDistanceToMario / 600.0));` — inexact **and** double-typed (class 9 overlap) **and** truncated to `s32`. Triple hazard. Leave.

**Mixed-type trap:** `game/skybox.c:174` — `f32 pitchInDegrees = (f32) sSkyBoxInfo[player].pitch * 360.0 / 65535.0;` — `360.0` and `65535.0` are **doubles**, so the whole chain evaluates in double and narrows once at the assignment. Rewriting the `/ 65535.0` as a multiply would need `1.0/65535.0` in double (still inexact). Leave.

### Risk / upstream
**Leave-alone.** The safe subset is exactly the subset the compiler already optimises; the unsafe subset is 72% of the class. Upstream plausibility: **essentially zero** — this would be read as a micro-optimisation PR that introduces float-precision risk for no measurable gain, on a codebase whose entire value proposition is bit-exactness.

**The precise statement to give the parent task**: *division and multiplication by a reciprocal are bit-identical only when the reciprocal is exactly representable, i.e. when the divisor is a power of two. For every other divisor in this codebase — and 72% of the hits have one — the rewrite silently changes results. This class should not be patched.*

### Top 5 files
`game/mario_actions_moving.c` (21), `engine/math_util.c` (15, 14 of them compile-time folds), `game/mario.c` (13), `goddard/renderer.c` (12), `goddard/joints.c` (12, overlapping the `//?` annotations).

---

## 12. `shift_as_mul.txt` (363 hits, 69 files)

### What the hits are
True-positive rate for "signed shift used as arithmetic that should be `*` or `/`": **~8%**. Dominated by legitimate bit manipulation:

- **150 hits (41%) in `audio/`** — RSP command word construction (`0x02020000 | ((channelIndex & 0xff) << 8)`, `external.c:1367,1547,1742`), fixed-point scaling (`mixer.c:1157-1164` `clamp16((*samples * g) >> 4)`), bitmask walking (`external.c:1801` `bit = bit >> 1`, `seqplayer.c:240,271` `channelBits >> 1`), nibble extraction (`seqplayer.c:2003` `(cmd >> 4) & 0xf`). All operate on unsigned or known-non-negative values and are packing/unpacking, not arithmetic. Leave.
- **63 hits (17%) are `#define` lines** — `game/save_file.h:137` `#define SAVE_FLAG_MOAT_DRAINED /* 0x00000200 */ (1 << 9)`, `game/moving_texture.h:49` `#define MOVTEX_AREA_TTC (0x14 << 8)`, `game/camera.h:39-43` (the `ZOOMOUT_AREA_MASK` bit assembly), `game/paintings.h:11` `#define PAINTING_ID(id, grp) id | (grp << 8)`. These are **flag definitions** — `1 << n` is the idiomatic spelling and `object_constants.h` uses it throughout. Not assembly-isms; the desired end state.
- **Graphics fixed-point**: `game/hud.c:69,87` and `game/ingame_menu.c:263-264,470` — `gSPTextureRectangle(…, x << 2, y << 2, …, 1 << 10, 1 << 10)`. The `<< 2` is the RDP's required 10.2 fixed-point coordinate format and `1 << 10` is the 5.10 texture-scale unity value. **Hardware ABI, not arithmetic.** Leave.
- **Drawing-layer packing**: `engine/graph_node.c:298`, `game/mario_misc.c:310`, `game/moving_texture.c:852`, `menu/intro_geo.c:60` — `(flags & 0xFF) | (LAYER_OPAQUE << 8)`. Field packing. Leave (but see class 6 — `game/object_helpers.c:83` writes the same field as bare `0x100` and should be made to match these).
- **RGBA16 packing**: `game/area.c:92,100` — `((red >> 3) << 11) | ((green >> 3) << 6) | ((blue >> 3) << 1) | 1`. Colour-format conversion on `u8` inputs. Leave.

### The genuine signed-shift hits

**`game/behaviors/rotating_platform.inc.c:35,41` — the best exemplar in the class:**
```c
s8 sp1F = o->oBehParams >> 24;
...
o->oAngleVelYaw = sp1F << 4;
```
`sp1F` is `s8` and is **routinely negative** (it is a signed rotation speed byte). It integer-promotes to `int`, then `<< 4`. **Left-shifting a negative `int` is undefined behaviour** in C99/C11 (6.5.7p4) — not implementation-defined, *undefined*. GCC and Clang define it in practice, but UBSan flags it and an optimiser is entitled to assume it cannot happen.

Rewrite: `o->oAngleVelYaw = sp1F * 16;`

Behaviour-preserving and strictly safer: `sp1F ∈ [-128, 127]`, so `sp1F * 16 ∈ [-2048, 2032]` — no `int` overflow, fully defined, and on every two's-complement target it produces the identical bit pattern the shift produced. This is a **UB removal that is provably a no-op on all real targets** — exactly the kind of patch upstream accepts.

**`audio/effects.c:182` (EU/SH path):**
```c
s16 get_vibrato_pitch_change(struct VibratoState *vib) {
    ...
    return vib->curve[index] >> 8;
}
```
`vib->curve` is `s16 *` (`audio/internal.h:131`; the US build at `:136` uses `s8 *`). For a negative curve sample, `>> 8` is an **arithmetic** shift — it rounds toward **negative infinity**, whereas `/ 256` rounds toward **zero**. `-1 >> 8 == -1` but `-1 / 256 == 0`. **These differ for every negative value not an exact multiple of 256.** Rewriting this as `/ 256` would be an audible behaviour change in the vibrato LFO. **Must keep the shift.** This is the canonical "arithmetic-shift-of-negative" trap and the reason this class is not mechanical.

**`audio/synthesis.c:1583`** — `dryGain = dryGain >> 2;` where `dryGain` was just assigned `(s16)(dryGain * depthFactor)` at `:1582`, so it **can be negative**. Same trap: `>> 2` floors, `/ 4` truncates toward zero. Keep. (This is port-added surround code, not original ROM code — see the comment at `:1577`.)

**`game/behaviors/pokey.inc.c:133`** — `o->oPokeyBodyPartDeathDelayAfterHeadKilled = (o->oBehParams2ndByte << 2) + 20;`. `oBehParams2ndByte` is a byte extracted as `(behaviorArg >> 16) & 0xFF` (`game/object_list_processor.c:491`), so it is non-negative and `<< 2` is well-defined. Rewrite to `* 4` is exact and slightly clearer. Low value, zero risk.

**Non-negative divides where `/` is exact and clearer:**
- `game/mario_misc.c:533` — `gBodyStates[asGenerated->parameter >> 1]` — `parameter` is a small non-negative geo-node parameter (the sibling line `:537` tests `parameter & 1`). `>> 1` here is deliberately paired with the `& 1`, i.e. it is *bit extraction*, not division. **Leave** — rewriting to `/ 2` would obscure the pairing.
- `audio/playback.c:56,58` — `smallPanIndex = pan >> 1` / `pan >> 3`, where `pan` is non-negative (`:51` comment: "EU pan is 0-127"). Exact as `/ 2`, `/ 8`. Cosmetic.
- `game/save_file.c:97` — `>> 3` on a value already cast to `u32`. See class 1; make it match `:69`'s `/ 8`.

### Risk / upstream
**Needs-care, with one standout mechanical patch.**

- **Mechanical/safe, high upstream value**: `game/behaviors/rotating_platform.inc.c:41` (`sp1F << 4` → `sp1F * 16`). A one-line UB fix with a provable no-op guarantee. Grep for the same shape elsewhere — `s8`/`s16` local shifted left — before submitting; it is likely not unique.
- **Leave-alone**: everything in `audio/`, every `#define`, every `gSP*` coordinate, every colour/layer pack.
- **Never rewrite**: `audio/effects.c:182`, `audio/synthesis.c:1583`, and any `>>` on a possibly-negative value. State the rule explicitly in the parent task: *arithmetic right shift of a negative value rounds toward −∞; integer division rounds toward zero; they differ for every negative operand that is not an exact multiple of the divisor. `>>` → `/` on signed values is never a safe mechanical rewrite.*

### Top 5 files
`audio/external.c` (48, all leave-alone), `audio/mixer.c` (31, all leave-alone), `game/ingame_menu.c` (22, RDP fixed-point), `game/moving_texture.h` (18, all `#define`), `audio/synthesis.c` (16).

---

# Assembly-shaped constructs the regexes missed

Found while reading; none of these appear in your log set.

1. **`BAD_RETURN(cmd)` → `void`** (`include/types.h:16`, ~295 uses in `game/camera.c`). The largest single decomp artefact in the tree. Already has a macro; the open question (keep the fiction or just write `void`?) is a fidelity decision. Worth its own class so it stops polluting `cast_s32`.

2. **Statement-order-preserved-for-matching, with a confession comment.** `game/object_helpers.c:380-381`:
```c
z1 = obj1->oPosZ; z2 = obj2->oPosZ; // ordering of instructions..
x1 = obj1->oPosX; x2 = obj2->oPosX;
```
The comment literally says the interleaving exists to match codegen. Grep for `// ordering`, `// instruction`, `// regalloc`.

3. **Compiler-behaviour comments that pin source layout.** `game/spawn_object.c:253`:
```c
// -O2 needs everything until = on the same line
for (i = 0; i < 0x50; i++) obj->rawData.asS32[i] = 0;
```
guarded by `#if IS_64_BIT` / `#else` against a normal multi-line loop at `:248-251`. A reformatter would break the non-64-bit build. Grep for `-O2`, `needs`, `don't reorder`.

4. **Deliberate out-of-bounds array read as a documented technique.** `engine/math_util.h:14-26`: `#define gCosineTable (gSineTable + 0x400)` with a 10-line comment explaining that `coss()` reads past the end of `gSineTable` into `gCosineTable`, that this is UB, that GCC breaks on it, and that non-IDO builds use a standard-compliant version. This is the single most interesting assembly-ism in the tree and no regex would find it.

5. **Three mutually-incompatible `ABS` macros.** `game/camera.h:20` (`> 0.f`, so `ABS(0)` → `-0`), `goddard/gd_macros.h:13` (`< 0`), and a *third* redefinition inside `goddard/particles.c:466`. Plus `ABS2` at `camera.h:21` differing from `ABS` only in `>` vs `>=`. A real, findable cleanup that none of your classes covers.

6. **Duplicated function bodies.** `engine/behavior_script.c:85-93` (`obj_update_gfx_pos_and_angle`) and `game/object_helpers.c:1873-1881` (`obj_set_gfx_pos_at_obj_pos`) are character-for-character identical apart from `oFaceAngle*` vs `oMoveAngle*`. Likewise `game/save_file.c:131-133` / `:146-148`, and `game/memory.c:144-145`'s twin locals.

7. **Float compared against integer literal after an integer cast** — `game/obj_behaviors.c:458` `if ((s32) o->oVelY == 0)`, `game/behaviors/bully.inc.c:101` `if (o->oForwardVel < 10.0 && (s32) o->oVelY == 0)`, `game/behaviors/cap.inc.c:264` `if ((s32) o->oForwardVel != 0)`. The `(s32)` makes `|v| < 1.0` compare equal to zero — i.e. it is a **tolerance test spelled as a cast**. Load-bearing, easy to "clean up" wrongly, and invisible to all your cast regexes because the interesting part is the comparison, not the cast.

8. **Byte-copy loops where `memcpy` is meant** — `goddard/renderer.c:1185` (`dest[i] = src[i]` over `(u8 *) p1cont` / `(u8 *) &sGdContPads[0]`, set up at `:1181-1182`), `:2405` (`((u8 *) prevInputs)[i] = ((u8 *) currInputs)[i]`), `:2704` (`((u8 *) p1cont)[i] = 0`), `goddard/objects.c:311-314` (zeroing a freshly-allocated object byte by byte). These are `memcpy`/`memset` open-coded because the original didn't call them. Safe, readable, mechanical — and a better upstream candidate than most of the classes above.
