# Reference: libultraship (LUS) integration

> **Provenance:** authored 2026-06/07 against Ghostship base `67e561c6`;
> **§4 (graphics) re-anchored 2026-09-06 to the current pin** `49c5312a`
> and its libultraship submodule `c151cc91` (1.3.1-544, the KiritoDv
> FORK). The decomp/port claims below hold; the LUS layout changed
> (`libultraship/src/fast/` interpreter + backends, a Vulkan backend),
> and the hook layer became `src/port/events/`. Anchors outside §4 not
> yet re-verified — check against the pinned checkout.

*Standing reference. What libultraship provides and — mostly — how Ghostship consumes it.
Read before tracing why an asset loads, a frame draws, or input arrives. Companions:
[architecture-overview.md](architecture-overview.md), [port-layer.md](port-layer.md),
[asset-pipeline.md](asset-pipeline.md).*

libultraship is vendored as the `libultraship/` submodule (from
github.com/Kenix3/libultraship) and reimplements N64 libultra services on modern hardware.
Wired in by CMake: `add_subdirectory(libultraship)` + `target_link_libraries(Ghostship
PRIVATE libultraship)` (`CMakeLists.txt:324-326`), include roots `libultraship/include` and
`libultraship/include/libultraship` (`:317-318`).

**Which libultraship this is (corrected 2026-09-06):** the submodule at this pin is
`c151cc91` / **1.3.1-544**, a **KiritoDv FORK** of libultraship (branch point `f30fe0ed` =
1.3.1-463, + 81 fork commits adding the Vulkan backend, GPU-side T&L, postprocessing
shaders, RT64-style mipmapping, async textures), NOT Kenix3 mainline. The imps
`tasks/reference/libultraship/` crawl docs describe MAINLINE release tags (its final stop is
this same 1.3.1-544 fork as iteration 18) — but for anything file-level, verify against THIS
submodule (`Ghostship/libultraship/`), since the fork's layout differs from the older
`e0c1b1fc`/1.3.1-399 the earlier docs were written against. The singleton `Context` API this
doc describes (`Context::GetInstance`, `CreateUninitializedInstance`, `InitResourceManager`/
`InitWindow`/…, called from `Engine.cpp`) still holds. **On a submodule bump, re-verify.**

**Three namespaces, inconsistent header spellings:**
- `Ship::` — the bulk (Context, ResourceManager, ArchiveManager, Window, GuiWindow, CVar).
- `Fast::` — the Fast3D graphics translator (`Fast3dWindow`, `Interpreter`, gfx factories).
- `LUS::` — vestigial; only `LUS::ControlDeck` survives (`Engine.cpp:140`).
- `<ship/...>` (internal short path) and `<libultraship/...>` (exported path) both resolve
  because both include roots are on the path. The umbrella `<libultraship.h>` pulls
  `libultra.h`, `bridge.h`, `color.h`, `luslog.h`, `classes.h`; `bridge.h` pulls all 8 bridges.

## 1. Init & ownership

Owner is the `GameEngine` singleton (`Engine.h:35`) holding
`std::shared_ptr<Ship::Context> context` (`Engine.h:46`). Ctor order (`Engine.cpp:125-164`):

1. `Ship::Context::CreateUninitializedInstance("Ghostship", "sm64", "ghostship.cfg.json")` (`:126`)
2. `InitConfiguration()` → `InitConsoleVariables()` (`:133-134`) — **must precede** ControlDeck
   construction (comment-flagged as fragile; fails deep in `ShipDeviceIndexMappingManager`
   otherwise).
3. `InitControlDeck(make_shared<LUS::ControlDeck>())` (`:140`)
4. `InitResourceManager({ghostship.o2r}, {}, 3)` (`:143`)
5. `InitConsole()` (`:144`)
6. `gsFast3dWindow = make_shared<Fast::Fast3dWindow>(...)` → `context->InitWindow(...)` (`:146`)
7. `GhostshipGui::SetupMenu()` (`:149`)

`FinishInit()` (`:222`) does phase 2: logging, gfx debugger, crash handler,
`InitAudio({32000,512,1100})` (`:276`), Fast3d tuning (`SetTargetFps(60)`,
`SetRendererUCode(ucode_f3d)` `:278-280`), the ~25 resource-factory registrations, then the
port subsystems. **Teardown ordering is manual and order-sensitive** (Fast3D window must die before the context): `gsFast3dWindow=nullptr;
context=nullptr;` is repeated at every exit path (Fast3D window must die before the context).

