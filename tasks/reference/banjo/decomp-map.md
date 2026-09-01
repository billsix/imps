# Reference: the Banjo-Kazooie decomp map (`src/core1/`, `src/core2/`, level overlays)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference — "where does X live" in the reverse-engineered game. Companions:
[architecture-overview.md](architecture-overview.md), [port-layer.md](port-layer.md),
[os-emulation-threading.md](os-emulation-threading.md).*

*Banner: Lighthouse at branch `bill`. The decomp is a near-1:1 port of the N64 ROM; every
decomp `.c` carries a provenance comment mapping it to the upstream BanjoDecomp file, e.g.
`// BanjoDecomp: code_0.c` (`init.c:1`).*

## The overlay layout (not a game/engine split)

Unlike the SM64/OoT siblings (which have `src/game` + `src/engine`), Banjo-Kazooie mirrors
the ROM's **overlay** structure. There is no engine/game directory split; the seams are:

- **`src/core1/` (63 files) — the always-resident boot/OS/driver core** (ROM code segment 0):
  threading + boot (`init.c`, `initthread.c`), PI/DMA (`pimanager.c`), VI/framebuffer
  (`vimgr.c`, `viewport.c`, `depthbuffer.c`, `framebufferdraw.c`), the RSP/RDP display-list
  pipeline (`display_list.c`, `graphics_thread.c`, `ucode.c`), matrix/vector math (`ml.c`,
  `mlmtx.c`, `gu_*.c`), memory/heap (`memory.c`, `defragmanager.c`), controller-pak
  (`pfsmanager.c`), the **full N64 audio driver** (`audio_*.c`, `musicplayer.c`, `n_audio/` —
  29 files), overlay loading (`overlay.c`, `overlaymanager.c`), collision (`collision.c`),
  sprites (`sprite.c`), Stop 'n' Swop (`sns.c`, `stopnswop.c`).
- **`src/core2/` (391 files) — the gameplay core**, loaded by core1 as **overlay 0**
  (`overlaymanager.c:32`, `overlaymanager_loadCore2()` at `overlaymanager.c:133`): the game
  loop (`gameloop.c`, `gamestate.c`), map/world system (`map/`), actor system
  (`actor_array.c`, `actor_cubepropsystem.c`, `spawnqueue.c`, `bundle.c`), player (`ba/` =
  Banjo actor, `bs/` = Banjo state machine), animation (`anim/`), rendering (`model/`, `vtx/`),
  particles/FX (`particle/`, `fx/`), collision (`collision/`), UI/game-control (`gc/`, `font/`,
  `dialog/`, `fileselect.c`), save (`savedata.c`, `file.c`, `*score.c`), game-level SFX
  (`sfx/`), camera (`nc/`), misc (`quiz/`, `mumbo*.c`).
- **Level overlays 1–14** in their own top-level dirs (`boot/overlaytable.c:41-55`): `CC`
  (Clanker's Cavern), `MMM`, `GV`, `TTC`, `MM` (Mumbo's Mountain), `BGS`, `RBB`, `FP`, `CCW`,
  `SM` (Spiral Mountain), `cutscenes`, `lair`, `fight`. Each holds only that level's
  actor/behavior C (e.g. `SM/quarrie.c`, `BGS/ch/mrvile.c`).
- **`src/boot/`** — ROM entry stub + decompressor (mostly stubbed on PC). **`src/unused/` (8
  files)** — vestigial, kept out of the build (`CMakeLists.txt` filters `src/unused/`).

**Conceptually:** core1 is the resident OS/driver/audio core; core2 is the swappable gameplay
overlay it loads and jumps into; level dirs are further overlays on top of core2. (Established
from `overlaymanager.c` + `overlaytable.c`, not guessed.)

## The per-frame update chain

