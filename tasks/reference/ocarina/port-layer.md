# Reference: The port layer (`soh/soh/`)

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

*Standing reference. The C++ glue that boots the OoT decomp on libultraship, drives the frame, and
bridges C↔C++. Read before touching `soh/soh/`. Companions:
[architecture-overview.md](architecture-overview.md), [libultraship-integration.md](libultraship-integration.md),
[enhancements-gui-rando.md](enhancements-gui-rando.md) (GameInteractor + the feature layer),
[frame-interpolation.md](frame-interpolation.md).*

## Entry & main loop — the decomp's N64 boot, with hardware hollowed out

The decomp keeps its original N64 boot structure; the port stubs the hardware and re-implements the
"threads" as ordinary calls.
- **`main()` / `SDL_main()`** — `soh/src/code/main.c:59` / `:47`. Sequence: `GameConsole_Init` →
  **`InitOTR(argc,argv)`** (LUS/port bring-up) → `CrashHandlerRegisterCallback` → `BootCommands_Init`
  → `Heaps_Alloc` → **`Main(0)`** → `DeinitOTR` → `Heaps_Free`.
- **`Main(void*)`** — `main.c:74` (the decomp's original proc): inits N64 objects (IrqMgr, Sched,
  AudioMgr, PadMgr) — mostly **stubbed** — then calls **`Graph_ThreadEntry(0)` inline** (`:141`), not
  as an OS thread (`osCreateThread`/`osStartThread` are no-ops).
