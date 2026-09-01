# libultraship — Fast3D renderer

> **Pinned:** libultraship tag **1.4.0**
> (`59427a67bf9af060a4928bb72e3acce3b0782177`, 2023-11-27). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## Provenance and shape

`src/graphic/Fast3D/` is a git-subrepo of Emill's `n64-fast3d-engine`
(`.gitrepo` → commit `7353aa30`), heavily forked for OTR. **Its README
is stale upstream text** (claims D3D12 support, omits Metal/GX2). The
interpreter is one 3309-line file, `gfx_pc.cpp`; `gfx_cc.{h,cpp}` holds
the color-combiner model shared by all shader generators.

## The GBI interpreter

`gfx_run_dl(Gfx*)` at `gfx_pc.cpp:2442`: `for(;;)` + one flat
`switch (cmd->words.w0 >> 24)`; `G_ENDDL` returns. **No `default:`** —
unknown opcodes are silently skipped (unhandled at this tag: plain
`G_BRANCH_Z`, `G_CULLDL`, `G_LINE3D`, `G_SETBLENDCOLOR`,
`G_RDPHALF_1/2`, all S2DEX except `G_BG_COPY` — which since 1.0.1
honors `G_BG_FLAG_FLIPS`, horizontal flip via negative dsdx).
`include/libultraship/libultra/gbi.h:50` hardcodes `F3DEX_GBI_2`, so
every F3D/F3DEX `#else` branch is dead.

**OTR opcodes** (gbi.h:162-186; 0x20-0x40 range) let display lists
reference assets by CRC64 hash or path: `G_SETTIMG_OTR_HASH/FILEPATH`,
`G_VTX_OTR_HASH/FILEPATH`, `G_DL_OTR_HASH/FILEPATH`, `G_MTX_OTR`,
`G_BRANCH_Z_OTR`, `G_MARKER`, `G_INVALTEXCACHE`, framebuffer ops
(`G_SETFB`/`G_RESETFB`/`G_SETTIMG_FB`), wide rects
(`G_TEXRECT_WIDE`/`G_FILLWIDERECT`), `G_SETGRAYSCALE`/`G_SETINTENSITY`,
and since 1.1.0 `G_EXTRAGEOMETRYMODE` (0x3A) driving
`rsp.extra_geometry_mode` — its one flag so far, `G_EX_INVERT_CULLING`,
negates the backface-cull cross product (for mirrored worlds).
They resolve through the resource bridge — and several **self-modify
the display list**, overwriting `w1` with the resolved pointer
(`:2584`, `:2815`; resource caching at the SETTIMG site was disabled to
fix HD-texture corruption, OTRTODO `:2806-2808`).

**Geometry:** CPU transform + lighting in `gfx_sp_vertex` (`:1207`,
`MAX_LIGHTS` raised to 32), 11-deep matrix stack, tri assembly in
`gfx_sp_tri1` (`:1359`) with state diffing, combiner-key assembly,
texture binding, and vertex emission into a 256-tri buffer flushed via
`gfx_rapi->draw_triangles`.

**Game-specific hacks baked into the "generic" library:** literal
OoT segmented addresses remapped to `clearMtx` (four at 1.0.0; six
since 1.2.2, adding PAL GC MQ and PAL1.0); a
"Bowser - Peach painting" LOD heuristic (`:1707`); full-screen fill
rects widened ±1024/2048 for widescreen fades (`:2323`); a commented
"Cursed Malon bug" offset (`:2425`). `SCREEN_WIDTH/HEIGHT` pinned to
320×240 with a TODO admitting 640×480 misrenders (`gfx_pc.h:14-16`).

## Backends at 1.0.0