The decomp's original boot chain (`core1_main` → `initThread` → `mainThread` → `while(1)
mainLoop()`, `init.c:37/217/238`) is **bypassed** by the port: `Game.cpp` calls `core1_init()`
directly and drives `mainLoop()` from `push_frame()` (see [port-layer.md](port-layer.md)). The
decomp functions themselves are unchanged:

1. **`core1_init()`** (`init.c:107`) — sets the boot map, `viMgr_init()`, **`overlayManager_loadCore2()`**
   (`:115`), `assetCache_init()`, `pfsManager_init()`, `baMotor_init()`, `audioManager_init()`,
   `graphicsCache_init()`, `ml_init()`, then `func_8023DA9C(3)` (`:132`) → app state 3. Much N64
   init is `#if 0`'d with `[port]` notes (`:111-122`).
2. **`mainLoop()`** (`init.c:143`) — one tick: bumps the global timer, `pfsManager_update()`,
   rumble, then dispatches on `D_8027A130` (top-level app state). **State 3 = in-game**
   (`:169-176`): heap/defrag housekeeping (`func_80255524`/`func_80255ACC`), spawn-queue update,
   `if (func_802E4424()) game_draw(FALSE)`, spawn-queue flush. Ends with
   `CALL_EVENT(GameFrameUpdate)` (`:213`) into the port event system.
3. **`func_802E4424()`** (`gameloop.c:504`) — the real per-frame game update: pending map/mode
   transitions (`:513`), `gsworld_update()` (`:593`), music, the `game_mode` state machine
   (`:597-643`). Returns whether to draw.
4. **`gsworld_update()`** (`map/gsworld.c:341`) — the world tick: particles, anim caches,
   cameras, cutscene triggers, and actor updates.
5. **Actor updates** — `func_803268B4()` (`actor_array.c:550`) iterates `suBaddieActorArray` and
   calls each actor's function pointer, `marker->actorUpdate2Func(actor)` (`:579`) or
   `marker->actorUpdateFunc(actor)` (`:587`); `ActorUpdateFunc` typed at `include/prop.h:108`.
6. **`game_draw()`** (`gameloop.c:322`) — builds the display list (`func_802E39D0`) and hands
   the frame to the port via `Graphics_PushFrame` (`gameloop.c:348`).

## Dispatch: function pointers, NOT a bytecode VM

