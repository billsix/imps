# libultraship — config, console variables, logging

> **Pinned:** libultraship **1.3.1-399**
> (`e0c1b1fc35e3b4143f9417b21c7ea6e75ccfb94b`, 2026-02-20). Updated
> 2026-09-01, iteration 14 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

## Config — JSON settings file

`Ship::Config` (`include/ship/config/Config.h`): nlohmann JSON,
`dump(4)` pretty-printed, at the port-chosen app-dir-relative path.
App dir: `SHIP_HOME` (honored on **Apple/Linux only** —
`Context.cpp:471-485`), `NON_PORTABLE` → `SDL_GetPrefPath`, else `"."`.

The dual nested/flattened model survives with both 1.4.2 defects:
**`Nested()` still unflattens the whole document on every get**
(`Config.cpp:47`), and the dotted-path walk still keeps the current
subtree when a component is missing (`:49-56`) — partially-missing keys
can return the wrong node. Fresh-install nuance: `Reload` leaves
`mNestedJson` null, but `ConsoleVariable::Load`'s index into it is now
benign (nlohmann promotes null to object, iterates zero times); the
old `ControlDeck::LoadSettings` co-victim no longer exists.

NEW API since 1.4.2: `Erase`, `EraseBlock`, `SetBlock`, `Copy`,
`Contains`, `GetNestedJson` — note `SetBlock`/`EraseBlock` each call
`Save()` internally, so a block write hits disk immediately.
`GetArray`/`SetArray` still dead (zero callers).

**`ConfigVersionUpdater` survives unchanged in shape** — but the
registration method is now **`RegisterVersionUpdater`** (the `Config`
infix is gone; the doxygen at `Config.h:20` still cites the old name —
an upstream doc bug). Zero updaters registered inside LUS; purely a
port hook. Migration at read: a config carrying `"pulse"` as audio
backend is rewritten to SDL (`Config.cpp:240-241`).

## CVars — union storage, build-time-configurable names

`CVar` is now a tagged **union** of
`Integer/Float/String(char*)/Color/Color24`
(`include/ship/config/ConsoleVariable.h:13-27`), strings manual
`strdup`/`free`. Persistence unchanged (`CVars.<name>` in the config
JSON, colors exploded into `.R/.G/.B/.A` + `.Type`).

**The biggest config-side surprise: CVar names are CMake macros.**
`cmake/cvars.cmake` defines 22 cache variables pushed as
`add_compile_definitions` string macros — `CVAR_VSYNC_ENABLED`
(= `"gVsyncEnabled"`), `CVAR_MSAA_VALUE`, `CVAR_INTERNAL_RESOLUTION`,
`CVAR_Z_FIGHTING_MODE`, `CVAR_AUDIO_CHANNELS_SETTING`, … plus two
**prefixes** concatenated at use sites: `CVAR_PREFIX_CONTROLLERS`
(`"gControllers"`) and `CVAR_PREFIX_ADVANCED_RESOLUTION`
(`"gAdvancedResolution"`). Consequences: a port can rename every engine
CVar from CMake, and **grepping the source for `"gStatsEnabled"` finds
nothing** — grep for the macro. `gAltAssets` is gone from the library
entirely (`resource-system.md`).

C bridge additions vs 1.4.2: `CVarClearBlock`, `CVarCopy`, and
`CVarExists` — **which is declared but never defined** (link error;
`consolevariablebridge.h:33`). `CVarGet` returning the
`shared_ptr<Ship::CVar>` remains C++-only.

**Union bugs at this pin:** `SetString`/`CopyVariable` test-and-`free()`
the `String` member after setting `Type` — if the CVar previously held
a number/color, that `free()` runs on reinterpreted value bits
(`ConsoleVariable.cpp:117-121`, `:228-232`). `LoadLegacy` double-strdups
and leaks (`:370`).

## Logging — spdlog, split sync/async

`Context::InitLogging` (`src/ship/Context.cpp:97-167`):

- **Log levels are now parameters** with defaults — debug builds
  `spdlog::level::debug`, release `warn` (`include/ship/Context.h:70-71`).
- **Debug builds get a plain synchronous logger** (`"multi_sink"`,
  `flush_on(trace)`); release gets the async logger (overflow block,
  `flush_on(info)`). `init_thread_pool(8192, 1)` still runs
  unconditionally even in debug where nothing uses it.
- Sinks unchanged: stdout color (debug Win32 re-points stdio via
  `AllocConsole`), rotating `logs/<Name>.log` 10 MB × 10. Same pattern.
  `spdlog::shutdown()` still last in `~Context`.
- The C shim lives at `src/libultraship/log/luslog.cpp`; `lusprintf`
  **still never calls `va_end`** (`:15-22`).

## Console (command registry)

`Console::Init()` is still empty (`src/ship/debug/Console.cpp:14-15`);
all commands come from the GUI's `ConsoleWindow::InitElement`
(`ConsoleWindow.cpp:304-317`) — no GUI, no commands. Command set:
`set`, `get`, `help`, `clear`, `bind`, `bind-toggle`, **`unbind`**
(replacing 1.4.0's `binding-clear`).
