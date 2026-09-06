# SM64 refdocs — Step 2: math & transforms

**Status:** done — 2026-09-06. Four topics: vectors (L2+L0), matrices
(L2+L1+L0), transformations (L2+L0), rotation showpiece (L2+L1+L0).
Archived same day.
**Priority:** 4
**Difficulty:** 4
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md` (do not start until step 1 lands — needs the template)
**Next:** `mario64-graphics-refdocs-step-3-camera-projection.md`

## BLUF

Four reference docs on the engine's vector/matrix/transform math, each
compared to how the maintainer teaches it. The headline is the **rotation
comparison**: SM64's fixed-point Euler binary angles vs. the course's GA
rotors. These topics overlap what the courses cover, so keep them SHORT
on the math and long on the delta ("here is the same idea in a shipping
30 Hz engine, in fixed point, at scale").

## Context

Read the umbrella (house style, gap analysis) and step 1's template.
Bodies: mostly decomp `src/engine/math_util.c` + `src/game/`, with the
port-side matrix pool. All anchors are at Ghostship `49c5312a`.

## Docs & anchors (from the seam-map — verify each before writing)

1. **`vectors-and-vector-math.md`** — `src/engine/math_util.c:33-157`:
   `vec3f_copy/set/add/sum`, `vec3f_cross:137`, `vec3f_normalize:145`,
   `vec3f_to_vec3s:116`. Note: **dot products are inlined at call sites**
   (no standalone `vec3f_dot`) — a teaching point about hand-optimized
   decomp. Types `Vec3f`/`Vec3s` in `include/types.h`. *Course link:*
   `modelviewprojection` ch05 Vector class, mathhomework1.
2. **`matrices-and-linear-algebra.md`** — builders in `math_util.c`
   (`mtxf_identity:171`, `mtxf_mul:501`, `mtxf_to_mtx:585`), fixed-point
   conversion `guMtxF2L` wrapped at `:589`; port matrix pool/recording
   `src/port/interpolation/matrix.c` (`gMainMatrixStack[]:20`, `guMtxF2L`
   `:353`/`:358`), `src/port/Matrix.cpp`. *Teaching angle:* float `MtxF`
   vs. N64 fixed-point `Mtx`, and why the port keeps both. *Course link:*
   ch19 matrix stacks, `perspective.rst`; gacalc `to_matrix`.
3. **`transformations.md`** — `math_util.c`: `mtxf_translate:186`,
   `mtxf_rotate_zxy_and_translate:279`, `mtxf_rotate_xyz_and_translate:313`,
   `mtxf_scale_vec3f:550`; geo matrix-stack application in
   `src/game/rendering_graph_node.c` driven by `src/engine/geo_layout.c`.
   *Teaching angle:* translate/rotate/scale COMPOSED down a geo tree —
   the running-engine form of the course's transform-composition chapters.
   *Course link:* ch08-09, ch16 (lambda stack).
4. **`rotation-euler-vs-rotors.md`** — THE comparison doc (maintainer
   explicitly wants it). SM64: 16-bit fixed-point Euler "binary angles"
   (bams), sine/cosine LUT (`math_util.c` sin/cos tables + `atan2s`),
   fixed-axis-order construction (`mtxf_rotate_zxy_*`/`xyz_*`). Contrast
   with the course's half-angle GA rotors + sandwich product
   (`modelviewprojection` ch07 `:326-329`, ch14; gacalc rotors,
   `unit-bivector-and-rotors.md`). Cover: same SO(3) rotation; Euler
   order-dependence & gimbal vs. coordinate-free rotor composition; how
   each interpolates (angle lerp + gimbal wobble vs. rotor slerp); why a
   30 Hz console used LUT Euler angles. This doc is the set's showpiece —
   give it room.

## Verification & done-state

Each anchor resolves at the pin; each doc has the banner + a "How this
relates to the course" section; the rotation doc names the specific
course chapters and states the agreement/difference/interpolation
contrast explicitly. Note candidate `doc-region` spans for the later
Sphinx pass. Stage the four docs; archive this step on completion.
