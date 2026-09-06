# Reference: Textures & texture mapping — N64 formats, tiles, palettes

> **Provenance:** authored 2026-09-06 against LUS submodule `c151cc91`
> (1.3.1-544 fork). Anchors in `libultraship/src/fast/interpreter.cpp`.
> Part of the mario64 graphics set — map at [`README.md`](README.md).
> Companions: `sampling-and-mipmapping.md`, `alternate-and-hd-assets.md`,
> `color-combiner-and-surface-shading.md` (texels are combiner inputs).

## TL;DR

A texture in SM64 is a **small, oddly-formatted N64 image** that the
interpreter **decodes and uploads** to the GPU on demand. `ImportTexture`
(`interpreter.cpp:1985`) dispatches on the N64 **format** (RGBA, CI, IA, I)
and **bit size** (4/8/16/32-bit) to a per-format decoder
(`ImportTextureRgba16:916`, `ImportTextureCi8:1371`, …). **CI (color-index)**
textures are palettized — the pixels are indices into a **TLUT** palette.
A **tile descriptor** holds the format, size, and **wrap/clamp/mirror**
modes (`cms`/`cmt`); texture coordinates address into it. Decoded results
are **cached** (`TextureCacheLookup:806`) so a texture is converted once.

## 1. Formats and the dispatcher (`ImportTexture:1985`)

The N64 stored textures in several compact formats; the interpreter decodes
each to RGBA for the GPU:

```c
uint8_t fmt = mRdp->texture_tile[tile].fmt;   // G_IM_FMT_RGBA / CI / IA / I
uint8_t siz = mRdp->texture_tile[tile].siz;   // G_IM_SIZ_4b / 8b / 16b / 32b
switch (fmt) {
  case G_IM_FMT_RGBA: siz==16b ? ImportTextureRgba16 : ImportTextureRgba32; break;
  case G_IM_FMT_IA:   ...   // intensity + alpha
  case G_IM_FMT_CI:   ...   // color index (palette)
}
```

- **RGBA16** (5/5/5/1) is the common wall/object texture — 16 bits, 1 alpha
  bit. **RGBA32** is rare (higher quality). **IA** is intensity+alpha
  (greyscale-ish, text/effects). **CI** is palettized.
- Each decoder unpacks the N64 bit layout into a full RGBA buffer the GPU
  can sample. This is where "what a texel *is*" gets concrete: a 16-bit
  RGBA16 pixel is bit-unpacked into four 8-bit channels.

## 2. Color-index textures and the TLUT (palette)

For `G_IM_FMT_CI` (`:2035`), each pixel is an **index** into a **TLUT**
(texture lookup table = palette) loaded separately by `GfxDpLoadTlut`. The
cache key includes the palette DRAM address and a `paletteIndex`
(`:1985`), so the same index data with a different palette is a different
texture. This is classic indexed-color — one small palette, many pixels
referencing it — a memory-saving scheme the course never touches.

## 3. Tile descriptors — wrap, clamp, mirror (`cms`/`cmt`)

A **tile** (`mRdp->texture_tile[tile]`) is the N64's texture binding: format,
size, size in bytes per line, and the **addressing modes** for S and T
(horizontal/vertical texture axes):

```c
bool clampS = (mRdp->texture_tile[tile].cms & G_TX_CLAMP) != 0;   // :947
bool clampT = (mRdp->texture_tile[tile].cmt & G_TX_CLAMP) != 0;
```

`cms`/`cmt` encode **wrap / clamp / mirror** per axis — how a texture
coordinate outside `[0,1)` is handled (tile it, clamp to edge, or mirror).
These map directly to the GPU sampler's address modes
(`sampling-and-mipmapping.md`). Texture *coordinates* themselves ride on the
vertices and are scaled by `GfxSpTexture`; the combiner then samples the
tile as `TEXEL0`/`TEXEL1` (`color-combiner-and-surface-shading.md`).

## 4. The texture cache (`TextureCacheLookup:806`)

Before decoding, the interpreter checks a cache keyed by
`(address, palette, fmt, siz, paletteIndex, size)` (`:2069`). A hit reuses
the already-uploaded GPU texture; a miss decodes + uploads (`UploadBaseTexture`)
and inserts. So each distinct N64 texture is converted **once per session**,
not per draw — the texturing analogue of the shader cache
(`shaders-and-gpu.md`).

## How this relates to the course

- **`modelviewprojection` explicitly EXCLUDES texturing** (ch20:62 lists it
  as not covered). So this whole doc is a clean gap-fill: what a texture is,
  what a texel and a texture coordinate are, palettized (indexed) color, and
  the wrap/clamp/mirror addressing that decides what happens off the edge.
- **Concrete "texture mapping":** the vertices carry coordinates, the tile
  says how to address the image, the sampler fetches a texel, and the
  combiner mixes it. The course teaches vertices→pixels but stops before any
  of this; SM64 shows the full texturing path a real material uses.
- **Gap filled:** N64 texture *formats* (RGBA16, CI+TLUT, IA) are a bonus
  lesson in compact image encodings — decoding, palettes, bit-unpacking —
  that no linear-algebra course would include.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/interpreter.cpp` around `ImportTexture`
  (`:1985-2130`): region `texture_format_dispatch` — format/size → decoder.
- `libultraship/src/fast/interpreter.cpp` around `ImportTextureRgba16`
  (`:916`): region `decode_rgba16` — bit-unpacking a 5551 texel.
- `libultraship/src/fast/interpreter.cpp` around the `cms`/`cmt` reads
  (`:947-948`): region `tile_wrap_modes` — clamp/wrap/mirror addressing.
