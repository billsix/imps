==================================
Rotation: Euler angles, not rotors
==================================

In *Model View Projection* you rotate things with a **rotor**: you name the
plane you want to turn in, and how much, and apply it with a sandwich product.
Rotors compose cleanly, never gimbal-lock, and interpolate along the shortest
arc. They are the right default.

Super Mario 64 does something completely different, and seeing why is the best
possible warm-up for reading a real engine. It stores an orientation as **three
integers** — an angle about X, about Y, about Z — and turns them into a
rotation matrix with a lookup table. No rotor, no bivector, not even radians.

Binary angles
=============

The first surprise is the unit. A full turn is not :math:`2\pi`; it is the
integer ``0x10000`` (65536). Because an angle is stored in 16 bits, adding to
it **wraps around the circle for free** — there is no "keep it in range" step,
because the counter *is* the circle:

.. code-block:: text

              0x0000  (0°)
                 |
      0xC000 ----+---- 0x4000        a quarter turn = 0x4000 (90°)
      (270°)     |     (90°)
              0x8000  (180°)

      add past 0xFFFF and it wraps back to 0x0000, automatically

Sine and cosine come from a table, not a function call. ``sins(x)`` is just an
array read, and cosine is the *same* table read a quarter-turn later.

From three angles to a matrix
=============================

Here is the real function that turns the three angles (plus a translation) into
a 4×4 matrix. It is pulled straight from the game's source:

.. literalinclude:: ../../Ghostship/src/engine/math_util.c
   :language: c
   :start-after: // doc-region-begin euler_zxy_to_matrix
   :end-before: // doc-region-end euler_zxy_to_matrix
   :caption: mtxf_rotate_zxy_and_translate — src/engine/math_util.c

Read the nine matrix entries: they are the product of three separate axis
rotations, multiplied out by hand, in a **fixed order** (here Z, then X, then
Y). The order is baked into the function's name. (The matrix it fills uses the
engine's transposed, translation-in-the-last-row layout — see :doc:`engine-math`.) That fixed order is exactly
what a rotor avoids — and it is why this scheme can *gimbal-lock*, losing a
degree of freedom when two axes line up.

.. admonition:: Try breaking it
   :class: caution

   In the matrix builder, force the Y-axis terms flat: set ``sy`` to ``0`` and
   ``cy`` to ``1`` (as if the Y angle were always zero). Rebuild and run.
   Objects can no longer turn left or right — Mario slides where he is going
   but never *faces* it, frozen looking one direction. You have deleted one of
   the three axes of rotation by hand, and you can see exactly which freedom it
   was.

The pipeline, at a glance:

.. graphviz::

   digraph rotation {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     angles [label="3 × s16\nEuler angles"];
     lut    [label="sine / cosine\nlookup table"];
     matrix [label="4×4 rotation\nmatrix"];
     angles -> lut [label="sins/coss"];
     lut -> matrix [label="hand-multiplied\nZ·X·Y"];
   }

Why would anyone do this?
=========================

Because in 1996 the trade paid off. Three ``s16`` angles are six bytes; a rotor
is sixteen. Integer angles never drift the way a float rotor slowly denormalizes.
And pulling a facing *out* of a direction — "which way should I aim?" — is a
single table lookup, which is why cameras and aiming code love it.

The price is real: a fixed axis order, gimbal lock, and interpolation that can
wobble. Mario 64 simply designs around all three (its objects rarely tumble
freely). Your rotor pays none of those costs — which is precisely why the
course teaches it as the default once you are *not* squeezed into six bytes.

.. admonition:: Go deeper
   :class: seealso

   The exhaustive version — the lookup-table memory trick, angle extraction
   with ``atan2s``, and the full rotor-vs-Euler comparison table — is in the
   reference note ``tasks/reference/mario64/rotation-euler-vs-rotors.md`` and
   its one-page orientation ``…-overview.md``. The sine-table packing trick has
   its own short appendix, :doc:`appendix-binary-angles`.