## 2. Resource system — load an asset by name from a `.o2r`

Types: `Ship::Context` → `Ship::ResourceManager` → `Ship::ArchiveManager` +
`Ship::ResourceLoader`; assets are `Ship::IResource` subclasses (`Ship::Font`,
`Fast::Texture`, SM64 factory outputs). Raw archive access via `Ship::O2rArchive`,
`Ship::MemoryStream`, `Ship::BinaryReader`.

- **Mounting:** `ghostship.o2r` at construction (`InitResourceManager`, `:143`); `sm64.o2r`
  added in `FinishInit` via `GetArchiveManager()->AddArchive(romPath)` (`:225`); then any
  `.otr/.o2r/.zip`/dir under `mods/` (`:236-256`, `.zip` warns "development only"). **Layering
  order = port → ROM → mods**, so a `mods/*.o2r` overrides base assets by path (texture packs).
- **Load-by-name:** C-callable `ResourceGetDataByName(const char* name)` — a LUS **bridge**
  function (decl `bridge/resourcebridge.h:28`, body in
  `libultraship/src/.../resourcebridge.cpp` — **not in this repo**, only call sites are).
  Wrapped by `LOAD_ASSET` (`Engine.h:3`): a pointer is either an `__OTR__` archive name
  (redirected via `GameEngine_OTRSigCheck` → `ResourceManager::OtrSignatureCheck`,
  `Engine.cpp:1168`) or a real pointer, passed through. This is how the decomp's segmented
  asset pointers transparently become archive lookups.
- **Custom factories** registered in `FinishInit` (`:285-335`):
  `loader->RegisterResourceFactory(factory, format, name, typeId, version)`. SM64-specific
  factories (Animation, AudioBank, Sample, Sequence, Dialog, Dictionary, Trajectory, Movtex,
  Painting, Collision, MacroObject) live in `src/port/importer/`; Fast3D's own
  (Texture/Vertex/DisplayList/Matrix/Light) and `Ship::…BlobV0` are LUS's. Pipeline:
  archive bytes → loader picks factory by (format, type-id, version) → typed `IResource` →
  `GetRawPointer()` to game code.

## 3. CVar bridge (the most-used integration header)

