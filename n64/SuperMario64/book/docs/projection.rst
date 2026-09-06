==================================
Projection and field of view
==================================

Perspective projection is the one piece of the pipeline *Model View
Projection* derives in full — the frustum, the field of view, the perspective
divide. Super Mario 64 builds the same matrix, so this is mostly familiar
ground, with two things your course did **not** cover: an orthographic
projection, and a field of view that is a live, animated signal.

Perspective — the matrix you already derived
============================================

When the renderer reaches a perspective node it calls the N64's
``gluPerspective`` analogue with a field of view, an aspect ratio, and near/far
planes:

.. literalinclude:: ../../Ghostship/src/game/rendering_graph_node.c
   :language: c
   :start-after: // doc-region-begin guPerspective_setup
   :end-before: // doc-region-end guPerspective_setup
   :caption: geo_process_perspective — the frustum you know, in fixed point

It is the exact construction from your book, built in the fixed-point form the
renderer wants (see :doc:`engine-math`), with one console wrinkle: the
``gSPPerspNormalize`` scalar keeps the fixed-point W-values in range — a detail
with no analogue on a modern GPU.

Orthographic — the projection your course names but never builds
================================================================

Your book mentions orthographic projection and then says implementing it would
take too much code, so it never does. A real game needs it for every HUD
element and menu — anything 2D, drawn without perspective so pixels map one to
one. Here it is, live:

.. literalinclude:: ../../Ghostship/src/game/rendering_graph_node.c
   :language: c
   :start-after: // doc-region-begin guOrtho_hud
   :end-before: // doc-region-end guOrtho_hud
   :caption: geo_process_ortho_projection — the HUD's projection

So in a single frame the world draws under perspective and the HUD draws under
orthographic. This is the worked orthographic example your course left as an
exercise.

Field of view is a signal, not a constant
==========================================

In your book the field of view is a fixed number you pick once. Mario 64 treats
it as a live value: a base FOV (45°) plus an offset plus a **shake** the game
drives for impact — a landing thump, taking damage, a cutscene punch. The FOV
handed to ``guPerspective`` each frame is ``base + offset + shake(phase)``,
which is why a big impact makes the whole world seem to lurch. A parameter you
thought was constant is actually animated.

.. admonition:: Go deeper
   :class: seealso

   The FOV-shake system and the fixed-point projection details:
   ``tasks/reference/mario64/field-of-view-and-projection.md``. Note that
   ``geometricalgebra`` deliberately stops right *before* this step — its
   ``to_matrix`` refuses the non-linear perspective divide — so this chapter is
   exactly the stage past where that library can go.
