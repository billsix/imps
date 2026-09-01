# libultraship — windowing, GUI, and input

> **Pinned:** libultraship tag **1.4.0**
> (`59427a67bf9af060a4928bb72e3acce3b0782177`, 2023-11-27). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## Window layer

`LUS::Window` (`src/window/Window.h:16`) is a thin facade over a
`GfxRenderingAPI*` + `GfxWindowManagerAPI*` pair plus a
`shared_ptr<Gui>`. Backend enum: `DX11, DX12, GLX_OPENGL, SDL_OPENGL,
SDL_METAL, GX2` (`Window.h`) — of which **DX12 and GLX_OPENGL are never
offered** (D3D12 is compiled out; GLX's code was deleted outright in
1.2.0, though its enum value lingers — see `build-system.md`).
Availability (`Window.cpp:77-90`): DX11 on Win32, SDL_METAL on Apple iff
`Metal_IsSupported()`, GX2 on Wii U, else SDL_OPENGL.

**Selection is config-driven and unvalidated** — `Window.Backend.Id`
from config is range-checked against the enum, not the availability
list; a stale value hits the `default:` in `InitWindowManager`
(`Window.cpp:273`) leaving **null API pointers** that `gfx_init`
dereferences. (The related seeded-keys mismatch died with
`CreateDefaultSettings`' removal in 1.1.0 — see
`config-cvars-logging.md`.)

SDL specifics (`gfx_sdl2.cpp`): GL 4.1 core on macOS / 2.1 on Switch;
fullscreen = `SDL_WINDOW_FULLSCREEN_DESKTOP` unless CVar
`gSdlWindowedFullscreen`, made multi-monitor aware in 1.2.1 (detects
the display in use, `SDL_SetWindowDisplayMode`, warns when the window
is off every display); frame pacing = `nanosleep` timer (default 60
FPS) then `SDL_GL_SwapWindow` — called **even under Metal** (Metal
presents its own drawable; the SDL backend is only partly Metal-aware).
F11 toggles fullscreen (config key `Shortcuts.Fullscreen`; the
default was F9 in 1.0.0 — 1.0.1 changed both the handler and the
seeded default). Steam Deck
gamescope is sniffed from `/etc/os-release` and forces 1280×800
fullscreen (`Window.cpp:44-63`). Window size/position persist to config
on fullscreen toggles and at Context destruction.

## GUI layer (ImGui, docking branch, vendored 1.89.3-WIP)

`LUS::Gui` (`src/window/gui/Gui.h:57`), owned by `Window`.
**Initialized by the graphics backend, not by Window** — `gfx_sdl2.cpp:366`,
`gfx_direct3d11.cpp:390`, `gfx_wiiu.cpp:310` each call
`GetGui()->Init(window_impl)` from inside their `init()`.

- Per-backend ImGui wiring: SDL2+OpenGL3 (GLSL `#version 120` except
  `410 core` on Apple), SDL2+Metal, Win32+DX11, WiiU+GX2. Viewports
  (multi-window) enabled when supported + `gEnableMultiViewports`.
- **Registration model:** `GuiElement` base (`InitElement`/
  `DrawElement`/`UpdateElement`), `GuiWindow` adds a name; windows
  register by name via `Gui::AddGuiWindow`. Visibility round-trips
  through a console variable per element
  (`SyncVisibilityConsoleVariable`). Built-ins constructed in `Gui`'s
  ctor: Stats (`gStatsEnabled`), Input Editor
  (`gControllerConfigurationEnabled`), Console (`gConsoleEnabled`).
- **Menu bar is a single slot** the game supplies (`Gui::SetMenuBar`);
  F1 (or gamepad Back with `gControlNav`) toggles it. No default menu
  exists.
- **The GUI drives the game's render resolution**: `Gui::DrawMenu`
  writes `gfx_current_dimensions` / `gfx_current_game_window_viewport`
  from the ImGui content region and applies `gLowResMode`. It opens
  `ImGui::Begin("Main Game")` and deliberately leaves it open;
  `Gui::StartFrame` composites the rendered game as an `ImGui::Image`
  and closes it. There is no ImGui-less mode.
