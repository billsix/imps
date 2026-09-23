# Assembly-isms survey — naming / `register` / `UNUSED` / filler classes

Repo: `n64/SuperMario64/Ghostship`. All anchors below are relative to `Ghostship/src/` unless prefixed `include/`. Everything asserted was read. (Reader report, 2026-09-22, verbatim.)

## 0. Build facts that drive every risk rating

- `CMakeLists.txt:203` defines **`VERSION_US=1`** only, and `CMakeLists.txt:255-256` globs `src/audio/*.c` wholesale. So several of the heaviest-hit files are compiled but **entirely `#ifdef`'d out**: `audio/load_sh.c:1` (`#ifdef VERSION_SH`), `audio/port_sh.c:1` (same), `audio/port_eu.c:7` (`#ifdef VERSION_EU`), and the EU/SH body of `seq_channel_layer_process_script` in `audio/seqplayer.c` (the US/JP build instead takes `audio/seqplayer.c:961 #include "copt/seq_channel_layer_process_script_copt.inc.c"`).
- This is a CMake/libultraship PC port with no ASM-matching target. Nothing in these classes is layout- or codegen-constrained **except** where data crosses a ROM/EEPROM/endianness boundary (section 8).
- `audio/copt/seq_channel_layer_process_script_copt.inc.c` is prefaced at `audio/seqplayer.c:960` with *"US/JP version with macros to simulate inlining by copt. **Edit if you dare.**"* — treat that file as leave-alone regardless of class.

## 1. `stack_named_locals` — 494 hits

**True-positive ratio: 494/494 (100%). Zero regex noise.** All are bare `sp<hex>` identifiers (`sp1C` ×94, `sp24` ×49, `sp20`/`sp18` ×36 …). 412 of 494 lines are declarations; 97 files; dirs: game 285, goddard 173, audio 31, menu 4, engine 1.

Almost none are scratch/register-like. The overwhelming majority are ordinary, well-scoped locals (and a fair number are **parameters**, e.g. `game/object_helpers.c:472` `spawn_obj_with_transform_flags(struct Object *sp20, s32 model, const BehaviorScript *sp28)`; `game/behaviors/chuckya.inc.c:83` `approach_forward_vel(f32 *forwardVel, f32 spC, f32 sp10)`). <5% are true single-use scratch; ≈95% are real variables with a stack-offset name.

Recoverability: ~90% of a 16-function sample is unambiguous. Upstream already half-did it in-file, giving a name oracle:

1. `game/object_collision.c:63-69` — `detect_object_hurtbox_overlap`: `f32 sp34 = a->oPosX - b->oPosX; f32 sp2C = a->oPosZ - b->oPosZ; f32 sp28 = a->hurtboxRadius + b->hurtboxRadius; f32 sp24 = sqrtf(sp34 * sp34 + sp2C * sp2C);` — its twin at `:26-32` (`detect_object_hitbox_overlap`) is already renamed with identical arithmetic: `dx`, `dz`, `collisionRadius`, `distance`. Also `sp3C`/`sp38` → `aBottomY`/`bBottomY`, `sp20`/`sp1C` → `aTopY`/`bTopY` (`:76-77`).
2. `game/object_helpers.c:961-963` — `cur_obj_extend_animation_if_at_end`: `s32 sp4 = …animFrame; s32 sp0 = …curAnim->loopEnd - 2;` → `animFrame`, `nearLoopEnd` (`cur_obj_check_if_near_animation_end` ~15 lines below already names them so).
3. `game/behaviors/chuckya.inc.c:83-100` — `approach_forward_vel(f32 *forwardVel, f32 spC, f32 sp10)` / `s32 sp4 = 0;` → `target`, `increment`, `reachedTarget`.
4. `game/object_helpers.c:199-203` — `obj_update_pos_from_parent_transformation(Mat4 a0, struct Object *a1)`: `spC/sp8/sp4` = `oParentRelativePosX/Y/Z` → `relX/relY/relZ` (params → `parentTransform`, `obj`).
5. `game/behaviors/bubba.inc.c:16` — `f32 sp24 = cur_obj_lateral_dist_to_home();` → `distToHome`.
6. `game/object_helpers.c:167-182` — `geo_switch_area`: `s16 sp26` / `struct Surface *sp20` → `roomCase` / `floor`.

Boundary (≈10%): `game/object_helpers.c:1585` `obj_spawn_loot_coins(…, f32 sp30, …)` — needs the second hop (`game/behaviors/coin.inc.c:70`) to justify `extraVelY`; same for `obj_spawn_loot_blue_coins(..., f32 sp28, ...)` at `:1612`.

