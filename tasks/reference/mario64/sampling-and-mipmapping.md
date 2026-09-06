# Reference: Sampling & mipmapping — filtering, wrap modes, and the mip chain

> **Provenance:** authored 2026-09-06 against LUS submodule `c151cc91`
> (1.3.1-544 fork). Anchors in `libultraship/src/fast/interpreter.cpp` and
> `backends/gfx_vulkan.cpp`. Part of the mario64 graphics set — map at
> [`README.md`](README.md). Companions: `textures-and-texture-mapping.md`,
> `absent-topics.md` (the "RT64 mipmapping" clarification).

## TL;DR

When a triangle samples a texture, the GPU **sampler** decides how: whether
to interpolate between texels (**nearest** vs **linear/bilinear**), how to
handle coordinates off the edge (**wrap / clamp / mirror**), and — in the
fork — whether to blend between **mip levels** (trilinear) using an
**auto-generated mip chain**. The Vulkan backend picks a sampler with
`GetSampler(linear, cms, cmt, autoMipmap)` (`gfx_vulkan.cpp:532`); the fork
builds HD mip chains with `UploadMipChain` (`interpreter.cpp:1950`). The N64
had a two-texel LOD mode; the fork extends it to real mipmapping for HD
texture packs.

## 1. Filtering: nearest vs linear (`GetSampler`)

```c
VkSampler GfxRenderingAPIVK::GetSampler(bool linear, uint32_t cms, uint32_t cmt, bool autoMipmap);  // :532
// ... tex.sampler = GetSampler(linear_filter, cms, cmt, tex.auto_mipmaps);  // :1379
```

- **`linear`** = bilinear filtering: sample the four nearest texels and
  interpolate, giving smooth (blurry) magnification. **`false`** = nearest:
  pick one texel, giving crisp blocky pixels. The N64 mostly used bilinear;
  the choice rides on the tile's filter setting.
- This is the sampler-level answer to "the texture is bigger/smaller than
  the triangle on screen" — the sampling problem the course names but never
  addresses.

## 2. Wrap modes come from the tile (`cms`/`cmt`)

`GetSampler` takes `cms`/`cmt` — the same clamp/wrap/mirror flags the tile
descriptor carries (`textures-and-texture-mapping.md` §3) — and maps them to
the GPU sampler's address modes. So "what texel do I get at coordinate 1.7?"
is answered here: wrap → 0.7, clamp → 1.0 (edge), mirror → 0.3.

## 3. Mipmapping — the fork's addition (`UploadMipChain:1950`, `autoMipmap`)

A **mip chain** is the texture pre-shrunk to 1/2, 1/4, … so a distant,
minified triangle samples a small level instead of aliasing a big one.

- The N64 had a limited two-level LOD scheme: `TEXEL1` could sample "the next
  mip level of texture 0" in MIP_LOD mode (`interpreter.cpp:616`), with the
  combiner blending by a LOD fraction (`:248-270`).
- The **fork generalizes this to true mipmaps**: `UploadMipChain(baseTile)`
  (`:1950`) builds a full chain for HD textures (only the base slot carries
  a chain, `:2710`), and `GetSampler(..., autoMipmap=true)` (`:532`) selects
  a **trilinear** sampler that interpolates *between* mip levels. This is the
  "smooth at all distances" path HD texture packs need.

## 4. This is what "RT64 mipmapping" actually is

People call the fork's auto-mip + trilinear feature "RT64 mipmapping," which
sounds like ray tracing. It is not — see `absent-topics.md`. It is exactly
§3: `UploadMipChain` + `GetSampler(autoMipmap)`. No rays, no path tracing;
just texture LOD done well.

## How this relates to the course

- **`modelviewprojection` does not cover sampling** (only rasterizer
  interpolation, ch20:161). So filtering (nearest vs bilinear), wrap modes,
  and mipmapping are all gap-fills. Mipmapping in particular is a lovely,
  concrete lesson: *why* a minified texture aliases, and how a pre-filtered
  pyramid fixes it — visible in any 3D game, absent from the course.
- **Sampling as the inverse of rasterization:** the course interpolates
  *vertex* attributes across a triangle; sampling interpolates *texels*
  across the texture the triangle maps to. Same "in-between values" idea,
  applied to the image instead of the geometry.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/backends/gfx_vulkan.cpp` around `GetSampler`
  (`:532`): region `sampler_selection` — filter + wrap + mipmap → VkSampler.
- `libultraship/src/fast/interpreter.cpp` around `UploadMipChain` (`:1950`):
  region `build_mip_chain` — generating the HD mip pyramid.
