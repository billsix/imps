# Reference: Water & moving textures — scrolling alpha quads (no refraction)

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/game/moving_texture.c`. Part of the mario64 graphics set —
> map at [`README.md`](README.md). Companions: `transparency-and-blending.md`,
> `textures-and-texture-mapping.md`.

## TL;DR

SM64 water is **scrolling, alpha-blended textured geometry** — the same
"moving texture" (movtex) system that also does sand, haze, mist, and
treadmills (`moving_texture.c:20`). A water surface is a mesh of quads whose
**texture coordinates scroll** over time and whose **per-vertex alpha** makes
it translucent (`struct` field `a`, `:103`). There is **no refraction
shader** — the "underwater looks bent" impression is scrolling texture + a
color/alpha tint, not a GPU refraction pass (verified: `grep refract` in the
shaders is empty). Water level is a gameplay value (`gWdwWaterLevelSet`)
separate from the visual mesh.

## 1. Movtex — one system, many surfaces (`:20-51`)

```
// (abbreviated movtex) ... used for water, sand, haze, mist and treadmills.
```

A movtex surface is defined by a `MovtexObject`/`MovtexQuad`
(`:83`, `:47`): a mesh with a texture index into `gMovtexIdToTexture`
(`:86`), a Y position, and per-vertex attributes. A geo node carries an **id**
that selects which `MovtexQuadCollection` to draw (`:48`). So water isn't a
special-case renderer — it's an instance of a general scrolling-surface
system shared with several other effects.

## 2. The animation: scroll the texture coordinates

Each frame the movtex code advances the surface's **S/T texture offsets**, so
the water texture slides across the fixed geometry — the illusion of flowing
water without moving a single vertex. This is the cheapest possible "animated
surface": the mesh is static; only the *coordinates into the texture* change.
(Contrast the paintings, `painting-wobble.md`, which move the actual
vertices.)

## 3. Transparency and the "pseudo-refraction"

Water quads live in a **transparent render layer**
(`transparency-and-blending.md`) with a per-vertex **alpha** (`:103`), so the
scene shows through them, tinted. What looks like refraction or caustics is
just: a translucent tinted surface + a scrolling texture + the world visible
underneath. **No GPU refraction, no reflection of the scene** — the honest
mechanism is much simpler than the effect suggests, which is exactly the kind
of thing worth documenting so it isn't over-imagined.

## How this relates to the course

- **Neither course covers water, animated textures, or transparency**, so
  this is a triple gap-fill. The key lesson is **texture-coordinate animation**:
  you can animate a surface convincingly by changing what part of a texture it
  samples over time, with zero geometry change — a technique with no analogue
  in a static linear-algebra course.
- **"Effects are cheaper than they look":** water here is transparency + a UV
  scroll, not a physical simulation. Naming the trick (and the absent
  refraction) is as valuable as any formula — it calibrates a student's sense
  of how games fake realism.
- **Depends on the transparency doc:** water is the marquee consumer of the
  render-layer/alpha machinery, so read the two together.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/moving_texture.c` around the movtex overview + `MovtexObject`
  (`:20-51`, `:83`): region `movtex_model` — one system for water/sand/mist.
- `src/game/moving_texture.c` around the per-vertex alpha field (`:103`):
  region `movtex_vertex_alpha` — where translucency lives.
