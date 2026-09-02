# Reference: The port layer (`src/port/`)

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference. The C++ glue that boots the decomp on libultraship, drives the frame,
bridges C↔C++, and adds the menu/cheats/hooks/rando. Read before touching `src/port/`.
Companions: [architecture-overview.md](architecture-overview.md),
[libultraship-integration.md](libultraship-integration.md). The cheat/enhancement *recipe*
is in the project's [`CLAUDE.md`](../../../n64/SuperMario64/CLAUDE.md).*

## Subdir map

| Path | Role |
|---|---|
| `Engine.{cpp,h}` | `GameEngine` singleton: LUS ownership, frame pump, C API, asset/audio tables |
| `Game.cpp` | `main()`, `push_frame()`, `exec_display_list` graphics seam |
| `ui/` | ImGui menu: `GhostshipMenu*`, widget builder, `cvar_prefixes.h`, `UIWidgets` |
| `hooks/` | EventSystem (event bus): `impl/`, `list/` catalog, `ui/EventDebugger` |
| `mods/` | Port gameplay mods: `PortEnhancements`, `achievements/`, `BetterLevelSelect` |
| `Rando/` | Full randomizer: logic, trackers, spoiler, static data |
| `importer/` | N64→O2R resource factories (anim, audio, dialog, movtex, painting…) |
| `interpolation/` | Frame interpolation (60→N fps) matrix stack |
| `console/` | `DevConsole` — registers LUS console commands |
| `data/` | Save (`Saves.cpp`, `SaveConversion.h`) |
| `GBIMiddleware.cpp` | GBI macro interception (`gSPDisplayList/Vertex`, gfx patching) |
| `GeoLayoutParser`, `util/GraphNode` | decomp geo/graph adapters into Fast3D |

## Entry & frame pump

- `main()` / `SDL_main()` — `Game.cpp:29-44`. `GameEngine::Create` → `alloc_pool` →
  `audio_init` → `sound_init` → `thread5_game_loop()` → `while (WindowIsRunning()) push_frame()`.
- `GameEngine::Create` — `Engine.cpp:802`: `new GameEngine()` (ctor `:125` builds Ship
  context, ControlDeck, ResourceManager, `Fast3dWindow`, calls `GhostshipGui::SetupMenu()`),
  then `RunExtract()` (ROM extraction/verify UI loop, `:351`), then `FinishInit()` (`:222` —
  registers ~25 resource factories, inits audio, `DevConsole_Init`, `PortEnhancements_Init`,
  `ShipInit::InitAll`).
- `push_frame()` — `Game.cpp:22`: `StartAudioFrame` → `StartFrame` (`:821`, drains keyboard
  scancodes) → **`thread5_iteration()`** (one decomp tick) → `EndAudioFrame`.
- Graphics: `exec_display_list` (`Game.cpp:18`) → `ProcessGfxCommands` (`Engine.cpp:1000`) →
  interpolation → `RunCommands` → Fast3D window. Audio: dedicated `HandleAudioThread`
  (`Engine.cpp:851`) + condition-variable handshake via Start/EndAudioFrame.
- **Gotcha:** `GameEngine_Malloc`/`Free` (`Engine.cpp:1411`) is a *leak-tracked vector with
  linear-scan free*, distinct from the decomp `main_pool` allocator (`Game.cpp:12`).

## CVar system (end to end)

The fork's cheats/enhancements are all CVars. Flow:

1. **Name macros** — `ui/cvar_prefixes.h`: `CVAR_CHEAT(v)` → `CVAR_PREFIX_CHEAT "." v`,
   `CVAR_ENHANCEMENT(v)` → `CVAR_PREFIX_ENHANCEMENT "." v` (`:7-8`). Also `CVAR_SETTING`,
   `CVAR_WINDOW`, …
