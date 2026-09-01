# libultraship — Fast3D renderer

> **Pinned:** libultraship **1.3.1-397**
> (`7f2baa104108af3fca9f094754ea974a4973bdeb`, 2026-02-28 —
> MajorasMask's pin; a close cousin of iteration 14's 1.3.1-399,
> not its descendant). Updated 2026-09-01, iteration 15 of the
> reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

## Provenance and shape

The git-subrepo of Emill's `n64-fast3d-engine` is over — no `.gitrepo`,
first-party source. **`gfx_pc.cpp` no longer exists**: the interpreter
is `class Fast::Interpreter` in `src/fast/interpreter.cpp` (4690 lines)
+ `include/fast/interpreter.h`. `gfx_cc.{h,cpp}` is folded in
(`gfx_cc_get_features` at `interpreter.cpp:4599`). `src/fast/README.md`
is *still* stale upstream text (advertises D3D12/GLX, points at the
deleted `gfx_pc.h`). The port-facing entry is `Fast::Fast3dWindow`
(`windowing-gui-input.md`); the residual C surface is just
`gfxbridge.h` (native dimensions + pixel-depth queries).

## The GBI interpreter — tables, not a switch

The flat `switch` is gone. Dispatch is **per-microcode 256-entry
function-pointer tables** (`UcodeHandler`, `interpreter.cpp:3888`):
`rdpHandlers` (`:3912`), `otrHandlers` (`:3943`), `f3dex2Handlers`
(`:3980`), `f3dexHandlers` (`:4001`), `f3dHandlers` (`:4024`),
`s2dexHandlers` (`:4048`). `gfx_step()` (`:4113`) checks OTR → RDP →
current-ucode table, first table containing the opcode wins; handlers
return `bool` = **"I already advanced the pointer"** (returning false
after advancing double-advances — the trap when writing one). Unknown
opcodes now `SPDLOG_CRITICAL` (`:4153`, `:4157`) instead of silently
skipping. Each slot carries a name string for the GFX debugger.

**Runtime multi-ucode** (new): `UcodeHandlers` enum — f3d(b), f3dex(b),
f3dex2, s2dex (`include/fast/ucodehandlers.h:3-11`); default f3dex2
(`interpreter.cpp:69`, reset in `Init` `:4211`); switched by
`G_LOAD_UCODE` or `Fast3dWindow::SetRendererUCode`. Runtime opcode
constants live in `include/fast/{f3dex.h,f3dex2.h,lus_gbi.h}`,
independent of the compile-time `gbi.h` (whose layout `GBI_UCODE`
governs — see `build-system.md` for the ABI trap). Recursion is gone:
`GfxExecStack g_exec_stack` (stack + call-path recording for the
debugger); `Run` loops `while (!g_exec_stack.cmd_stack.empty())`
(`:4363`). S2DEX now implements `G_BG_COPY`, `G_BG_1CYC`,
`G_OBJ_RECTANGLE`.

**OTR opcodes** (runtime values `lus_gbi.h:39-72`, macros
`gbi.h:160-194`): the 1.4.2 set (0x20–0x3A) survives unchanged, plus
NEW: `G_COPYFB` 0x3B, `G_IMAGERECT` 0x3C, `G_DL_INDEX` 0x3D, `G_READFB`
0x3E, `G_REGBLENDEDTEX` 0x3F (blended-texture registration as an
opcode), `G_SETINTENSITY` 0x40, `G_MOVEMEM_HASH` 0x42, `G_LOAD_SHADER`
0x43, and RDP-table `RDP_G_SETTILESIZE_INTERP` 0x44 /
`RDP_G_SETTARGETINTERPINDEX` 0x45 (frame interpolation).
`G_EXTRAGEOMETRYMODE` now has two flags: `G_EX_INVERT_CULLING` and
`G_EX_ALWAYS_EXECUTE_BRANCH` (0x2). OTR handlers **still self-modify
the display list** with resolved pointers (`interpreter.cpp:3405` —
comment literally `// TODO: wtf??` — and `:3021`); the SETTIMG
caching-disabled OTRTODO survives (`:3395-3397`).

**Matrix interpolation hook** (the Shipwright/Ghostship injection
point, new vs 1.4.2): `Run(commands, mtxReplacements)` stores the map
(`:4350`); `GfxSpMatrix` (`:1065`) looks up the incoming `Mtx*` and
substitutes the port's `MtxF`, re-quantized 16.16 (`:1068-1073`).

**Game hacks still baked in:** Bowser–Peach-painting LOD (`:1727`);
±1024/2048 widened full-screen fill rects (`:2440-2446`);
`SCREEN_WIDTH/HEIGHT` 320×240 (`interpreter.h:22-23`); `MAX_LIGHTS 32`,
256-tri buffer. GONE: the OoT `clearMtx` segmented-address remaps and
the "Cursed Malon bug" comment.

## Backends

