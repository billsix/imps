# Reference: libultraship (LUS) integration

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference. What LUS provides and how Lighthouse consumes it. Read before tracing why an
asset loads, a frame draws, or input/audio arrives. Companions:
[architecture-overview.md](architecture-overview.md), [port-layer.md](port-layer.md),
[asset-pipeline.md](asset-pipeline.md).*

## Pin & how to study it (READ FIRST)

**Lighthouse's `libultraship` submodule is pinned at `2917d0f4` = `1.3.1-482`.** That is the SHA
to trust; re-check drift with `git -C libultraship rev-parse HEAD` vs this banner and re-verify if
it moved.

There is a separately-documented standalone LUS clone (`github.com/billsix/libultraship`, pinned
`64a17bdf` / **`1.3.1-400`**, branch `bill`) with its own 8-doc `tasks/reference/` set
(architecture-overview, bridge-api, resource-system, fast3d-renderer, windowing-gui-input,
audio-and-libultra-shims, config-cvars-logging, build-system). **Use those docs for LUS
*knowledge*, but they describe `400`, and Lighthouse builds `482` — 82 commits / ~318 files
apart.** The **core seams are stable across that gap** (singleton `Context` bootstrap, Fast3D,
`.o2r` resource system, CVar bridge, ControlDeck), so the `400` docs remain a reliable guide for
everything Lighthouse actually exercises. See the [new-subsystems](#new-lus-482-subsystems) section
for what changed. **Do not write docs into either LUS directory** — cite the submodule's own
`file:line` and banner this pin.

## Three namespaces

- **`Ship::`** — the core platform layer, by far the most used (~220 `Ship::Context` refs):
  Context/ownership, `Ship::GuiWindow` base for every custom window, resource types (`IResource`,
  `Blob`, `File`, `BinaryReader`, `O2rArchive`, `MemoryStream`), `Ship::Menu`, `Ship::Console`,
  input-mapping types, `Ship::KbScancode`, platform init (`Ship::Switch`/`WiiU`).
- **`Fast::`** — the Fast3D renderer: `Fast::Fast3dWindow`, `Fast::Interpreter`, `Fast::Fast3dGui`,
  `Fast::Texture`/`Vertex`/`DisplayList`/`Matrix`, and the `Fast::ResourceFactory*` set. All
  rendering + dimensions/aspect math.
- **`LUS::`** — nearly vestigial (~4 uses): `LUS::ControlDeck` (the concrete control deck,
  `Engine.cpp:157`), `LUS::Gui`, `LUS::BinaryWriter`. Lighthouse touches `LUS::` almost only to
  instantiate the ControlDeck; everything else migrated to `Ship::`/`Fast::`.

The umbrella `<libultraship.h>` is included broadly; the `<fast/…>` and `<ship/…>` roots are used
directly; the two C-callable bridge seams the decomp reaches LUS through are
`libultraship/bridge/gfxbridge.h` (`Engine.cpp:22`) and `libultraship/bridge/resourcebridge.h`
(`GfxBridge.c`, `ResourceHelpers.cpp`).

## 1. Init & ownership

`GameEngine` owns a **raw `Ship::Context*`** (`Engine.h:40`) — not a `shared_ptr`. Ctor order and
`FinishInit` phases are in [port-layer.md](port-layer.md#gameengine--boot--ownership-enginecpp).
Key LUS calls: `CreateUninitializedInstance("Lighthouse","bk","lighthouse.cfg.json")` (`:143`),
`InitControlDeck` (`:159`), `InitResourceManager({lighthouse.o2r},{},3,true)` (`:160`),
`InitWindow(Fast3dWindow)` (`:181`), `InitAudio({22000,736,2208})` (`:387`), `SetTargetFps(60)`
(`:389`). Teardown nulls the Fast3D window **before** the context (order-sensitive).

## 2. Graphics — decomp display lists → Fast3D

The one seam: the decomp submits F3DEX tasks through thread5; the window thread's `ServiceRcp` →
`RenderTask` → **`GameEngine::ProcessGfxCommands`** (`Engine.cpp:1367`). It casts the window to
`Fast::Fast3dWindow` (`:1368`), sets the ucode (`:1377`), computes interpolation, then
**`RunCommands`** (`:1242`) drives the `Fast::Interpreter`: per subframe `gui->StartDraw()`,
`interpreter->StartFrame()`, **`interpreter->Run(Commands, m)`** (`:1280`), `gui->EndDraw()`,
`interpreter->EndFrame()`. VI-black handling via the rendering API (`:1281-1285`). Dimensions/aspect
helpers read `Fast::Interpreter` fields (`mCurDimensions`/`mNativeDimensions`). The GBI-macro
interception that swaps `__OTR__` paths into loaded lists is `src/port/Resource/GfxBridge.c`
(`gSPDisplayList`, `gSPVertex` → LUS `__gSP*`). Full pacing/replay in
[frame-interpolation.md](frame-interpolation.md).

## 3. Resource system

Load-by-name is split: LUS's `ResourceGetDataByName` (submodule
`bridge/resourcebridge.cpp:44`) + Lighthouse's `src/port/ResourceHelpers.cpp` (`GetResourceByName`
`:192`, `ResourceMgr_LoadByAssetId` `:271`, `LoadGfxByName`/`LoadVtxByName`/`LoadMtxByName`
`:345/:350/:354`). A local `sResourceRefCache` (`:203`) retains `shared_ptr`s so raw pointers don't
dangle on LUS eviction (flushed at Destroy, `:359`). Archive mounting order and the
`LOAD_ASSET`/`__OTR__` seam are in [asset-pipeline.md](asset-pipeline.md). Factories registered at
`Engine.cpp:271-315`.

