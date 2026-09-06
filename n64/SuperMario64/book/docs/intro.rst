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

Each chapter takes one topic, shows the real code, and compares it to how you
already think about the subject:

- **Rotation** — the same rotation you build with a rotor, done with three
  integer Euler angles and a lookup table (this chapter).
- Transforms, the matrix stack, and the scene graph.
- The graphics pipeline: from an N64 display list to a modern GPU.
- Lighting, textures, the color combiner, and generated shaders.
- Cameras, animation, collision, and the effects that give a world life.

Where a chapter glosses over something, a later chapter or an appendix carries
the detail. The margin notes point at the reference material in the imps
``tasks/reference/mario64/`` set, which is where the exhaustive version lives.

.. note::

   The code you see is the actual Ghostship source at a pinned commit. The
   snippets are named regions inside that source, so when the game's code
   moves around, the book still pulls the right lines.