`src/fast/backends/`: **OpenGL**, **D3D11** (+`gfx_direct3d_common`),
**Metal**, window managers **SDL2** (GL + Metal) and **DXGI**. GX2/Wii U
deleted; D3D12/GLX deleted (only the never-defined `ENABLE_DX12` macro
remains in 7 guards). No Vulkan (zero hits). The 34-positional-pointer
structs are now all-virtual interfaces: `GfxRenderingAPI`
(`gfx_rendering_api.h:30`) and `GfxWindowBackend`
(`gfx_window_manager_api.h:6`, 30 pure virtuals — the whole window
API, not a small interface). DXGI is still the only real frame pacer;
SDL's `IsFrameReady` just returns true.

## Shader generation — Prism templates, loaded FROM THE ARCHIVE

The hand-emitted GLSL/HLSL/MSL strings are gone. Shaders are **text
templates** (`src/fast/shaders/{opengl,directx,metal}/default.shader.*`)
with `@prism`/`@if`/`@for` directives, processed at runtime by the
FetchContent'd **prism-processor**. The templates are **not compiled
in** — they load as `Ship::Shader` resources **out of the game
archive**: `LoadResource("shaders/opengl/default.shader.fs")`, and on
failure `SPDLOG_ERROR("… missing f3d.o2r?"); abort();`
(`gfx_opengl.cpp:300-304`, `:356-363`). **A missing or stale `f3d.o2r`
aborts the process at first draw** — the most likely first-run failure
when bringing up this LUS.

Combiner model: `ColorCombinerKey{combine_mode, options}` — two fields;
a custom-shader id is packed into `options` at bit 17 (`:1500`).
`GenerateCC` (`:185`), `LookupOrCreateColorCombiner` (`:394`, memoized
map + one-entry fast path, 16 clamp variants per combiner). Still true:
the **`#version 110` VS / `#version 130` FS mismatch** on desktop
non-Apple GL (`gfx_opengl.cpp:344` vs `:286`), and the
**`SHADER_INPUT_5..7` gap** — now exported as Prism symbols but
`shader_item_to_str` handles only 1–4 and returns `""` → compile
failure → `abort()` (`:396`). Loud instead of silent, still broken.

## Frame flow

`Fast3dWindow::DrawAndRunGraphicsCommands(Gfx*, mtxReplacements)`
(`Fast3dWindow.cpp:185-206`): `IsFrameReady` early-out → `Gui::
StartDraw` (menu + **CalculateGameViewport**) → `Interpreter::
StartFrame` → `Run` → `Gui::EndDraw` (DrawGame + overlay + CVar save)
→ `EndFrame`. The 1.4.2 unbalanced-`Begin("Main Game")` hack is gone
(balanced in both `CalculateGameViewport` and `DrawGame`). **The GUI
still owns the render resolution** (`Gui.cpp:662-667` writes
`mCurDimensions` from the ImGui content region; Advanced Resolution +
low-res overrides applied there) — still no headless mode. NEW:
`RunGuiOnly()` (GUI with no game DL) and `mRendersToFb` (offscreen FB +
MSAA resolve whenever viewport ≠ window res or MSAA > 1).

## Texture path

LRU cache still 500 entries (`TEXTURE_CACHE_MAX_SIZE`,
`interpreter.cpp:65`); key gained `size_bytes`
(`interpreter.h:170-186`), hash still address-only. One global decode
buffer up to 256 MB — **now freed**: `Interpreter::Destroy()` frees it
and unrefs cached resources (`:4216-4223`; TODO narrowed to "should
also destroy rapi"). Unsupported formats no longer `abort()` —
`SPDLOG_ERROR` and continue (`:929-932`). HD is still two mechanisms:
`alt/` resources with `HByteScale`/`VPixelScale`, and masked/blended
textures — 6-sampler model (`SHADER_MAX_TEXTURES 6`,
`interpreter.h:95-98`), registration now also via the
`G_REGBLENDEDTEX` opcode.

## Verified bugs at this pin (new since 1.4.2's ledger)

- **`mInterpolationIndex` is never written** (read `:1897`, `:1923`,
  `:3624`; declared uninitialized `interpreter.h:518`) — the
  `G_SETTARGETINTERPINDEX` compare reads garbage.
- **Custom shaders (`G_LOAD_SHADER`) are inert**: no backend reads
  `cc_features.shader_id`; `shader_ids` is write-only, never deduped —
  a DL issuing the opcode per frame grows it unboundedly; and the
  null-path reset writes `mRsp->current_shader` where set/read use
  `mRdp->current_shader` (`:2921` vs `:2927`/`:1452`), so a null load
  never clears the active shader.
- `default.shader.vs` declares itself `type='fragment'` (copy-paste,
  `:1`).
- Still true from 1.4.2: SDL `GetTime()` returns 0.0,
  `SetMaxFrameLatency` no-op, SDL swaps GL buffers even under Metal.
  CHANGED: SDL `CanDisableVsync()` now returns **true**; vsync is
  live-toggleable per frame via `CVAR_VSYNC_ENABLED`.
