# Reference: The color combiner — SM64's tiny fixed-function shading language

> **Provenance:** authored 2026-09-06 against LUS submodule `c151cc91`
> (1.3.1-544 fork). Anchors in `libultraship/src/fast/interpreter.cpp`.
> Part of the mario64 graphics set — map at [`README.md`](README.md).
> Feeds `shaders-and-gpu.md` (how this becomes a real shader) and
> `lighting-illumination-reflection.md`.

## TL;DR

The N64 shades every pixel with a **color combiner**: a two-stage unit that
computes, per stage ("cycle"), the formula **`out = (A − B) · C + D`** for
RGB and separately for alpha, where each of A, B, C, D is **selected** from a
small menu of inputs — texture texel 0/1, the primitive color, the
environment color, the per-vertex shade (lighting) color, constants 0/1, and
a few others. A material picks those selections with a single
`combine_mode` bitfield (`GfxDpSetCombineMode`, `:3677`). This is SM64's
entire "surface shading" language — no per-pixel lighting model, just a
configurable multiply-add over chosen inputs. `GenerateCC` (`:361`) decodes
the bitfield into the inputs a shader will use.

## 1. The formula and its inputs

Per cycle, for RGB and for alpha independently:

```
out = (A − B) · C + D
```

Each slot is a **mux code** naming an input. `GenerateCC` extracts them from
the packed `combine_mode` (`interpreter.cpp:370-378`):

```c
uint32_t rgbA = (key.combine_mode >> (i*28))      & 0xf;   // cycle i, RGB A
uint32_t rgbB = (key.combine_mode >> (i*28 + 4))  & 0xf;
uint32_t rgbC = (key.combine_mode >> (i*28 + 8))  & 0x1f;
uint32_t rgbD = (key.combine_mode >> (i*28 + 13)) & 7;
// ...alphaA..D similarly at +16
```

The selectable inputs (the "menu") include:

- **`TEXEL0` / `TEXEL1`** — the sampled texture color(s)
  (`textures-and-texture-mapping.md`);
- **shade** — the **per-vertex color from lighting**
  (`lighting-illumination-reflection.md`), the combiner's link to lighting;
- **primitive** and **environment** colors — per-material constants set by
  other commands;
- **`0` and `1`** — constants;
- LOD fraction, noise, and a few specials.

## 2. One or two cycles (`is2Cyc`)

A material runs the combiner **once or twice** (`is2Cyc`,
`interpreter.cpp:362`). Two cycles let one material do, e.g., a texture times
shade in cycle 1, then blend toward an environment color in cycle 2 — the
output of cycle 1 becomes an available input to cycle 2. That is the extent
of "programmability": two chained multiply-adds over a fixed input menu.

## 3. Normalization — degenerate selections collapse to 0

`GenerateCC` cleans up no-op configurations before they reach a shader
(`:389-401`): if `A == B` (so `A − B = 0`) or the multiplier `C` is the
zero mux, the whole term is forced to `G_CCMUX_0`. This shrinks the space of
distinct combiners, so the shader cache (`shaders-and-gpu.md`) holds fewer,
canonical programs. A teaching point: the "compiler" for this tiny language
does constant-folding.

## 4. Where it's set (`GfxDpSetCombineMode:3677`)

`GfxDpSetCombineMode(rgb, alpha, rgb_cyc2, alpha_cyc2)` is the command the
display list issues to install a combiner configuration; the per-draw
constant inputs (primitive/env colors, LOD fraction) are latched separately
in `LatchCombinerUniforms` (`:197`). So a material = a combine mode + its
latched constants + its textures.

## How this relates to the course

- **`modelviewprojection` ch20-21 (fragment shaders)** teach shading as
  arbitrary code you write in GLSL. The N64 combiner is the **ancestor**:
  a *fixed* shading pipeline you *configure* rather than program — one
  formula, `(A−B)·C+D`, with a menu of inputs and at most two stages. Seeing
  it makes concrete what "fixed-function" meant and why programmable shaders
  were such a leap: the combiner is the whole expressive budget a 1996 pixel
  had.
- **"Surface shading" here is input selection, not a lighting model.** There
  is no Phong/specular term to configure — the lighting result arrives
  pre-baked as the per-vertex *shade* input, and the combiner just mixes it
  with textures and colors. That division (lighting in the vertex stage,
  mixing in the combiner) is itself a lesson the course, with its free-form
  fragment shader, doesn't surface.
- **Gap filled:** the course has no notion of a fixed-function combiner or a
  configurable-vs-programmable shading unit; this is the missing historical
  and architectural rung between "no shaders" and "write your own."

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/interpreter.cpp` around the combine_mode decode in
  `GenerateCC` (`:370-401`): region `combiner_decode` — extracting A/B/C/D
  and the normalization fold.
- `libultraship/src/fast/interpreter.cpp` around `GfxDpSetCombineMode`
  (`:3677`): region `set_combine_mode` — installing a material's combiner.
