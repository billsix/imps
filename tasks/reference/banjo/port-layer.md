# Reference: the port layer (`src/port/`)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference. The C++ layer that boots the decomp on libultraship, drives the two-thread
frame model, bridges C↔C++, and adds the menu/enhancements/rando. Companions:
[architecture-overview.md](architecture-overview.md),
[os-emulation-threading.md](os-emulation-threading.md),
[libultraship-integration.md](libultraship-integration.md),
[frame-interpolation.md](frame-interpolation.md).*

*Banner: Lighthouse at branch `bill`; LUS submodule pin `2917d0f4` (`1.3.1-482`).*

## Subdir map (`src/port/`)

| Path | Role |
|---|---|
| `Engine.{cpp,h}` | `GameEngine` singleton — LUS ownership, boot, C API, resource/audio tables |
| `Game.cpp` | `SDL_main`, the two-thread pump (`push_frame`/`ServiceRcp`), graphics seam |
| `OS/` | N64 OS reimplementation — see [os-emulation-threading.md](os-emulation-threading.md) |
| `Audio/` | `AudioSync` (osSetIntMask→mutex), `AudioInterface`, `AudioSoundFont`, `mixer` |
| `Interpolation/` | frame interpolation — see [frame-interpolation.md](frame-interpolation.md) |
| `Resource/` | `LOAD_ASSET`, `GfxBridge.c`, factories (`Importers/`,`Type/`), `Alt/` HD assets |
| `Extractor/` | in-app ROM extractor (Torch `Companion`) |
| `Enhancements/` | the big feature tree: `Cheats`, `Fixes`, `Camera`, `Cutscenes`, `Modes`, `Restorations`, `Backports`, `Gameplay`, `Save`, `Trackers`, `Events/Hooks` |
| `Rando/` | randomizer: `Logic`, `StaticData`, `CheckTracker`, `CustomObject`, `*Behavior` |
| `UI/` | ImGui menu (`LighthouseModMenuWindow`, `Menu`, `Notification`), `DeveloperTools` |
| `DevTools/` | `ThreadWatchdog`, `EventDebugger`, `DevSequences`, `OcclusionDebug` |
| `Controller/` | `ControlSchemes`, `Mapper` (custom input-mapping window) |
| `Network/Anchor/` | netplay (behind `USE_NETWORKING`) |
| `Save/`, `GameVersion`, `Localization`, `Nametag`, `ObjectExtension`, `Patches`, `Romhack` | supporting subsystems |

Gotcha: both `Enhancements/` and a lowercase `enhancements/Gameplay/` exist — watch case when grepping.

## Entry & the two-thread pump

`SDL_main` (`Game.cpp:278`; `#define SDL_main main` on GCC, `:274-276`):

1. Anchor the working dir (`SHIP_HOME` / `APPIMAGE` / app-bundle path, `:285-299`).
2. **`GameEngine::Create(argc, argv)`** (`:301`) — construct engine, run the ROM extractor UI,
   `FinishInit`, init port subsystems. (Details below.)
3. Allowlist `viMgr_entry` (`:303`) and **`EnableThread5()`** (`:304`) — allowlist thread5 /
   pfsManager / audioManager and mark their queues blocking — **before** the threads exist.
4. **`core1_init()`** (`:305`) — the decomp creates its (now-allowlisted) threads and boots to map.
5. **`ThreadWatchdog_Start()`** (`:306`).
6. Launch the **game/tick thread** (`:308-315`): `while (WindowIsRunning()) { Beat(GAME_TICK);
   push_frame(); }`.
7. The main thread becomes the **window/RCP loop** (`:316-339`): `HandleEvents` → `OS_SiService`
   → `DrainRenderService` → `ServiceRcp`; during a game-tick stall it renders **gui-only** frames
   so the menu + watchdog dump stay reachable (`:329-336`).
8. Cooperative shutdown (`:342-366`): request exit, wake `sSvcCv`, `OS_BeginShutdown`, join the
   tick thread, `OS_JoinDecompThreads`, stop watchdog/VI, `Destroy`, `RelaunchIfRequested`.

`push_frame()` (`:235-271`): `StartFrame` → record interpolation (unless demo) → **`mainLoop()`**
(the decomp tick, `core1/init.c:143`) → title refresh once/second via `port_runOnRenderThread`.
The graphics/tick/OS mechanics are in [os-emulation-threading.md](os-emulation-threading.md) and
[frame-interpolation.md](frame-interpolation.md); this doc covers the C++ engine around them.

## `GameEngine` — boot & ownership (`Engine.cpp`)

`GameEngine::Instance` (`Engine.cpp:91`) holds a **raw `Ship::Context*`** (`Engine.h:40`) — note:
NOT a `shared_ptr` like the siblings. Constructor order (`:142`):

1. `Ship::Context::CreateUninitializedInstance("Lighthouse", "bk", "lighthouse.cfg.json")` (`:143`)
2. `InitConfiguration()` (`:150`) → `InitConsoleVariables()` (`:151`) — **order-sensitive**: config
   before console vars (else `Config::Reload` fails); console vars before the ControlDeck ctor
   (else it fails in `ShipDeviceIndexMappingManager`).