Goddard convention to follow: `goddard/joints.c:228` `struct ObjJoint *j; // sp24`, `goddard/skin.c:315` `struct GdObj *obj; // sp4` — renamed variable, original slot kept in a trailing comment. Unrenamed goddard blocks: `goddard/joints.c:332-338`, `:134-176` (`sp5C` → `rotMtx`, `sp44` → `screenPos`, `sp50` → `cursorDelta`).

Rating: mechanical/safe in `game/`, `engine/`; needs-care in `goddard/`; leave-alone in `audio/copt/*.inc.c`. Upstream plausibility high for `game/`. Hot files: `goddard/joints.c` (49), `goddard/objects.c` (41), `game/object_helpers.c` (31), `goddard/shape_helper.c` (23), `goddard/particles.c` (22) / `game/object_collision.c` (22).

Gap: the regex misses **register-named parameters** `a0/a1/a2/f12/f14`: `game/object_helpers.c:198` `(Mat4 a0, struct Object *a1)`, `:230` `create_transformation_from_matrices(Mat4 a0, Mat4 a1, Mat4 a2)`, `:943` `cur_obj_set_vel_from_mario_vel(f32 f12, f32 f14)`, `:1015` `cur_obj_check_frame_prior_current_frame(s16 *a0)`, `game/behaviors/bub.inc.c:47` `bub_move_vertically(s32 a0)` (→ `speed`).

## 2. `temp_phi_var_locals` — 61 hits

100% true positive, only 6 distinct identifiers: `temp_s0` ×38, `temp_a0_5` ×25, `temp_f2` ×15, `temp_f12` ×12, `phi_s3` ×7, `temp_s2` ×6. No `var_*`.

| identifier | site | compiled in US build? |
|---|---|---|
| `temp_s0` | `audio/load_sh.c:1418+` | No (`#ifdef VERSION_SH`) |
| `temp_f2`/`temp_f12` | `audio/seqplayer.c:481-882` | No (EU/SH branch) |
| `temp_f2`/`temp_f12` | `audio/copt/…copt.inc.c:135-136, 425-440` | Yes — "edit if you dare" |
| `temp_s2`/`phi_s3` | `audio/heap.c:1498-1556` | Yes |

1. `audio/heap.c:1498-1556` — `func_sh_802f1ec4`: `phi_s3 = pool->pool.cur` (allocation start; `pool->pool.start` when wrapped), `temp_s2 = pool->pool.cur` afterwards (end); both loops evict entries overlapping [start, end) → `allocStart`, `allocEnd`.
2. `audio/seqplayer.c:851-852` (and `copt.inc.c:425-426`): `temp_f2 = gNoteFrequencies[cmd] * tuning; temp_f12 = gNoteFrequencies[layer->portamentoTargetNote] * tuning;` → `noteFreqScale`, `portamentoTargetFreqScale`.
3. `audio/load_sh.c:1418` `struct AudioBankSample *temp_s0;` → `sample`.

Rating: mechanical/safe, low value (3 of 4 sites uncompiled). Recommended: `audio/heap.c:1498-1556` only. Upstream medium. Hot files: `audio/load_sh.c` (25), `audio/seqplayer.c` (19), `audio/heap.c` (9), copt (8).

## 3. `arg_params` — 347 hits

~154 declarations/definitions, 45 in `.h`, rest uses. Dirs: audio 237, game 52, goddard 50, engine 8. Noise: `audio/internal.h:829-837` are **struct fields** (`op/arg1/arg2/arg3`, endianness-ordered). The audio 237 are dominated by uncompiled SH/EU files and `func_sh_*` of unknown semantics.

Recoverability 9/12 in `game/`:
1. `game/mario_actions_stationary.c:816` (+ `.h:31`) `landing_step(struct MarioState *m, s32 arg1, u32 action)` → `animation` (second arg of `set_mario_animation`).
2. `game/mario_actions_moving.c:1594` `common_ground_knockback_action(m, s32 animation, s32 arg2, s32 arg3, s32 arg4)`: `arg2` → `accelEndFrame` (`if (animFrame < arg2) apply_landing_accel`), `arg3` → `playHeavyLandingSound` (TRUE/FALSE), `arg4` → `actionArg` (every caller passes `m->actionArg`).
3. `game/mario_actions_submerged.c:870` `common_water_knockback_step(..., s32 arg3)` → `actionArg`.
4. `game/behaviors/king_bobomb.inc.c:46` `mario_is_far_below_object(f32 arg0)` → `minDistBelow`.
5. `game/behaviors/eyerok.inc.c:17` `eyerok_check_mario_relative_z(s32 arg0)` → `maxRelZ`.
6. `game/obj_behaviors_2.c:341-360` one-liners → `animIndex` / (`animIndex`, `animFrame`); `:364` `cur_obj_play_sound_at_anim_range(s8 arg0, s8 arg1, u32 sound)` → `frame1`, `frame2`.

