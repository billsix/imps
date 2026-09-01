# libultraship — config, console variables, logging

> **Pinned:** libultraship **1.3.1-482**
> (`2917d0f4fe62c579174561dcd34f327c9410bb72`, 2026-07-29 —
> BanjoKazooie's pin; direct descendant of 1.3.1-397, 85 commits).
> Updated 2026-09-01, iteration 16 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## Config — JSON settings file

`Ship::Config`: nlohmann JSON, `dump(4)`, port-chosen app-dir path.
App dir: `SHIP_HOME` Apple/Linux only (`Context.cpp:553-572`),
`NON_PORTABLE` → `SDL_GetPrefPath`, else `"."`.

- The dual nested/flattened model survives with both defects:
  **`Nested()` unflattens the whole document on every get**
  (`Config.cpp:44`) and the dotted-path walk keeps the current subtree
  on a missing component (`:46-52`).
- **`Reload` hardened**: both JSONs pre-initialized to empty objects,
  parse failures logged (`Config.cpp:204-212`) — the old
  "fresh install leaves `mNestedJson` null" nuance is obsolete.
- **Backend persistence moved OUT of Config (#1097)**: audio backend
  get/set (and the `"pulse"`→SDL migration) now live on `Ship::Audio`
  (`Audio.cpp:66-105`, migration `:75-78`); window-backend persistence
  on `Ship::Window` (`Window.cpp:70`, `:125-126`). Config no longer
  knows about backends.
- **NEW consumer of the config file: the Keystore** (scripting builds)
  — trusted ed25519 keys persist under a top-level `"Keystore"` node
  (`Keystore.cpp:59-86`; see `resource-system.md`).
- `SetBlock`/`EraseBlock` still `Save()` internally
  (`Config.cpp:131-186`); `GetArray`/`SetArray` still dead;
  `mIsNewInstance` still write-only. `RegisterVersionUpdater` is the
  method (`Config.h:188`); the doxygen still cites the nonexistent
  `RegisterConfigVersionUpdater` (`Config.h:19`).

## CVars

- Union storage unchanged, **and its bugs survive**: `SetString`/
  `CopyVariable` set `Type` then `free()` the possibly-reinterpreted
  `String` bits (`ConsoleVariable.cpp:117-121`, `:228-232`);
  `LoadLegacy` double-`strdup` leak (`:370`).
- **Lookup is allocation-free (#1022)**: transparent hash/equal
  (`TransparentStringHash`, `ConsoleVariable.h:199-211`) — `Get(const
  char*)` builds no temporary string.
- `cmake/cvars.cmake` is now **24 macros**; new:
  `CVAR_ALLOW_BACKGROUND_INPUTS` (`gAllowBackgroundInputs`, used in
  `Fast3dGui.cpp:92,100` + `gfx_dxgi.cpp:513`) and
  `CVAR_SCRIPT_SAFE_LEVEL` (`gScriptSafeLevel` — **zero code
  references** at this pin). Grep for macros, not name literals.
- Bridge: `CVarClearBlock`/`CVarCopy` defined
  (`consolevariablebridge.cpp:73,77`); **`CVarExists` still declared,
  never defined** (`consolevariablebridge.h:138`) — link error, now
  even exported.

## Logging

`Context::InitLogging`:

- Levels still parameters (debug/warn defaults,
  `include/ship/Context.h:196-197`); debug = synchronous `"multi_sink"`
  flush-on-trace (`Context.cpp:172-174`); release = async
  overflow-block flush-on-info — now fed by a **Context-owned**
  `mLogThreadPool` (`:176-178`) instead of the global spdlog pool. Yet
  `spdlog::init_thread_pool(8192, 1)` **still runs unconditionally**
  (`:128`), so the global pool is now unused in *both* build types.
- Console sink level explicit (`:163`); sinks/pattern/rotation
  unchanged (10 MB × 10, `:167`).
- **Teardown reworked (#1103)**: no `spdlog::shutdown()`; `~Context`
  tears members down explicitly, then `mLogger->flush(); mLogger =
  nullptr;` — an **unconditional deref**: a Context destroyed before
  `InitLogging` crashes (`Context.cpp:64-68`).
- `lusprintf` still never calls `va_end`
  (`src/libultraship/log/luslog.cpp:15-22`).

## Console (command registry)

`Console::Init()` still empty (`Console.cpp:15-16`); all 7 commands
(`set get help clear unbind bind bind-toggle`) still registered by the
GUI's `ConsoleWindow::InitElement` (`ConsoleWindow.cpp:304-321`).
Internals cleaned (#1067): `Run` single-`find`, no `CommandEntry` copy
(`Console.cpp:38-45`); **`GetCommand` now throws `std::out_of_range`**
instead of default-inserting (`:70-76`).

## Test coverage note

The new gtest suite covers **none** of Config, CVars, Console, or
logging (`tests/` covers utils/resource/events/audio-decoder).
