# Reference: Lighthouse architecture overview

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference — **read this FIRST** to get oriented without re-reading the codebase. It is
the map; the companion docs are the territory:*
*[decomp-map.md](decomp-map.md) · [port-layer.md](port-layer.md) ·
[os-emulation-threading.md](os-emulation-threading.md) ·
[libultraship-integration.md](libultraship-integration.md) ·
[frame-interpolation.md](frame-interpolation.md) · [asset-pipeline.md](asset-pipeline.md) ·
[build-system.md](build-system.md).*

*Banner: Lighthouse at branch `bill`; `libultraship` submodule pin `2917d0f4` (`1.3.1-482`),
`Torch` submodule. Port tag `1.0.0` released 2026-07-31.*

## What Lighthouse is

A PC/console port of **Banjo-Kazooie** (Harbour Masters, lead Malkierian), in the "Ship of
Harkinian" family alongside Ghostship (SM64) and Shipwright (OoT). It combines three bodies of
code:

1. **The Banjo-Kazooie decomp** (`src/core1/`, `src/core2/`, level-overlay dirs, `src/boot/`) —
   the reverse-engineered N64 game, near-1:1 with the ROM, ~⅓–½ still `func_`/`D_` named.
2. **The port layer** (`src/port/`) — C++ glue that boots the decomp, drives the frame, bridges
   C↔C++, reimplements the N64 OS, adds interpolation, and hosts the ImGui menu / enhancements /
   randomizer.
3. **libultraship (LUS)** (`libultraship/` submodule) — the shared runtime: windowing, the
   **Fast3D** display-list translator (→ OpenGL/DX11/Metal), the `.o2r` resource/archive system,
   controller input, audio, ImGui. **Torch** (`Torch/` submodule) is the offline asset extractor.

Ships **no copyrighted assets**: the player supplies a ROM; Torch extracts it to `bk.o2r`.
Port-authored assets ship in `lighthouse.o2r`.

## The layered picture

```
              ┌───────────────────────────────────────────────┐
  your ROM ─▶ │ Torch (offline / in-app) → bk.o2r (ROM assets) │
              │ port/ dir (offline) → lighthouse.o2r (port)    │   asset-pipeline.md
              └────────────────────────┬──────────────────────┘
                                       │ loaded by name at runtime
   ┌──────────────────────────┐        ▼
   │  BK decomp (C)           │  ┌────────────────────────────────┐
   │  core1 = OS/driver/audio │  │  libultraship (C++)            │
   │  core2 = gameplay overlay│◀▶│  Context · ResourceManager     │
   │  level overlays 1–14     │  │  Fast3D · ControlDeck · Audio  │  libultraship-
   │  actor + BS state machine│  │  ImGui GuiWindow framework     │  integration.md
   └───────────┬──────────────┘  └───────────────┬────────────────┘
   decomp-map  │   ▲   ▲                          │
      .md      │   │   │ extern "C" + events +    │ owns / drives
               ▼   │   │ CVars                    ▼
        ┌────────────────────────────────────────────────────────┐
        │  port layer  src/port/  (C++)                           │
        │  SDL_main · two-thread pump · GameEngine · CVars ·      │  port-layer.md
        │  N64 OS reimpl (OS/) · interpolation · menu · rando     │  os-emulation-threading.md
        └────────────────────────────────────────────────────────┘
```

## The frame model — the spine, and where Lighthouse diverges

**Lighthouse does NOT flatten the N64 OS.** Where Ghostship/Shipwright stub the scheduler and run
a single-threaded pump, Lighthouse **reimplements libultra** so the decomp's own threading runs
(see [os-emulation-threading.md](os-emulation-threading.md)). The result is a genuine **two-thread
model** (`Game.cpp`):

```c
int SDL_main(...) {
    GameEngine::Create(...);   // build LUS context/window, run ROM extractor, FinishInit
    OS_EnableThreadEntry(viMgr_entry); EnableThread5();  // allowlist decomp threads
    core1_init();              // decomp creates its (allowlisted) threads, boots to map
    ThreadWatchdog_Start();
    sGameThread = thread([]{ while (WindowIsRunning()) push_frame(); });  // TICK thread
    while (WindowIsRunning()) {                                          // WINDOW/RCP thread
        HandleEvents(); OS_SiService(); DrainRenderService(); ServiceRcp();
    }
}
void push_frame() {            // one game tick, on the tick thread
    StartFrame(); FrameInterpolation_StartRecord();
    mainLoop();                // ← ONE decomp game tick (core1/init.c:143)
    FrameInterpolation_StopRecord();
}
```

