=====================================
Smooth motion from choppy logic
=====================================

Super Mario 64's game logic runs at a fixed **30 steps per second**. Modern
screens want 60, 120, or more. The port bridges that gap with a trick you have
already glimpsed in the :doc:`pipeline` chapter, and it is elegant enough to
deserve its own.

Do not run the game faster — draw it more
=========================================

The obvious idea — run the game logic faster — is wrong: it would change how the
game *plays*. Instead the port keeps the game at 30 steps per second and draws
the **same** frame several times, each time nudging everything a little further
along between where it was last step and where it is this step.

Concretely, as the game builds a frame it **records** every matrix it produces.
It keeps this step's set and last step's set. To draw an in-between frame, it
blends each matrix part-way between the two — a quarter of the way, half, three
quarters — and replays the frame's drawing commands with the blended matrices.
That replay loop is the ``ProcessGfxCommands`` you saw in the pipeline chapter.

.. graphviz::

   digraph interp {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     prev [label="last step's\nmatrices"];
     cur  [label="this step's\nmatrices"];
     lerp [label="blend at t = ¼, ½, ¾, 1"];
     draw [label="replay the frame\nwith blended matrices"];
     prev -> lerp; cur -> lerp; lerp -> draw;
   }

Because the blending happens at the **matrix** level, everything moves smoothly
at once — objects, the camera, animated joints — without the game logic ticking
any faster. It is why a 1996 game runs buttery-smooth on a modern display while
still playing exactly as it did on the console. (Sound, tied to the game step,
is deliberately left alone.)

.. admonition:: Go deeper
   :class: seealso

   The full mechanism — how matrices are matched across frames by identity — is
   the most detailed note in the set:
   ``tasks/reference/mario64/frame-interpolation.md``.
