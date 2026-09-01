# Reference: frame interpolation (30 Hz tick → N-subframe render)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference. How Lighthouse decouples the fixed game tick from render FPS by replaying
each display list N times with interpolated matrices. Companions:
[port-layer.md](port-layer.md), [os-emulation-threading.md](os-emulation-threading.md),
[libultraship-integration.md](libultraship-integration.md).*

*Banner: Lighthouse at branch `bill`. This IS present and substantial (~25 source files
`#include` it) — a BK-specific implementation of the same family as the SM64/OoT siblings.*

## The model in one paragraph

The game logic ticks at a **fixed 30 Hz**; the renderer presents at the display's rate (60,
120, 144, …). To fill the gap, the tick thread **records** every matrix the frame produced, and
the window thread **replays the same display list N times**, each with matrices blended between
the previous tick and the current one. `N = render_fps / 30`. So motion is smooth at high refresh
without running game logic faster.

## Where it lives

- `src/port/Interpolation/FrameInterpolation.h` (95 lines) / `.cpp` (698 lines) — the core.
- `FrameInterpolation_Interpolate(float t, std::unordered_map<Mtx*, MtxF>& out)`
  (`FrameInterpolation.cpp:613`) blends two recorded matrix "trees" at factor `t` → a map of
  `Mtx*` → interpolated `MtxF` the interpreter consults during replay.
- Recording API is called **from decomp game code** (`#include "port/Interpolation/
  FrameInterpolation.h"` in ~25 files) — e.g. every matrix write goes through
  `FrameInterpolation_RecordMatrixToMtx` in `mlMtxApply` (`src/core1/mlmtx.c:49`); camera
  projection/position at `src/core1/viewport.c:131,134`; actors/effects across
  `actor_cubepropsystem.c`, `fx/weather_*.c`, `map/gsworld.c`, etc.

## The tick rate & decoupling

- **VI ticker (frame clock):** `src/port/OS/OS_VI.cpp:38-61` — `osCreateViManager` spawns a real
  thread sleeping on an absolute 60 Hz schedule (`kVi = 16666667 ns`), latching the framebuffer
  and firing `OS_EVENT_VI` each tick (`:56-58`). Its header (`:18-21`) notes it replaced LUS's
  drifting 62.5 Hz SDL timer with "a real 60 Hz on an absolute schedule."
- **`gVIsPerFrame = 2`** (`Engine.cpp:1151`) → game logic runs at **60/2 = 30 Hz** (documented
  `Engine.cpp:1329`).
- **Subframe pacing:** `ComputeSubframePacing` (`Engine.cpp:1316-1364`):
  `effective_logic_fps = 60 / viPerTick` (`:1339`); `subframesPerTick = target_fps /
  effective_logic_fps` (`:1347`). `target_fps` comes from `GetInterpolationFPS` (`:1440-1451`:
  refresh rate / vsync / the `InterpolationFPS` CVar). `IsInterpolationEnabled()` (`:1303`) is
  true only when target FPS > 30.
- **`push_frame` is not time-throttled in the normal path** (`Game.cpp:235-271`): the natural
  pace comes from `mainLoop()` blocking on the VI-driven decomp queues, not a sleep here. Present
  throttling is downstream via `SetTargetFps` / `sPassBudgetNs` (`Engine.cpp:1412`), giving the
  tick its exact wall-time budget so game-time == wall-time.

## The graphics flow — one list, replayed N times

Split precisely along the two threads (see [port-layer.md](port-layer.md)):

1. **Tick thread records.** `push_frame` brackets `mainLoop()` with
   `FrameInterpolation_StartRecord()`/`StopRecord()` (`Game.cpp:250-255`) — unless a demo/attract
   mode (`func_802E4A08()`) is active, which renders at native rate with no interpolation
   (`Game.cpp:248`).
