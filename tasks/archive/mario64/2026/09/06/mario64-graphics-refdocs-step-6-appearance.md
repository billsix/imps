# SM64 refdocs — Step 6: appearance (lighting, transparency, skybox, water, paintings)

**Status:** done — 2026-09-06 (lighting L2+L1+L0; transparency/skybox/water/paintings L2+L0). Archived same day.
**Priority:** 3
**Difficulty:** 6
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md` (and reads step 4's combiner doc)
**Next:** `mario64-graphics-refdocs-step-7-engine-systems.md`

## BLUF

Five docs on how the game LOOKS — lighting/reflection, transparency,
skyboxes, water, and the wobbling paintings. This is the **biggest course
gap** (the book omits lighting outright and has no transparency/skybox/
water), so it carries a lower priority-number than the other content
steps. Several were named directly by the maintainer ("how are those
paintings made to wobble?", water/transparency).

## Context

Read the umbrella, step 1's template, and step 4's
`color-combiner-and-surface-shading.md` (lighting/transparency are
expressed through the combiner). Bodies: mostly decomp `src/game/` with
LUS for the GPU-executed lighting. Anchors at Ghostship `49c5312a` / LUS
`c151cc91`.

## Docs & anchors (verify each before writing)

1. **`lighting-illumination-reflection.md`** — the #1 gap. Fast3D moves
   N64 lighting/texgen into the VERTEX SHADER:
   `interpreter.cpp:2243` `CalculateNormalDir`, light upload `:2887-2913`
   (point-light support `is_point:2908`). Decomp supplies `Lights1`/
   ambient via GBI in actor/geo DLs. Reflection = env-map (see paintings)
   + shadow projection `src/game/shadow.c`. *Teaching angle:* diffuse
   vertex lighting, normals, ambient+directional — the lighting the book
   says it does NOT cover (ch20:71-72, ch03:175). **No Phong/specular
   per-pixel model here** — say so; SM64 is vertex (Gouraud-style)
   lighting.
2. **`transparency-and-blending.md`** — standard N64 alpha-blend layers
   via the combiner (see step 4's doc); render-layer/blend-mode buckets
   in the master display list (`rendering_graph_node.c`
   `geo_process_master_list_sub:149`, layer buckets). *Teaching angle:*
   draw order, alpha layers, and blending — absent in the course
   (no `GL_BLEND`). Keep tight; it leans on the combiner doc.
3. **`skyboxes.md`** — `src/game/skybox.c`: `struct Skybox:59`,
   `sSkyboxTextures[10]:77`, tile vertex build `make_vertex:212+`, FOV
   pinned to 90° in `draw_skybox_facing_camera` (`:132`), per-camera-yaw
   column/scroll indexing. *Teaching angle:* a skybox as a
   camera-locked textured backdrop — absent in the course.
4. **`water-and-moving-textures.md`** — moving-texture water in
   `src/game/moving_texture.c` (movtex overview `:20-51`, per-vertex
   alpha `:103`, `gMovtexIdToTexture[]:132` incl. water/mist/lava), water
   level `gWdwWaterLevelSet:122`; quads/boxes via
   `src/port/importer/MovtexFactory.cpp`/`MovtexQuadFactory.cpp`.
   *Teaching angle:* water as scrolling alpha-blended movtex geometry.
   **Be precise:** there is NO refraction shader (grep `refract` in
   shaders = none); the "pseudo-refraction" is scrolling movtex + alpha,
   not a GPU refract pass.
5. **`painting-wobble.md`** — asked by name. `src/game/paintings.c`:
   ripple math `painting_ripple_x:303` / `calculate_ripple_at_point:614`,
   mesh deform `painting_generate_mesh:680`, per-triangle envmap normals
   `painting_calculate_triangle_normals:712`, ripple state machine
   (`:28-59`); neighbor-tri lighting table
   `seg2_painting_mesh_neighbor_tris` (bin); port data via
   `src/port/importer/PaintingFactory.cpp`. *Teaching angle:* CPU mesh
   deformation (a sinusoidal ripple over a grid) + per-vertex recomputed
   normals for the env-map shimmer — a great "vertex animation +
   lighting" worked example.

## Verification & done-state

Anchors resolve at the pin; each doc has the banner + course-comparison;
the lighting doc states the no-per-pixel-specular boundary; the water doc
states the no-refraction-shader fact. Note candidate `doc-region` spans
(the ripple math is a lovely `literalinclude`). Stage the five docs;
archive this step on completion.
