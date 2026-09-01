# Reference: Ghostship architecture overview

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference — read this FIRST to get oriented without re-reading the codebase.
It is the map; the four companion docs are the territory:*
*[decomp-map.md](decomp-map.md) · [port-layer.md](port-layer.md) ·
[libultraship-integration.md](libultraship-integration.md) ·
[asset-pipeline.md](asset-pipeline.md) · [build-system.md](build-system.md).*
*The maintainer's fork-specific workflow + gameplay gotchas live in the root
[`CLAUDE.md`](../../CLAUDE.md); this doc is the architecture underneath them.*

## What Ghostship is

A PC/console port of **Super Mario 64**, in the "Ship of Harkinian" family. It combines three
bodies of code:

1. **The SM64 decomp** (`src/game`, `src/engine`, `src/audio`, `src/menu`, `src/buffers`,
   `src/goddard`, `include/`, `levels/`, `actors/`, `data/`) — the reverse-engineered N64
   game, near-1:1 with the ROM. Standard n64decomp/sm64 lineage.
2. **The port layer** (`src/port/`) — C++ glue that boots the game, drives one frame at a
   time, bridges decomp C ↔ modern C++, and adds the ImGui menu / cheats / achievements /
   randomizer.
3. **libultraship (LUS)** (`libultraship/` submodule) — the shared runtime that reimplements
   N64 services on modern hardware: windowing, the **Fast3D** display-list translator
   (→ OpenGL/DX11/Metal), the **resource/archive** system (`.o2r`/`.otr`), controller input,
   audio, and the ImGui framework. **Torch** (`Torch/` submodule) is the offline asset
   extractor that turns a ROM into the `.o2r` bundle.

Ghostship ships **no copyrighted assets**. The player supplies a ROM; Torch extracts it to
`sm64.o2r` at build/first-run. Port-authored assets ship in `ghostship.o2r`.

## The layered picture

```
                 ┌─────────────────────────────────────────────┐
   your ROM ───▶ │ Torch (offline)  →  sm64.o2r  (ROM assets)   │
                 │ port/ dir (offline) → ghostship.o2r (port)   │   asset-pipeline.md
                 └───────────────────────┬─────────────────────┘
                                         │ loaded by name at runtime
   ┌───────────────────────────┐         ▼
   │  SM64 decomp  (C)          │   ┌───────────────────────────────┐
   │  game / engine / audio     │   │  libultraship (C++)           │
   │  gameplay, 3 bytecode VMs, │   │  Context · ResourceManager    │
   │  GraphNode renderer,       │◀─▶│  Fast3D · ControlDeck · Audio │  libultraship-
   │  surface collision         │   │  ImGui GuiWindow framework    │  integration.md
   └───────────┬───────────────┘   └───────────────┬───────────────┘
   decomp-map  │        ▲   ▲                       │
      .md      │        │   │  extern "C" bridge     │  owns / drives
               ▼        │   │  (Engine.h)            ▼
        ┌──────────────────────────────────────────────────────┐
        │  port layer  src/port/  (C++)                         │
        │  main() · GameEngine singleton · frame pump ·         │  port-layer.md
        │  CVars · ImGui menu · EventSystem hooks · mods · Rando│
        └──────────────────────────────────────────────────────┘
```

## The frame loop — the spine of everything

`src/port/Game.cpp` (verified by reading):

```c
int main(...) {
    GameEngine::Create(argc, argv);   // builds Ship::Context, window, resources, menu; runs ROM extractor
    alloc_pool();                     // N64-style main_pool_init over a static 32 MB pool
    audio_init(); sound_init();
    thread5_game_loop();              // decomp loop SETUP (not a loop here)
    while (WindowIsRunning())         // LUS window liveness
        push_frame();
    GameEngine::Instance->Destroy();
}
void push_frame() {                   // one game frame
    GameEngine::StartAudioFrame();
    GameEngine::Instance->StartFrame();
    thread5_iteration();              // ← ONE decomp game tick (game_init.c:678)
    GameEngine::EndAudioFrame();
}
```