- 1.2.2 added Advanced Resolution Mode controls to the GUI (the
  `gAdvancedResolution` family driving internal-resolution scaling);
  1.3.0 extended them, fixed keyboard-resize handling, improved
  Windows SDL frame pacing, and fixed SDL button-release masking;
  1.3.1 fixed an Input Editor overflow and >100% DPI cropping.
- Overlays (`GameOverlay` — CVar watches + fading notifications, fonts
  from the OTR) and `InputViewer` are separate objects drawn after the
  registered windows, not GuiElements.
- GUI textures go through Fast3D, not ImGui: `Gui::LoadTexture` (stb) /
  `LoadGuiTexture` (LUS Texture resource) — both acknowledged leaks.
  Since 1.2.1 `LoadGuiTexture` routes through the resource system's
  alt/HD path, so GUI icons honor HD texture packs.
- Ctrl+R (Cmd+R) dispatches the console `reset` command.

## Controller / input stack

`LUS::ControlDeck` (`src/controller/ControlDeck.h`) manages devices and
4 ports; `LUS::Controller` is the abstract device
(`src/controller/Controller.h:36`) with `SDLController`,
`KeyboardController`, `DummyController` (+ WiiU pair on `__WIIU__`).

- **Scan order is load-bearing**: SDL gamecontrollers, then an "Auto"
  dummy, then the keyboard, then a "Disconnected" dummy **last**
  (`ControlDeck.cpp:32-78`). The window layer reaches the keyboard by
  the fragile index `GetNumDevices() - 2` (`Window.cpp:151` etc.).
  Port 0 defaults to device 0; an "Auto"-bound port reads **every**
  device (`:94-104`).
- **Mapping model:** per-(device,port) `DeviceProfile` with
  `map<deviceButtonId, n64Bitmask>`; the bitmask set extends real N64
  with `BTN_MODIFIER1/2`, stick and virtual-stick bits above 0xFFFF
  (stripped by the `& 0xFFFF` before reaching the game —
  `Controller.cpp:153`). Axes encode as `axis|AXIS_SCANCODE_BIT`
  (negated for the negative direction). Sticks: circular deadzone →
  octagonal gate (`16.0/69.0` slope math) → optional notch snapping;
  range ±85 (`MAX_AXIS_RANGE`).
- **Extended `OSContPad`**: floats `gyro_x/y` and `right_stick_x/y`
  beyond the real N64 struct
  (`include/libultraship/libultra/controller.h:121-130` — its offset
  comments and `// size = 0x24` are stale/wrong).
- 1.2.0 niceties: the Input Editor gained a live joystick preview
  (#324); display/multi-monitor handling improved (#326); a DXGI
  window-position type-conversion bug was fixed (#322); the cursor now
  shows when starting fullscreen with the menubar open (#318).
- Input lag simulation: a 6-deep pad buffer indexed by
  `gSimulatedInputLag` — but the buffer is **per device, not per
  port**, so "Auto" multi-port reads share one delay line.
- Rumble/LED/gyro exist on the device classes (`SDL_GameControllerRumble`
  etc.) but **nothing in LUS calls SetRumble/SetLedColor and no C
  bridge exists** — the game must drive them via C++.
- Input blocking: `ControllerBlockGameInput`/`Unblock` (C bridge) plus
  automatic blocks — controllers when the menu + `gControlNav` are
  active, keyboard when ImGui wants capture; blocked devices still tick
  so state stays fresh.

## Verified bugs at this tag

- (1.0.0's `SaveSettings` double-increment — only slots 0 and 2
  persisting — was fixed in 1.0.1; all four slots now save.)
- `SDLController::mSupportsGyro` read uninitialized when the device
  failed to open (`SDLController.cpp:21-33`).
- The `TARGET_WEB` block in `SDLController::ReadDevice` references
  `AxisValue` vs local `axisValue` — would not compile if enabled.
- Backend-selection null-deref path (above).
