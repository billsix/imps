# SM64 refdocs — Step 5: textures, sampling & alternate assets

**Status:** done — 2026-09-06 (textures, sampling, HD assets; all L2+L0). Archived same day.
**Priority:** 4
**Difficulty:** 5
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md`
**Next:** `mario64-graphics-refdocs-step-6-appearance.md`

## BLUF

Three docs on texturing — mapping/decode, sampling/mipmapping, and the
alternate/HD asset path (which the maintainer specifically admires). The
course EXCLUDES texturing entirely (ch20:62), so this is a clean gap fill.
Mostly libultraship; extends the existing `asset-pipeline.md` for the
HD-asset runtime resolution.

## Context

Read the umbrella and step 1's template; skim `asset-pipeline.md` (the
ROM→`.o2r`→runtime story) so the HD-asset doc extends it, not repeats it.
Bodies: LUS `Ghostship/libultraship/`. Anchors at LUS `c151cc91`.

## Docs & anchors (verify each before writing)

1. **`textures-and-texture-mapping.md`** — upload/decode per N64 format:
   `interpreter.cpp` `ImportTexture*` family (`ImportTextureRgba16:916` …
   `ImportTextureCi8:1371`, dispatcher `ImportTexture:1985`); tile
   descriptors `GfxDpSetTile:3372`/`GfxDpSetTileSize:3404`, TLUT
   `GfxDpLoadTlut:3413`, load block/tile `:3457`/`:3557`, tex-coord scale
   `GfxSpTexture:3333`; texture cache `TextureCacheLookup:806`. *Teaching
   angle:* what a texture, a UV/tex-coord, a tile, and a palette (TLUT)
   ARE, shown by a real decoder — the course has none of this.
2. **`sampling-and-mipmapping.md`** — filtering + auto-mip sampler
   selection in Vulkan `gfx_vulkan.cpp:532`
   `GetSampler(bool linear,…,bool autoMipmap)`; HD mip-chain generation
   `interpreter.cpp:1950` `UploadMipChain` (+ `UploadBaseTexture:1863`);
   LOD-fraction combiner inputs `:248-270`. *Teaching angle:* nearest vs.
   linear filtering, mip levels, and LOD — the sampling topic absent from
   the course. Cross-link `absent-topics.md`: this is the real "RT64
   mipmapping," NOT ray tracing.
3. **`alternate-and-hd-assets.md`** — runtime alt-asset resolution in
   `libultraship/src/ship/resource/ResourceManager.cpp`
   (`IsAltAssetsEnabled:452`, alt-prefix path logic `:111/:136/:255`);
   interpreter honors replacements via the `importReplacement` flag +
   `mMaskedTextures`/`GetBaseTexturePath` (`interpreter.cpp:920+`),
   HD-clamp handling `:949`; archive load from `.o2r` in
   `ship/resource/archive/O2rArchive.cpp`. *Teaching angle:* how a
   base-game texture is transparently swapped for a high-res authored one
   at load — the "they look great!" path — and what constraints (clamp,
   masking) HD replacement imposes. Extends `asset-pipeline.md`.

## Verification & done-state

Anchors resolve against the pinned submodule; each doc has the banner +
course-comparison; the HD-asset doc links `asset-pipeline.md` rather than
restating it; the sampling doc cross-links `absent-topics.md`. Note
candidate `doc-region` spans. Stage the three docs; archive this step on
completion.
