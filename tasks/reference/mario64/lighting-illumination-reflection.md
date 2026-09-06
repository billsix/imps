# Reference: Lighting, illumination & reflection — vertex Gourand, N64-style

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a` /
> LUS `c151cc91`. Anchors in `libultraship/src/fast/interpreter.cpp` and
> the decomp (`src/game/shadow.c`, actor DLs). Part of the mario64 graphics
> set — map at [`README.md`](README.md). L1:
> [`lighting-illumination-reflection-overview.md`](lighting-illumination-reflection-overview.md).
> Companions: `color-combiner-and-surface-shading.md`, `shaders-and-gpu.md`,
> `painting-wobble.md` (env-map reflection).

## TL;DR

SM64 lighting is **per-vertex diffuse** (Gouraud): each vertex's normal is
dotted with one or more **directional lights** to produce a **shade color**,
which is then interpolated across the triangle and fed to the color combiner
as an input (`vShade`). There is **no per-pixel Phong/specular model.** In
the fork, this vertex lighting runs **in the generated vertex shader**
(`interpreter.cpp:2383` "Lighting and texgen now run in the vertex shader");
`CalculateNormalDir` (`:2243`) prepares each light. Reflection is faked two
ways: **environment mapping** (texgen from the normal — used by the shiny
paintings, `painting-wobble.md`) and **projected blob shadows**
(`shadow.c`), not real reflections.

## 1. The model: normal · light → shade (directional, diffuse)

Each N64 light is a **direction + color**. Lighting a vertex is: for each
light, `dot(normal, light_dir)` scales the light's color; sum over lights,
add ambient; the result is the vertex's shade. `CalculateNormalDir`
(`:2243`) pre-transforms each light direction into the model's space via the
transposed matrix (so normals stay correct under the model transform):

```c
float light_dir[3] = { light->dir[0]/127.f, light->dir[1]/127.f, light->dir[2]/127.f };
TransposedMatrixMul(coeffs, light_dir, ...);   // light dir into normal space
```

Lights are re-uploaded only when `lights_changed` (`:2386`), then applied to
every vertex. **Diffuse only** — the dot product gives Lambertian shading;
there is no view-dependent specular highlight in the base model.

## 2. It runs in the vertex stage, and arrives at the shader as `vShade`

The comment at `:2383` is the crux: lighting and texgen happen in the
**vertex** shader, not per fragment. So by the time a pixel is shaded, its
lighting is already a single interpolated color — the combiner
(`color-combiner-and-surface-shading.md`) just **mixes** that `vShade` with
textures and tints (it's combiner input 7, `shaders-and-gpu.md` §1). This is
the division of labor to remember: **lighting is computed on vertices;
shading (mixing) is done in the combiner.** Gouraud, not Phong.

## 3. "Reflection" without reflections

SM64 has no reflective surfaces, but fakes the look two ways:

- **Environment mapping (texgen):** a texture is addressed by the vertex
  **normal direction** instead of UVs, so a surface appears to mirror a
  fixed environment texture as it turns. The shiny, rippling **paintings**
  use this (`painting-wobble.md` recomputes per-triangle normals precisely
  to drive it). It is a normal-to-texcoord trick, not a reflection pass.
- **Shadows (`shadow.c`):** a self-contained subsystem projecting a **blob
  or geometry-shaped shadow** onto the floor below an object, with a
  solidity/alpha 0-255 (`shadow.c:24-43`). It is a drawn dark decal placed
  by a floor raycast (`collision-detection.md`), not a shadow-map or ray.

## How this relates to the course

- **`modelviewprojection` says outright it does NOT cover lighting**
  (ch20:71-72, ch03:175 "we are not using lighting to add realism"). This
  is the **single biggest gap the whole set targets.** SM64 fills it with
  the simplest real model: per-vertex diffuse (Gouraud) directional lights.
- **Gouraud vs. Phong is the lesson.** SM64 lights *vertices* and
  interpolates the color (cheap, slightly flat, can miss highlights inside a
  triangle); the modern default the course would build toward lights *every
  pixel* (Phong). Seeing SM64's vertex lighting makes the trade concrete —
  and explains why big flat N64 polygons look the way they do.
- **`geometricalgebra` uses "normal" only to mean `normalize`** — it has no
  lighting concept. So the very idea of a surface normal *driving shading*
  (and env-map reflection) is new here relative to both courses.
- **Gap filled:** diffuse lighting, ambient, the normal's role in shading,
  Gouraud interpolation, fake reflection (env-map), and projected shadows —
  none in either course, all foundational to how any lit 3D scene looks.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/interpreter.cpp` around `CalculateNormalDir`
  (`:2243-2247`): region `light_dir_to_normal_space` — the transposed-matrix
  light transform.
- `libultraship/src/fast/interpreter.cpp` around the vertex-lighting apply
  (`:2383-2388`): region `apply_vertex_lighting` — dot normals with lights.
- `src/game/shadow.c` around `struct Shadow` (`:24-48`): region
  `shadow_subsystem` — projected blob shadows.
