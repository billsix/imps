============
Introduction
============

You already know, from *Model View Projection*, how to place a point in the
world and get it onto the screen: build a model transform, a view transform,
and a projection, compose them, and hand the result to the GPU. You learned
rotation the clean way — as a geometric-algebra rotor.

This book picks up exactly there and asks a different question: **what does a
real game actually do?** The answer is both reassuring and surprising. The
math you learned is all present — but a shipping console game from 1996 made
very different engineering choices than a from-scratch teaching renderer, and
it also does a dozen things your course never covered.

The plan
========

The book follows a real **frame** — from the game's logic to the pixels on
screen — as its spine. One central chapter, :doc:`pipeline`, walks that whole
path at arm's length as a **black box**; from it, links open each stage into a
**white-box** chapter that shows the actual code. Read straight through, or
follow the frame and click into whichever box you want opened.

Three parts:

- **Part I — from your math to a real engine.** Rotation (this chapter), the
  engine's matrices and scene graph, the camera as a system, and projection.
- **Part II — the graphics pipeline.** One frame's journey end to end
  (:doc:`pipeline`), then the color combiner and generated shaders, textures,
  and lighting.
- **Part III — making a world feel alive.** Animation, collision, the effects
  that sell a place (skybox, water, the rippling paintings), the smooth-motion
  trick, and sound.

Five appendices carry the deepest detail. Every **"Go deeper" box** at the end
of a chapter points at the exhaustive per-topic reference note in the imps
``tasks/reference/mario64/`` set, which is where the whole story lives.

.. note::

   The code you see is the actual Ghostship source at a pinned commit. The
   snippets are named regions inside that source, so when the game's code
   moves around, the book still pulls the right lines.