Key idea: **the N64's OS-thread scheduler is dead.** The decomp's threaded loop is
flattened to a single-threaded, port-driven `thread5_iteration()` per frame. Inside that
tick the **level-script bytecode VM** (`level_script_execute`) is what actually calls
gameplay — see the full update chain in [decomp-map.md](decomp-map.md#the-per-frame-update-chain).

## The two seams that make the port work

These are the crux; everything else is detail.

1. **Graphics seam — `exec_display_list`.** The decomp emits N64 display lists (`Gfx*`)
   exactly as on hardware. The port **redefines** the decomp's `exec_display_list`
   (`Game.cpp:18`, `extern "C"`, name fixed by the decomp) to forward them to
   `GameEngine::ProcessGfxCommands` → Fast3D → the GPU backend. That single function is the
   entire N64-graphics → PC-renderer handoff. (`ProcessGfxCommands` also replays the list N
   times per frame with interpolated matrices for high-FPS — see libultraship doc.)

2. **Asset seam — `LOAD_ASSET` / OTR signature check** (`Engine.h:3`):
   ```c
   #define LOAD_ASSET(path) (path==NULL ? NULL :
       (GameEngine_OTRSigCheck(path) ? ResourceGetDataByName(path) : path))
   ```
   A decomp asset pointer is **either** a real in-memory pointer **or** an `__OTR__` archive
   name, disambiguated at runtime by `OtrSignatureCheck`. This is how the decomp's static
   segmented-address asset references transparently become archive lookups from the `.o2r`.
   The classic decomp's `levels/*/` and `actors/*/` geometry has been **stripped to the
   archive**; only code (scripts, behavior tables) remains in-tree.

## C ↔ C++ interop (three mechanisms)

- **`extern "C"` boundary** — port C++ exposes a `GameEngine_*` / `OTR*` C API
  (`Engine.h:86-134`) the decomp calls for assets, audio banks, dialog, HUD/aspect math,
  malloc; port `.cpp` wraps decomp headers in `extern "C" { #include "sm64.h" }`.
- **EventSystem hooks** — the primary decomp→port callback path (there is **no**
  SoH `GameInteractor` here; it was reimplemented as a lighter event bus). Decomp C fires
  `CALL_CANCELLABLE_EVENT`; port C++ listeners react and can cancel the guarded block. See
  [port-layer.md](port-layer.md) and [`wiki/EventSystem.md`](../../wiki/EventSystem.md).
- **CVars** — libultraship's string-keyed console-variable store, reached from decomp `.c`
  via `#include <libultraship/bridge/consolevariablebridge.h>`. The fork's cheats/enhancements
  are all CVar toggles (`gCheats.*` / `gEnhancements.*` — string namespaces, **not** structs).

## Where things live — quick index

| I want to… | Go to |
|---|---|
| change gameplay physics / Mario actions | `src/game/mario*.c` — [decomp-map.md](decomp-map.md) |
| understand the per-frame call chain | [decomp-map.md](decomp-map.md#the-per-frame-update-chain) |
| add a cheat / menu toggle | `src/port/ui/GhostshipMenuEnhancements.cpp` + root `CLAUDE.md` recipe |
| override decomp behavior from the port | EventSystem — [port-layer.md](port-layer.md), `wiki/EventSystem.md` |
| know how an asset gets loaded | [asset-pipeline.md](asset-pipeline.md), [libultraship-integration.md](libultraship-integration.md) |
| build / understand CMake / CI | [build-system.md](build-system.md) |
| understand the LUS API surface | [libultraship-integration.md](libultraship-integration.md) |

## Provenance / fork facts

- Upstream is HarbourMasters/Ghostship, lead dev Lywx/KiritoDv (`git shortlog`: KiritoDv
  367 commits). The fork of the maintainer (William Emerison Six <billsix@gmail.com>) is the **`bill`** branch (`origin`/`bills` remotes on a Pi).
- The fork is **small and surgical**: 11 commits over the `develop` merge-base, 12 files —
  9 in `src/game/` (fly/jump/no-hurt/no-skybox cheats), 1 menu file, the root `CLAUDE.md`,
  and `docs/plans/cheats-and-menu-enhancements.md`. `git diff $(git merge-base develop bill)..bill`
  shows the whole delta. Don't rebase onto `develop` without asking — the history is
  intentionally "mistake-driven".
- Port bootstrap milestones are legible in git history: *"First build (with linker errors)"*
  → *"added main entry point"* → *"no audio, but goddard is working"* → audio. That order
  (build → goddard intro → audio → gameplay) is how a decomp gets stood up on LUS.
