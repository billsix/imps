# libultraship — architecture overview

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> submodule pin). **This pin is a KiritoDv FORK branch, not Kenix3
> mainline**: branch point `f30fe0ed` (1.3.1-463) + 81 fork commits
> (branch `fix/scripting/v2+bass3l-fixes+postprocessing`); the 23
> mainline commits 464–486 that iterations 16–17 documented are ABSENT
> here — their older shapes stand. Updated 2026-09-01, iteration 18
> (final) of the reference crawl
> (`crawl.md`). Re-sync check: compare
> `PIN_SHA` in `n64/libultraship/fetch.sh` with the SHA above; git history
> on these docs is the time axis (486-mainline state = the previous
> commit).

**What LUS is at this pin:** the 463-era engine (zip `.o2r` archives,
event system, opt-in TCC scripting + keystore, gtest suite) **plus the
fork's renderer rewrite**: vertex transform / lighting / texgen / fog /
culling / CI-palette lookup moved to the GPU, a **Vulkan backend** (4th
renderer), a post-processing/multipass system with archive-declared
custom shaders, native + auto mipmapping, async HD-texture loading, and
a **python-free build**. Interpreter is 7124 lines.

## The three trees, three namespaces

Same split as mainline (`Ship::` 231 files incl. `events/`,
`scripting/`, `security/`; `Fast::` 76; `LUS::` 74); the #1097
cross-layer cleanup predates the branch, so `Fast3dGui`,
id-typed backends, and the `libultraship/`-tree InputEditor/GfxDebugger
windows are all present. New fork pieces: `ShaderSettingsWindow`
(`include/ship/window/gui/ShaderSettingsWindow.h:19`),
`ship/port/mobile/MobileImpl`, `cmake/SetupTccRuntime.cmake`.

## `Ship::Context` — REVERTED to the pre-#1103 shape

**The mainline `GetRawInstance`/`DestroyInstance` rework is absent.**
Storage is `static std::weak_ptr<Context>` (`src/ship/Context.cpp:32`);
**`GetInstance()` returns `shared_ptr<Context>`** (`:34-36`);
`CreateInstance`/`CreateUninitializedInstance` return `shared_ptr`
(`include/ship/Context.h:68-74`) — a 486-era `GetRawInstance()` caller
does not compile here; the 397-era hold-the-shared_ptr pattern does.
Destructor is the old shape (`Context.cpp:38-61`): unguarded
`GetWindow()->SaveWindowToConfig()` (`:40`), `GetConfig()->Save()`
(`:58`), then `spdlog::shutdown()` (`:60`); fork adds a scripting-gated
`mScriptLoader->UnloadAll()` + keystore drop (`:51-57`).

Init chain (`Context.cpp:104-111`): logging → config → cvars →
resource mgr → control deck → crash handler → console → window → audio
→ event system → file-drop → *(scripting)* script loader.
`InitKeystore()` inside `InitResourceManager` (`:222-225`). Missing
archive still messagebox-fatal (`:241-250`, + iOS `exit(0)`);
`InitWindow`/`InitControlDeck` still fail on null. **SDL
game-controller init is back inside `osContInit` with
`exit(EXIT_FAILURE)` on failure** (`os.cpp:15-36`) — the mainline move
to `InitControlDeck` was #1103.

## Fork subsystems (on top of the 463 base)

- **Vulkan renderer** — auto-detected at configure (`LUS_ENABLE_VULKAN`
  ← `find_package(Vulkan QUIET)`, all platforms except iOS/Android),
  `WindowBackend::FAST3D_SDL_VULKAN = 4`, runtime prism→GLSL→SPIR-V via
  shaderc. See `fast3d-renderer.md`/`build-system.md`.
- **Post-processing + material/custom shaders** — passes and per-DL
  material shaders declared in any archive's `manifest.json`
  (`"shaders"` section) or registered via C API; per-pack shader
  settings persisted as a dynamic `gShaderSettings.*` CVar namespace.
- **GPU-side T&L** — object-space vertices + a 64-entry matrix history
  ring, 8-slot matrix palette per batch, 32 GPU lights, shader-side
  texgen/fog/palettes. The CPU vertex pipeline is gone.
- **Script compile cache** — `ScriptLoader::SetCacheDir` keys compiled
  script binaries on manifest checksum + code version + build options;
  **dormant by default** (no in-tree caller sets the dir).
- **Python-free build** — the keys-header generator is now a C++ host
  tool; zero `find_package(Python3)`.
- Platform work: iOS (drops CoreAudio, codesign handling), GLES3,
  emscripten/web at code level only (no cmake dispatch; app dir
  `"/storage"`, `Context.cpp:528-530`).

## Integration pattern at this pin

As at 463: hold the `shared_ptr<Context>`, inject `Fast3dWindow` +
`LUS::ControlDeck`, register the `Fast::` factories, loop on
`WindowIsRunning()`. Fork-specific: `DrawAndRunGraphicsCommands` takes
a `dlReplacements` map besides `mtxReplacements`
(`Fast3dWindow.cpp:207`), and frame interpolation is a **four-field**
port contract (`mInterpolationIndex/IndexTarget/Total/Frac`, all
port-written — `fast3d-renderer.md`).

## What does NOT exist at this pin

- The 23 mainline 464–486 commits: no `GetRawInstance`, no `.meta`
  archive-priority resolution, no `ResolveResourceCached`, no
  `CacheExternalResource`, no FileBrowser window, no
  `G_SETTILESIZE_LERP`, no virtual `~AudioPlayer`, no NullAudioPlayer
  Buffered fix, no Windows-arm64 CI pin.
- Still no thread shims, no install/export, no version constant, no
  D3D12/GLX/Switch/WiiU.
- `EnableSRGBMode` was **removed** (SRGB became a post-pass the port
  registers itself).

## Sibling docs

`build-system.md` · `resource-system.md` · `fast3d-renderer.md` ·
`windowing-gui-input.md` · `audio-and-libultra-shims.md` ·
`config-cvars-logging.md` · `bridge-api.md`
