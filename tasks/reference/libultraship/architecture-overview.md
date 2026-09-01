# libultraship — architecture overview

> **Pinned:** libultraship tag **1.1.0**
> (`04ef63c74270dfe9df458bd8335aac7a7097468a`, 2023-06-10). Authored
> 2026-09-01 as iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above — if they
> differ, the crawl has advanced and this doc state describes an older
> tag (each tag's state is a separate imps commit).

**What LUS is at this pin:** a static C++20 library (`libultraship.a`) that
gives an N64 decompilation "somewhere to run" — a Fast3D display-list
renderer with pluggable graphics backends, an MPQ-based (`.otr`) asset
archive + typed resource system, SDL-based audio/input, an ImGui overlay
shell, JSON config + CVars, spdlog logging, and a very thin slice of
libultra OS shims. It is consumed by `add_subdirectory` only (no
install/export rules) and was freshly de-branded from Ship of Harkinian
(the "LUS of Harkinian" comment at `src/resource/ResourceType.h:18` and
OoT-only CRCs in `src/resource/GameVersions.h` are leftovers).
Namespace: `LUS`. No version constant exists in code — the tag is the
only version identifier.

## The three-layer picture

1. **`include/libultraship/`** — the nominal public surface:
   `libultraship.h` pulls `libultra.h` (27 reimplemented N64 SDK
   headers), `bridge.h` (C-linkage bridges), `color.h`, `luslog.h`, and
   (C++ only) `classes.h`. Mostly forwarding shims into `src/` — the
   boundary is a naming convention, not an enforcement, because `src/`
   itself is a PUBLIC include dir (`src/CMakeLists.txt:355`).
2. **`src/public/`** — the game-facing C-linkage layer: `bridge/` (six
   bridge headers) and `libultra/os.cpp` (the shims). See
   `bridge-api.md`.
3. **`src/` subsystems** — `Context` (the root), `resource/`,
   `graphic/Fast3D/`, `window/` (+ `window/gui/`), `audio/`,
   `controller/`, `config/`, `debug/`, `log/`, `utils/`, `port/`
   (Switch/Wii U only).

## `LUS::Context` — the root singleton

`src/Context.h:19`; a **weak_ptr-held singleton** (`src/Context.cpp:17`),
not a leaked global: `CreateInstance(name, shortName, configFilePath,
otrFiles, validHashes, reservedThreadCount)` (`src/Context.cpp:39`)
creates it once and **returns the shared_ptr the game must keep alive**
— dropping it destroys everything. `GetInstance()` = `mContext.lock()`.

**Init order** (`Context::Init`): logging → config → console
variables → resource manager → control deck → crash handler → console →
window → audio. (Until 1.0.1 a bulk default-settings seeding step ran
after the resource manager; 1.1.0 removed it in favor of per-read
fallbacks + the `ConfigVersionUpdater` migration system — see
`config-cvars-logging.md`.) Notes:

- `InitResourceManager` (`:185`) reads `Game.Main Archive` /
  `Game.Patches Archive` from config; a missing OTR shows a message box
  and **continues booting** with the resource thread pool permanently
  paused (`src/resource/ResourceManager.cpp:92` — "Nothing ever
  unpauses the thread pool"), so later blocking loads hang rather than
  fail fast.
- `InitControlDeck` (`:212`) only **constructs** the deck; device
  scanning happens when the game calls `osContInit()`
  (`src/public/libultra/os.cpp:27`).
- Destruction (`~Context`, `src/Context.cpp:23-37`) tears down in
  explicit reverse order so `spdlog::shutdown()` runs last; window size
  is saved to config on the way out.

## The integration pattern (how a game consumes LUS at this tag)

No sample exists in-tree; the pattern read off the code:

1. `add_subdirectory(libultraship)`, link target `libultraship`.
2. Hold `Context::CreateInstance(...)`'s return value for the process
   lifetime.
3. Call `osContInit()` (finishes controller setup) and per-frame
   `osContGetReadData()` (`src/public/libultra/os.cpp:31`, `:60`).
4. Register game resource factories via
   `ResourceLoader::RegisterResourceFactory` — LUS ships only the six
   generic types; the 15 `SOH_*` enum entries have no factories here.
5. Provide a menu bar via `Gui::SetMenuBar` and windows via
   `Gui::AddGuiWindow`.
6. Run `Window::MainLoop(gameIter)`; per frame the game calls
   `gfx_start_frame()` → build display list → `gfx_run(cmds, ...)` →
   `gfx_end_frame()` (contract in `src/graphic/Fast3D/README.md`, which
   is otherwise stale upstream text).
7. Push audio each frame via `AudioPlayerPlayFrame` — LUS never calls
   it itself; the game owns audio cadence.

Env vars: `SHIP_BIN_DIR` (Linux bundle dir), `SHIP_HOME` (Linux/macOS
data dir), both defaulting to `"."` (`src/Context.cpp:290-308`) — SoH
branding that survived the de-branding.

## The seams a port crosses

- **Graphics/asset seam:** the display list may reference assets by
  CRC64 hash or file path via OTR-specific GBI opcodes; the interpreter
  resolves them through the resource system (and self-modifies the
  display list with resolved pointers). See `fast3d-renderer.md` §OTR
  opcodes.
- **Bridge seam:** C-linkage functions for resources, audio, controller
  blocking, window metrics, CVars, crash callback (`bridge-api.md`).
- **libultra seam:** only controller init/read, `osGetTime`/`osGetCount`
  (wall-clock, NOT N64 counter units), and non-blocking message queues
  exist. **No threads, no rumble shim, no interrupts** — see
  `audio-and-libultra-shims.md`.

## What does NOT exist yet at this pin (verified absences)

- No thread shims (`osCreateThread` etc.) — types only.
- No Vulkan backend; D3D12 and GLX code exist but are compiled out
  (flags never defined — see `build-system.md`).
- No SDL3, no GLFW; SDL2 + DXGI only.
- No install/export/package config; no tests of any kind.
- No `.gitmodules` — every dependency is a hand-vendored source copy.
- No mod-manifest system — only MPQ patch-archive scanning plus the
  `alt/` prefix CVar (`resource-system.md`).
- Metal IS present already (often assumed later), as is Wii U
  (`CMAKE_SYSTEM_NAME` = `CafeOS`) and Switch support.

## Sibling docs

`build-system.md` · `resource-system.md` · `fast3d-renderer.md` ·
`windowing-gui-input.md` · `audio-and-libultra-shims.md` ·
`config-cvars-logging.md` · `bridge-api.md`
