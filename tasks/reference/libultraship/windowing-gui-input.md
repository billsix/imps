# libultraship — windowing, GUI, and input

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> pin; **KiritoDv FORK branch** = 1.3.1-463 + 81 fork commits; mainline
> 464–486 absent). Updated 2026-09-01, iteration 18 (final) of the
> reference crawl (`crawl.md`). Re-sync
> check: compare `PIN_SHA` in `n64/libultraship/fetch.sh`.

## Window layer

`Ship::Window` abstract + `Fast::Fast3dWindow` concrete, ctor
`(gui, mouseStateManager)`, id-typed backends on ship / enum on fast —
all the pre-463 structure holds (`Window.h:75`, `:206-284`;
`MouseStateManager` `Window.h:264-290`, `FastMouseStateManager` in
fast; `StartFrame` per frame `Fast3dWindow.cpp:228`).

- **Backend enum gains Vulkan**: `FAST3D_DXGI_DX11=1, FAST3D_SDL_OPENGL
  =2, FAST3D_SDL_METAL=3, FAST3D_SDL_VULKAN=4`
  (`include/fast/Fast3dWindow.h:22-27`). Availability
  (`Fast3dWindow.cpp:35-50`): DX11 on `_WIN32`, Metal on Apple +
  `Metal_IsSupported()`, Vulkan under `ENABLE_VULKAN` +
  `Vulkan_IsSupported()`, and **OpenGL now behind `#ifdef
  ENABLE_OPENGL`** — the long-standing iOS
  advertise-but-compiled-out null-deref is **FIXED** here.
- **Occlusion skip (NEW)**: `GfxWindowBackend::IsWindowVisible()`
  (default true, `gfx_window_manager_api.h:32-36`);
  `DrawAndRunGraphicsCommands` skips render+present and sleeps 8 ms
  when occluded (`Fast3dWindow.cpp:216-226`) — Metal's `nextDrawable`
  otherwise stalls ~1 s/frame. macOS occlusion via `isWindowOccluded`
  (`include/ship/utils/macUtils.h`). Related: a focus-loss lag fix.
- F11/F2 shortcuts (`Fast3dWindow.cpp:106-110`); Steam-Deck/gameMode
  sniff (`:72-96`); `SupportsWindowedFullscreen` GL-only never-Apple
  (`:323-333`); `GetCurrentRefreshRate` (`:317`); GfxDebugger
  constructed in `Fast3dWindow::Init` (`:112-113`). **`EnableSRGBMode`
  is REMOVED** (SRGB became a registrable post-pass —
  `fast3d-renderer.md`).
- `DrawAndRunGraphicsCommands` now also takes a `dlReplacements` map
  (`Fast3dWindow.cpp:207`).

## GUI layer

`Ship::Gui` renderer-agnostic + `Fast::Fast3dGui` (816 lines) — the
pre-463 split holds; interpreter grabbed once in `ImGuiWMInit`, still
an unguarded deref but intra-family (`Fast3dGui.cpp:122-124`).

- **Default windows: THREE** (`Gui.cpp:23-45`): Stats,
  `SDLAddRemoveDeviceEventHandler`, Console. Mainline's **FileBrowser
  (#1139) is absent**; InputEditor/GfxDebugger port-opt-in as before.
  The fork's `ShaderSettingsWindow` ships but is also **port opt-in**
  (nothing auto-constructs it).
- **`RefreshImGuiGamepads` (#1112/#1138) absent** — hotplug still
  pumps SDL device events through the GUI but does NOT rebind ImGui's
  gamepad backend.
- **Palette4bpp GUI textures (#1157) absent** — `LoadGuiTexture`
  rejects palette types (`Fast3dGui.cpp:674-678`); no `palettePath`.
- GUI still owns the render resolution (writes `mCurDimensions`,
  `Fast3dGui.cpp:410-441`); still no headless mode; two menu slots +
  F1/Esc as before; background-inputs CVar honored (`:129-131`).
- `Fast3dGui::LoadTextureFromResource` still leaks GPU textures by
  design (TODO at `Fast3dGui.cpp:657`).

## Controller / input

Pre-463 structure throughout: ControlDeck → ControlPort →
`LUS::Controller` (per-port 6-deep input-lag buffer), mapping matrix +
`physicaldevice/` layer, event-driven keyboard/mouse, `WheelHandler`,
stick math, wrong `OSContPad` offsets, rumble via
`osMotorStart/Stop`, LED driven by nothing, ref-counted input
blocking. **Reverted vs mainline**: SDL game-controller init is back
inside `osContInit` with `exit(EXIT_FAILURE)` on failure
(`os.cpp:15-36`) — the non-fatal `InitControlDeck` move was #1103.

## Verified bugs at this pin

- Uninitialized `SDL_Renderer* mRenderer` under GL/Vulkan
  (`gfx_sdl.h:59`, `gfx_sdl2.cpp:480`/`:823`).
- SDL `GetTime()` 0.0; `SDL_GL_SwapWindow` unconditional even under
  Metal/Vulkan (`gfx_sdl2.cpp:827-835`).
- FIXED here: the iOS backend-selection null-deref (guarded
  advertisement, above).
