=====================================
Effects: skybox, water, and paintings
=====================================

A few of Super Mario 64's most memorable touches — the sky, flowing water, the
rippling castle paintings — are worth a chapter because the tricks behind them
are so much cheaper than they look. That is a lesson in itself: games fake
realism, and knowing the fake is as valuable as any formula.

The sky is a flat backdrop, scrolled by turning
================================================

The sky is **not** a cube around the world. It is a flat image, drawn behind
everything, scrolled sideways by how far the camera has turned. One line does the
scroll — the camera's yaw becomes a horizontal offset into the image:

.. literalinclude:: ../../Ghostship/src/game/skybox.c
   :language: c
   :start-after: // doc-region-begin skybox_yaw_scroll
   :end-before: // doc-region-end skybox_yaw_scroll
   :caption: calculate_skybox_scaled_x — turning becomes scrolling

Only the yaw matters — not position, not pitch — which is exactly why the sky
reads as infinitely far away.

Water animates its texture, not its geometry
============================================

Water (and sand, and mist) is flat, translucent geometry whose **texture
coordinates scroll** every frame. The mesh never moves; only which part of the
texture it samples changes, which is the cheapest possible way to animate a
surface. The see-through, slightly-bent look is just translucency plus that
scroll plus the world showing through — there is no refraction, no reflection of
the scene.

The paintings move their actual vertices
========================================

The rippling paintings are the opposite trick: the game moves the painting's
**mesh vertices** on the CPU each frame, by a traveling wave that spreads out
from where Mario entered:

.. literalinclude:: ../../Ghostship/src/game/paintings.c
   :language: c
   :start-after: // doc-region-begin ripple_traveling_wave
   :end-before: // doc-region-end ripple_traveling_wave
   :caption: calculate_ripple_at_point — a cosine wave that travels outward

The subtle part is what comes after: having moved the vertices, the game
**recomputes the surface normals**, so the environment-mapped shimmer
(:doc:`lighting`) slides across the painting as it undulates. Move the geometry
and the lighting goes stale unless you move the normals too. Water scrolls a
texture; paintings deform vertices — two animation strategies for two looks.

.. admonition:: Go deeper
   :class: seealso

   ``tasks/reference/mario64/skyboxes.md``, ``water-and-moving-textures.md``,
   ``painting-wobble.md``, and ``transparency-and-blending.md``.
