# Reference: The SM64 decomp core — "where does X live"

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference. What the reverse-engineered N64 game code is and where each kind of
gameplay logic lives. Read this before touching `src/game/` or `src/engine/`. Companion:
[architecture-overview.md](architecture-overview.md) for how the port wraps it.*

Ghostship's `src/game`, `src/engine`, `src/audio`, `src/menu`, `src/buffers`, `src/goddard`
are the standard **n64decomp/sm64** source, near-1:1 with the N64 ROM. ~720 `.c` files.
The port layer (`src/port/`, [port-layer.md](port-layer.md)) drives it; the OS-thread
scheduler is dead.

## The per-frame update chain (every gameplay call runs through here)

The frame is **driven by the level-script bytecode VM**, not a plain `update()`:

```
main() loop                       src/port/Game.cpp:39      (port layer)
 └ thread5_iteration()            src/game/game_init.c:678  (PORT-ADDED per-frame entry)
    ├ audio_game_loop_tick / select_gfx_pool / read_controller_inputs   game_init.c:703-705
    ├ addr = level_script_execute(addr)   src/engine/level_script.c      ← top of update chain
    │   └ (a LEVEL_CMD calls C) lvl_init_or_update   src/game/level_update.c:1238
    │      └ update_level()                          level_update.c:1134
    │         └ play_mode_normal()                   level_update.c:969
    │            └ area_update_objects()             src/game/area.c:291
    │               └ update_objects(0)              object_list_processor.c:627
    │                  └ per-list cur_obj_update()   object_list_processor.c:293-370
    │                     └ Mario: execute_mario_action(gCurrentObject)  object_list_processor.c:271
    └ display_and_vsync()                            game_init.c:716
```

`addr` is a **persistent static cursor** into the active level's script (`game_init.c:659,713`).
If you can't find where gameplay gets called, follow `level_script_execute`.

- `thread1_idle` / `thread3_main` / `thread5_game_loop` (`src/game/main.c`, `game_init.c:650`)
  look like the entry point but are **vestigial** — the scheduler is ignored. The live
  per-frame func is `thread5_iteration` (`game_init.c:678`), a port addition absent from
  vanilla decomp. `src/game/main.c` is excluded from the build (see build-system doc).

## Three bytecode VMs — easily confused

A `.c`/`.inc.c` file full of ALL-CAPS macros is almost always one of these. Check which:

| VM | Interpreter | Per-what | Command macros | Data |
|----|-------------|----------|----------------|------|
| **Level scripts** | `src/engine/level_script.c` | per level; drives the whole frame | `include/level_commands.h` | `levels/*/script.c` |
| **Geo layouts** | `src/engine/geo_layout.c` | builds the GraphNode render tree at load | `include/geo_commands.h` | actor/level geo (now in `sm64.o2r`) |
| **Behavior scripts** | `src/engine/behavior_script.c` | per-object AI, each frame | `include/macros`/behavior cmds | `data/behavior_data.c` |

## `src/game/` — gameplay

### Objects & behavior (Mario is an Object)
- **Object pool:** `struct Object gObjectPool[1024]` (`object_list_processor.c:69`,
  `OBJECT_POOL_CAPACITY` in `.h:26`). Pre-allocated; spawn claims a slot.
- **Object struct:** `include/types.h:154`. **No named fields** — a generic word array
  accessed through `oXxx` macros in `include/object_fields.h`; the same memory word means
  different things per behavior. *You cannot read behavior code without that header open.*
- **Object lists** by category (`gObjectLists`, `object_list_processor.c:81`): spawner +
  surface processed first (`:564`), then Mario, then the rest in fixed priority.
- **Behavior bytecode** lives in `data/behavior_data.c` (the single giant `bhvXxx` table);
  interpreter `behavior_script.c` (`bhv_cmd_*`). Higher-level AI in `behavior_actions.c`,
  `obj_behaviors*.c`, and per-object files in `src/game/behaviors/`. Spawn: `spawn_object.c`.