- The **tick thread** runs the decomp at a fixed **30 Hz** (`gVIsPerFrame=2`) via `mainLoop()`,
  which is paced by blocking on the decomp's VI-driven message queues (a real 60 Hz VI ticker
  thread fires `OS_EVENT_VI`).
- The **window/RCP thread** plays the RCP: it drains the SP task the decomp submitted, renders it,
  and raises SP/DP — and replays each display list **N times with interpolated matrices** for
  high-FPS output (see [frame-interpolation.md](frame-interpolation.md)).
- **"After importing the ROM"** is the `Create()` → `core1_init()` → first-`mainLoop()` boundary —
  the moment the decomp's emulated threads first run. That is where a post-import freeze lives.

## The seams that make the port work

1. **Graphics seam.** The decomp emits N64 display lists as on hardware and submits them via
   thread5; the window thread's `ServiceRcp` → `RenderTask` → `GameEngine::ProcessGfxCommands`
   (`Engine.cpp:1367`) → Fast3D. GBI-macro `__OTR__` resolution is `src/port/Resource/GfxBridge.c`.
2. **Asset seam.** `LOAD_ASSET` (`Engine.h:3`) disambiguates a decomp asset pointer as either a
   real pointer or an `__OTR__` archive name (`GameEngine_OTRSigCheck` → `ResourceGetDataByName`).
   Decomp geometry/models/levels are stripped to `bk.o2r`; only code remains in-tree. See
   [asset-pipeline.md](asset-pipeline.md).
3. **OS seam (Lighthouse-specific).** `src/port/OS/` reimplements `osCreateThread`/`osRecvMesg`/
   `osSpTask*`/VI with real threads + opt-in condvar-blocking queues, gated by an allowlist. This
   is the biggest divergence from the siblings and the first place to look for a hang. See
   [os-emulation-threading.md](os-emulation-threading.md).

## C ↔ C++ interop (three mechanisms)

- **`extern "C"` boundary** — the decomp calls a `GameEngine_*` / `OTR*` / `port_*` C API.
- **Event system** — Lighthouse's **own** event bus (`src/port/Enhancements/Events/`;
  `CALL_EVENT`/`CALL_CANCELLABLE_EVENT`), distinct from LUS's new `ship/events` bus (which
  Lighthouse only initializes for a debug window).
- **CVars** — LUS's string-keyed store; enhancements/cheats are CVar toggles persisted to
  `lighthouse.cfg.json`.

## Where things live — quick index

| I want to… | Go to |
|---|---|
| the per-frame tick / game update chain | [decomp-map.md](decomp-map.md) (`mainLoop` → `func_802E4424` → `gsworld_update`) |
| the two-thread pump / boot sequence | [port-layer.md](port-layer.md), `Game.cpp` |
| **why it freezes after ROM import** | [os-emulation-threading.md](os-emulation-threading.md) (watchdog + audio busy-waits) |
| how a display list gets drawn / high-FPS | [frame-interpolation.md](frame-interpolation.md), [libultraship-integration.md](libultraship-integration.md) |
| how an asset loads | [asset-pipeline.md](asset-pipeline.md) |
| build / CMake / flags (and headless-build gotchas) | [build-system.md](build-system.md) |
| the LUS API surface + version pin | [libultraship-integration.md](libultraship-integration.md) |

## Provenance / fork facts

- Upstream HarbourMasters/Lighthouse; Bill's fork is the **`bill`** branch (Pi-mirror `origin`).
  The fork delta over `develop` is small (docs + this reference set); the engineering is upstream.
- Bootstrap history (`git log --reverse`) is decomp-first (`core2/gczoombox.c done`, `code_87E30.c
  progress`, `80%`) — a reverse-engineering effort that grew a port layer on top.
- **Sibling reference sets** worth cross-reading: Ghostship (`github.com/billsix/Ghostship`,
  `tasks/reference/`) and Shipwright (`github.com/HarbourMasters/Shipwright`; its doc set is at `../ocarina/` in imps).
  They describe the *flattened* single-thread model — useful contrast, but Lighthouse's OS
  emulation + two-thread model is materially different; trust this set for Lighthouse.
