=====================
Objects and behaviors
=====================

The last chapter showed Mario welded into the engine's C. So a fair question:
are the *enemies* the same — is a Goomba, a Bob-omb, a Koopa also hundreds of
lines of bespoke code? Mostly **no**, and the difference is one of the most
important ideas in game architecture: enemies run through a shared **object and
behavior system**, so each one is largely *configured* rather than *coded*.

A behavior is a little program
==============================

Every ordinary object has a **behavior script** — bytecode, run by a small
virtual machine each frame. Here is the Goomba's, straight from the data:

.. literalinclude:: ../../Ghostship/data/behavior_data.c
   :language: c
   :start-after: // doc-region-begin goomba_behavior_script
   :end-before: // doc-region-end goomba_behavior_script
   :caption: bhvGoomba — a Goomba, mostly as data

Read what is **data** here: which update list the object joins, its flags, its
**physics** (gravity ``-400``, friction, bounciness — plain numbers you could
tune without a compiler), and which animations to load. The script drops the
Goomba to the floor, sets its home, loads its animations, and then loops one
thing: ``CALL_NATIVE(bhv_goomba_update)``. Most of the Goomba is a table of
settings; only its per-tick logic is a C call.

The native loop mostly calls shared helpers
============================================

That C loop, ``bhv_goomba_update``, is hand-written — but look at what it does:
``obj_update_standard_actions``, ``cur_obj_update_floor_and_walls``,
``cur_obj_init_animation_with_accel_and_sound``, ``obj_handle_attacks``. These
are **shared** helpers from a big common library (``object_helpers.c``) that
every enemy reuses — movement, collision, animation, attack handling. Only the
Goomba's *specific* actions (walk, get-attacked, jump) are its own code, and
even those lean on the shared toolbox.

.. graphviz::

   digraph obj {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     script [label="behavior script\n(data: list, flags,\nphysics, anims)"];
     vm     [label="behavior VM\nruns it each frame"];
     native [label="CALL_NATIVE\nbhv_goomba_update"];
     helpers[label="shared helpers\n(cur_obj_move, collision,\nanimation, attacks)"];
     script -> vm -> native -> helpers;
   }

Where each character sits
=========================

So the spectrum, from configured to coded:

- **Ordinary enemy** (Goomba, Bob-omb, Koopa) — a behavior script of settings,
  plus a short native loop that mostly calls shared helpers. A new simple enemy
  is often *assembled* from script commands and existing helpers. Semi-data-
  driven.
- **Boss** (Bowser, King Bob-omb) — the same system, but with large, elaborate
  native code for phases and cutscenes. The bespoke end.
- **Mario** — outside the system entirely: his own state struct, special-cased
  in the object loop, an action machine that *is* the code
  (:doc:`hardcoded`).

There are **533** behavior scripts in the game, and they share one behavior VM
and one helper library. That is how a small team shipped dozens of distinct
creatures without writing each from scratch — the 1996 ancestor of a modern
engine's components and prefabs.

.. admonition:: Try breaking it
   :class: caution

   In ``bhvGoomba``, change the gravity argument in ``SET_OBJ_PHYSICS`` from
   ``-400`` to something small like ``-50``. Rebuild and find a Goomba: it now
   drifts and floats, barely pulled down. You just retuned an enemy's physics by
   editing **one number of data** — no C, no recompiling gameplay logic. That is
   the whole point of the behavior script.

.. admonition:: Go deeper
   :class: seealso

   The behavior VM, the command set, and the shared helper library:
   ``tasks/reference/mario64/object-and-behavior-system.md`` and
   ``hardcoded-vs-data-driven.md``.
