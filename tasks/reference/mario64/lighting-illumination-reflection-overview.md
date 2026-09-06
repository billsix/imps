# Orientation (L1): Lighting in SM64 — the mental model

> **Provenance:** Ghostship pin `49c5312a` / LUS `c151cc91`, 2026-09-06.
> **L1** (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in
> [`lighting-illumination-reflection.md`](lighting-illumination-reflection.md).

The maintainer's course says plainly that it does not do lighting — objects
are drawn in flat colors, with no attempt at realism. SM64 does light its
world, and it does so in the simplest way that still looks like light, which
makes it the ideal first example of the topic the course skips.

The whole idea rests on one quantity: a surface's **normal**, the little
arrow that says which way the surface faces. A light also has a direction.
If a surface faces straight into the light, it is bright; if it faces away,
it is dark; in between, it is somewhere in between. That "somewhere in
between" is just how closely the two arrows agree — a single number you get
by comparing the surface normal with the light direction. Multiply the
light's color by that number, add a little baseline "ambient" so shadows
aren't pure black, and you have the color of that spot on the surface. That
is diffuse lighting, and it is essentially all SM64 does.

Two details give SM64 lighting its particular character. First, it is
computed **at the corners** of each triangle, not at every pixel. The corner
colors are then smoothly blended across the triangle's face. This is cheap
and looks fine on small triangles, but on the big flat polygons of a 1996
game it can look a little soft and can miss a highlight that falls in the
middle of a face. (The modern alternative the course would build toward
computes lighting at every pixel instead — more expensive, more accurate.)
Second, once a corner's lit color is computed, the rest of the pipeline
treats it as just another **input to mix** with the textures — the lighting
is "baked in" early and the later shading stage only blends it with the
texture and tints. Lighting and mixing are two separate jobs.

SM64 has no true reflections, but it fakes the *look* of shininess two ways
worth naming. It can address a texture by the surface's facing direction
instead of the usual texture coordinates, so the surface appears to mirror a
fixed backdrop as it turns — this is what makes the castle's paintings
shimmer. And it draws simple dark blobs on the ground beneath objects to
stand in for shadows. Neither is physically computed; both are inexpensive
tricks that read as "reflective" and "grounded" to the eye.

So lighting here is: compare each surface corner's facing to the light, tint
by the result, blend across the triangle, and hand the lit color on to be
mixed with textures. That short sentence is the entire lighting model the
course omits — and seeing it is what makes the more advanced per-pixel models
legible later.
