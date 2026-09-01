# libultraship — windowing, GUI, and input

> **Pinned:** libultraship **1.3.1-397**
> (`7f2baa104108af3fca9f094754ea974a4973bdeb`, 2026-02-28 —
> MajorasMask's pin; a close cousin of iteration 14's 1.3.1-399,
> not its descendant). Updated 2026-09-01, iteration 15 of the
> reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

## Window layer

`Ship::Window` (`include/ship/window/Window.h:27`) is now a **pure
abstract base** (~30 pure virtuals: init/frame/events/geometry/mouse/
fullscreen/`IsRunning`/`GetKeyName`), holding `mGui` and a deliberate
hard `shared_ptr<Config>` (the Context singleton is gone by the time
the destructor saves window state — comment at `:94-95`). The one
concrete implementation is **`Fast::Fast3dWindow : Ship::Window`**
(`include/fast/Fast3dWindow.h:10`), which owns the `GfxRenderingAPI*` /
`GfxWindowBackend*` pair + the `Interpreter`, and adds
`SetRendererUCode`, `SetTextureFilter`, `SetTargetFps`,
`DrawAndRunGraphicsCommands`, `GetInterpreterWeak`. **The port
constructs the window and passes it to `Context::CreateInstance`** —
`InitWindow` fails on null. `Window::MainLoop` is gone; the port loops
on the `WindowIsRunning()` bridge.

Backend enum is now `enum class WindowBackend { FAST3D_DXGI_DX11,
FAST3D_SDL_OPENGL, FAST3D_SDL_METAL }` (`Window.h:13`) — DX12/GLX/GX2
values deleted. Selection is availability-validated now
(`Window.cpp:74-84`, `Config::GetWindowBackend` falls back sanely) —
the 1.4.2 null-deref is fixed except one residual: on **iOS**,
SDL_OPENGL is advertised but its `InitWindowManager` case is compiled
out (`ENABLE_OPENGL` undefined there), so selecting it still leaves
null API pointers (`Fast3dWindow.cpp:36` vs `:136`,
`src/CMakeLists.txt:143` vs `:171-173`).

SDL specifics: GL 4.1 core forward-compat on Apple only; windowed
fullscreen via `CVAR_SDL_WINDOWED_FULLSCREEN` —
`SupportsWindowedFullscreen()` is now **OpenGL-only, never Apple**
(`Fast3dWindow.cpp:288-297`); `nanosleep`/waitable-timer pacer then
`SDL_GL_SwapWindow` — still called even under Metal. Steam Deck
gamescope sniff moved to `Fast3dWindow::Init` (`:56-72`) and now also
forces `gameMode` on Android/iOS. Shortcuts: fullscreen default **F11**,
NEW mouse-capture default **F2** (`:89-92`).

## GUI layer (ImGui v1.91.9b-docking, FetchContent + patch)

`Ship::Gui`, still owned by Window, still **initialized by the graphics
backend from inside its `Init()`** (`gfx_sdl2.cpp:422`,
`gfx_direct3d11.cpp:283`). **Not renderer-agnostic despite the split**:
`Gui::Init` hard-`dynamic_pointer_cast`s the window to
`Fast::Fast3dWindow` with no null check (`Gui.cpp:152`, duplicated at
`:156`) and holds a `weak_ptr<Fast::Interpreter>` — a non-Fast3D
`Window` subclass null-derefs here.

- Class tree: `GuiElement` → `{GuiWindow, GuiMenuBar}`; hooks are
  `InitElement`/`DrawElement`/`UpdateElement`; window visibility still
  CVar-backed.
- **Two menu slots now**: `SetMenuBar` (a `GuiMenuBar`; F1 or
  gamepad-Back toggles) and `SetMenu` (a full-screen `GuiWindow`; Esc
  toggles). There is no `Ship::Menu` class. Ctrl/Cmd+R still dispatches
  console `reset`.
- **Five default windows** constructed in the `Gui` ctor
  (`Gui.cpp:58-87`), each pre-emptable by name: Stats, Input Editor
  (1409 lines), `SDLAddRemoveDeviceEventHandler`, Console,
  GfxDebuggerWindow (namespace `LUS`).
- **Controller hotplug rides the GUI**: `SDLAddRemoveDeviceEventHandler`
  is a GuiWindow that draws nothing — its `UpdateElement` pumps
  SDL_CONTROLLERDEVICEADDED/REMOVED into
  `ConnectedPhysicalDeviceManager`. Remove it and hotplug dies.