- **Frame loop** (`soh/src/code/graph.c`): `Graph_ThreadEntry` (`:519`) = `while (WindowIsRunning())
  RunFrame();`. **`RunFrame` (`:438`) is a hand-written coroutine** (`runFrameContext.state`, `goto
  nextFrame`): per frame it runs `Graph_StartFrame` → `PadMgr_ThreadEntry` → `Graph_Update` (one
  decomp game-state update, builds an N64 display list) → `Graph_ProcessGfxCommands` (hands it to the
  port), then returns with `state=1` and resumes next iteration. See
  [decomp-map.md](decomp-map.md#the-per-frame-driver--a-coroutine-not-a-blocking-loop).

**The three port bridge functions** (`soh/soh/OTRGlobals.cpp`, declared C-side in `OTRGlobals.h`):
- `Graph_StartFrame()` (`:1670`) — reads the LUS window's last keyboard scancode and dispatches
  hardcoded hotkeys: **F5/F7 save-state save/load, F6 slot cycle** (`gSaveStateMgr`), F9 TTS, **TAB =
  alt-assets toggle**.
- `Graph_ProcessGfxCommands(Gfx*)` (`:1804`) — the **C→C++ render handoff**: signals the audio thread,
  computes interpolation cadence, then `RunCommands` (`:1776`) → `wnd->DrawAndRunGraphicsCommands(...)`
  into Fast3D. Full detail: [frame-interpolation.md](frame-interpolation.md),
  [libultraship-integration.md](libultraship-integration.md).
- `OTRGetPixelDepth`/`Prepare` (`:1870`/`:1879`) — depth-buffer readback (lens of truth, etc.).

## `OTRGlobals` — the central glue object

`soh/soh/OTRGlobals.cpp` (2533 lines). Singleton `OTRGlobals::Instance` (`OTRGlobals.h:48`) owns the
`Ship::Context`, SaveStateMgr, Randomizer, fonts. Three-phase bring-up:
1. **Ctor** (`:278`) — builds the LUS context via the singleton API `CreateUninitializedInstance(...,
   "shipofharkinian.json")` + `InitConfiguration/InitConsoleVariables/InitControlDeck/
   InitResourceManager/InitConsole/InitWindow`. Config file is **`shipofharkinian.json`** (not
   `cfg.json`). Full sequence in [libultraship-integration.md](libultraship-integration.md#how-soh-owns--inits-the-context-singleton-init-sequence).
2. **`Initialize()`** (`:789`) — adds `oot-mq.o2r`/`oot.o2r`, `InitLogging`, `InitCrashHandler`,
   `InitAudio({.SampleRate=32000,…})` (`:830`), then registers **every resource factory** (`:844+`).
3. **`InitOTR()`** (`:1527`) — orchestrator called from `main`: `new OTRGlobals` → `RunExtract` →
   `Initialize` → constructs the managers (`CustomMessageManager`, `ItemTableManager`,
   `GameInteractor::Instance = new GameInteractor()` `:1534`, `SaveManager`, `AudioCollection`,
   `ActorDB`, `SpeechSynthesizer`, `CrowdControl`/`Sail`/`Anchor`) → config version updaters →
   **`ShipInit::InitAll()`** (`:1601`).

- **Audio thread** — `OTRAudio_Thread()` (`:1022`), a dedicated `std::thread` woken by the gfx
  thread's condition variable each frame, **self-pumping every ~5 ms** so a slow frame can't starve
  the backend. Synthesizes PCM via decomp `AudioMgr_CreateNextAudioBuffer`, submits via
  `AudioPlayer_Play`. (This loop has hand-written drift-correction comments not in stock SoH — treat
  as possibly a local modification; verify against upstream.)

## The CVar system

- **Bridge API** (C-callable): `<libultraship/bridge/consolevariablebridge.h>` —
  `CVarGetInteger/Float/String/Color`, `CVarSet*`, `CVarRegister*` (no-op if set), `CVarClearBlock`,
  `CVarLoad`/`CVarSave` (persist to the config JSON).
- **Prefix macros** — `soh/soh/cvar_prefixes.h`: `CVAR_SETTING`, `CVAR_ENHANCEMENT`, `CVAR_CHEAT`,
  `CVAR_COSMETIC`, `CVAR_WINDOW`, `CVAR_GENERAL`, `CVAR_TRACKER*`, `CVAR_REMOTE*`. Each expands
  `CVAR_PREFIX_X "." var`.
- **Gotcha:** the `CVAR_PREFIX_*` strings are **not in any header** — they're compile definitions from
  **`CMake/soh-cvars.cmake`** (`CVAR_PREFIX_SETTING="gSettings"`, …). So `CVAR_SETTING("AltAssets")` →
  `"gSettings.AltAssets"`. **Grep for `CVAR_SETTING("AltAssets")`, never the resolved string.**
- **Flow:** a menu widget calls `CVarSetInteger` → gameplay reads `CVarGetInteger(CVAR_...("Foo"),
  default)` at the site → `CVarSave` writes `shipofharkinian.json`. Config **version updaters**
  (`SOH::ConfigVersion1..7Updater`, `config/ConfigUpdaters.cpp`) migrate old JSON.

## Resource / OTR glue (decomp DMA → LUS ResourceManager)

The decomp thinks it's DMA-ing ROM segments; the port intercepts and serves from the ResourceManager.
- **`GbiWrap.cpp`** — the N64 GBI macros (`gSPSegment`, `gSPDisplayList`, `gSPVertex`,
  `gDPSetTileSize*`) are **redefined as real functions**; each runs `ResourceMgr_OTRSigCheck(ptr)` and,
  if the "pointer" is a `__OTR__` path string, resolves it via `ResourceMgr_LoadGfxByName`/etc. before
  the real `__gSP*`. See [libultraship-integration.md](libultraship-integration.md#graphics-handoff--display-lists--fast3d).
- **`ResourceMgr_OTRSigCheck`** (`ResourceManagerHelpers.cpp:580`) — returns 1 iff low bit clear and
  bytes 0-6 are `"__OTR__"`. The core trick distinguishing a path string from a real pointer.
- **`ResourceManagerHelpers.cpp`** (688 lines) — the big `extern "C"` `ResourceMgr_*` bridge
  (`Load{Gfx,Vtx,Col,Anim,Skeleton,Seq,AudioSample}ByName`, `LoadDirectory` precache, MQ handling,
  alt-assets, `ResourceMgr_PatchGfxByName` for cosmetics, Link-tunic DL swapping).
- **OTR-ified loaders** (replace raw-ROM-struct parsers): `z_play_otr.cpp` (`OTRPlay_SpawnScene`
  loads a `SOH::Scene` resource), `z_scene_otr.cpp` (the scene-command interpreter, casts parsed
  `SOH::ISceneCommand*` into decomp structs), `z_message_OTR.cpp` (message tables from `SOH::Text`).
- **`gu_pc.c`** — plain-C reimplementation of the N64 `gu*` fixed-point matrix helpers (no LUS dep).

## Save / extraction / networking

- **`SaveManager.cpp`** (2827 lines, `SaveManager::Instance`) — a **section-based JSON save system**
  (`nlohmann::json`): sections `base/randomizer/sohStats/entrances/scenes/trackerData` register in the
  ctor; **versioned** `AddLoadFunction("base", 1..4, …)` handlers migrate old saves; saves run on a
  1-thread `BS::thread_pool`. Decomp SRAM read/write bridged by `Ctx_ReadSaveFile`/`Ctx_WriteSaveFile`
  (`OTRGlobals.cpp:1951/1955`).
- **`Extractor/`** — the ROM-extraction UI (`Extract.cpp`), validates a ROM (size/CRC/decompress),
  drives ZAPD into an `.o2r`; invoked by `OTRGlobals::RunExtract` (`:398`). See
  [asset-pipeline.md](asset-pipeline.md).
- **`Network/`** — `class Network` (SDL_net TCP client with a receive thread); the base for the
  **remote-control** integrations `CrowdControl`/`Sail`/`Anchor`. "Multiplayer" here is a JSON command
  channel, not peer game-state sync. See [enhancements-gui-rando.md](enhancements-gui-rando.md).
- **`Notification/`** — transient toast overlay (`Ship::GuiWindow`).

## C++ ↔ C interop & boot infrastructure

- **`OTRGlobals.h` is the boundary contract** — a C++ half (`OTRGlobals` class, `Ship::Context*`,
  STL) and a plain-C `extern` block listing every port function the decomp may call.
- **C++→C**: the port calls decomp funcs declared `extern "C"` (`PadMgr_ThreadEntry`,
  `AudioMgr_CreateNextAudioBuffer`, `Play_InitScene`). **C→C++**: every port function the decomp
  invokes is `extern "C"` in the `.cpp` (`Graph_ProcessGfxCommands`, all `ResourceMgr_*`, all
  `GameInteractor_Execute*`). The GBI macros in `GbiWrap.cpp` replace inline macros with linked
  `extern "C"` functions.
- **`ShipInit.hpp`** — `RegisterShipInitFunc foo(fn, {paths})` registers `fn` under `"*"` (run once by
  `ShipInit::InitAll()`) and each path; `ShipInit::Init("path")` re-runs the subset when a CVar might
  have changed. How self-contained enhancement modules wire themselves in without being called
  explicitly. See [enhancements-gui-rando.md](enhancements-gui-rando.md).
- **`stubs.c`** (268 lines) — empty-body impls of every libultra HW function the decomp links against
  (`osCreateThread`/`osStartThread` no-ops — why "threads" run inline; cache ops; `osPfs*`; RSP/RDP
  task submission). Also defines global state the decomp expects (framebuffers, `osMemSize=1 GB`,
  `osTvType=NTSC`, `gDmaDataTable`).

## Newcomer trip-hazards

- **Pointers that are actually strings.** Any GBI segment/DL/vertex/texture pointer may really be a
  `"__OTR__objects/..."` path; `ResourceMgr_OTRSigCheck` is the gate. Dereferencing one as data gives
  garbage — resolve it first.
- **CVar strings don't exist as literals** — `CVAR_PREFIX_*` are `-D` defs from CMake. Grep the macro
  call, not the resolved string.
- **The decomp threads are fiction** — `osCreateThread`/`osStartThread` are no-ops; `Main` calls
  `Graph_ThreadEntry` inline. The only real extra threads are the OTR audio thread + SaveManager's
  1-thread pool.
- **`RunFrame` is a coroutine-by-hand** (`graph.c:438`), not a `for`-loop.
- **`Graph_ProcessFrame` (`GbiWrap.cpp:7`) is dead code** — don't follow it.
- **Config filename is `shipofharkinian.json`.**
- **Behavior overrides go through `GameInteractor_Should(VB_…)`**, not `#ifdef`s (~178 decomp
  branches) — see [enhancements-gui-rando.md](enhancements-gui-rando.md).
