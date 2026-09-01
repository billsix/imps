# Reference: The OoT decomp core — "where does X live"

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

*Standing reference. What the reverse-engineered Ocarina of Time code (`soh/src/`) is and where
each kind of gameplay logic lives. Read before touching `soh/src/`. Companion:
[architecture-overview.md](architecture-overview.md) for how the port wraps it, and
[port-layer.md](port-layer.md) for `soh/soh/`.*

Shipwright's `soh/src/` is standard **zeldaret/oot** decomp (z_-prefixed files, actor overlays, the
GameState system), with a few SoH port changes noted inline. Decomp code lives under `soh/src/`,
headers under `soh/include/`. The port layer (`soh/soh/`) is [port-layer.md](port-layer.md).

## The per-frame driver — a coroutine, not a blocking loop

The N64 boot chain still exists (`soh/src/boot/`: `bootproc` `boot_main.c:13` → `Idle`/`Main`
thread entries), but the live driver is the host window loop:

```
Graph_ThreadEntry            graph.c:519   while (WindowIsRunning()) RunFrame();
 └ RunFrame()                graph.c:438   ← ONE game frame per call (a coroutine)
    ├ pick GameState from gGameStateOverlayTable[0]     graph.c:450
    ├ GameState_Init                                    graph.c:472
    └ while (GameState_IsRunning): one frame, then return
        ├ Graph_StartFrame / PadMgr_ThreadEntry
        ├ Graph_Update           graph.c:276   (THGA disp arena, opens WORK/POLY_OPA/XLU/OVERLAY)
        │   └ GameState_Update    game.c:258    ← the heartbeat
        │       ├ gameState->main(gameState)    game.c:270   (the active state's main func)
        │       └ GameState_Draw  game.c:164
        └ Graph_ProcessGfxCommands              (hands display lists to the port → LUS Fast3D)
```

- **`RunFrame` is written as a state machine** (`runFrameContext.state`; `case 1: goto nextFrame`)
  so exactly one game frame runs per call and control returns to the window loop (`graph.c:438`).
  This is the biggest structural change from vanilla OoT's blocking graphics-thread loop.
- SoH brackets the update with `GameInteractor_ExecuteOnGameStateMainStart`/`OnGameFrameUpdate`
  (the hook system — see [enhancements-gui-rando.md](enhancements-gui-rando.md)).

## The GameState system

- **`GameState`** (`z64.h:1281`, size 0xA4): `{ gfxCtx, main, destroy, init, size, input[4], tha,
  alloc, running, frames }` — **the three func pointers ARE the state's behavior.**
- **`gGameStateOverlayTable[]`** (`z_game_dlftbls.c:14`) — 6 states: `TitleSetup`, `select`
  (scene/map debug select), `title`, **`Play_Init`/`Play_Destroy` (PlayState — the actual
  gameplay, statically linked not an overlay)**, `opening`, `file_choose`.
- Lifecycle in `game.c`: `GameState_Init` (`:411`), `GameState_Update` (`:258`), `GameState_Draw`
  (`:164`), `GameState_Destroy` (`:465`). Arena: `GameState_Alloc` (`:511`).
- **Transitions are implicit** — a departing state sets the successor's `init` pointer;
  `Graph_GetNextGameState` (`graph.c:126`) decodes it. No state stack — current + "what's next".
- Overlay game states live in `soh/src/overlays/gamestates/` (`ovl_title`, `ovl_select`,
  `ovl_opening`, `ovl_file_choose`). PlayState is not an overlay.

## Actors — overlays, but SoH swapped the table for `ActorDB`

