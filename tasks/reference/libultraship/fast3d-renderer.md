# libultraship — Fast3D renderer

> **Pinned:** libultraship **1.3.1-482**
> (`2917d0f4fe62c579174561dcd34f327c9410bb72`, 2026-07-29 —
> BanjoKazooie's pin; direct descendant of 1.3.1-397, 85 commits).
> Updated 2026-09-01, iteration 16 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## Shape

`Fast::Interpreter`, `src/fast/interpreter.cpp` — grown 4690 → **5501
lines** in this range. Backend headers moved under
`include/fast/backends/`. Port entry stays `Fast::Fast3dWindow`
(`windowing-gui-input.md`); GUI split into `Fast::Fast3dGui`.

## The GBI interpreter — tables, not a switch (re-anchored)

`UcodeHandler` `interpreter.cpp:4630`; tables `rdpHandlers :4654`,
`otrHandlers :4689`, `f3dex2Handlers :4730`, `f3dexHandlers :4751`,
`f3dHandlers :4774`, `s2dexHandlers :4798`; `gfx_step()` `:4863` with
OTR → RDP → current-ucode order (`:4889-4917`); handlers return bool =
"I advanced the pointer"; unknown opcodes `SPDLOG_CRITICAL`
(`:4918/:4922`). `GfxExecStack` `interpreter.h:143-169`; `Run` `:5131`.
Runtime multi-ucode + `GfxExecStack` + self-modifying OTR handlers
(`:4054` caching-disabled OTRTODO, `:4063` `// TODO: wtf??`) all as
before.

**OTR opcodes — RENUMBERED ≥0x44** (`include/fast/lus_gbi.h:39-77`):
`G_LOAD_SHADER` (0x43) is **gone**, replaced by `OTR_G_PUSH_SHADER`
0x43 / `OTR_G_POP_SHADER` 0x44; `RDP_G_SETTILESIZE_INTERP` moved
0x44→**0x45**, `RDP_G_SETTARGETINTERPINDEX` 0x45→**0x46**. NEW:
`RDP_G_LOADBLOCK_WIDE` 0x47 (`interpreter.cpp:4254`), `RDP_G_VTX_WIDE`
0x48 / `RDP_G_TRI1_WIDE` 0x49 (`:4726-4727`), `RDP_G_SETTILESIZE_LERP`
0x4a (#1141). **Any asset or port built against 397's numbering
misreads 0x44+.**

**Frame interpolation is now an explicit port contract**: the port
writes `mInterpolationIndex` and the new `mInterpolationT` before each
`DrawAndRunGraphicsCommands` (documented at `interpreter.h:559-562`;
still garbage if it doesn't — declared uninitialized `:557`).
`G_SETTILESIZE_LERP` lerps tile coords by `mInterpolationT`
(`:4318-4340`), interpolated sizes rounded (#1164, `:584-592`, which
also returns 0 for undefined tile regions, #1135). The `Mtx*`→`MtxF`
matrix-replacement hook unchanged (`GfxSpMatrix` `:1489-1492`).

**Game hacks still baked in:** Bowser–Peach LOD `:2217`; widened fill
rects `:3053-3056`; 320×240 `interpreter.h:25-26`; `MAX_LIGHTS 32`.

## Shaders — Prism, custom shaders now LIVE

- Templates merged to **one file per backend**
  (`src/fast/shaders/{opengl/default.shader.glsl, directx/default.shader.hlsl,
  metal/default.shader.metal}`) with a `VERTEX_SHADER` prism context
  flag; still loaded **from the game archive** — missing `f3d.o2r`
  still aborts at first draw (`gfx_opengl.cpp:322-323`, `:388-389`).
  (The template header still says `type='fragment'` while serving both
  stages — cosmetic.)
- **The 397 "custom shaders are inert" bug cluster is fixed by
  redesign (#972/#1051)**: `G_PUSH_SHADER`/`G_POP_SHADER` maintain a
  shader **stack** (`gfx_push_shader` `:3514-3542` — validates the
  pointer, dedups against `mShaders`; `gfx_pop_shader` `:3544-3551`;
  drained in `Init` `:4929-4930`). Top-of-stack id packs into combiner
  options bits 17..32 (`SHADER_ID_SHIFT 17`, `interpreter.h:138-141`);
  `gfx_cc_get_features` widened to `(uint64_t, uint64_t, …)`
  (`:5395`); **all three backends now read `cc_features.shader_id`**
  and load `<name>.glsl/.hlsl/.metal` instead of the default template
  (`gfx_opengl.cpp:311-316`, `gfx_metal_shader.cpp:257`,
  `gfx_direct3d11.cpp:1443`; id→path via `gfx_get_shader`
  `:3553-3563`).
- Still true: `#version 110` VS / `#version 130` FS mismatch on
  desktop non-Apple GL (`gfx_opengl.cpp:365` vs `:298`; Apple `410
  core`, GLES `300 es`); the `SHADER_INPUT_5..7` gap
  (`shader_item_to_str` handles 1–4 only, `:111-117`/`:153-159` →
  `""` → compile-fail abort `:426/:440`) — and `gfx_cc_get_features`
  now even counts inputs up to 7 (`interpreter.cpp:5430`), so it's
  reachable on paper.
- NEW `gfx_shader_cache_clear()` C API (#1064, `:5488-5494`).

## New RDP/render features in this range

- **Chroma key / convert (#1089)**: `G_SETKEYR/GB` → `key_center`/
  `key_scale`, `G_SETCONVERT` K0–K5 sign-extended (`:2767`, handlers
  `:4385-4405`); CENTER/SCALE/K4/K5 as per-slot combiner inputs
  (`:282-292`, `:2233-2247`).
- **`G_SETPRIMDEPTH`/`G_ZS_PRIM` implemented** (#1080): `:3815-3819`,
  `:131-136`; `ShaderOpts::PRIM_DEPTH`.
- **`GfxDpSetBlendColor` finally implemented** (#1021/#1081): state
  `:2801-2806`, consumed for `G_BL_CLR_BL` fog-alpha blending
  (`:1876-1877`, `:2163-2167`).
- **Depth test requires `Z_CMP`** (#1059): `:1836-1839`.
- **1-cycle TEXEL1 slot fix** (#1055): `gfx_opengl.cpp:120-140`.
- **Partial depth clears** (#1046/#1173): fill-rect to the Z buffer →
  scissored `ClearDepthRegion` with aspect-adjusted coords
  (`:3011-3044`). The #1046 coverage simulation was **reverted**
  (#1073) — zero `coverage` hits at this pin.
- **FB texture passthrough** (#1046): `Register/UnregisterFbTexture`
  (`:4945-4951`) — `ImportTexture` binds a registered GPU FB directly,
  no CPU readback (`:1270-1279`).
- **`ReadFramebufferToCPU` on all three backends** (#1045): pure
  virtual `gfx_rendering_api.h:70`; Metal does a retained
  `waitUntilCompleted` + BGRA8→RGBA5551 CPU-side.
- **`fixedAspect` framebuffers** (#1109): `forceFixedAspect` threaded
  through `CreateFrameBuffer`; `AdjXForAspectRatio` skips widescreen
  adjustment for them (`:1559-1568`).
- `G_EX_INVERT_CULLING` now applies to **all** ucodes (#1091,
  `:1813-1815`).

## Texture path

- Cache **500 → 1024** entries (`interpreter.cpp:69`); key gained
  `palette_addrs[2]` + `palette_index` (#1044, `interpreter.h:181-196`
  — CI textures keyed by original DRAM palette pointer; multi-palette
  CI4, `:984-992`); hash still address-only. Rehash prevention
  (`reserve`, `:481-483`) and dangling-pointer nulling on eviction
  (#1041, `:505-560`).
- Import refactor (#1043): `GetEffectiveLineSize` DRAM-stride heuristic
  (`:568-577`), per-line 2D copy loops, RGBA32 TMEM-interleave; RAW
  block-load reshape for giant-line uploads (#1172/#1143,
  `:1233-1252`); wrap-period clamping of over-loaded masked textures
  (#1151, `:2023-2032`); clamp gating to mipmap-like/CLAMP/HD cases
  (#1090/#1118, `:2017-2041`); address filtering before deref (#1042,
  `gfx_check_image_signature` `:3466-3487`); null guards on every
  `ImportTexture*` (#1008).
- Decode buffer is now member `mTexUploadBuffer` (`interpreter.h:514`),
  freed in `Destroy()` (`:4993-4995`).
- Opt-in resolve memoization (#1175): `ResolveResourceCached`
  (`:450-471`), default off, hits-only, cleared with the texture cache.

## Verified bugs at this pin

- **NEW: `ColorCombinerKey.shader_id` is never assigned** — the struct
  gained the field (`interpreter.h:90-98`) but key construction sets
  only `combine_mode`/`options` (`:1942-1944`); the indeterminate field
  participates in the defaulted comparison. (The real id rides inside
  `options`; the field is vestigial.)
- **NEW: `cc_options |= -1 << SHADER_ID_SHIFT`** (`:1926`) —
  negative-left-shift; unmasks to id 0xFFFF → no shader found → default
  template; works by accident.
- Carried over: `mInterpolationIndex` garbage if the port doesn't write
  it; uninitialized `SDL_Renderer* mRenderer` deref on GL vsync toggle
  (`gfx_sdl.h:58`, `gfx_sdl2.cpp:426/:746`); `SHADER_INPUT_5..7`;
  VS-110/FS-130; SDL `GetTime()` 0.0 (`:756-758`),
  `SetMaxFrameLatency` no-op (`:768-770`), GL swap under Metal
  (`:750`); DXGI still the only real frame pacer.
