=========================================
The engine's math: matrices and the scene
=========================================

You arrived here fluent in vectors, matrices, and composing transforms. A real
engine uses all of it — but stores it differently and organizes it into a data
structure your course never needed. This chapter recasts the familiar math in
the engine's terms so the pipeline chapters have solid ground. We gloss the
fiddly parts; the appendices carry the depth.

Matrices, stored two ways and transposed
=========================================

Two surprises about a matrix in Super Mario 64. First, it lives in **two
forms**: an ordinary float 4×4 while the engine does math, and a **fixed-point**
form (integer + fraction) that the renderer actually draws with. The float one
is converted to the fixed-point one just before drawing. (Why fixed point? It
is the format the original N64 hardware used; Appendix A has the bridge.)

Second, and more important for reading the code: the layout is the **transpose**
of what you learned. Your course (and OpenGL) put translation in the last
**column** and transform a point as ``M · v``. Mario 64 puts translation in the
last **row** and treats a point as a **row vector**, ``v · M``:

.. code-block:: text

    your course / OpenGL          Super Mario 64
    ┌ r r r tx ┐                  ┌ r r r 0 ┐
    │ r r r ty │                  │ r r r 0 │
    │ r r r tz │                  │ r r r 0 │
    └ 0 0 0 1  ┘                  └ tx ty tz 1 ┘   ← translation in the last ROW

You can see the convention directly in the multiply. Notice it only ever fills
a 3×3 rotation plus a translation **row**, and stamps the last column as "no
projection here":

.. literalinclude:: ../../Ghostship/src/engine/math_util.c
   :language: c
   :start-after: // doc-region-begin mtxf_mul_affine
   :end-before: // doc-region-end mtxf_mul_affine
   :caption: mtxf_mul — src/engine/math_util.c

The same rotation and translation you know, laid out mirror-image. A model
matrix you build the course's way would simply need transposing to feed this.

Composition happens on a tree
=============================

In your course you placed a handful of objects by hand: push a transform, draw,
pop. A whole game level has hundreds of nested pieces, so the engine organizes
the scene as a **tree** and composes transforms by walking it. Each node builds
its local transform and multiplies it onto its parent's, depth-first:

.. literalinclude:: ../../Ghostship/src/game/rendering_graph_node.c
   :language: c
   :start-after: // doc-region-begin compose_local_onto_parent
   :end-before: // doc-region-end compose_local_onto_parent
   :caption: geo_process_translation_rotation — one node composing onto its parent

Read the shape: build ``mtxf`` (this node's transform), multiply ``local ·
parent`` onto the next stack slot, push, make the fixed-point twin the renderer
will draw with, recurse into children, pop. That is your "stack of composed
transforms" from *Model View Projection*, made concrete over a whole scene —
one matrix multiply per node, thousands per frame.

.. graphviz::

   digraph scene {
     node [shape=box, fontname="sans-serif"];
     root  [label="root"];
     cam   [label="camera\n(view transform)"];
     persp [label="perspective"];
     mario [label="Mario\n(transform)"];
     body  [label="body geometry"];
     hat   [label="hat\n(transform)"];
     hatg  [label="hat geometry"];
     root -> cam -> persp -> mario;
     mario -> body;
     mario -> hat -> hatg;
   }

Because the walk follows the tree's nesting, a child inherits its parent's
frame automatically — the hat rides on the head because it hangs beneath it in
the tree. Everything later in this book — cameras, projection, lighting, draw
order — is one kind of node, or one thing that happens during this walk.

.. admonition:: Go deeper
   :class: seealso

   The float↔fixed-point bridge is **Appendix A**. Why vectors are bare mutable
   arrays with a ``dest``-first convention (and why there is no named dot
   product) is in ``tasks/reference/mario64/vectors-and-vector-math.md``; the
   full matrix and scene-graph notes are ``matrices-and-linear-algebra.md`` and
   ``scene-graph-and-data-structures.md``.
