# Reference: libultraship (LUS) integration

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.
> **Note:** the libultraship pin described here (1.3.1-463) is 1.3.1-486 at the current pin.

*Standing reference. How SoH consumes libultraship — the integration surface. Read before tracing
why an asset loads, a frame draws, or input arrives. Companions:
[architecture-overview.md](architecture-overview.md), [port-layer.md](port-layer.md),
[asset-pipeline.md](asset-pipeline.md).*

**Version:** Shipwright's `libultraship/` submodule is pinned to **`f30fe0ed` / `1.3.1-463`** (branch
`port-maintenance`, `github.com/kenix3/libultraship`). This is the **singleton `Context` API**
(`GetInstance()` + `CreateUninitializedInstance` + `Init*` methods — not the newer Component tree).
A full LUS reference set pinned to a slightly older **`1.3.1-399`** lives at
`github.com/Kenix3/libultraship`'s `bill` branch (`tasks/reference/`: architecture-overview,
bridge-api, resource-system, fast3d-renderer, windowing-gui-input, audio-and-libultra-shims,
config-cvars-logging, build-system) — read those for LUS internals; the architecture matches, with
the **463-vs-399 differences** noted below.

## The 463-vs-399 difference — the `Fast::` namespace split

At `1.3.1-463` the Fast3D renderer has been extracted into its **own `Fast::` namespace under
`<fast/...>`**, separate from core `Ship::` under `<ship/...>`. Only controller/InputEditor/
GfxDebuggerWindow classes remain in the legacy **`LUS::`** namespace (e.g. `LUS::ControlDeck`). The
399 reference docs largely predate this split, so when they say `interpreter.cpp`/`Fast3dWindow.cpp`,
those are the `fast/` module here.

## The real LUS header dependency surface

By frequency (grep over `soh/`):
- **`<libultraship/libultra.h>` (527 hits)** — the dominant surface: the libultra ABI shim
  (`OSContPad`, `Gfx`, `Mtx`, `os*` types) that lets unmodified decomp compile.
- **Bridge (C-callable) headers** — the C→C++ seam: `bridge/consolevariablebridge.h` (22),
  `resourcebridge.h` (15), `gfxbridge.h`, `windowbridge.h`, `gfxdebuggerbridge.h`, `audiobridge.h`,
  `crashhandlerbridge.h`.
- **C++ class headers** (`OTRGlobals.cpp:13-108`): `<ship/Context.h>`,
  `<ship/resource/ResourceManager.h>`, `<ship/window/Window.h>`, `<ship/audio/AudioPlayer.h>`,
  `<ship/resource/ResourceFactoryBinary.h>`/`ResourceFactoryXML.h` (the bases SoH's factories derive
  from); `<fast/Fast3dWindow.h>`, `<fast/interpreter.h>`, `<fast/resource/factory/*Factory.h>`.
- Controller: `<libultraship/controller/controldeck/ControlDeck.h>`.

## How SoH owns + inits the Context (singleton `Init*` sequence)

`OTRGlobals` holds `std::shared_ptr<Ship::Context> context`; ctor `OTRGlobals.cpp:279-316`:
```
CreateUninitializedInstance("Ship of Harkinian", appShortName, "shipofharkinian.json")   :279
InitConfiguration() ; InitConsoleVariables()                                             :287-288
controlDeck = make_shared<LUS::ControlDeck>({ ...buttons... }) ; InitControlDeck(...)     :290,302
InitResourceManager({ portArchivePath }, {}, 3, true)   // 3 = threads                    :303
InitConsole()                                                                            :304
sohFast3dWindow = make_shared<Fast::Fast3dWindow>({ sohInputEditorWindow }) ; InitWindow  :308,310
```
Second stage (`:810-830`): `InitConfiguration`/`InitConsoleVariables` again, `InitLogging`,
`InitCrashHandler`, `InitAudio({.SampleRate=32000,…})`. Accessors everywhere:
`Ship::Context::GetRawInstance()->GetResourceManager()/GetWindow()/GetControlDeck()`. **SoH
constructs the Window and ControlDeck itself and hands them to `Init*`** — LUS doesn't pick them.
Teardown zeroes `sohFast3dWindow` (`:1627`). (The double init across the two stages is intentional.)

## Resource system + SoH's own factories

- Data access: `soh/soh/ResourceManagerHelpers.cpp` — `ResourceGetDataByName(path)` →
  `LoadResource(...)->GetRawPointer()` (`:279-289`). The typed C accessors (`ResourceMgr_LoadColByName`,
  `LoadVtxByName`, `LoadSeqByName`, `LoadAnimByName`, `LoadSkeletonByName`) are thin casts over it
  (`:555-643`). **Master-Quest handling is a path rewrite** `/nonmq/`→`/mq/`
  (`ResourceMgr_GetResourceByNameHandlingMQ`, `:271-279`). Alt-assets prepend
  `Ship::IResource::gAltAssetPrefix` and fall back to vanilla (`:601-643`).