3. resolve `lighthouse.o2r` (`:154-155`, gates `portArchiveVersionMatch`)
4. `InitControlDeck(make_shared<LUS::ControlDeck>())` (`:157-159`)
5. `InitResourceManager({ lighthouse.o2r }, {}, 3, true)` (`:160`) — mounts the port archive,
   3 loader threads
6. `InitConsole()` (`:161`) + register `reset`/`quit` console commands (`:164,:173`)
7. `InitWindow(make_shared<Fast::Fast3dWindow>(...))` (`:180-181`)
8. `LighthouseGui::SetupMenu()` (`:183`); load fonts if the archive matched (`:186-192`)

**`GameEngine::Create`** (`:1021`): `new GameEngine()` → `GfxSetNativeDimensions(292,216)` (`:1026`)
→ **`RunExtract`** (the ROM-import UI, `:423`) → **`FinishInit`** (`:353`) → `PortEnhancements_Init`
→ `Anchor::Init` → `SaveManager_Init` → `ShipInit::InitAll()` / `ShipInit::Init("BOOT")` (`:1032-33`).

**`FinishInit`** (`:353`): mount `bk.o2r` (`:354-359`), mods/loose/lang (`:367-369`),
`InitLogging`/`InitCrashHandler`/**`InitEventSystem`** (`:378-385`), **`InitAudio({22000,736,2208})`**
(`:387`), `SetTargetFps(60)`/`SetMaximumFrameLatency(1)`/`SetRendererUCode(ucode_f3d)` (`:389-391`),
interpreter memoization (`:394-396`), `RegisterResourceFactories` (`:402`), `SetAltAssetsEnabled`
(`:404`).

**Teardown** (`GameEngine::Destroy`, `:1051`) is manual and order-sensitive: stop rumble, null
`lhFast3dWindow` **before** the context, clear ref cache, `UnloadResources("*")`, null `context`.

## C ↔ C++ interop

Three mechanisms (same family as the siblings):

1. **`extern "C"` boundary** — the port exposes a `GameEngine_*` / `OTR*` / `port_*` C API the
   decomp calls (asset load, audio, dimensions, the `Graphics_PushFrame`/`port_runOnRenderThread`/
   `port_pipelineSyncPoint` seam in `Game.cpp`); port `.cpp` wraps decomp headers in `extern "C" {
   #include … }`.
2. **The event system** — decomp C fires `CALL_EVENT` / `CALL_CANCELLABLE_EVENT`; port C++
   listeners react/cancel. Events + hooks live under `src/port/Enhancements/Events/`
   (`Hooks/Events.h`), registered via `RegisterShipInitFunc`. `mainLoop` fires
   `CALL_EVENT(GameFrameUpdate)` (`init.c:213`); `OnMapLoad` drives the thread5 sync
   (`Game.cpp:178-185`). **Note:** this is Lighthouse's **own** event system, distinct from LUS's
   new `ship/events` bus (which Lighthouse only initializes for the EventDebugger — see
   [libultraship-integration.md](libultraship-integration.md#new-lus-482-subsystems)).
3. **CVars** — LUS's string-keyed store (`<libultraship/bridge/consolevariablebridge.h>`), reached
   directly from decomp `.c`. Enhancements/cheats are CVar toggles; persisted to
   `lighthouse.cfg.json` in the run dir. `ShipInit` reactive init re-runs a bound function when its
   CVar changes (no restart).

## Enhancements / Rando / DevTools (brief)

- **`Enhancements/`** — the fork's feature surface: `Cheats/`, `Fixes/` (bug fixes),
  `Restorations/` (beta/cut content), `Backports/` (features from newer BK-related work),
  `Camera/`, `Cutscenes/`, `Modes/`, `Gameplay/`, `Save/`, `Trackers/`. Each self-registers via
  `RegisterShipInitFunc` and gates behavior behind a CVar + event listener.
- **`Rando/`** — a full randomizer: `Logic/` (region access), `StaticData/`, `CheckTracker/`,
  `CustomObject/`, `ObjectBehavior`/`MiscBehavior`.
- **`DevTools/`** — `ThreadWatchdog` (deadlock diagnostic, see
  [os-emulation-threading.md](os-emulation-threading.md#6)), `EventDebugger` (the sole consumer of
  LUS's new event bus), `DevSequences`, `OcclusionDebug`.
- **`UI/`** — `LighthouseModMenuWindow` (mod discovery/enable), `Menu` (audio backend etc.),
  `Notification`; `DeveloperTools/`.

## Provenance / fork facts

- Upstream is HarbourMasters/Lighthouse (lead Malkierian); the port tag `1.0.0` released
  2026-07-31. Bill's fork is the **`bill`** branch (`origin` = a Pi mirror). The delta over
  `develop` is tiny (docs + this reference set); the substantive engineering is upstream.
- Bootstrap milestones are legible in git history (`git log --reverse`): early commits are decomp
  progress (`core2/gczoombox.c done`, `code_87E30.c progress`, `80%`), consistent with a
  reverse-engineering effort that grew a port layer on top. The decomp is ~⅓–½ still `func_`/`D_`
  named — see [decomp-map.md](decomp-map.md#naming-state-partially-decompiled).