Banjo-Kazooie has **no** bytecode interpreter (unlike SM64's 3 script VMs). Two C-function-pointer
systems drive everything:

- **Actor system** — actors are structs in `suBaddieActorArray` with per-actor update/draw
  function pointers, dispatched at `actor_array.c:550-602`. Spawn tables in `bundle.c`,
  `actor_cubepropsystem.c` (the "cube prop" spatial system for map objects), `spawnqueue.c`.
  Actor *behaviors* live per-level (`BGS/ch/mrvile.c`, `CC/ma/clanker.c`) and shared in
  `core2/bs/`, `core2/ch/`.
- **Player (Banjo) state machine** — `core2/bs/bs_statemachine.c`: an integer state indexes a
  table of {init, update, end, interrupt} method pointers via `bs_setState`/`bs_updateState`/
  `bs_checkInterrupt` (`:14-60`). The ~53 `bs/*.c` files (`bFly.c`, `climb.c`, `carry.c`,
  `die.c`, …) are the individual states; `bsList.c` is the registry.
- **Map/level dispatch** — `map/gsworld.c`, `map/list.c` (map→level table, `:9`),
  `map/warp_dispatch.c`, `map/loadzone.c`, `map/overlay.c` (per-map overlay callbacks).

## Audio decomp & the three boot-freeze busy-waits

`core1/audio_*.c` + `n_audio/` are the N64 `libaudio` synthesizer + sequence player;
`core2/sfx/source.c` is the game-level SFX pool. Three spin-waits here are the **prime
suspect for a post-import freeze** (they wait on audio state the callback normally clears):

- `audio_instruments.c:368-371` (in `func_8024FA98`) — spins while a sequence player's
  `cseqp.state != AL_STOPPED`.
- `audio_instruments.c:390-399` (in `func_8024FB8C`) — stops all 6 players, spins until every
  one is `AL_STOPPED`.
- `source.c:451-463` (in `func_8030D778`) — frees all busy SFX sources, spins until none is `busy`.

Each got a `[port]` escape hatch `if (gPortResetPending) break;` — but `gPortResetPending` is set
**only during a console `reset`**, never at normal boot (cleared in `mainLoop` at `init.c:182`).
So if the audio worker (`audioManagerThread_entry`) isn't advancing on the first frame, any of
these spins forever — and because they're busy-spins, not queue waits, the ThreadWatchdog sees a
stalled `game-tick` with **no queue park** (see [os-emulation-threading.md](os-emulation-threading.md#6)).

## Stripped assets vs in-tree code

**All binary asset data — geometry, models, level layout, textures, animation — is stripped to
the `.o2r` archive; only code remains in-tree.**

- Asset access goes through `assetcache_get()` (`anim/anim_bonetransform.c:397`), which on the
  port is `return ResourceMgr_LoadByAssetId(assetId)` — a Resource Manager lookup, not RAM/ROM.
  `assetCache_init()` (`:501`) has the original ROM-metadata-table setup `#if 0`'d (`:508-518`);
  `func_8033BDAC` (`:556`) hard-returns 0 so callers fall to the o2r path.
- Assets are referenced by numeric `enum asset_e` IDs; only pure index tables survive in-tree
  (`sAnimAssetIds[]`, `core1/lookup.c:5`). `__OTR__`-tagged paths are resolved in the port
  (`port/Resource/GfxBridge.c`). See [asset-pipeline.md](asset-pipeline.md).
- Level geometry (`<LEVEL>_rzip` segments, `boot/overlaytable.c:14-33`) is likewise archived;
  in-tree level dirs hold only behavior C.

## Naming state — partially decompiled

The decomp is **partially named**: subsystem boundaries are clean (`gsworld_update`,
`bs_setState`, `assetcache_get`, `audioManager_init`), but internals still carry raw addresses —
**329** distinct `func_XXXX` in core1, **2732** in core2, and **1587** `D_80XXXXXX` data symbols
combined, against ~5500 named core2 functions (roughly a third to a half of functions still bear
raw addresses). Many carry inline hints in comments (`func_80255198(); //heap_flush_free_queue`,
`init.c:50`).

## Dead / vestigial / port-stubbed (flagged, verify before trusting removed)

- **`src/unused/` (8 files)** — out-of-build vestigial decomp (`antitamper_seed.c`,
  `datalookup.c`, `debug_*.c`, `dummy_overlay_callbacks.c`, `version_compat.us.v10.c`, …).
- **Large `#if 0` N64-only blocks** — `init.c:38-42` (bzero/osInitialize), `:111-122`
  (ucode/heap/rarezip init), `:159-163` (EEPROM CRC), `:186-210` (CRC-failure glitch renderer);
  `assetCache_init` `:508-518`.
- **Anti-tamper stubs** — `gsworld.c:360-376`: a 150M-iteration CPU stall `#if 0`'d with a
  `[port]` note that it caused a boot/BGS hang; `codeCF5F0_triggerAntiTamperMeasurement()`
  (`gsworld.c:345`) is still called but the stall body is gone.
- **Stub no-ops** retained for call-graph parity — `ucode_stub1` (`init.c:70`), `func_8030D8A8`
  (`source.c:472`, bare `return`), `depthbuffer_stub`, `gsworld_stub1/3`.
- **Known-preserved bugs** annotated `// BUG:` — e.g. `game_draw` explicit-`TRUE` compare
  (`gameloop.c:335`).

## Quick index

| I want to… | Go to |
|---|---|
| the per-frame tick | `mainLoop` `init.c:143` → `func_802E4424` `gameloop.c:504` → `gsworld_update` `gsworld.c:341` |
| an actor's behavior | per-level dir (`BGS/`, `TTC/`, …) or `core2/bs/`, `core2/ch/`; dispatch `actor_array.c:550` |
| Banjo's moves/states | `core2/bs/*.c`; state machine `bs_statemachine.c:14` |
| audio / music | `core1/audio_*.c`, `n_audio/`, `musicplayer.c`; SFX `core2/sfx/source.c` |
| a boot freeze | the 3 audio busy-waits above + [os-emulation-threading.md](os-emulation-threading.md) |
| how an asset loads | `assetcache_get` `anim_bonetransform.c:397` + [asset-pipeline.md](asset-pipeline.md) |