- `GameOverlay` drawn from inside `DrawGame`; **`InputViewer` no longer
  exists**.
- GUI textures still route through Fast3D via the `GuiTexture`
  resource type + `LoadTextureFromRawImage` (upload code inline;
  `LoadTextureFromResource` is a 399-side commit this pin lacks);
  `UnloadTexture` exists, the upload-leak TODO is acknowledged in
  place.
- The GUI computes the game viewport/resolution (`CalculateGameViewport`,
  `Gui.cpp:654-698`) and composites the game FB as an `ImGui::Image` in
  `DrawGame` (`:709-761`) — balanced Begin/End now; still no
  ImGui-less mode.
- **Mouse is first-class**: Window pure-virtuals for pos/delta/wheel/
  capture; `Gui::HandleMouseCapture` + cursor auto-hide ticks.

## Controller / input — total rewrite (nothing of 1.4.2 survives)

`DeviceProfile`, `SDLController`/`KeyboardController`/`DummyController`,
the `GetNumDevices()-2` index, `AXIS_SCANCODE_BIT`, `BTN_MODIFIER1/2` —
all gone. The new ownership tree:

```
ControlDeck → ControlPort[n] → Controller
                                 ├─ ControllerButton / 2× ControllerStick
                                 ├─ ControllerGyro / ControllerRumble / ControllerLED
                                 └─ …each holding typed ControllerMappings
```

- Mapping matrix under
  `src/ship/controller/controldevice/controller/mapping/`: sources
  keyboard/mouse/SDL × targets Button/AxisDirection/Gyro/Rumble/LED,
  plus factories (~40 files). NEW `physicaldevice/` layer:
  `ConnectedPhysicalDeviceManager` (per-port device sets + ignore
  lists), `PhysicalDeviceType {Keyboard, Mouse, SDLGamepad}`.
- **Abstract/concrete split**: `Ship::ControlDeck::WriteToPad` and
  `Ship::Controller::ReadToPad` are pure virtual; **LUS ships the
  concrete N64-shaped `LUS::ControlDeck`** (final,
  default-constructible, `MAXCONTROLLERS` ports, 14 N64 button names —
  `include/libultraship/controller/controldeck/ControlDeck.h:14-29`).
  A port passes `make_shared<LUS::ControlDeck>()` into
  `InitControlDeck`.
- `ControlDeck::Init` forces port 0 connected and applies default
  keyboard+mouse+gamepad mappings if unconfigured
  (`ControlDeck.cpp:25-41`). Keyboard/mouse are **event-driven** via
  `Fast3dWindow::Key*/MouseButton*` → `ProcessKeyboardEvent/
  ProcessMouseButtonEvent`; wheel via a `WheelHandler` singleton pumped
  in `WriteToOSContPad`.
- Stick math unchanged in substance (circular deadzone → `16.0/69.0`
  octagonal gate → notch snapping) but per-stick per-port CVars
  (`Controllers.Port%d.<Stick>.…`, defaults 100/20/0), and the **right
  stick is first-class**.
- `OSContPad` still extended (gyro + right stick), offset comments and
  `// size = 0x24` still wrong (`controller.h:96-107`).
- **Rumble now works through plain `osMotorStart/Stop`**
  (`os.cpp:88-97`) — no C++ needed. LED mappings are configurable but
  nothing in LUS triggers color changes and there is still no LED
  bridge.
- Input-lag simulation: the 6-deep buffer is now per-`Controller` =
  per-port — the 1.4.2 shared-delay-line bug is fixed by construction
  (`Controller.cpp:26-74`).
- Input blocking unchanged: ref-counted blockers + the two bridge
  functions.

## Verified bugs at this pin

- iOS backend-selection residual null-deref (above).
- `Gui::Init` duplicated interpreter grab (`Gui.cpp:152`, `:156`) and
  unguarded cast (above).
- **Uninitialized `SDL_Renderer* mRenderer`** read under OpenGL:
  assigned only on the Metal path (`gfx_sdl2.cpp:406`) but
  `SDL_RenderSetVSync(mRenderer, …)` runs whenever the vsync CVar
  changes (`:692`) — indeterminate pointer on GL builds.
- 1.4.2's `SDLController` bugs (uninitialized `mSupportsGyro`,
  non-compiling `TARGET_WEB` block, `SaveSettings` double-increment):
  all moot — the classes were deleted in the rework.
