# libultraship — windowing, GUI, and input

> **Pinned:** libultraship **1.3.1-486**
> (`62e973aeb4a53ad4d22bb91e2d9373ecdfcd246c`, 2026-08-15 —
> OcarinaOfTime's pin; 4 commits past 1.3.1-482).
> Updated 2026-09-01, iteration 17 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## Window layer

`Ship::Window` is still the pure abstract base and `Fast::Fast3dWindow`
the one concrete implementation; the port constructs it and passes it
to `Context::CreateInstance` (fails on null); no `MainLoop` — the port
loops on `WindowIsRunning()`.

- **Window ctor now takes `(gui, mouseStateManager)`**
  (`Window.h:59-75`): mouse capture/visibility moved into a
  **`MouseStateManager`** abstraction (#1009,
  `include/ship/window/MouseStateManager.h:15` — `StartFrame`,
  auto-capture, forced visibility, capture override);
  `Fast::FastMouseStateManager` adds a cursor-hide timer keyed to
  target FPS. Frame flow calls `GetMouseStateManager()->StartFrame()`
  (`Fast3dWindow.cpp:206`).
- **Backend selection is id-typed in ship, enum in fast** (#1097):
  `Ship::Window` traffics in `int32_t` backend ids
  (`Window.h:206-291`); the (now plain) `enum WindowBackend` lives in
  `include/fast/Fast3dWindow.h:22`. Availability declared in the
  `Fast3dWindow` ctor via `AddAvailableWindowBackend`
  (`Fast3dWindow.cpp:31-40`); pairing in `InitWindowManager`
  (`:136-162`). Window-backend persistence moved from Config onto
  `Ship::Window` (`Window.cpp:70`, `:125-126`).
- **iOS residual null-deref persists**: SDL_OPENGL advertised
  unconditionally (`Fast3dWindow.cpp:40`) but its case is compiled out
  on iOS (`ENABLE_OPENGL` undefined there, `src/CMakeLists.txt:177-215`)
  → both API pointers stay null past an `SPDLOG_ERROR` (`:158-160`).
- SDL specifics unchanged: F11 fullscreen / F2 mouse-capture
  (`Fast3dWindow.cpp:101-105`); Steam Deck sniff + Android/iOS
  `gameMode` (`:63-79`); `SupportsWindowedFullscreen` OpenGL-only,
  never Apple (`:301-312`). NEW: `EnableSRGBMode` (`:169`),
  `GetCurrentRefreshRate` (`:295`); DirectX gets a **WARP software
  fallback** (#967, `gfx_dxgi.cpp:1047`); macOS Metal resize crash
  fixed (#970, `gfx_sdl2.cpp:641-647`); GL state-switching reduced via
  caching (#982); `sysctl kern.clockrate` pacing calibration for
  OpenBSD/macOS (#1023, `gfx_sdl2.cpp:365-368`).
- The GfxDebugger moved INTO `Fast3dWindow` (`Fast3dWindow.cpp:104-105`)
  — no longer a Context subsystem.

## GUI layer — `Ship::Gui` is now renderer-agnostic

**The 397 "Gui hard-casts to Fast3dWindow" bug cluster is fixed by
restructuring**: `Ship::Gui` (`Gui.cpp` shrank to 421 lines, zero
Fast3D references) exposes virtual hooks — `ImGuiBackendInit/Shutdown`,
`ImGuiWMInit/Shutdown/NewFrame`, `ImGuiRenderDrawData`, `DrawGame`,
`CalculateGameViewport`, `RefreshImGuiGamepads`, `SupportsViewports`
(`Gui.h:80-224`) — implemented by **`Fast::Fast3dGui : Ship::Gui`**
(`src/fast/Fast3dGui.cpp`, 773 lines), which grabs the interpreter
weak_ptr **once** in `ImGuiWMInit` (`Fast3dGui.cpp:143`; cast still
unguarded but only `Fast3dWindow` constructs it,
`Fast3dWindow.cpp:47`). Window backends call
`Fast3dGui::Init(GuiWindowInitData)` (`gfx_sdl2.cpp:440-441`);
`GuiWindowInitData` moved to `Fast3dGui.h:28-49` (vestigial Gx2 arm
included).

- **Default windows: 5 → 4** (`Gui.cpp:23-52`): Stats,
  `SDLAddRemoveDeviceEventHandler`, Console, **FileBrowser** (NEW,
  #1139 — ImGui fallback file dialog). **InputEditorWindow and
  GfxDebuggerWindow are no longer auto-constructed** — both moved to
  the `libultraship/` tree and the port opts in via the `guiWindows`
  ctor argument (`classes.h` no longer re-exports InputEditorWindow.h).
- Two menu slots (`SetMenuBar`/`SetMenu`, `Gui.h:123-132`); F1 /
  gamepad-Back toggles (`Gui.cpp:19-20`).
- **Hotplug still rides the GUI**: `SDLAddRemoveDeviceEventHandler`
  pumps SDL device events (`SDLAddRemoveDeviceEventHandler.cpp:23-33`)
  — and now also refreshes the **ImGui gamepad backend binding**
  (#1112/#1138: `RefreshImGuiGamepads` →
  `ImGui_ImplSDL2_SetGamepadMode(AutoAll)`, `Fast3dGui.cpp:242-248`,
  re-invoked on hotplug).
- **GUI still owns the render resolution, no headless mode**:
  `CalculateGameViewport` writes `interpreter->mCurDimensions`
  (Advanced Resolution + low-res overrides) — now
  `Fast3dGui.cpp:306-360`; `DrawGame` composites the game FB
  (`:362-420`).
- GUI textures: `Fast3dGui::LoadGuiTexture` handles NEW
  `Palette4bpp` with a `palettePath` (#1157, `Fast3dGui.cpp:578-620`);
  `LoadTextureFromResource` present (`:566`).
- NEW: background-inputs toggle (#994, `CVAR_ALLOW_BACKGROUND_INPUTS`,
  default on — SDL hint at `Fast3dGui.cpp:92-101`; DXGI blocks game
  input on focus loss, `gfx_dxgi.cpp:506-514`). StatsWindow uses a
  fixed-width format so its rendered size is stable (#1020).
- The shipped `EventDebuggerWindow` is instantiated by nobody — port
  opt-in (`architecture-overview.md`).

## Controller / input

Ownership tree unchanged (ControlDeck → ControlPort → Controller →
Button/Stick/Gyro/Rumble/LED → typed mappings; `physicaldevice/`
layer). Deltas:

- **Concrete layer restructured**: `Ship::Controller::ReadToPad` pure
  virtual (`Controller.h:117`); the concrete **`LUS::Controller`**
  implements `ReadToOSContPad` including the per-controller (= per-port)
  6-deep input-lag buffer (`src/libultraship/controller/.../Controller.cpp:40-72`).
  `LUS::ControlDeck` constructs its own ports and takes injectable
  `ControllerDefaultMappings` + a button-name map
  (`ControlDeck.cpp:11-47`; the 14 N64 names are now the ctor default
  argument).
- SDL game-controller init moved to `Context::InitControlDeck`
  (non-fatal) — see `architecture-overview.md`; `osContInit` shrank
  accordingly.
- Keyboard/mouse still event-driven (`ProcessKeyboardEvent`/
  `ProcessMouseButtonEvent`, `ControlDeck.cpp:43-62`); wheel via
  `WheelHandler`; stick math unchanged; `OSContPad` offsets still
  wrong; rumble via `osMotorStart/Stop` macros over `__osMotorAccess`
  (`motor.h:9-10`, `os.cpp:75-84`); LED still driven by nothing;
  input blocking unchanged.

## Verified bugs at this pin

- iOS backend-selection residual (above).
- Uninitialized `SDL_Renderer* mRenderer` under GL (`gfx_sdl.h:58` vs
  `gfx_sdl2.cpp:426`/`:746`) — see `fast3d-renderer.md`.
- FIXED since 397: the `Gui::Init` duplicated grab + hard-cast cluster
  (restructured away — single grab, `Fast3dGui.cpp:143`).
