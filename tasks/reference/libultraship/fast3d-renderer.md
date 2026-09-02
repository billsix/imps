# libultraship — Fast3D renderer

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> pin; **KiritoDv FORK branch** = 1.3.1-463 + 81 fork commits; mainline
> 464–486 absent). Updated 2026-09-01, iteration 18 (final) of the
> reference crawl (`crawl.md`). Re-sync
> check: compare `PIN_SHA` in `n64/libultraship/fetch.sh`.
>
> **This is the fork's core: the renderer was rewritten.** T&L moved to
> the GPU, Vulkan added, postprocessing/material shaders added, native
> + auto mipmapping added. `interpreter.cpp` is **7124 lines**
> (mainline 486: 5501).

## Interpreter shape — still tables, re-anchored

`UcodeHandler` `interpreter.cpp:6105`; tables `:6129-6278`;
`gfx_step()` `:6343`, OTR → RDP → ucode order (`:6369-6396`); unknown
opcodes `SPDLOG_CRITICAL` (`:6398-6402`); `GfxExecStack`
`interpreter.h:172-199`; `Run` `:6644` — **now takes
`dl_replacements` too** (display-list substitution for interpolation).
NEW: a null/segment-address guard before the five filepath OTR opcodes
(`:6370-6384`). Self-modifying SETTIMG handler survives (`// TODO:
wtf??` `:5424`). **The Bowser–Peach LOD hack is GONE** (it lived in
the deleted CPU vertex-LOD path); widened fill rects (`:3990`) and
320×240 (`interpreter.h:29-31`) remain.

## OTR opcode map — collision warning vs mainline

0x20–0x40 as before; then (`include/fast/lus_gbi.h:39-81`):
`OTR_G_SETTIMG_PAL` **0x41**, `MOVEMEM_HASH` 0x42, `PUSH_SHADER` 0x43,
`POP_SHADER` 0x44, `SETTILESIZE_INTERP` 0x45, `SETTARGETINTERPINDEX`
0x46, WIDE 0x47–0x49, **`OTR_G_INVAL_TEX_BY_PAL` 0x4A** — the slot
mainline 486 uses for `G_SETTILESIZE_LERP`, which is **absent** here —
then `OTR_G_SET_STRICT_DECAL` 0x4B, `OTR_G_SETUNIFORM` 0x4C,
`RDP_G_SETTILESCROLL_INTERP` 0x4D. A mainline-486 asset stream's 0x4A
would invalidate texture caches instead of lerping. Semantics:
`SETTIMG_PAL` exposes palette staging as a texture source keyed by
palette DRAM address (`:5485-5535`); `INVAL_TEX_BY_PAL` invalidates by
palette address (`:5535-5551`); `gDPReadFBToI8` is a **flag bit** on
`G_READFB` 0x3E (`:5600`), not an opcode; `SET_STRICT_DECAL` →
`mRapi->SetStrictDecal(bool)` (depth-equal decals, `:5553-5559`);
`SETUNIFORM` writes a custom uniform register (`:4468-4480`).

## GPU-side T&L — the rewrite

- **CPU vertex transform is gone.** `GfxSpVertex` (`:2353-2417`)
  stores object-space position + raw normal in `LoadedVertex`
  (`interpreter.h:253-266`) tagged with a **matrix-history slot**: MP
  matrices (widescreen aspect folded into column 0) captured on change
  into a 64-entry ring (`AppendMtxHistory`, `:158-175`,
  `interpreter.h:653-656`); per draw batch up to **8 palette entries**
  go to the VS (`GFX_MTX_PALETTE_SIZE`, `gfx_rendering_api.h:48`;
  `TransformUniforms` `:54-58`).
- Lighting/texgen/fog/point lights run in the VS (`LightingUniforms`,
  `GFX_MAX_GPU_LIGHTS 32`, `gfx_rendering_api.h:63-78`); light
  direction coefficients still CPU-computed at vertex load
  (`:2385-2397`). New `ShaderOpts`: `LIGHTING, POINT_LIGHTING, TEXGEN,
  TEXGEN_LINEAR` (`:2434-2455`, `:2607-2622`).
- Clip rejection + backface culling on the GPU (`:2408-2412`,
  `:2465-2480`); `G_EX_INVERT_CULLING` still honored (`:2476-2478`).
