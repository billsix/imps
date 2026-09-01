# libultraship — config, console variables, logging

> **Pinned:** libultraship tag **1.1.0**
> (`04ef63c74270dfe9df458bd8335aac7a7097468a`, 2023-06-10). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## Config — JSON settings file

`LUS::Config` (`src/config/Config.h:11`): nlohmann JSON, pretty-printed,
at app-dir-relative path chosen by the game via
`Context::CreateInstance`. App dir = `$SHIP_HOME` on Linux/macOS, else
`"."`.

Implementation model worth knowing: it keeps BOTH a nested and a
flattened JSON; **writes** go to the flattened form via JSON-pointer
keys (`"Window.Backend.Id"` → `/Window/Backend/Id`), **reads** call
`Nested()`, which **unflattens the entire document on every single
get** (`Config.cpp:46`) — startup does many full unflattens. The dotted
path walk also *keeps the current subtree* when a component is missing
instead of returning null, so partially-missing keys can return the
wrong node.

Default handling changed in 1.1.0: `Context::CreateDefaultSettings`
(which bulk-seeded 640×480 @(100,100), F11 fullscreen key, etc. — and
whose seeded `Window.GfxBackend`/`GfxApi` keys never matched what
`GetWindowBackend` reads) was REMOVED; defaults now come from the
fallback arguments at each read site. In its place, 1.1.0 adds **config
migrations**: `ConfigVersionUpdater` (`src/config/Config.h`) — subclass
it, implement `Update(Config*)`, register via
`RegisterConfigVersionUpdater`, and `RunVersionUpdates()` applies each
updater whose version exceeds the file's `ConfigVersion` key, bumping
the key as it goes.

**Fresh-install bug:** with no config file, `Reload` returns early and
`mNestedJson` stays null; `ConsoleVariable::Load` and
`ControlDeck::LoadSettings` immediately index into it.

Audio/window backend persistence lives here too
(`Window.AudioBackend` = "wasapi"/"pulse"/"sdl";
`Window.Backend.Id`+`.Name`). `GetArray`/`SetArray` are protected
templates with zero callers — dead.

## Console variables (CVars) — present at 1.0.0

`LUS::ConsoleVariable` (`src/config/ConsoleVariable.h:23`): a
`map<string, shared_ptr<CVar>>` where `CVar` is a fat struct holding
all five types (`Integer, Float, String, Color(RGBA), Color24(RGB)`).
Get/Set/Register triples per type; `Register*` = set-if-absent.

Persistence: `Save()` writes every CVar under `CVars.<name>` into the
Config JSON (colors exploded into `.R/.G/.B/.A/.Type` sub-keys);
`Load()` walks `CVars` recursively. A **legacy migration** reads a
pre-JSON `cvars.cfg` (key=value, `#RRGGBBAA` colors) and deletes it
after import (`ConsoleVariable.cpp:262-309`).

The C bridge (`CVarGetInteger/Float/String/Color/Color24`, the Set/
Register triples, `CVarClear`, `CVarLoad`, `CVarSave`) is the busiest
game-facing API in LUS — see `bridge-api.md`. `CVarGet` (returning the
`shared_ptr<CVar>`) is C++-only.

CVar names observed in-library at this tag (all game-namespace `g*`):
`gAltAssets`, `gSimulatedInputLag`, `gOpenMenuBar`, `gControlNav`,
`gEnableMultiViewports`, `gTextureFilter`, `gLowResMode`,
`gStatsEnabled`, `gControllerConfigurationEnabled`, `gConsoleEnabled`,
`gSdlWindowedFullscreen`, `gSwitchPerfMode` — the CVAR_PREFIX macro
system of later versions does not exist yet.

## Logging — spdlog 1.11.0, async

Wired in `Context::InitLogging` (`src/Context.cpp:100-175`):

- Async logger, thread pool (8192, 1 thread), overflow policy
  **block**; registered as spdlog's default logger.
- Sinks: stdout color (skipped on release Win32/WiiU; on debug Win32 it
  `AllocConsole()`s and re-points stdio), rotating file at
  `logs/<Name>.log` (10 MB × 10, name = the game's name passed to
  `CreateInstance`).
- Pattern `[%Y-%m-%d %H:%M:%S.%e] [%@] [%l] %v`.
- `spdlog::shutdown()` runs last in `~Context` — the reason the
  destructor nulls subsystems in explicit order.

C shim for game code: `luslog(file, line, level, msg)` and
`lusprintf(file, line, level, fmt, ...)` (`src/log/luslog.cpp`) +
`LUSLOG_TRACE..CRITICAL` macros. Levels cast raw to
`spdlog::level_enum`. Bug: `lusprintf` never calls `va_end`.

## Console (command registry)

`LUS::Console` (`src/debug/Console.h:31`) — commands =
`function<int32_t(shared_ptr<Console>, vector<string> args, string*
output)>` with typed argument metadata. `Run()` splits on spaces.
**`Console::Init()` is empty**; every built-in command (`bind`,
`bind-toggle`, `help`, `clear`, `set`, `get`) is registered by the
GUI's `ConsoleWindow` (`src/window/gui/ConsoleWindow.cpp:231-243`) —
no GUI, no commands.