2. **On display-list submit** (still tick thread), `port_thread5_onSubmit` (`Game.cpp:100-132`)
   captures the recording slot pair (`FrameInterpolation_GetRecordingPair`, `:109`), claims those
   ring slots, `StopRecord`s, and stores the pair keyed by the task's data pointer in `sTaskInterp`.
3. **Window thread renders.** `ServiceRcp()` (`Game.cpp:152-161`) pulls the pending task and calls
   `RenderTask` (`:135-148`) → looks up the interp pair → `FrameInterpolation_BeginRenderPass` →
   `GameEngine::ProcessGfxCommands`.
4. **`ProcessGfxCommands`** (`Engine.cpp:1367-1438`) computes pacing, then for each of N subframes
   builds an interpolated matrix map `FrameInterpolation_Interpolate(t=i/subframesPerTick, …)`
   (`:1396-1410`) — subframe 1 inline, the rest via `std::async` (`:1403`).
5. **`RunCommands`** (`Engine.cpp:1242-1301`) loops `frameCount` times, each calling
   `interpreter->Run(Commands, m)` (`:1280`) — **the same `Commands` display list**, replayed with
   subframe `m`. Adaptive budget cutoff: a subframe that won't fit the remaining wall time breaks
   early (`:1268`). The **last** subframe (`i == subframesPerTick`) uses the empty/cleared map
   (`:1407`) — the game's own end-of-tick matrices as ground truth; in-betweens are interpolated.

## What makes it more than a lerp

- **Stable cross-tick pairing:** each matrix is stored per-scope with an FNV path signature
  (`RecordOpenChild`/`Hash3`, `.cpp:281,300,316`); `BuildInterpolationCache` (`.cpp:447-536`)
  matches current↔previous by signature. A 4-slot lock-free ring of frame trees
  (`gRing[kRingSlots]`, `.cpp:118-120`) + atomic claim counters + generation counters keep the
  recorder from recycling a tree the renderer is still blending; stale pairs drop after a full ring
  trip (`kInterpStaleAfter=4`, `Game.cpp:67,124-131`).
- **Angle-aware camera:** BK stores camera rotation in the projection matrix, so Euler angles are
  recorded separately (`RecordCameraProjectionRotation`, `.cpp:330`) and rebuilt with shortest-path
  angle lerp (`.cpp:679-697`) — element-wise matrix lerp degenerates on fast spins
  (`FrameInterpolation.h:52-56`). `shouldSnap` (`.cpp:435`) snaps instead of blending on >90° flips.
- **Sprites/billboards** rebuilt each subframe (`emitSprite`, `.cpp:540-609`) so they face the
  blended camera; `NoInterpolatePush/Pop` (`.cpp:355-363`) flags matrices that must not be lerped.
- **Object identity** (`RegisterId`/`GetId`/`UnregisterId`, `.cpp:402-427`) gives short-lived heap
  objects stable cross-tick identity so a freed-then-reused address doesn't inherit a dead object's
  matrix pairing.
- Supporting pacing helpers: `src/port/Patches/FramePacingPatches.cpp` (`port_getInterpolationFpsCap`
  cap at `:126`), `src/core1/vimgr.c`.

## Caveat — not universal

Demo/attract/replay modes (`func_802E4A08()`) and some music-synced cutscenes **disable**
interpolation and render one native-rate frame per tick (`push_frame` skips recording,
`Game.cpp:248`; `ComputeSubframePacing` forces `subframesPerTick=1`, `Engine.cpp:1353`).
Interpolation is the normal-gameplay path, not a global.

## Relevance to a freeze

The interpolation ring uses lock-free claim/generation counters, not blocking primitives, so it
is **not** a likely deadlock source — but it is the reason a stalled tick and a stalled render are
distinct failures: recording happens on the tick thread, replay on the window thread. A freeze in
which the window keeps drawing (menu responsive) but the world is frozen points at the tick side
(`mainLoop`), not interpolation. See [os-emulation-threading.md](os-emulation-threading.md).