- Matrix load handles fixed-point AND float GBIs, incl. the
  `MtxF`-replacement path under `#ifndef GBI_FLOATS` (`:2251-2283`).
- **GPU palettization**: CI4/CI8 upload raw indices; palette lookup +
  post-lookup 3-point/bilinear filtering in the FS
  (`ShaderOpts::TEXEL0/1_PALETTE`, `:2625-2657`, uniforms
  `:3063-3077`) — TLUT swaps are free (`TextureCacheKey.indexed`).

## Shaders — stack, materials, settings, uniforms

- `SHADER_ID_SHIFT` is **25** (not 17; static_assert vs
  `ShaderOpts::PRISM_SHADER`, `interpreter.h:162-167`). Push/pop stack
  as at 486 but: dedup in `RegisterShaderPath` (`:4522-4537`, skips
  the 0xFFFF sentinel), drained per-`Run` in `SpReset` (`:6408-6412`),
  empty stack writes the sentinel `(uint64_t)0xFFFF << 25` (`:2578`) —
  **the mainline `-1 << SHIFT` UB is fixed here**.
- **Material shaders (NEW)**: any archive's `manifest.json`
  `"materials"` maps a display-list path to a shader;
  `ApplyMaterialShader`/`PopMaterialShaderScopes` push/pop around DL
  execution (`:4498-4521`; manifest loader `LoadPostPassManifest`
  `:4583-4645`).
- **Shader settings (NEW)**: `@setting` tweakables per pack, injected
  as prism context (`gfx_opengl.cpp:409-411`), persisted as
  `gShaderSettings.*` CVars, UI in `ShaderSettingsWindow` (port
  opt-in).
- **32 custom uniform registers (NEW)** (`GFX_NUM_CUSTOM_UNIFORMS`,
  `gfx_rendering_api.h:79-90`; regs 0/1 = engine frame/time/fb-dims,
  filled per frame `:6589-6596`; stale "2..15" comment at `:87`);
  written by `G_SETUNIFORM` (`:4455-4480`).
- Templates still archive-loaded — missing `f3d.o2r` still aborts
  (`gfx_opengl.cpp:428-430`, `:511-513`); NEW prism **include**
  mechanism (`shaders/opengl/include/`, `gfx_opengl.cpp:313-326`) and
  a `srgb.shader.*` per backend.
- **`SHADER_INPUT_5..7` gap FIXED**: INPUT_5/6 map to `uInputs[4]/[5]`
  and INPUT_7 is the shade varying in all backends
  (`gfx_opengl.cpp:178-192`, `:231-247`; `gfx_metal_shader.cpp:38-50`);
  `gfx_cc_get_features` `:6965`, shade-varying handling `:7001-7016`.
- Still true: `#version 110` VS / `#version 130` FS on desktop
  non-Apple GL (`gfx_opengl.cpp:487` vs `:400`).

## Post-processing (NEW)

Registered passes = prism templates run as fullscreen steps at frame
end, ping-ponging two lazy FBs, executed through the interpreter
itself (shader push + `GfxDpImageRectangle`): `PostPass`
`interpreter.h:467-472`; register/unregister/enable API
(`:4541-4580`; C API `gfx_register_post_pass` `:7089`);
`RunPostPasses` `:4649-4765` (MSAA resolve first, RDP state
save/restore); auto-registration from any archive manifest's
`"passes"`. **`EnableSRGBMode` was REMOVED** — SRGB is now just a
shipped `srgb.shader.*` template the port registers as a pass.

## Dither / noise (NEW)

Per-draw FS dither from the RDP `G_CD_*` bits (magic square / bayer /
noise / truncate / off; `:3056-3059`), gated by
`gEnhancements.Graphics.DitherNoise`, **default disabled**.

## Mipmapping (NEW)

- **Native mip pyramids**: `DetectMipChain` (`:1571-1660`) validates
  tiles + a TMEM load journal (requires `G_TL_LOD` + 2-cycle,
  increasing TMEM addrs, halving lines, single DRAM raster; rejects
  Paper-Mario same-address tile aliasing `:1622-1628`); uploads via
  `UploadTextureMip`, sets `ShaderOpts::MIP_LOD`; bare `G_TL_LOD` sets
  `TEX_LOD` (`:2594-2604`).