### Mario's action-state machine
- **State** `struct MarioState` / `gMarioState` (`include/types.h:270`). `m->action` is a
  32-bit value: `ACT_ID_MASK 0x1FF` (id 0–511) + `ACT_GROUP_MASK 0x1C0` (7 groups) + high
  behavior flags (`ACT_FLAG_AIR 0x800`, `ACT_FLAG_ATTACKING 0x800000`,
  `ACT_FLAG_SHORT_HITBOX 0x8000`, …). Constants in `include/sm64.h:151-188`
  (e.g. `ACT_IDLE 0x0C400201`).
- **Dispatch:** `execute_mario_action` (`mario.c:1756`) switches on `action & ACT_GROUP_MASK`
  to one group executor (`mario.c:1776-1801`). One file per group, one `case ACT_XXX:` per
  action:
  - stationary → `mario_actions_stationary.c` · moving → `mario_actions_moving.c`
  - airborne → `mario_actions_airborne.c` · submerged → `mario_actions_submerged.c`
  - cutscene → `mario_actions_cutscene.c` · automatic → `mario_actions_automatic.c`
    (ledge-grab, pole, hang) · object → `mario_actions_object.c` (punch/kick/grab)
- **Movement primitives:** `mario_step.c` — `perform_air_step`/`perform_ground_step`
  quarter-step physics, wall/floor/ceiling resolution.
- **Per-frame Mario order:** `update_mario_geometry_inputs` (`mario.c:1340`, calls
  `find_floor`, writes `m->floor`) → action executor → qstep (`mario_step.c`). Overriding
  `m->floor` needs doing in **both** the geometry-inputs and qstep phases (see the fork's
  pseudo-floor notes in the root `CLAUDE.md`).
- **Interaction:** `interaction.c` — Mario-vs-object (bounce, grab, damage, collect);
  Mario-vs-enemy uses `hitboxRadius` sums at `interaction.c:618`.
- **Camera:** `camera.c` (~6000 lines) — all Mario-following modes funnel through
  `focus_on_mario` (`camera.c:709`); cutscene cameras are separate.
- **`level_geo.c`** — geo-layout render callbacks (`geo_envfx_main`, `geo_skybox_main`), not
  gameplay.

## `src/engine/` — collision, math, render graph, level VM

### Surface collision (`surface_collision.c/.h`, `surface_load.c`)
- World hard-bounded to `[-8192,+8192]` X/Z: `LEVEL_BOUNDARY_MAX 0x2000`
  (`surface_collision.h:9`). Surface verts are `s16` — a hard cap on world size.
- **16×16 spatial partition:** `CELL_SIZE 0x400` → `NUM_CELLS 16`/axis. Two grids:
  `gStaticSurfacePartition[16][16]` (geometry) + `gDynamicSurfacePartition[16][16]` (moving
  platforms), `surface_load.c:24-25`. Cells split into floors/walls/ceilings.
- coord→cell: `index = (coord + 0x2000) / 0x400` (`surface_load.c:204-210`); OOB early-outs.
- Queries: `find_floor`, `find_ceil`, `find_wall_collisions` (`surface_collision.h:33`).
  Limits `CELL_HEIGHT_LIMIT 20000`, `FLOOR_LOWER_LIMIT -11000` (`.h:13-14`).

### Math — `math_util.c/.h`: `mtxf_*` (float 4×4), `vec3f_*`/`vec3s_*`, `atan2s`; sine/cosine
via `include/trig_tables.inc.c`.

### Geo layout / GraphNode render system
- **GraphNode** = a scene-graph tree. Types at `graph_node.h:26-53`: `ROOT`,
  `PERSPECTIVE`, `MASTER_LIST` (display-list buckets), `CAMERA`, `OBJECT`, `ANIMATED_PART`,
  `BILLBOARD`, `DISPLAY_LIST`, `SCALE`, `ROTATION`/`TRANSLATION`, `SHADOW`, `SWITCH_CASE`,
  `LEVEL_OF_DETAIL`, `BACKGROUND`, `HELD_OBJ`. `FUNCTIONAL` types (`0x100` bit) carry a
  `GraphNodeFunc` callback (`graph_node.h:73`).
- **Geo-layout VM** `geo_layout.c` builds the tree at load (`GeoLayoutJumpTable[]` :13).
- **Rendering:** `src/game/rendering_graph_node.c` — `geo_process_root` walks the tree each
  frame, emitting F3D display lists into master-list buckets. Nodes managed by
  `graph_node_manager.c`.