Not clearly explainable (3/12): `game/obj_behaviors_2.c:246` `cur_obj_spin_all_dimensions(f32 arg0, f32 arg1)`, `game/behaviors/unagi.inc.c:45` `unagi_act_1_4(s32 arg0)`, every `func_sh_*` in `audio/`.

Rating: mechanical/safe for `game/`; watch **header duplicates** (`game/mario_actions_stationary.h:31`, `game/obj_behaviors.h:67/90/103`, `game/level_update.h:124-126`, `audio/heap.h:112-131`, `audio/load.h:77-104`). Do not REMOVE `UNUSED` args on table-dispatched functions: `game/level_update.c:1255` `lvl_init_from_save_file(UNUSED s16 arg0, s32 levelNum)` — signature fixed by `engine/level_script.c:230-232` (`typedef s32 (*Func)(s16, s32)`); renaming is fine. Hot files: `audio/heap.c` (64), `audio/load_sh.c` (56), `audio/port_sh.c` (37), `goddard/renderer.c` (35), `audio/port_eu.c` (26); best actionable: `game/obj_behaviors_2.c` (16).

## 4 & 5. `unnamed_funcs` (407) / `unnamed_data` (416) — characterisation only

- 115 of 407 `func_` lines are comments, 106 of them `orig name:` breadcrumbs above already-renamed functions (`goddard/renderer.c:2288`, `goddard/skin.c:300`). Distinct `func_*` symbols: 191 → **85** without those. Clustering: goddard 302, audio 98, game 7. goddard's remaining `func_*` bodies **are** the disassembly-shaped ones (co-occur with `sp<hex>`, `UNUSED u8 fillerN[]`, `register … // a1`); audio's are readable C with unnamed symbols, and many are calls into EU/SH-only functions.
- `D_*`: 105 distinct symbols / 416 lines; goddard 254, game 123, audio 31, engine 8. goddard/audio statics (`goddard/skin_movement.c:14` `static Mat4f D_801B9EA8; // TODO: rename to sHead2Mtx?`) vs `game/behaviors/*` per-behavior lookup tables trivially nameable from one use (`tox_box.inc.c:5`, `skeeter.inc.c:20`, `fire_piranha_plant.inc.c:36`). Hot: `goddard/renderer.c` (88), `goddard/shape_helper.c` (37), `goddard/joints.c` (34), `audio/external.c` (30), `goddard/objects.c` (28).

## 6. `register` — 106 hits

104/106 true (2 comments: `engine/geo_layout.c:100,102`). Modern GCC/Clang ignore it for allocation; its only C semantics is forbidding `&x`; **no `register` variable has its address taken** (enumerated + grepped; the tree builds). Removal is purely cosmetic. `engine/math_util.c:175` "These loops must be one line to match on -O2" is a matching-era comment — leave it. Sites: `engine/math_util.c:159-161, 172-173, 508-510, 571-573`; `engine/surface_collision.c:22-30` (13 in one block); `engine/surface_load.c:86, 304-306, 665-667`; `goddard/gd_memory.c:153-155`; `game/object_helpers.c:2406`. In goddard it is fused with the register-map comments (`goddard/skin.c:306-315`, `renderer.c:2971-2978`, `:3624-3629`).

Rating: mechanical/safe; upstream medium (weakest argument: cosmetic). Propose `engine/math_util.c` (28) first. Hot: `engine/math_util.c` (28), `goddard/skin.c` (16), `engine/surface_collision.c` (13), `goddard/renderer.c` (12), `goddard/skin_movement.c` / `draw_objects.c` / `engine/surface_load.c` (7 each).

## 7. `UNUSED` — 1128 hits

`include/macros.h:28` `#define UNUSED __attribute__((unused))`. ~439 lines are unused **parameters**; ~1033 are `UNUSED <type> <name>;` declarations of which **375 are `filler`/`pad`**; the rest unused file-scope data.

Rule: **keep** an `UNUSED` parameter iff the function's address is taken (dispatch table, callback, typedef'd pointer called from ROM data); **keep** an `UNUSED` local iff its initializer has side effects; everything else removable.

Keep (verified): `game/camera.c:1585` `update_fixed_camera(…, UNUSED Vec3f pos)` (`CameraTransition sModeTransitions[]`, `:465-466`); `game/camera.c:1847`; `game/object_helpers.c:166` `geo_switch_area(…, UNUSED void *context)` (`GraphNodeFunc`, `engine/graph_node.h:73`); `game/level_update.c:1255/1294/1333` (`engine/level_script.c:230-232`). **Side-effecting `UNUSED` locals (20 tree-wide; deleting changes behaviour):** `game/behaviors/end_birds_1.inc.c:5` / `end_birds_2.inc.c:5` `UNUSED f32 sp30 = random_float();` (advances the RNG), `bowling_ball.inc.c:231` `UNUSED s16 collisionFlags = object_step();`, `snowman.inc.c:81` `object_step_without_floor_orient()`, `red_coin.inc.c:29` `find_floor(...)` — rewrite to bare statements (`object_step();`, `(void) random_float();`), never delete.