`<libultraship/bridge/consolevariablebridge.h>` — C-linkage API over `Ship::CVar`:
getters `CVarGetInteger/Float/String/Color/Color24(name, default)` (`:14-18`), setters
`CVarSet*` (`:20-24`), plus `CVarRegister*`, `CVarClear`, `CVarExists`, `CVarLoad`,
`CVarSave` (`:26-38`). Because it's `extern "C"`, **decomp `.c` files include it directly**
(not transitive — a few files get it via `<libultraship.h>`). Persisted to
`Ghostship.cfg.json`. Port name macros (`CVAR_CHEAT`, …) layer on top — see
[port-layer.md](port-layer.md#cvar-system-end-to-end).

## 4. Graphics — decomp display lists → Fast3D → GPU

1. Decomp builds N64 `Gfx*` display lists as on hardware (`alloc_display_list`,
   `src/game/memory.c:393`).
2. **The one seam:** decomp's `exec_display_list(SPTask*)` is redefined in the port
   (`Game.cpp:26`, `extern "C"`) → `GameEngine::ProcessGfxCommands` (`Game.cpp:27`).
3. `ProcessGfxCommands` (`Engine.cpp:1387`) computes frame-interpolation matrix replacements
   (`FrameInterpolation_Interpolate`, called at `:1409`) for the target FPS, then
   `RunCommands` (`:1352`, invoked `:1421`) casts the window to `Fast::Fast3dWindow`, gets
   its `Fast::Interpreter`, and calls `DrawAndRunGraphicsCommands(Commands, r.mtx[, r.dl])`
   (`:1367`/`:1369`) **once per interpolation sub-frame** (newcomers expecting one draw per
   frame get surprised). Matrices are `Mat4` (float 4×4) here, not the old `MtxF` name.
4. `Fast::Interpreter::Run` (`libultraship/src/fast/interpreter.cpp:6644`, taking the
   `unordered_map<Mtx*, MtxF>` replacements) walks the F3D/F3DEX list and, per batch, emits
   `mRapi->DrawTriangles(...)` (`interpreter.cpp:146`) to a `GfxRenderingAPI` backend
   (`fast/backends/gfx_opengl.cpp`, `gfx_vulkan.cpp`, `gfx_d3d11.cpp`, `gfx_metal.*`) →
   OpenGL / **Vulkan** / DX11 / Metal. Backend chosen inside LUS at window creation, **not**
   in Ghostship (see `SuperMario64/CLAUDE.md` for the OpenGL-default seed / Vulkan-hang
   caveat). Shaders are GENERATED from the N64 color combiner — see
   [`shaders-and-gpu.md`](shaders-and-gpu.md).
- **GBI interception:** `src/port/GBIMiddleware.cpp` intercepts individual macros
  (`gSPDisplayList`, `gSPVertex` — resolves `__OTR__` vertex names via `ResourceGetDataByName`
  at `:80`, `ResourceMgr_PatchGfxByName`). HUD/aspect helpers (`OTRGetDimensionFromLeftEdge`,
  render width/height) read `Fast::Interpreter::mCurDimensions` (`Engine.cpp:1073-1286`).
  Alt-asset (HD) toggle clears the Fast3D texture cache (`gfx_texture_cache_clear`, `:996`).

## 5. Controller & audio crossing

- **Controller — no port shim.** The decomp uses the *standard N64 osCont API*
  (`osContStartReadData`/`osContGetReadData`, `game_init.c:534-705`), and **LUS provides
  those symbols** (`libultraship/src/.../libultra/os.cpp`), fed from `LUS::ControlDeck`
  (installed `Engine.cpp:140`). Chain: SDL → ControlDeck → osCont* → decomp `gControllerPads`.
  Remap UI is a LUS `GuiWindow` subclassed as `GhostshipInputEditorWindow` (`GhostshipGui.cpp:82`).
- **Audio — decomp-produced, LUS-played.** `push_frame()` wraps each decomp frame in
  `StartAudioFrame`/`EndAudioFrame` (condition-variable handshake with `HandleAudioThread`,
  `Engine.cpp:851-902`). Decomp's `create_next_audio_buffer` makes samples; the port scales by
  master-volume CVar and pushes via the `AudioPlayer*` bridge (`AudioPlayerBuffered`,
  `AudioPlayerPlayFrame`, `Engine.cpp:865-879`, `bridge/audiobridge.h`). Device inited with
  `context->InitAudio({.SampleRate=32000,...})` (`:276`).

## 6. The real dependency surface (what the port actually includes)

Beyond the umbrella `<libultraship.h>`: **CVar bridge** `bridge/consolevariablebridge.h`
(the decomp recipe include); **resources** `ship/resource/{Resource,ResourceManager,
ResourceType,ResourceFactoryBinary}.h`, `resource/factory/BlobFactory.h`, bridge
`resourcebridge.h`; **context** `ship/Context.h`; **Fast3D** `fast/interpreter.h`,
`fast/Fast3dWindow.h`, `fast/resource/factory/{DisplayList,Texture,Matrix,Vertex,Light}Factory.h`,
`fast/backends/{gfx_rendering_api,gfx_metal}.h`; **GUI** `ship/window/gui/{GuiWindow,
GuiMenuBar,GuiElement,ConsoleWindow,Fonts}.h`, `gui/resource/Font.h`, `ship/window/Window.h`;
**controller** `ship/controller/controldeck/ControlDeck.h` + `controldevice/.../mapping/*`;
**utils** `ship/utils/StringHelper.h`, `ship/utils/binarytools/{BinaryReader,endianness}.h`;
**libultra shims** `libultraship/libultra/{types,controller}.h`; **platform**
`ship/port/switch/SwitchImpl.h` (Switch only).

## 7. Newcomer trip-hazards

- **`exec_display_list` is the whole graphics bridge** — a decomp-signature `extern "C"` fn
  redefined in `Game.cpp:18`. Don't rename it.
- **`ResourceGetDataByName` has no body in this repo** (it's a LUS bridge symbol).
- **`LOAD_ASSET`'s dual nature** — a pointer is either an `__OTR__` name or a real pointer,
  disambiguated at runtime.
- **Init/teardown order is fragile and comment-flagged**, not obvious from types.
- **The ROM extractor runs inside a live LUS ImGui frame loop** (`RunExtract`,
  `Engine.cpp:351-751`) — the window/GUI is up *before* the game boots.
- **The GPU backend (GL/DX11/Metal) is chosen inside LUS**, not in Ghostship code.