### Level-script VM — `level_script.c`
`level_cmd_*` funcs. Control flow: `load_and_execute`/`exit_and_execute` (:92,:103),
`jump`/`jump_and_link`/`return` (:146-159), `loop_begin`/`loop_until` (:179-185),
`jump_if`/`skip_if` (:194-211), `sleep` (:124). Other commands load segments, alloc the
level pool, set terrain, spawn objects (`OBJECT(...)`), place warps, mark painting/water
boxes, and call `lvl_init_or_update`. Macros: `include/level_commands.h`.

## `levels/`, `actors/`, `data/` — hollowed out vs. upstream

**Grepping in-tree for a model's vertices or a level's geometry finds nothing** — this port
strips the geo/model/anim `.inc.c` data to `sm64.o2r` and keeps only *code*.

- **`levels/`** — one subdir per course; in this port each holds **only `script.c`** (the
  `LevelScript` array). Geometry comes via `#include "assets/levels/bob.h"` from the o2r
  bundle (`levels/bob/script.c:17`). A script is `OBJECT(model,x,y,z,angle,behParam,beh)`
  macros + area/warp/terrain commands. Shared infra at `levels/` root: `scripts.c`,
  `entry.c`, `level_defines.h`, `course_defines.h`. Level enum: `include/level_table.h`.
- **`actors/`** — **not per-actor dirs**; 20 aggregator headers (`common0/1.h`,
  `group0.h`–`group17.h`), each `#include`ing extracted asset headers
  (`actors/common1.h:6-24`). The groups mirror SM64's segmented-actor loading (a level loads
  only the groups it needs). Model IDs `include/model_ids.h`, anim IDs
  `include/mario_animation_ids.h`.
- **`data/`** — one file, `behavior_data.c`: every object's behavior bytecode.

## Subsystem one-liners
- **`src/audio/`** — N64 sequenced-audio engine. `seqplayer.c` (sequence bytecode),
  `playback/synthesis/mixer.c` (render), `effects.c`, `load.c`/`heap.c` (banks/heap),
  `external.c` (game API: `play_music`, `play_sound`). **Region variants coexist**
  (`load_sh.c`, `port_eu.c`, `synthesis_sh.c`) — use the file matching the build's version,
  don't assume `load.c` is live. Pumped by `audio_game_loop_tick()` (`game_init.c:703`).
- **`src/menu/`** — front-end screens: `title_screen.c` (boot / level-select dispatch),
  `file_select.c`, `star_select.c`, `intro_geo.c`.
- **`src/buffers/`** — raw memory regions: `framebuffers.c`, `zbuffer.c`,
  `gfx_output_buffer.c`, `buffers.c` (segment/decompression staging + audio heap backing).
- **`src/goddard/`** — the interactive Mario-head intro (Nintendo's GD dynamic-object
  engine). Self-contained mini-3D engine with *its own* display-list interpreter
  (`dynlist_proc.c`), renderer, and face skinning (`skin*.c`). Entry `gd_main.c` (`gd_init`
  :35). Independent of the GraphNode renderer. Getting goddard working was an early port
  milestone (see git: *"no audio, but at least goddard is working now"*).

## `include/` — key shared headers
- **`types.h`** — core structs: `Object` (:154), `MarioState` (:270), `Surface` (:232),
  `GraphNode`/`GraphNodeObject` (:121), `Area`; `Vec3f`/`Mat4` typedefs.
- **`sm64.h`** — `ACT_*` constants, group masks, flags (:151-188).
- **`object_fields.h`** — the `oXxx` macros over the generic object array (essential).
- Also: `object_constants.h`, `behavior_data.h` (`bhvXxx` externs), `model_ids.h`,
  `level_table.h`, `seq_ids.h`/`sounds.h`, `surface_terrains.h` (`SURFACE_*`), `dialog_ids.h`.
- VM command macros: `level_commands.h`, `geo_commands.h`, `command_macros_base.h`.
- `segment_symbols.h`/`segments.h` — N64 segmented-memory symbols (segments now index into
  loaded assets). `variables.h` — aggregated global-state externs.
