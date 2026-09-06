# Mario 64 book: chapter outline (the teachable arc)

**Status:** decisions made 2026-09-06 — (1) MIXTURE: the 'follow one frame'
spine is the BLACK BOX; links open the white-box detail chapters (click for
depth). (2) Granularity fine for now. (3) Ch9 (lighting) placement fine.
Authoring in this order.
**Priority:** 3
**Difficulty:** 4
**Part of:** `mario64-sphinx-book.md` (umbrella)

## BLUF

A proposed chapter sequence for the book, for a reader who has finished
`modelviewprojection`. It starts from the math they know, recasts it in a real
engine's terms, then expands into everything a linear-algebra course omits —
glossing early, pushing depth into later chapters and appendices (each backed
by a `tasks/reference/mario64/` note). This is a **proposal to reshape
together**, not a locked plan.

## Principle

The student knows the model-view-projection math and rotors. So the book does
NOT re-teach that; it shows what a shipping game does *differently* and *in
addition*. One running thread — "follow one frame from game logic to pixels" —
gives the sequence a spine, the way mvp uses one running example.

## Proposed sequence

**Part I — From your math to a real engine** (the familiar, recast)
1. Introduction — *written*.
2. Rotation: Euler angles vs rotors — *written* (the warm-up: same rotation,
   very different choice). ← `rotation-euler-vs-rotors`
3. The engine's math: vectors, matrices, and the scene graph — mutable arrays,
   fixed-point matrices, the transposed convention, composition down a tree.
   ← `vectors-…`, `matrices-…`, `transformations`, `scene-graph-…`
4. The camera as a system — Lakitu, modes, collision-aware placement.
   ← `camera-system`
5. Projection and field of view — perspective, plus the orthographic you
   never implemented. ← `field-of-view-and-projection`

**Part II — The graphics pipeline** (after the model matrix)
6. One frame's journey: N64 display list → Fast3D → GPU. ← `graphics-pipeline`,
   `frame-interpolation`
7. The color combiner and generated shaders. ← `color-combiner-…`,
   `shaders-and-gpu`
8. Textures, sampling, and HD assets. ← `textures-…`, `sampling-…`,
   `alternate-and-hd-assets`
9. Lighting and the look of a surface. ← `lighting-illumination-reflection`

**Part III — Making a world feel alive**
10. Animation: skeletal keyframes. ← `animation`
11. Collision detection. ← `collision-detection`
12. Effects: skybox, water, transparency, the wobbling paintings. ←
    `skyboxes`, `water-…`, `transparency-…`, `painting-wobble`
13. Smooth motion: 30 Hz logic → high-FPS render. ← `frame-interpolation`
14. Sound. ← `sound-processing`

**Appendices** (deep detail referenced from chapters)
- A. Fixed-point matrices and the `guMtxF2L` bridge.
- B. The binary-angle sine table.
- C. The geo-layout bytecode.
- D. Curves & splines (cutscene cameras).
- E. Pointer to the full reference set (`tasks/reference/mario64/`).

## How chapters get built (per-chapter child work)

Each chapter: write the narrative from its reference note(s); add the
`doc-region` markers its `literalinclude`s need (grows patch 0005 / the LUS
lane); draw the Graphviz/ASCII figures; build-verify HTML (+ the other formats
periodically). Authoring may spawn NEW reference docs / deeper levels of detail
when a chapter finds a gap (the maintainer's standing expectation).

## Resolved (2026-09-06)

- **Structure = black box + white box.** The "one frame's journey" chapter is a
  black-box overview; each stage links (Sphinx `:doc:`/`:ref:`) to the white-box
  chapter that details it, and detail chapters link back up. A reader follows
  the frame at a high level and clicks through for depth. Chapters also keep the
  "Go deeper" links to the reference set.
- Granularity (~14 ch + appendices) and lighting at ch9 are fine as proposed.