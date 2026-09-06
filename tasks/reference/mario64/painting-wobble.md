# Reference: The wobbling paintings — CPU vertex-deform + recomputed normals

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/game/paintings.c`. Part of the mario64 graphics set — map
> at [`README.md`](README.md). Companions:
> `lighting-illumination-reflection.md` (env-map reflection),
> `scene-graph-and-data-structures.md`.

## TL;DR

The castle paintings ripple because the game **moves their mesh vertices on
the CPU every frame** and then **recomputes the surface normals** so the
lighting shimmers with the wave. The displacement is a **radial traveling
wave**: each vertex is pushed out of the painting plane by
`rippleMag · cos(rippleRate · 2π · (time − distanceFromRippleOrigin))`
(`calculate_ripple_at_point:614`). `painting_generate_mesh` (`:680`) applies
that to every vertex; `painting_calculate_triangle_normals` (`:712`)
rebuilds the normals from the deformed mesh, which — through environment
mapping — makes the surface glint as it undulates. A small state machine
(`:28-59`) drives when and where ripples start.

## 1. The wave (`calculate_ripple_at_point:614`)

```c
f32 rippleZ = rippleMag * cosf(rippleRate * (2 * M_PI) * (rippleTimer - rippleDistance));
```

Read it as a **traveling ripple on a pond**:

- `rippleDistance` = how far this vertex is from where the ripple was
  triggered (Mario's entry point). Subtracting it inside the cosine makes the
  wave **arrive later** the farther out you are — the ring expands outward.
- `rippleTimer` advances each frame, so the phase moves — the wave travels.
- `rippleRate` sets spatial/temporal frequency; `rippleMag` the amplitude,
  which **decays** over time so the ripple settles (the state machine resets
  to idle when magnitude gets small, `:55-59`).

The result is a per-vertex Z offset (out of the painting's flat plane).

## 2. Deform the mesh, then rebuild normals

`painting_generate_mesh` (`:680`) walks the painting's grid of vertices and
adds each one's `rippleZ`, producing a rippled surface **on the CPU** (there
is no vertex shader doing this — it's decomp C, per vertex, per frame).
Crucially, `painting_calculate_triangle_normals` (`:712`) then **recomputes
each triangle's normal** from the moved vertices, using a neighbor-triangle
table (`seg2_painting_mesh_neighbor_tris`). Fresh normals are the whole point:
the painting is **environment-mapped** (`lighting-illumination-reflection.md`
§3 — texture addressed by normal), so as the normals tilt with the wave, the
reflected image slides across the surface and it **glints**. Deform without
recomputing normals would ripple the shape but not the shine.

## 3. The state machine (`:28-59`)

Paintings sit in states IDLE / RIPPLE / PROXIMITY / CONTINUOUS, triggered by
Mario approaching or entering (passive vs. entry ripples, left/middle/right —
`:64-89`). PROXIMITY paintings ripple when Mario is near and settle to IDLE;
CONTINUOUS ones ripple perpetually. So "when does it wobble" is a tiny
per-painting controller, separate from "how it wobbles" (§1-2).

## How this relates to the course

- **This is vertex animation + lighting, both absent from the course.** The
  course's geometry is rigid; here a mesh is *reshaped every frame by a math
  function*, which is the essence of procedural vertex animation (waves,
  cloth, flags). The traveling-wave formula is a clean, liftable example.
- **The normal-recompute is the subtle lesson.** It connects directly to the
  lighting doc: shading depends on normals, so *animating geometry means
  animating normals* or the lighting goes stale. A student who lit a static
  mesh in the course sees here what moving that mesh actually entails.
- **A worked answer to a concrete "how do they do that?"** — the paintings
  are a memorable effect, and the mechanism (CPU wave deform + env-map +
  fresh normals) is both simple and complete. It also pairs with
  `water-and-moving-textures.md` as the contrast: water animates *texture
  coordinates* (cheap, no geometry change), paintings animate *vertices*
  (more work, real shape change) — two different animation strategies for two
  different looks.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/paintings.c` around `calculate_ripple_at_point` (`:614-641`):
  region `ripple_traveling_wave` — the cosine wave with distance delay.
- `src/game/paintings.c` around `painting_generate_mesh` (`:680`): region
  `deform_painting_mesh` — apply the per-vertex displacement.
- `src/game/paintings.c` around `painting_calculate_triangle_normals`
  (`:712`): region `recompute_normals` — fresh normals for the env-map glint.