Rendering (`GfxRenderingAPI`, 34 positional function pointers,
`gfx_rendering_api.h:33`): **OpenGL** (`gfx_opengl.cpp`), **D3D11**
(`gfx_direct3d11.cpp`), **Metal** (`gfx_metal.cpp` + metal-cpp — yes,
already at 1.0.0), **GX2** (Wii U), and D3D12 **compiled out**
(`ENABLE_DX12` never defined). Window managers
(`GfxWindowManagerAPI`): **SDL2** (serves both GL and Metal), **DXGI**
(the only real frame pacer — vsync statistics, frame dropping by
returning false from `start_frame`; vsync handling reworked in 1.0.1,
and the 1.3.0 keyboard-resize change partially reverted in 1.3.2;
1.3.3 fixed a missing switch break there that caused input lag),
Wii U shim. GLX was compiled-out dead code until its deletion in 1.2.0
(which also improved the SDL pacing timer, #325). No Vulkan, no GLFW.

## Shader generation

No shader files anywhere: every backend emits source text at runtime
from a 96-bit key — `ColorCombinerKey{combine_mode, options}`
(`gfx_cc.h:57`), options = `SHADER_OPT_*` bits (fog, texture-edge,
noise, 2-cycle, alpha threshold, grayscale, per-texel clamp/mask/blend).
`gfx_generate_cc` (`gfx_pc.cpp:318`) normalizes and maps N64 CCMUX
inputs to generic vertex attributes; emitters: GLSL
(`gfx_opengl.cpp:247` — VS `#version 110` vs FS `#version 130`, a
mismatched pair that links only in compatibility contexts), HLSL
(`gfx_direct3d_common.cpp`, shared with dead D3D12), MSL
(`gfx_metal_shader.cpp`), GX2 register-level generation
(`gx2_shader_gen.c`). Combiners memoized per key + 16 clamp-variants
per combiner. **Gap:** `SHADER_INPUT_5..7` exist in the model but no
emitter handles them — a >4-input combiner emits broken shaders.

## Frame flow (the host-game contract)

Per frame: `gfx_start_frame()` (`:3091` — pump events, **run the whole
ImGui menu via `Gui::DrawMenu`**, recompute dimensions) → game builds
display list → `gfx_run(cmds, mtx_replacements)` (`:3142` — pacing
gate via `wapi->start_frame` with a balanced ImGui frame on drops;
interpret; composite the game framebuffer as an `ImGui::Image`;
`Gui::RenderViewports`; swap) → `gfx_end_frame()`. Two structural
surprises: **the GUI decides the render resolution** (`Gui::DrawMenu`
writes `gfx_current_dimensions` from the ImGui content region —
there is no headless mode), and `ImGui::Begin("Main Game")` is left
open by `DrawMenu` for `Gui::StartFrame` to close.

## Texture path

LRU cache of 500 entries keyed on
`{addr, palettes, fmt, siz, palette_index}` (`gfx_pc.cpp:83`,
`gfx_pc.h:33`); lazy decode in `gfx_sp_tri1` → `import_texture`
(`:963`) → per-format decoders to RGBA8888 into one global
`tex_upload_buffer` (up to **256 MB**, malloc'd at init, never freed).
Unsupported combos `abort()` (one is commented out with an OTRTODO
"seemingly randomly, we end up here", `:1000`). TMEM is a two-slot
approximation (`tmem_index = (tmem != 0)`, `:1934`).

HD support = two mechanisms: the resource-level `alt/` prefix (see
`resource-system.md`) with `HByteScale`/`VPixelScale` letting oversized
assets satisfy N64-sized loads (`:1989`), and
`gfx_register_blended_texture` masks/replacements bound to extra
sampler slots as `SHADER_OPT_TEXEL*_MASK/BLEND` (`:3294`, `:1473-1484`,
6-slot model in `gfx_cc.h:66-69`).

## API surface

`gfx_pc.h:74-91`: `gfx_init/destroy/start_frame/run/end_frame`,
`gfx_set_target_fps`, `gfx_set_maximum_frame_latency`,
`gfx_texture_cache_clear` (C), `gfx_create_framebuffer` (C),
pixel-depth queries, `gfx_push_current_dir`,
`gfx_check_image_signature`, `gfx_register_blended_texture`; globals
`gfxFramebuffer`, `gfx_current_*dimensions`, `gfx_msaa_level`.
**Defined but undeclared** (consumers hand-declare):
`gfx_get_dimensions`, `gfx_set_framebuffer`, `gfx_reset_framebuffer`,
`clearMtx`. None of this is exported through
`include/libultraship/` — consumers include `graphic/Fast3D/gfx_pc.h`
off the public `src/` include dir.

## Dead/oddities ledger

D3D12 (above; GLX deleted in 1.2.0); SDL's `get_time` returns 0.0, `can_disable_vsync`
returns false, `set_maximum_frame_latency` is a no-op; empty
`on_resize`/`finish_render` bodies in GL/Metal; leftover breakpoint
hook (`:1928`) and unused `int dummy` (`:2444`); `gfx_destroy` frees
nothing (TODO at `:3077`).
