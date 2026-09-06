# Reference: Objects & behaviors — the behavior VM and the shared helper library

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`data/behavior_data.c`, `src/engine/behavior_script.c`,
> `src/game/behaviors/*.inc.c`, `src/game/object_helpers.c`). Part of the mario64
> set — map at [`README.md`](README.md). Companion:
> `hardcoded-vs-data-driven.md` (where this sits on the spectrum),
> `scene-graph-and-data-structures.md`.

## TL;DR

Ordinary enemies — Goomba, Bob-omb, Koopa, Bully, Chain Chomp — are **not**
hardcoded the way Mario is. Each runs through a shared **object + behavior
system**: a **behavior script** (bytecode, in `data/behavior_data.c`, run by a
little VM in `src/engine/behavior_script.c`) plus a hand-written native update
loop that leans heavily on a **big shared helper library** (`cur_obj_*` /
`obj_*` in `object_helpers.c`). The script carries a lot of the object as
**data** — its object list, flags, physics parameters, animations — and mostly
`CALL_NATIVE`s the per-tick C. There are **533 behavior scripts** and **751
`CALL_NATIVE`s** in the game. So an enemy is *semi-data-driven*: configured by
data, with bespoke-but-helper-heavy C for its logic.

## 1. A behavior is a script (data), run by a VM

`bhvGoomba` is a `BehaviorScript` array — a small program:

```c
const BehaviorScript bhvGoomba[] = {
    BEGIN(OBJ_LIST_PUSHABLE),
    OR_INT(oFlags, OBJ_FLAG_COMPUTE_DIST_TO_MARIO | ...),
    DROP_TO_FLOOR(),
    LOAD_ANIMATIONS(oAnimations, goomba_seg8_anims_...),
    SET_HOME(),
    SET_OBJ_PHYSICS(/*radius*/40, /*gravity*/-400, /*bounciness*/-50,
                    /*drag*/1000, /*friction*/1000, /*buoyancy*/0, 0, 0),
    CALL_NATIVE(bhv_goomba_init),
    BEGIN_LOOP(),
        CALL_NATIVE(bhv_goomba_update),
    END_LOOP(),
};
```

The VM (`behavior_script.c`) walks these commands each frame. Notice how much is
**data**: which update list the object joins, its flags, its **physics
parameters** (gravity, friction, bounciness — literally numbers you could tune
without touching code), which animations to load. Only the per-tick logic is a
native call. This is the data-driven layer `hardcoded-vs-data-driven.md`
contrasts Mario against.

## 2. The native loop leans on shared helpers (`goomba.inc.c`)

`bhv_goomba_update` is hand-written C, but look at what it calls — almost all
shared machinery:

```c
obj_update_standard_actions(...);          // shared
cur_obj_scale(...); obj_update_blinking(...);
cur_obj_update_floor_and_walls();          // shared physics/collision
cur_obj_init_animation_with_accel_and_sound(...);
switch (o->oAction) { case GOOMBA_ACT_WALK: goomba_act_walk(); ... }  // bespoke
obj_handle_attacks(&sGoombaHitbox, ...);   // shared
```

`object_helpers.c` is a large toolbox — `cur_obj_move_using_vel`,
`cur_obj_rotate_yaw_toward`, `cur_obj_update_floor_height`, `cur_obj_move_xz`,
homing, physics stepping — that every enemy reuses. So the Goomba's *specific*
behavior (its walk/attack/jump actions) is bespoke C, but the movement,
collision, animation, and attack plumbing underneath is shared. A new simple
enemy is often a behavior script plus a short native loop that mostly calls
existing helpers.

## 3. The spectrum (why enemies ≠ Mario)

| | data-driven part | bespoke C part | reuse |
|---|---|---|---|
| **Ordinary enemy** (Goomba) | script: list, flags, physics, anims | a native update loop + a few action fns | heavy — shared `cur_obj_*` helpers |
| **Boss** (Bowser) | a script | large, elaborate native code (phases, cutscenes) | some |
| **Mario** | **none** — not in this system | the whole action state machine | he *is* the machine |

Mario is outside all of this (`gMarioState`, special-cased in the object loop —
`hardcoded-vs-data-driven.md`). Enemies live inside it and reuse it.

## How this relates to the course

- **No course covers an object/entity system.** This is the game-architecture
  lesson: a **behavior VM** (the third of SM64's three bytecode VMs, with geo
  layout and level scripts) plus a **shared helper library** is how a game gets
  dozens of distinct enemies without dozens of from-scratch implementations —
  the 1996 ancestor of a modern component/prefab system. And the physics-as-data
  in each script is a clean example of *tuning without recompiling*.

## Candidate doc-region spans (added to patch 0005)

- `data/behavior_data.c` `goomba_behavior_script` — the `bhvGoomba` script:
  data + `CALL_NATIVE`.
