=======================
The camera as a system
=======================

In *Model View Projection* the camera is a matrix: you learned that the view
transform is the inverse of placing the camera, and that moving the camera
means changing that placement. That is exactly right, and Super Mario 64 agrees
— the view matrix is one line. The interesting part, the part a course never
reaches, is everything that *decides* where the camera should be.

The easy part: one look-at
==========================

When the renderer reaches the camera node, all the real work has already
happened. It just reads the camera's position, focus, and roll, builds the view
transform, and composes it onto the matrix stack like any other node:

.. literalinclude:: ../../Ghostship/src/game/rendering_graph_node.c
   :language: c
   :start-after: // doc-region-begin camera_view_matrix
   :end-before: // doc-region-end camera_view_matrix
   :caption: geo_process_camera — the view matrix is the easy part

``mtxf_lookat`` is the "camera space = inverse of placing the camera" transform
you already know. Everything below is about where ``pos`` and ``focus`` came
from.

The hard part: a character named Lakitu
=======================================

Mario 64 personifies its camera as Lakitu, a cameraman with **state**. He has a
*goal* — where he would like to be — and a *current* position, and each frame he
**eases** from current toward goal instead of snapping. That deliberate lag is
why the camera feels weighty rather than glued to Mario. So the camera is not a
matrix you set; it is a little controller you *run* every frame, whose output is
the ``pos``/``focus`` the code above consumes.

Behind Lakitu is a menu of **modes** — a different rule for computing the goal
in different situations:

.. literalinclude:: ../../Ghostship/src/game/camera.h
   :language: c
   :start-after: // doc-region-begin camera_modes
   :end-before: // doc-region-end camera_modes
   :caption: camera modes — one interface, many controllers

Switching modes does not cut abruptly; the camera **blends** from the old mode's
answer to the new one's over a set number of frames. And the whole controller is
**collision-aware**: it asks the same surface-collision system Mario uses ("is
there a ceiling here? a floor there?") and pulls itself in so it never clips
through walls.

.. graphviz::

   digraph camera {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     mario [label="Mario state\n+ level"];
     mode  [label="current mode\n(radial, C-up, …)"];
     goal  [label="goal\npos / focus"];
     coll  [label="collision\n(find_ceil/floor)"];
     ease  [label="Lakitu eases\ncurrent → goal"];
     look  [label="mtxf_lookat\n(view matrix)"];
     mario -> mode -> goal -> ease -> look;
     coll -> ease [label="pull in"];
   }

So "camera management" in a real game is four things your course leaves out: a
smoothed follower, a set of behavioral modes, blended transitions, and
collision-aware placement. The view matrix you already understand is only the
trivial last step.

.. admonition:: Go deeper
   :class: seealso

   Modes, easing, and the collision coupling in full:
   ``tasks/reference/mario64/camera-system.md`` and its one-page mental model
   ``camera-system-overview.md``. Collision itself gets its own chapter later.