## 4. Controller / input

`LUS::ControlDeck` installed at `Engine.cpp:157-159`. Decomp `osCont*` calls route through
`src/port/OS/OS_Cont.cpp`: `osContInit` → `GetControlDeck()->Init` (`:24`); **a deliberate
request/complete split** — `osContStartReadData` posts a pending read (`:45`), `OS_SiService`
(`:55`, called on the window thread) does `GetControlDeck()->WriteToPad` (`:63`) and answers
`OS_EVENT_SI`, `osContGetReadData` copies the latched pads (`:70`). Rumble via `__osMotorAccess`
(`:79`) → `GetRumble()->StartRumble/StopRumble`. **Input GUI:** Lighthouse does **not** use LUS's
stock `InputEditorWindow`; it subclasses `Ship::GuiWindow` directly —
`LighthouseInputEditorWindow` and a custom `Mapper::MapperWindow` (`Controller/Mapper.h:123`,
registered `LighthouseGui.cpp:119,123`; `Mapper` uses `Fast::Fast3dGui`).

## 5. Audio

`InitAudio({22000,736,2208})` (`Engine.cpp:387`). The AudioPlayer bridge is `src/port/OS/
OS_AI.cpp`: `osAiGetLength` (`:23`) / `osAiSetNextBuffer` (`:28`) call LUS `AudioPlayerBuffered` /
`AudioPlayerGetDesiredBuffered` / `AudioPlayerPlayFrame`, with master-volume scaling here
(`:36-46`). **`src/port/Audio/AudioSync.cpp` repurposes `osSetIntMask`** (`:43`) into a
`std::recursive_mutex` (`gAudioLock`, `:17`): `OS_IM_NONE` enters the lock, a restored mask exits —
serializing the free-running audio worker against the game thread's SFX/music writes with **zero
edits to the N64 audio code**. Soundfonts load from the OTR as Blobs (`LoadSoundfonts`,
`Engine.cpp:1187`).

**Correction to earlier notes:** there is **no `GameEngine::HandleAudioThread`** method — that name
survives only in a stale comment (`AudioSync.cpp:2`). The real audio worker is the decomp's
**`audioManagerThread_entry`** (`core1/audio_manager.c:355`), allowlisted in `EnableThread5`
(`Game.cpp:171`). See [os-emulation-threading.md](os-emulation-threading.md).

## New LUS-482 subsystems — what Lighthouse actually uses

The `400`→`482` gap added `ship/events` (event bus), `ship/scripting`, `ship/security`
(keystore/signature), `ship/Api.h`, `Fast3dGui`, `FastMouseStateManager`, `WindowEvent`, plus a
window/GUI reorg. Consumption in `src/` (grepped 2026-07-31):

| Subsystem | Used by Lighthouse? | Evidence |
|---|---|---|
| `ship/events` (EventSystem) | **Yes, lightly** | `context->InitEventSystem()` (`Engine.cpp:385`); sole consumer is the DevTools window `EventDebugger.cpp`. Not on the game/boot hot path beyond the one-line init. |
| `ship/scripting` | **No** | zero includes/uses in `src/` |
| `ship/security` (Keystore/signature) | **No** | zero refs; the only "signature" hits are the unrelated `__OTR__` magic-string check |
| `ship/Api.h` | **No** | never included in `src/` |
| `Fast3dGui` | **Yes** | `ShipUtils.cpp`, `Controller/Mapper.cpp`, `Enhancements/Backports/EggAim.cpp`, `UI/Notification.cpp` |
| `FastMouseStateManager` | **Yes (indirect)** | `GetMouseStateManager()->StartFrame()` (`Engine.cpp:1277`) |
| `WindowEvent` | **No (not by name)** | window events pumped via `HandleEvents()` |

**Bottom line for a boot freeze:** scripting, security/keystore/signature, and `ship/Api.h` are
entirely off Lighthouse's path — including boot. **No keystore/signature check runs at boot**, so a
freeze is not attributable to LUS security. The only new subsystem even initialized is the event
bus (for a debug window). Investigate a freeze in the graphics/thread handshake
(`Game.cpp` thread5 / `ServiceRcp` / `port_runOnRenderThread`) or the audio path — not LUS's new
surface. The `400`-era LUS docs are sufficient for everything Lighthouse exercises, with the single
caveat that `InitEventSystem`/`GetEventSystem` is newer surface.