- **Auto-mipmaps: HD replacement textures only**, never
  palette-indexed; alpha-weighted downsampler (`:1820-1860`); smallest
  level ≥ 16 (`:1878-1881`); trilinear+aniso hint to the backend
  (`SetNextTextureAutoMipmap`); `gMipDebug` tints levels.

## Texture path

Cache 1024, hash address-only; key gained `size_bytes, mip_levels,
indexed` (`interpreter.h:210-221`). **NEW deferred texture frees**:
freed GPU ids recycle **next frame** (`interpreter.h:402`,
`:885-896`, `:6607-6611`) so deferred encoders never see mid-frame id
reuse. **NEW async HD loading**: `AcquireDrawTexture` (`:743-806`)
resolves vanilla-vs-`alt/` by explicit path; with
`gEnhancements.Graphics.AsyncTextureLoad` the HD decode runs on the
thread pool while vanilla renders; swap-in sticky and budgeted
(`TextureUploadBudget`, default 1/frame). **Absent vs mainline 486**
(revert-to-463): #1151 wrap clamping, #1118 clamp skips, #1172 RAW
reshape, #1176 in-module pointers, #1175 memoization, #1239
IsPyramidLike, #1135/#1164 tile-size fixes.

## Frame interpolation — four port-written fields

`mInterpolationIndex / mInterpolationIndexTarget / mInterpolationTotal
/ mInterpolationFrac` (`interpreter.h:771-774`) — all declared
uninitialized, all written **only by the port** (no library writer;
garbage otherwise). `G_SETTILESIZE_INTERP` applies only when
index==target (`:5744-5763`); NEW `G_SETTILESCROLL_INTERP` lerps a
scrolling tile by `mInterpolationFrac` (`:5773-5811`);
`G_MW_SEGMENT_INTERP` selects segment pointers by index
(`:3297-3329`). Mainline's `mInterpolationT`/`SETTILESIZE_LERP` do not
exist here.

## Backends

- **Vulkan (NEW)**: `src/fast/backends/gfx_vulkan.cpp` (2413 lines) —
  runtime prism → Vulkan GLSL → SPIR-V via **shaderc**
  (`gfx_vulkan.cpp:51`, `:293-303`); `WindowBackend::FAST3D_SDL_VULKAN
  = 4` registered when `Vulkan_IsSupported()`
  (`Fast3dWindow.cpp:43-47`); SDL window gets `SDL_WINDOW_VULKAN`;
  portability-subset handling, y-flip viewport, depth clamp only when
  supported.
- **Metal**: manual FB clear + stutter fix (`ClearFramebuffer`
  `gfx_metal.cpp:1066`); postprocess-on-Metal fixed.
- **Occlusion skip (NEW)**: `IsWindowVisible()` on the window backend
  (default true); `DrawAndRunGraphicsCommands` skips render+present
  and sleeps 8 ms when occluded (Metal's `nextDrawable` stalls ~1 s
  otherwise; `Fast3dWindow.cpp:216-226`).
- GL: `GL_DEPTH_CLAMP` enabled (`gfx_opengl.cpp:931`); GLES3/web
  guards at HEAD. DXGI still the only real frame pacer.

## Verified bugs at this pin

- `ColorCombinerKey.shader_id` still never assigned (field
  `interpreter.h:107`, construction `:2659-2661`) — indeterminate
  member in the defaulted comparison.
- Uninitialized `SDL_Renderer* mRenderer` (`gfx_sdl.h:59`): Metal-only
  assignment (`gfx_sdl2.cpp:480`) but read in `SDL_RenderSetVSync`
  (`:823`) and null-checks (`:581`, `:700`) under GL/Vulkan.
- SDL `GetTime()` 0.0 (`:833-835`); `SetMaxFrameLatency` no-op;
  `SDL_GL_SwapWindow` unconditional in `SwapBuffersBegin` (`:827`)
  even for Metal/Vulkan pairings.
- The four interpolation fields garbage if unset (above).
- FIXED here vs mainline: `-1 << SHADER_ID_SHIFT` (sentinel now
  unsigned); `SHADER_INPUT_5..7`; the iOS backend-advertisement
  null-deref (`windowing-gui-input.md`).