2. **Prefix strings come from CMake, not a header** — `cmake/ghostship-cvars.cmake` injects
   `CVAR_PREFIX_CHEAT="gCheats"`, `CVAR_PREFIX_ENHANCEMENT="gEnhancements"` via
   `add_compile_definitions`. So `CVAR_CHEAT("InfiniteHealth")` == the literal
   `"gCheats.InfiniteHealth"`. **Grepping C++ for `#define CVAR_PREFIX_CHEAT` finds
   nothing; building outside CMake leaves these undefined.**
3. **`gCheats` / `gEnhancements` are string namespaces, NOT C++ structs.** The store is
   libultraship's flat string-keyed CVar table (`CVarGetInteger(name,default)` /
   `CVarSetInteger`) from `<libultraship/bridge/consolevariablebridge.h>`. (The root
   CLAUDE.md's "resolves to `gCheats.Name`" means the config *key*, not a member access.)
4. **Persistence** — config file `ghostship.cfg.json` in the run dir (`Engine.cpp:126`;
   CLAUDE.md/README spell it `Ghostship.cfg.json` — same file, case differs). Menu writes
   auto-persist. Deleting the file = reset to defaults.
5. **Read at gameplay sites** — decomp `.c` calls `CVarGetInteger("gCheats.X", 0)` directly;
   the file needs `#include <libultraship/bridge/consolevariablebridge.h>` (not transitive).
6. **Set from menu** — a widget bound `.CVar(...)` calls `CVarSetInteger` on toggle, then
   fires `ShipInit::Init(cvarName)` (see reactive init below).

## ImGui menu (`ui/`)

- `GhostshipMenu` subclasses LUS `Ship::Menu` (`ui/GhostshipMenu.h:11`). Registered by
  `GhostshipGui::SetupMenu()` (`GhostshipGui.cpp:46`); other windows (console, achievements,
  event debugger, object viewer, save editor, input editor, rando trackers) in
  `SetupGuiElements()` (`:56-115`).
- Content built in `GhostshipMenu::InitElement()` (`GhostshipMenu.cpp:122`): `AddMenuSettings
  / AddMenuEnhancements / AddMenuRando / AddMenuAchievements / AddMenuDevTools`, each its own
  file (`GhostshipMenuEnhancements.cpp` = cheats + enhancements).
- **Builder pattern:** `AddWidget(WidgetPath&, name, WidgetType) → WidgetInfo&`
  (`GhostshipMenu.cpp:63`) returns a reference for fluent chaining:
  `.CVar(...).RaceDisable(...).Options(CheckboxOptions().Tooltip(...)).Callback(...)`
  (example `GhostshipMenuEnhancements.cpp:40`). Widget types
  (`WIDGET_CVAR_CHECKBOX/COMBOBOX/SLIDER_*`, `WIDGET_SEPARATOR_TEXT` = section heading,
  `WIDGET_BUTTON`, `WIDGET_WINDOW_BUTTON`, `WIDGET_COLOR_PICKER`) in `ui/MenuTypes.h`;
  render/CVar-write in `ui/UIWidgets.cpp`. `WidgetPath{section, sidebar, SECTION_COLUMN_1}`.
- **Gotcha:** the menu is constructed twice (ctor `GhostshipGui.cpp:48` and again in
  `SetupGuiElements` `:76`); the second, richer instance wins. There is **no**
  `GameMenuBar.cpp` — the bar is LUS's `GuiMenuBar` + `Ship::Menu`.

## Hooks = an EventSystem (event bus, NOT function hooking)

*This is the primary way the port overrides decomp behavior. Full how-to in
Ghostship's own `wiki/EventSystem.md` (in the checkout).*

- Core: `hooks/impl/EventSystem.{h,cpp}` — a static singleton
  (`EventSystem::Instance`, `EventSystem.cpp:7`) holding a
  `unordered_map<EventID, EventRegistration>` of priority-sorted listeners.
- Macro DSL (`EventSystem.h:57-88`, compiles in **both C and C++**): `DEFINE_EVENT(Name,
  fields…)`, `REGISTER_EVENT`, `REGISTER_LISTENER(evt, cb, priority)`, and fire macros
  `CALL_EVENT`, `CALL_CANCELLABLE_EVENT` (runs its `{ }` block only if uncancelled),
  `CALL_CANCELLABLE_RETURN_EVENT`.
- **Cancellation is the override mechanism:** a listener sets `event->cancelled = true` and
  the decomp's guarded block is skipped. E.g. Infinite Health cancels `PlayerHealthChange`
  (`PortEnhancements.cpp:56`; decomp fires it at `mario.c:1503,1516,1531`).
- Event catalog in `hooks/list/`: `EngineEvent.h` (`GameFrameUpdate`,
  `RenderPauseCourseOptions`, `LevelScript*`, `OnGameFileLoad/Save`, `EntityDistanceRender`…),
  `PlayerEvent.h` (`PlayerHealthChange`, `PlayerLivesChange`, `PlayerDeath`,
  `PlayerExecuteAction`, + rando events), `GameEvent.h` (`CapSwitchActivated`, `BossDefeated`,
  `MusicChanged`, `GameEnded`…). All registered in `PortEnhancements_Register()`
  (`PortEnhancements.cpp:100`); listeners in `PortEnhancements_Init()` (`:51`).
- `hooks/ui/EventDebugger` — ImGui window listing events + `__FILE__:__LINE__` caller
  metadata + hit counts (recorded at each `CALL_EVENT`, `EventSystem.cpp:51`).
- **Key limitation:** you can only override where a `CALL_*_EVENT` fire site *exists*. To
  hook new decomp behavior you must add a fire site in the decomp first, then a listener.

## `ShipInit` reactive init

`ShipInit.hpp`: `RegisterShipInitFunc(fn, {cvarPaths})` registers `fn` under `"*"` (run once
at boot via `ShipInit::InitAll()`, `Engine.cpp:348`) **and** under each CVar path. When a
menu widget writes a CVar, `UIWidgets.cpp` calls `ShipInit::Init(cvarName)` to re-run the
bound init — so toggling a CVar re-patches/reconfigures **without a restart**. The
`CVAR_INT_SHIP_INIT` macro (`GhostshipMenuEnhancements.cpp:3`) does set+init together.

## mods / Rando / console (brief)

- **`mods/PortEnhancements.{cpp,h}`** — central registry: registers every event + the
  built-in listeners (Infinite Health/Lives, PauseExitWhenever, DisableLakituCutscene,
  DisableDrawDistance), does GBI display-list patching (`PatchSetupDList`, `:25`, via
  `ResourceMgr_PatchGfxByName`), calls `Rando::Init()` and `LoadGuiTextures()`.
- **`mods/achievements/`** — save-backed tracking (`AchievementSaveData`, 100 entries) +
  menu + window. **`mods/BetterLevelSelect`** — enhanced named level-select (EN+JP),
  self-registers via a global instance.
- **`Rando/`** — large randomizer: `Logic/Regions/*` (per-level access logic,
  self-registering via `RegisterShipInitFunc`), `StaticData/` (Checks/Items/Entrances/
  Options), `Spoiler/`, tracker windows, behavior overrides via hook events. Save data hangs
  off `gSaveBuffer.files[n]->shipSaveData` (`Rando.h:21`). Entry `Rando::Init()`.
- **`console/DevConsole`** — thin registrar; currently only registers `reset`
  (`warp_special(-8)`, guarded on play mode, `DevConsole.cpp:33`). The console *window* is
  LUS's `Ship::ConsoleWindow`.

## The three C↔C++ interop mechanisms

1. **`extern "C"` boundary** — port exposes `GameEngine_*` / `OTR*` C API (`Engine.h:86-134`,
   defined `Engine.cpp:1043+`); port `.cpp` wraps decomp headers in `extern "C" { #include … }`.
2. **EventSystem** (above) — decomp C → port C++ callbacks. Replaces SoH's `GameInteractor`
   (which does **not** exist in this fork — grep-negative).
3. **CVars** — shared string-keyed store (above).
