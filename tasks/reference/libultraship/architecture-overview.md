# libultraship — architecture overview

> **Pinned:** libultraship **1.3.1-399**
> (`e0c1b1fc35e3b4143f9417b21c7ea6e75ccfb94b`, 2026-02-20 — the old
> Ghostship fork's submodule pin; first stop of the consumer-pin leg).
> Updated 2026-09-01 as iteration 14 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above — if they
> differ, the crawl has advanced (each iteration is a separate imps
> commit; `git log` on this file is the time axis).
>
> **Version-number trap:** `1.3.1-399` is `git describe` from the last
> tag on THIS line — which is ~18 months **newer** than tag `1.4.2`
> (2024-08). The 1.4.x tags are a different, older release line. Do not
> order these docs' history by version string.

**What LUS is at this pin:** a static C++20 library (`libultraship.a`)
that gives an N64 decompilation "somewhere to run" — a Fast3D
display-list interpreter (`Fast::Interpreter`) with per-microcode
dispatch and Prism-templated shaders, a **zip-based (`.o2r`)** archive +
typed resource system (MPQ/`.otr` is opt-in and off by default), SDL
audio/input with a fully reworked controller stack, an ImGui overlay
shell, JSON config + CVars (names now CMake-overridable macros), spdlog
logging, and a much thicker libultra shim slice (VI timing, PI DMA,
EEPROM, rumble). Still `add_subdirectory`-only (no install/export, no
tests, no version constant in code).

## The three trees, three namespaces

The 1.4.2-era flat `LUS::` + `src/graphic/Fast3D/` + `src/public/`
layout is gone. Headers all live under `include/` (zero `.h` under
`src/`), split three ways, all compiled into the **one** static target
(`src/CMakeLists.txt:3`):

| Tree | Namespace | Contents |
|---|---|---|
| `include/ship/` + `src/ship/` | `Ship::` (191 files) | the game-agnostic engine: `Context`, `resource/`, `config/`, `debug/`, `window/` (+gui), `controller/`, `audio/`, `utils/` |
| `include/fast/` + `src/fast/` | `Fast::` (42 files) | the Fast3D renderer: `interpreter.cpp`, `Fast3dWindow`, `backends/`, graphics resource types, `shaders/` (Prism templates) |
| `include/libultraship/` + `src/libultraship/` | `LUS::` (8 decls) | the concrete N64-shaped layer: libultra shims (8 files), C `bridge/`, `LUS::ControlDeck`/`LUS::Controller`, `log/luslog.cpp` |

The pattern: **`Ship::` is abstract and game-agnostic; `LUS::` is the
concrete N64 implementation on top.** `LUS::ControlDeck` and
`Ship::ControlDeck` are both real, different classes — mechanical
`LUS::`→`Ship::` renames are mostly right and occasionally very wrong.
The include/src boundary is now real, not advisory (though `src/` is
still a PUBLIC include dir, it exposes no headers any more).

## `Ship::Context` — the root singleton

Still a **weak_ptr-held singleton** (`src/ship/Context.cpp:27-31`), not
a Component tree (that comes later on this line). The creation API grew:

```
CreateInstance(name, shortName, configFilePath,
               archivePaths = {}, validHashes = {}, reservedThreadCount = 1,
               audioSettings = {}, window = nullptr, controlDeck = nullptr)
```

(`include/ship/Context.h:33-39`.) `otrFiles` became `archivePaths`; the
three trailing params are new — and the last two are **injection
points, not conveniences**: `InitWindow`/`InitControlDeck` FAIL on null
(`src/ship/Context.cpp:312-327`, `:234-247`). `Ship::Window` is pure
abstract; the port passes a `Fast::Fast3dWindow` (or its own subclass)
and typically a `std::make_shared<LUS::ControlDeck>()`. 1.4.2-era code
calling the old 6-arg form compiles (defaults) and then dies at runtime
with "Failed to initialize window."
`CreateUninitializedInstance(name, shortName, configFilePath)` still
exists (`Context.h:40-41`) for hand-driving the `Init*` methods.

**Init order** (`Context::Init`, `src/ship/Context.cpp:91-94`, a
short-circuiting `&&` chain): logging → config → console variables →
resource manager → control deck → crash handler → console → window →
audio → **gfx debugger** → **file-drop manager** (last two are new).
Each `Init*` is idempotent (already-non-null → return true).

- **Missing archive is now fatal**: `InitResourceManager` shows the
  message box and returns **false** (`:220-229`), short-circuiting the
  chain so `CreateInstance` returns `nullptr` (`:58-63`). The 1.4.2
  "boots with a permanently paused thread pool" hazard is narrowed to
  the opt-in `allowEmptyPaths=true` path (the pause itself survives,
  `src/ship/resource/ResourceManager.cpp:58-60`).
- Destruction still tears down in explicit reverse order so
  `spdlog::shutdown()` runs last — but `~Context` calls
  `GetWindow()->SaveWindowToConfig()` **unguarded** (`:35`): an
  uninitialized-instance consumer that never reached `InitWindow`
  null-derefs on teardown. `mGfxDebugger`/`mFileDropMgr` are not
  explicitly nulled, so they destruct *after* `spdlog::shutdown()`.

## The integration pattern at this pin

1. `add_subdirectory(libultraship)`, link `libultraship`; include
   `include/libultraship/libultraship.h`.
2. Construct a `Fast::Fast3dWindow` + `LUS::ControlDeck`, pass both to
   `CreateInstance` (or use `CreateUninitializedInstance` and drive
   `Init*` yourself — what Ghostship does). Hold the returned
   `shared_ptr` for process lifetime.
3. Register game resource factories — **LUS registers almost none
   itself**: Json + Shader at startup, GuiTexture + Font at GUI init.
   The `Fast::` graphics factories (Texture, Vertex, DisplayList,
   Matrix, Light) ship in-tree but the **port must register them**
   (`resource-system.md`).
4. `Gui::SetMenuBar` / `Gui::AddGuiWindow` as before (plus a new
   full-screen `SetMenu` slot).
5. **`Window::MainLoop` no longer exists.** The port owns the loop,
   conditioned on the `WindowIsRunning()` bridge, and calls
   `Fast3dWindow::DrawAndRunGraphicsCommands(Gfx*, mtxReplacements)`
   once per frame — the `mtxReplacements` map is the
   frame-interpolation injection point (`fast3d-renderer.md`).
6. Audio is still push-only via `AudioPlayerPlayFrame`; sample rate and
   channel layout now come from the `AudioSettings` struct.

App dirs: `SHIP_HOME` honored on Apple/Linux only; `NON_PORTABLE` →
`SDL_GetPrefPath`; else `"."` (`src/ship/Context.cpp:471-499`).
`LocateFileAcrossAppDirs` survives (`include/ship/Context.h:46`).

## What does NOT exist at this pin (verified absences)

- No thread shims — `osCreateThread` etc. grep to zero; only the
  `OSThread` ABI struct in `thread.h`.
- No Vulkan; **D3D12 and GLX are deleted outright** (no dead files —
  only a never-defined `ENABLE_DX12` macro in 7 `#if` guards).
- **Switch and Wii U are gone** (zero `__SWITCH__`/`__WIIU__` hits);
  Android and iOS took their place (`src/ship/port/mobile/`).
- No events bus, no scripting, no keystore, no Component/Tickable
  framework, no tests — those belong to later commits on this line.
- No `.gitmodules` — but now because everything is **FetchContent**,
  not vendored (`build-system.md`).

## Sibling docs

`build-system.md` · `resource-system.md` · `fast3d-renderer.md` ·
`windowing-gui-input.md` · `audio-and-libultra-shims.md` ·
`config-cvars-logging.md` · `bridge-api.md`
