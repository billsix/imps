# Reference: Shipwright (SoH) architecture overview

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

*Standing reference — read FIRST to get oriented on Shipwright (Ship of Harkinian), the Ocarina of
Time PC port, without re-reading the codebase. The map; the companion docs are the territory:*
*[decomp-map.md](decomp-map.md) · [port-layer.md](port-layer.md) ·
[libultraship-integration.md](libultraship-integration.md) · [asset-pipeline.md](asset-pipeline.md) ·
[frame-interpolation.md](frame-interpolation.md) · [enhancements-gui-rando.md](enhancements-gui-rando.md) ·
[build-system.md](build-system.md).*

## What SoH is

Shipwright / **Ship of Harkinian (SoH)** is a PC/console port of **The Legend of Zelda: Ocarina of
Time**, in the "Ship of Harkinian" family — the **original** port whose approach Ghostship (the SM64
port) later derived from. It combines three bodies of code:

1. **The OoT decomp** (`soh/src/` — `boot`, `code`, `overlays`, `buffers`, `include/`) — the
   reverse-engineered N64 game (zeldaret/oot lineage, z_-prefixed files, actor overlays, the GameState
   system). [decomp-map.md](decomp-map.md).
2. **The port layer** (`soh/soh/`) — C++ glue (`OTRGlobals` is the central object) that boots the
   decomp on libultraship, drives one frame at a time, bridges C↔C++, and hosts SoH's huge feature
   layer (enhancements, the randomizer, the SohGui menu). [port-layer.md](port-layer.md),
   [enhancements-gui-rando.md](enhancements-gui-rando.md).
3. **libultraship (LUS)** (`libultraship/` submodule, pinned **`1.3.1-463`**) — the shared runtime:
   windowing, the Fast3D renderer, the resource/archive (`.o2r`) system, controller, audio, ImGui.
   [libultraship-integration.md](libultraship-integration.md).

Assets come from the player's OoT ROM via **ZAPD + OTRExporter** → `oot.o2r`/`oot-mq.o2r`
(ROM-derived) + `soh.o2r` (port-authored). SoH ships no copyrighted assets.
[asset-pipeline.md](asset-pipeline.md).

## The frame loop — a hand-written coroutine

The decomp keeps its N64 boot structure but the hardware is stubbed and the "threads" are inline
calls:
```
main()                        soh/src/code/main.c:59  → InitOTR → Main(0)
 Main(void*)                  main.c:74               → Graph_ThreadEntry(0)  (inline, not an OS thread)
  Graph_ThreadEntry           graph.c:519  while (WindowIsRunning()) RunFrame();
   RunFrame()                 graph.c:438  ← ONE game frame per call (a coroutine; goto nextFrame)
    ├ Graph_Update            (one decomp GameState update → builds an N64 display list)
    └ Graph_ProcessGfxCommands  OTRGlobals.cpp:1804  (hands the display list to the port → LUS Fast3D)
```
`osCreateThread`/`osStartThread` are no-ops (`stubs.c`); the only real extra threads are the OTR audio
thread and SaveManager's pool. See [decomp-map.md](decomp-map.md), [port-layer.md](port-layer.md).

## The seams that make the port work

- **Graphics + assets — `GbiWrap.cpp` + `__OTR__`.** The decomp emits N64 GBI where segment pointers
  are actually `"__OTR__objects/..."` **path strings** (baked in by ZAPD/OTRExporter). `GbiWrap.cpp`
  redefines the GBI macros as real functions that run `ResourceMgr_OTRSigCheck` (a 7-byte `"__OTR__"`
  prefix test) and resolve each to loaded data via the LUS ResourceManager before handing a normal
  `Gfx*` list to `Fast3dWindow::DrawAndRunGraphicsCommands`. [libultraship-integration.md](libultraship-integration.md),
  [asset-pipeline.md](asset-pipeline.md).
- **Behavior hooks — GameInteractor.** SoH has a **full hook/event system**: the decomp fires named
  events and `GameInteractor_Should(VB_…)` decision points (~178 sites, 421 `VB_*` flags); enhancement
  and rando code subscribes without editing decomp. This is the mechanism behind every cheat, fix, and
  the randomizer. [enhancements-gui-rando.md](enhancements-gui-rando.md).

## libultraship: version `1.3.1-463`, singleton Context

SoH pins LUS `1.3.1-463` (singleton `Context::GetInstance()` + `CreateUninitializedInstance` + `Init*`
methods — **not** the newer Component tree). A LUS reference set pinned to a nearby `1.3.1-399` exists
at `github.com/Kenix3/libultraship`'s `bill` branch (`tasks/reference/`); the architecture matches,
with one notable difference at 463: **the Fast3D renderer is split into its own `Fast::` namespace
under `<fast/...>`** (only controller/InputEditor classes remain `LUS::`). See
[libultraship-integration.md](libultraship-integration.md).

## Frame interpolation (your priority) — SoH is the original

SoH's frame interpolation (`soh/soh/frame_interpolation.cpp`) is the **original** that Ghostship's
Mario 64 version pared down. Same core mechanism (record matrix ops keyed by identity, replay the same
display list N times per tick with lerped matrices, substitute at `gSPMatrix` in the LUS interpreter),
but SoH is fuller: it varies the game tick (**20/30/60 Hz** via `R_UPDATE_RATE`, not a fixed 30),
records the **entire matrix stack** so it interpolates transform *inputs*, keeps the actor
rotation-decompose anti-"paper-flip" mitigation live, and actively drives camera-cut suppression. Full
detail + the SoH-vs-Ghostship comparison: [frame-interpolation.md](frame-interpolation.md).

## Where things live — quick index

| I want to… | Go to |
|---|---|
| find OoT gameplay logic (actors, player, scenes) | [decomp-map.md](decomp-map.md) |
| understand `OTRGlobals`, the frame loop, CVars, save | [port-layer.md](port-layer.md) |
| add a cheat/enhancement or a menu widget | [enhancements-gui-rando.md](enhancements-gui-rando.md) |
| understand how an asset loads / `__OTR__` / `.o2r` | [asset-pipeline.md](asset-pipeline.md), [libultraship-integration.md](libultraship-integration.md) |
| understand the high-FPS interpolation | [frame-interpolation.md](frame-interpolation.md) |
| build SoH / extract assets | [build-system.md](build-system.md) |

## Provenance

~4,075 commits of the **HarbourMasters/soh** lineage (top authors briaguya, aMannus, Malkierian,
Garrett Cox). **This checkout's `bill` branch is level with upstream `develop` — 0 custom commits
ahead**, so it's essentially stock SoH (no personal cheats fork, unlike Ghostship). One caveat found
during the survey: the OTR **audio thread** (`OTRGlobals.cpp:1022-1090`) carries drift-correction /
self-pump code not in stock SoH — possibly a local modification; verify against upstream before
treating it as canonical.
