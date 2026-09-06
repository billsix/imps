=========
Lighting
=========

*Model View Projection* says it plainly: it does not do lighting. Objects are
flat colors, with no attempt at realism. That makes lighting the single biggest
thing this book adds — and Super Mario 64 does it in the simplest way that still
reads as light, which is exactly what makes it a good first example.

One number: how much a surface faces the light
===============================================

Every surface has a **normal** — the direction it faces. Every light has a
direction. How lit a spot is comes down to how closely those two agree: face the
light, bright; face away, dark. That "how closely" is a single number you get by
comparing the two directions, and multiplying the light's color by it (plus a
little baseline "ambient" so shadows are not pure black) gives the surface color.
That is diffuse lighting, and it is essentially all SM64 does.

To compare a light against a surface, the light's direction first has to be put
into the surface's frame:

.. literalinclude:: ../../Ghostship/libultraship/src/fast/interpreter.cpp
   :language: c
   :start-after: // doc-region-begin light_dir_to_normal_space
   :end-before: // doc-region-end light_dir_to_normal_space
   :caption: CalculateNormalDir — prepare a light for the vertices

Lit at the corners, blended across
==================================

Two facts give SM64 lighting its character. It is computed **per vertex** — at
the corners of each triangle — and blended smoothly across the face (Gouraud
shading), which is cheap but can look soft on the big flat polygons of a 1996
game. And the lit color is computed **early**, in the vertex stage, then handed
to the shader as the ``vShade`` input you met in :doc:`shaders` — so the shader
only *mixes* the pre-computed lit color with textures. Lighting and mixing are
two separate jobs. (The modern alternative your course would build toward lights
every pixel instead — Phong — which is more expensive and more accurate.)

.. graphviz::

   digraph light {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     n [label="vertex normal"];
     l [label="light dir + color"];
     d [label="dot(normal, light)\n+ ambient"];
     s [label="vShade\n(lit vertex color)"];
     m [label="combiner mixes\nvShade × texture"];
     n -> d; l -> d; d -> s -> m;
   }

Reflection without reflections
==============================

SM64 has no true reflections but fakes the look two cheap ways. It can address a
texture by a surface's *facing direction* instead of its coordinates, so the
surface seems to mirror a fixed backdrop as it turns — this is the shimmer on
the castle paintings. And it draws simple dark blobs under objects to stand in
for shadows. Neither is physically computed; both read as "reflective" and
"grounded" to the eye.

.. admonition:: Go deeper
   :class: seealso

   Diffuse vs Phong, env-mapping, and shadows in full:
   ``tasks/reference/mario64/lighting-illumination-reflection.md`` and its
   one-page mental model ``lighting-illumination-reflection-overview.md``.