- **Factory registration** (`OTRGlobals.cpp:843-914`): `RegisterResourceFactory(factory, format,
  typeName, typeID, version)`:
  - From LUS/Fast (SoH just registers them): `Fast::ResourceFactoryBinaryTextureV0/V1`, `VertexV0`,
    `DisplayListV0`, `MatrixV0`, `Ship::ResourceFactoryBinaryBlobV0`.
  - **SoH-owned** (`SOH::` namespace, `soh/soh/resource/importer/` + `type/`, enum
    `SohResourceType.h`): Array, Animation, PlayerAnimation, Scene/`SOH_Room`, CollisionHeader,
    Skeleton, SkeletonLimb, Path, Cutscene, Text, AudioSample/SoundFont/Sequence (V2), Background —
    each in `RESOURCE_FORMAT_BINARY` and often `RESOURCE_FORMAT_XML`. They derive from
    `Ship::ResourceFactoryBinary`/`ResourceFactoryXML`.
- Archives mounted via `GetArchiveManager()->AddArchive(...)` (`:792-796`); game-version validation
  reads `GetGameVersions()` vs `ValidHashes` (`:938-951`).

## Graphics handoff — display lists → Fast3D

- `extern "C" void Graph_ProcessGfxCommands(Gfx* commands)` (`OTRGlobals.cpp:1804`, "C→C++ Bridge")
  computes interpolation counts, then `RunCommands` → `wnd->DrawAndRunGraphicsCommands(Commands,
  mtx_replacements)` (`:1797`), `wnd` = the `Fast::Fast3dWindow` from the singleton. SoH pokes
  interpolation state directly on the interpreter: `wnd->GetInterpreterWeak().lock()->mInterpolationT
  /mInterpolationIndex` (`:1786-1798`). See [frame-interpolation.md](frame-interpolation.md).
- **The `__OTR__` mechanism** is the crux. `soh/soh/GbiWrap.cpp` overrides the GBI macros as real
  `extern "C"` functions; each runs **`ResourceMgr_OTRSigCheck(ptr)`** first — a **string-prefix test
  on the pointer** (`ResourceManagerHelpers.cpp:580-596`: odd-address bailout, then a literal 7-byte
  `"__OTR__"` compare). When a decomp pointer is actually an `__OTR__objects/...` path (baked in by
  ZAPD/OTRExporter), the wrapper resolves it: `gSPDisplayList` (`GbiWrap.cpp:67`) →
  `ResourceMgr_LoadGfxByName`; `gSPVertex` (`:108`) → `ResourceMgr_LoadVtxByName`; `gSPSegment` →
  `ResourceMgr_LoadIfDListByName`; else falls through to the real `__gSP*`. `gu_pc.c` supplies the
  matrix helpers (`guMtxF2L`, `guPerspective`) converting float matrices to N64 `Mtx`. New SoH GBI
  ops `gDPSetTileSizeInterp`/`Lerp` inject `G_SETTILESIZE_INTERP` for texture-coord interpolation.

## CVars, controller, audio crossings

- **CVars**: `<libultraship/bridge/consolevariablebridge.h>` — `CVarGetInteger`/`Set`/`GetFloat`
  (hundreds of sites under `soh/soh/Enhancements/`). SoH wraps names with `CVAR_*` prefix macros
  (`soh/soh/cvar_prefixes.h`). Store + JSON persistence are LUS-side.
- **Controller**: the decomp `soh/src/libultra/io/` shims (`contreaddata.c`, …) are **present but
  EXCLUDED from the build** (`soh/CMakeLists.txt:194` filters `src/libultra/io/`). The real `osCont*`
  come from LUS `libultraship/src/libultraship/libultra/os.cpp`: `osContGetReadData` →
  `Context::GetInstance()->GetControlDeck()->WriteToPad(pad)`. Decomp `padmgr.c` transparently pulls
  from the LUS ControlDeck. Rumble/LED are direct calls (`OTRGlobals.cpp:2175-2190`).
- **Audio**: `soh/soh/OTRAudio.h` defines a file-scope `audio` struct (thread + condition_variable +
  atomics). `OTRAudio_Thread()` (`OTRGlobals.cpp:1022+`) calls decomp `AudioMgr_CreateNextAudioBuffer`
  to synthesize samples, then pushes them to LUS via `AudioPlayer_Play(buf,len)` (`:1053`);
  `InitAudio({.SampleRate=32000,…})` (`:830`) sets up the LUS `Ship::AudioPlayer`.
  `Graph_ProcessGfxCommands` notifies the audio thread each rendered frame — audio cadence ties to
  the gfx frame.

## Newcomer trip-hazards

- **The decomp libultra I/O is vestigial in-tree** — `soh/src/libultra/{io,libc,os,rmon}/` are
  EXCLUDE-filtered from the build (`soh/CMakeLists.txt:194-197`, only `libc/sprintf.c` re-added).
  Reading `contreaddata.c`/`sirawdma.c` to trace controller flow is reading dead code; the live impls
  are LUS `libultra/os.cpp`.
- **The `Fast::` namespace split** is the biggest visible 463-vs-399 difference — `fast/`
  (Fast3dWindow, interpreter, factories) is a distinct module from core `ship/`.
- **`__OTR__` detection is a string-prefix test on a pointer** — fragile-looking, but the whole asset
  pipeline rests on it.
- **The audio thread looks locally reworked** — `OTRGlobals.cpp:1022-1090` carries a
  `sample_debt_thirds` accumulator and a ~5 ms self-pump fallback with hand-written comments not in
  stock SoH's simpler wake-on-gfx loop. **Likely a local modification in this checkout — verify
  against upstream before treating as canonical.**
