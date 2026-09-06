# Reference: topics that are ABSENT in Ghostship (don't go hunting)

> **Provenance:** Ghostship pin `49c5312a`, libultraship submodule
> `c151cc91` (1.3.1-544 fork), authored 2026-09-06. Part of the mario64
> graphics set — see [`README.md`](README.md).

Two graphics topics a reader might expect are **genuinely not implemented
here.** Documented so nobody wastes time searching, per the maintainer's
reference-authoring rule (state what is absent, with the check that proves
it).

## Ray tracing — ABSENT

There is **no RT64 / path tracer** in this libultraship fork. `grep -ri
rt64 Ghostship/libultraship/src/fast/` returns nothing. The Fast3D
renderer is a classic rasterizer: it translates N64 display lists to
triangles and hands them to a GL/Vulkan/DX11/Metal backend
(`libultraship/src/fast/interpreter.cpp` `DrawTriangles:146`), with no
ray/visibility pass anywhere.

**What people mean by "RT64 mipmapping"** is the fork's automatic
mipmap generation plus trilinear sampling — a texture-quality feature, not
ray tracing: `interpreter.cpp` `UploadMipChain:1950` builds the mip chain,
and Vulkan's `gfx_vulkan.cpp` `GetSampler(..., bool autoMipmap):532`
selects the trilinear sampler. See `sampling-and-mipmapping.md`. The name
is a red herring inherited from the RT64 renderer project; this fork does
not include RT64's ray-traced path.

## Implicit modeling (SDF / metaballs) — ABSENT

No signed-distance-field, metaball, marching-cubes, or implicit-surface
code exists in the decomp, the port, or libultraship. All geometry is
explicit polygonal meshes delivered as N64 display lists (see
`scene-graph-and-data-structures.md`). Curved-looking surfaces (hills,
Mario himself) are low-poly meshes, not implicit surfaces; the only
curve math present is piecewise camera splines (`curves-and-splines.md`).

## How this relates to the course

Neither course covers ray tracing or implicit modeling either, so there is
no gap to fill — the value here is purely negative knowledge: if you came
looking for a ray tracer or an SDF because the fork is "modern," stop, it
isn't here.