OoT actors are **compiled code overlays** (unlike SM64's behavior bytecode), one per type in
`soh/src/overlays/actors/ovl_*/` (~428 dirs). Each defines an **`ActorInit`** (`z64actor.h:34`,
0x20): `{ id, category, flags, objectId, instanceSize, init, destroy, update, draw }` — the 4 func
pointers are the actor's whole lifecycle. The runtime instance is `Actor` (`z64actor.h:223`, 0x14C),
which copies `init/destroy/update/draw` from the DB entry at spawn (`:274-277`).

- **SoH port change:** vanilla `gActorOverlayTable` is **gone**. `Actor_Spawn` (`z_actor.c:3322`)
  calls **`ActorDB_Retrieve(actorId)` → `ActorDBEntry`** (the C++ `soh/soh/ActorDB.{h,cpp}`) instead
  of indexing a static overlay table. Actor code is statically linked and always resident, so the
  overlay DMA/relocation path (`relocation.c`, `loadfragment2.c`) is **vestigial for actors**.
  *A newcomer hunting for `gActorOverlayTable` won't find it — the id→func map is in
  [`ActorDB.cpp`](port-layer.md).*
- **The actor list** feeding ActorDB: `soh/include/tables/actor_table.h` (`DEFINE_ACTOR(Name,
  ACTOR_ENUM, ALLOCTYPE_*)`, 474 entries; Player=0x0000 and En_Item00=0x0015 are
  `DEFINE_ACTOR_INTERNAL`).
- **Actor management** (`z_actor.c`, 6493 lines): `Actor_Spawn` (`:3322`), `Actor_SpawnEntry`
  (`:3474`, from the scene actor list), **`Actor_UpdateAll` (`:2574`, the per-frame loop over all
  categories)**, `Actor_DrawAll` (`:3041`), `Actor_Kill` (`:1201`).
- **`ActorContext`** (`z64.h:372`, 0x140) holds `actorLists[ACTORCAT_MAX]` — actors bucketed by
  category (`ACTORCAT_*`: switch/bg/player/explosive/npc/enemy/prop/item/misc/boss/door/chest).
  Lives at `PlayState.actorCtx`.

## Player — `soh/src/overlays/actors/ovl_player_actor/z_player.c`

**The biggest file in the tree: 16,639 lines.** Actor 0x0000.
- **`Player`** (`z64player.h:759`, 0xA94): `currentBoots`, `heldItemAction`/`itemAction`,
  `skelAnime`, **`actionFunc` (`:831`)**, `stateFlags1/2/3` (`:833`), **`upperActionFunc` (`:859`,
  a separate upper-body action machine — item use runs concurrently with locomotion)**.
- **The action state machine is function pointers, not a switch.** `Player_SetupAction(play, this,
  actionFunc, flags)` (`z_player.c:3305`) assigns `this->actionFunc`; the funcs are `Player_Action_*`
  (`Player_Action_Idle` `:259`, `_Roll` `:279`, and dozens still with raw-address names like
  `Player_Action_80840450`). Each frame `Player_Update` → `Player_UpdateCommon` calls
  `actionFunc(this, play)` and `upperActionFunc(...)`. Item behavior via `Player_InitItemAction`
  (`:130`) + per-item initializers.
- **PlayState↔Player is decoupled via function pointers**: `PlayState` holds `playerInit`,
  `playerUpdate`, `grabPlayer`, `talkWithPlayer`, `damagePlayer`, … (`z64.h:1451-1467`), so
  `z_play.c` never calls player code directly. `GET_PLAYER(play)` fetches the instance.

## Other `src/code/` systems (line count = complexity signal)

- **Collision — TWO systems, confusingly similar names:** `z_bgcheck.c` (4539 lines) = static world
  geometry (`CollisionContext colCtx`); `z_collision_check.c` (3659) = actor hitboxes/damage
  (`Collider*`, `CollisionCheckContext colChkCtx`).
- **Camera — `z_camera.c` (8385 lines, 2nd-biggest):** modes/settings; `Camera mainCamera` +
  `subCameras`. Data in `z_camera_data.inc`.
- **Scenes/objects — `z_scene.c`:** scene & room command parsing, object-bank loading
  (`Object_GetIndex`); `ObjectContext objectCtx`. Room streaming `z_room.c`. Tables:
  `soh/include/tables/{scene_table,object_table,entrance_table}.h`.
- **Skeletal animation — `z_skelanime.c` (1953):** `SkelAnime` limb hierarchies + playback;
  `z64animation.h`, `z64skin.h`.
- **Effects/particles:** `z_effect.c` + `z_effect_soft_sprite*.c`; overlays in
  `soh/src/overlays/effects/ovl_Effect_Ss_*`. Table `effect_ss_table.h`.
- **Message/textbox — `z_message_PAL.c`:** `MessageContext msgCtx`; `elf_message/` = the C-Up Navi
  message tables.
- **Lights** `z_lights.c`; **cutscenes** `CutsceneContext csCtx` (`z64cutscene.h`); **HUD/pause**
  `InterfaceContext` + `PauseContext` (drives `ovl_kaleido_scope`).

## Overlays directory (`soh/src/overlays/`)

- **`actors/`** — ~428 `ovl_*` dirs, one actor per dir.
- **`gamestates/`** — the 4 overlay game states.
- **`effects/`** — Effect_Ss soft-sprite overlays.
- **`misc/`** — `ovl_kaleido_scope` (the pause/equip/map/quest menu — a large subsystem),
  `ovl_map_mark_data`.
- Overlay relocation (`relocation.c` `Overlay_Relocate`, `loadfragment2.c`
  `Overlay_AllocateAndLoad`) is **vestigial for actors** (statically linked); gamestate overlays
  still use `Overlay_LoadGameState`.

## Key headers (`soh/include/`)

- **`z64.h`** — the master header: `GameState` (`:1281`), **`PlayState` (`:1418`, size **0x12518** —
  the god-struct; every subsystem is a context field with an annotated offset)**, `GameStateOverlay`
  (`:1662`), `ActorContext` (`:372`). To find "where does X state live," grep the PlayState field
  list.
- **`z64actor.h`** — `ActorInit` (`:34`), `Actor` (`:223`), `ActorCategory` (`:449`).
- **`z64player.h`** — `Player` (`:759`), action-func typedefs, boots/item-action enums.
- **`z64save.h`** — `SaveContext`/`gSaveContext` (inventory, flags, scene flags, language).
- Domain headers: `z64bgcheck.h`, `z64camera.h`, `z64collision_check.h`, `z64animation.h`,
  `z64scene.h`, `z64math.h` (`Vec3f`/`MtxF`), `z64cutscene.h`, `z64item.h`.
- **Global glue:** `functions.h` (extern func decls), `variables.h` (`gSaveContext`, `gPlayState`,
  `gSegments`, `HREG`/`SREG`/…), `macros.h`, `gfx.h` (GBI display-list macros).
- **Tables:** `soh/include/tables/` — `actor_table.h`, `object_table.h`, `scene_table.h`,
  `entrance_table.h`, `effect_ss_table.h`, `dmadata_table*.h`.

## Newcomer trip-hazards

1. **The frame loop is a coroutine** (`RunFrame` `graph.c:438` returns after one frame). No classic
   `while(1)` — the host window loop drives frames.
2. **`gActorOverlayTable` is gone** — the actor id→func map is in `soh/soh/ActorDB.cpp`
   (`ActorDB_Retrieve`); actor overlay DMA/relocation is vestigial.
3. **`PlayState` (0x12518) IS the world** — almost every subsystem is a context field with an
   annotated offset (`z64.h:1418`).
4. **`z_player.c` is 16.6k lines; the state machine is function pointers** (`actionFunc` +
   `upperActionFunc`), many still raw-address-named.
5. **Two collision systems**: `z_bgcheck.c` (world) vs `z_collision_check.c` (hitboxes) — different
   structs, similar names.
6. **State transitions are implicit** (a state sets the next `init` pointer; no stack).
7. **Player↔Play cross-refs go through PlayState function pointers**, not direct calls.