Removable (verified): `game/camera.c:927-928` `cenDistX/Z`; `game/object_collision.c:29,66` `UNUSED f32 sp30 = sp3C - sp38;`; `game/camera.c:1008-1009, 1412, 1417`; `game/camera.c:1185` `update_yaw_and_dist_from_c_up(UNUSED struct Camera *c)` (after a table check); `goddard/shape_helper.c:34-46`; `audio/external.c:446`.

Rating: needs-care (statement-by-statement; no scripted sweep). Upstream low–medium; best-value subset: the ~20 side-effect cases → bare statements (a readability bug fix). Hot: `game/camera.c` (239), `goddard/renderer.c` (85), `goddard/shape_helper.c` (46), `game/interaction.c` (39), `goddard/draw_objects.c` (32).

## 8. `filler` / `pad` / `unused` struct members — 455 hits

**Only 70 of 455 hits are in `.h` files**; the rest are **function-local stack-padding declarations** (`game/camera.c:672/754/1229/1405/1416/1876`, `goddard/joints.c:50/333/681`, `goddard/shape_helper.c:910/1062`, `engine/surface_load.c:595`, `audio/synthesis.c:513/515/587/1293`, most `game/behaviors/*.inc.c`) — unconditionally removable in a PC port. ~85% trivially removable; ~15% struct members. `include/types.h` was not scanned — check separately.

Rule: **keep** a filler member iff the struct's byte layout is externally fixed: (a) overlays ROM data, (b) save file / EEPROM, (c) memcpy'd/DMA'd/checksummed, (d) union arm or index-accessed, (e) endianness placement. Remove otherwise.

Keep (verified): `game/save_file.h:104` `u8 filler[EEPROM_SIZE / 2 - …]` (EEPROM-sized, signed; port appends `ShipSaveData` after the signature); `include/types.h:168-186` `struct Object` `rawData` union (index-addressed by `object_fields.h`); `audio/internal.h:846-857` `pad0[3]`/`pad1[3]` (little-endian byte placement) and `:825-838` field order; `audio/heap.h:63` `u32 pad2[4]` in `struct SoundMultiPool` (offset-mapped pool carving); `goddard/gd_types.h` fillers (38; absolute-offset comments, raw `u8*` whole-struct copies at `goddard/renderer.c:2296-2299`).

Removable (verified): `engine/surface_collision.h:30-36` `struct FloorGeometry { u8 filler[16]; …}` (only producer `surface_collision.c:384-399` writes normals + originOffset; consumers read normals only); `engine/surface_collision.h:20-27` `struct WallCollisionData` `u8 filler[2]` (runtime in/out param); `engine/graph_node.h:219, :345` trailing `u8 filler[2]` (allocated by `sizeof` only, `graph_node.c:251`); `include/types.h:273` `struct MarioBodyState` tail `u8 filler[4]`; all function-local fillers; `game/camera.h:545-608` (runtime-only; low value, high review friction).

Rating: mechanical/safe for function-local fillers; needs-care for `.h` members; leave-alone for `save_file.h`, `audio/internal.h`/`heap.h`, `goddard/gd_types.h`, `types.h` rawData. Upstream medium-high for the function-local sweep, low for header members. Hot: `game/camera.c` (88), `goddard/gd_types.h` (38), `goddard/renderer.c` (28), `goddard/objects.c` (25), `goddard/joints.c` (21).

## 9. Recommended patch order (smallest → most contentious)

1. `game/object_collision.c:63-77` — finish the rename its twin already got.
2. `audio/heap.c:1498-1556` — `phi_s3`/`temp_s2` → `allocStart`/`allocEnd`.
3. `game/obj_behaviors_2.c:341-372` + `game/mario_actions_stationary.c:816`/`.h:31` — `argN` → `animIndex`/`animation`.
4. The ~20 side-effecting `UNUSED` locals → bare statements.
5. `engine/math_util.c` `register` removal (28 lines) as a taste-test.
6. Function-local `UNUSED u8 filler[N];` sweep in `game/behaviors/*.inc.c`.
7. Everything in `goddard/` and `audio/` SH-EU — last or not at all.

## 10. Things the parent task should not do

- Do not script any of these (the side-effecting `UNUSED` and the endianness pads look identical to safe neighbours under a regex).
- Do not rename parameters in a `.c` without the matching `.h`.
- Do not touch `audio/copt/seq_channel_layer_process_script_copt.inc.c` or any `#ifdef VERSION_SH` / `VERSION_EU` region — uncompiled under `VERSION_US=1`, therefore unverifiable.
